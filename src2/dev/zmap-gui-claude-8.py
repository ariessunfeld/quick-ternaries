import sys
import os
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import plotly.graph_objects as go
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QHBoxLayout, QDialog, QLabel
)
from PySide6.QtCore import QUrl, QObject, Slot, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineScript

# ---------------------------------------------------------
# Handler exposed via QWebChannel to receive JS callbacks.
# ---------------------------------------------------------
class PlotHandler(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @Slot(str, str, str)
    def cellDoubleClicked(self, facies, target, other):
        print(f"Double clicked cell: facies={facies}, target={target}, other={other}")
        self.main_window.generate_scatter_plot(facies, target, other)
    
    @Slot(str)
    def debugLog(self, message):
        print(f"JS Debug: {message}")

# ---------------------------------------------------------
# Main application window.
# ---------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Correlation Heatmap Viewer")
        self.resize(1000, 800)

        # Initialize file path and plot list.
        self.csv_path = None
        self.heatmap_files = []
        self.current_index = 0
        self.current_target = None  # Store the current target element
        
        # Store element and facies data for plots
        self.plot_data = {}  # Will store {target: {elements: [...], facies: [...]}}
        
        # Store DataFrame for reuse
        self.df = None
        self.facies_types = {}  # Track original data types

        # Main widget and layout.
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top control buttons.
        btn_layout = QHBoxLayout()
        self.btnBrowse = QPushButton("Browse CSV")
        self.btnGenerate = QPushButton("Generate Plots")
        self.btnPrev = QPushButton("Prev")
        self.btnNext = QPushButton("Next")
        btn_layout.addWidget(self.btnBrowse)
        btn_layout.addWidget(self.btnGenerate)
        btn_layout.addWidget(self.btnPrev)
        btn_layout.addWidget(self.btnNext)
        main_layout.addLayout(btn_layout)

        # Status label
        self.statusLabel = QLabel("No plot loaded")
        main_layout.addWidget(self.statusLabel)

        # QWebEngineView for displaying the plots.
        self.webView = QWebEngineView()
        
        # Configure WebEngine settings to allow JavaScript and external content
        settings = self.webView.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        main_layout.addWidget(self.webView)

        # Connect signals.
        self.btnBrowse.clicked.connect(self.browse_file)
        self.btnGenerate.clicked.connect(self.generate_plots)
        self.btnPrev.clicked.connect(self.prev_plot)
        self.btnNext.clicked.connect(self.next_plot)

        # Set up QWebChannel for communication from JS.
        self.channel = QWebChannel()
        self.handler = PlotHandler(self)
        self.channel.registerObject("pyHandler", self.handler)
        self.webView.page().setWebChannel(self.channel)
        
        # Connect loadFinished signal to inject JavaScript
        self.webView.loadFinished.connect(self.on_load_finished)
        
        # Debug helper
        self.debug_timer = QTimer()
        self.debug_timer.timeout.connect(self.debug_check_js)
        self.debug_timer.setInterval(1000)  # Check every second

    def browse_file(self):
        # Let the user select a CSV file.
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.csv_path = file_name
            print(f"Selected CSV: {self.csv_path}")
            self.statusLabel.setText(f"Selected CSV: {os.path.basename(self.csv_path)}")

    def debug_check_js(self):
        """Periodically check the JavaScript environment"""
        self.webView.page().runJavaScript(
            """
            (function() {
                var debug = {
                    hasPlotly: typeof Plotly !== 'undefined',
                    hasPyHandler: typeof pyHandler !== 'undefined',
                    hasPlot: document.getElementById('plot') !== null,
                    documentReady: document.readyState
                };
                return JSON.stringify(debug);
            })();
            """, 
            QWebEngineScript.ScriptWorldId.MainWorld,
            lambda result: print(f"JS Debug Status: {result}")
        )

    def generate_plots(self):
        if not self.csv_path:
            print("No CSV file selected!")
            self.statusLabel.setText("Error: No CSV file selected!")
            return

        self.statusLabel.setText("Generating plots...")
        QApplication.processEvents()  # Update the UI

        # Hardcoded elements list.
        elements = ['SiO2', 'TiO2', 'Al2O3', 'FeOT', 'MgO', 'CaO', 'Na2O', 'K2O', 'MnO']

        # Read the CSV.
        self.df = pd.read_csv(self.csv_path)
        if 'Facies' not in self.df.columns:
            print("CSV must have a 'Facies' column.")
            self.statusLabel.setText("Error: CSV must have a 'Facies' column.")
            return

        # Store the type of the Facies column for later use
        self.facies_type = self.df['Facies'].dtype
        print(f"Facies column data type: {self.facies_type}")
        
        # Print sample values from the Facies column
        print(f"Sample facies values: {self.df['Facies'].head().tolist()}")
        
        # Get a mapping of facies values to their original python types
        self.facies_types = {str(facies): type(facies) for facies in self.df['Facies'].unique()}
        print(f"Facies value types: {self.facies_types}")

        # Get sorted facies values.
        facies_list = sorted(self.df['Facies'].unique())

        # Group the data by facies and compute pairwise Spearman correlations.
        correlations = {}
        pvals = {}
        for facies, group in self.df.groupby('Facies'):
            data = group[elements].dropna()
            corr_matrix, p_matrix = spearmanr(data)
            corr_df = pd.DataFrame(corr_matrix, index=elements, columns=elements)
            pval_df = pd.DataFrame(p_matrix, index=elements, columns=elements)
            correlations[facies] = corr_df
            pvals[facies] = pval_df

        # Ensure plots folder exists.
        plots_dir = "plots"
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)

        # Reset heatmap files list.
        self.heatmap_files = []
        self.plot_data = {}

        # Create one heatmap for each target element.
        for target in elements:
            other_elements = [e for e in elements if e != target]
            z_matrix = []
            customdata = []  # will hold [facies, otherElement] for each cell.
            for other in other_elements:
                row = []
                row_custom = []
                for facies in facies_list:
                    r = correlations[facies].loc[target, other]
                    p = pvals[facies].loc[target, other]
                    # Only display r if significant.
                    if p <= 0.05:
                        row.append(r)
                    else:
                        row.append(None)
                    row_custom.append([facies, other])
                z_matrix.append(row)
                customdata.append(row_custom)

            # Store plot data for JavaScript
            self.plot_data[target] = {
                'facies': facies_list,
                'elements': other_elements
            }

            # Build the heatmap figure.
            fig = go.Figure(data=go.Heatmap(
                z=z_matrix,
                x=facies_list,
                y=other_elements,
                customdata=customdata,
                colorscale='RdBu',  # cool-warm colorscale.
                zmin=-1,
                zmax=1,
                showscale=True,
                hoverongaps=False
            ))

            fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False)
            fig.update_xaxes(showgrid=False)
            fig.update_layout(
                title=f"Spearman's R: {target} vs Other Elements",
                xaxis_title="Facies",
                yaxis_title="Element",
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=50, r=50, t=50, b=50)
            )

            # Add QWebChannel script and plot metadata
            facies_js = json.dumps(facies_list, default=str)  # Convert all values to strings
            elements_js = json.dumps(other_elements)
            
            webchannel_js = """
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            // Plot metadata
            var TARGET_ELEMENT = "%s";
            var FACIES_LIST = %s;
            var OTHER_ELEMENTS = %s;
            
            // Set up web channel connection to Python
            var pyHandler;
            new QWebChannel(qt.webChannelTransport, function(channel) {
                pyHandler = channel.objects.pyHandler;
                console.log("QWebChannel established", pyHandler !== undefined);
                
                if (pyHandler) {
                    try {
                        pyHandler.debugLog("QWebChannel connected for " + TARGET_ELEMENT);
                    } catch (e) {
                        console.error("Error calling debugLog:", e);
                    }
                    
                    // Set up the click handler once QWebChannel is ready
                    document.addEventListener("DOMContentLoaded", setupClickHandler);
                    // Also try immediately in case DOM is already loaded
                    if (document.readyState === "complete") {
                        setupClickHandler();
                    }
                }
            });
            
            // Function to create a custom double-click handler
            function setupClickHandler() {
                if (!pyHandler) {
                    console.error("PyHandler not available");
                    setTimeout(setupClickHandler, 100);
                    return;
                }
                
                try {
                    pyHandler.debugLog("Setting up click handler");
                } catch (e) {
                    console.error("Error calling debugLog:", e);
                }
                
                // Get the plot div
                var plotDiv = document.getElementById('plot');
                if (!plotDiv) {
                    console.error("Plot div not found");
                    setTimeout(setupClickHandler, 100);
                    return;
                }
                
                // Wait for Plotly to be fully loaded
                var checkPlotly = function() {
                    if (typeof Plotly === 'undefined' || !plotDiv._fullLayout) {
                        setTimeout(checkPlotly, 50);
                        return;
                    }
                    
                    // Get plot layout info for coordinate conversion
                    var layout = plotDiv._fullLayout;
                    var xaxis = layout.xaxis;
                    var yaxis = layout.yaxis;
                    
                    // Get the actual plot area dimensions
                    var plotArea = {
                        left: layout.margin.l,
                        top: layout.margin.t,
                        width: layout.width - layout.margin.l - layout.margin.r,
                        height: layout.height - layout.margin.t - layout.margin.b
                    };
                    
                    pyHandler.debugLog("Plot area: " + JSON.stringify(plotArea));
                    
                    // Add a simple click handler to the plot
                    var lastClickTime = 0;
                    plotDiv.onclick = function(event) {
                        var currentTime = new Date().getTime();
                        var isDoubleClick = (currentTime - lastClickTime < 300);
                        lastClickTime = currentTime;
                        
                        if (!isDoubleClick) return; // Only process double-clicks
                        
                        try {
                            // Get mouse position relative to plot
                            var rect = plotDiv.getBoundingClientRect();
                            var x = event.clientX - rect.left;
                            var y = event.clientY - rect.top;
                            
                            pyHandler.debugLog("Click position: " + x + ", " + y);
                            
                            // Check if click is inside the actual plot area
                            if (x < plotArea.left || x > (plotArea.left + plotArea.width) ||
                                y < plotArea.top || y > (plotArea.top + plotArea.height)) {
                                pyHandler.debugLog("Click outside plot area");
                                return;
                            }
                            
                            // Convert to relative position within the plot area (0-1)
                            var relX = (x - plotArea.left) / plotArea.width;
                            var relY = (y - plotArea.top) / plotArea.height;
                            
                            // Convert to data indices
                            var faciesIndex = Math.floor(relX * FACIES_LIST.length);
                            var elementIndex = Math.floor(relY * OTHER_ELEMENTS.length);
                            
                            // Invert Y index (Plotly's Y axis goes from bottom to top)
                            elementIndex = OTHER_ELEMENTS.length - 1 - elementIndex;
                            
                            // Make sure indices are in bounds
                            faciesIndex = Math.min(Math.max(faciesIndex, 0), FACIES_LIST.length - 1);
                            elementIndex = Math.min(Math.max(elementIndex, 0), OTHER_ELEMENTS.length - 1);
                            
                            var facies = FACIES_LIST[faciesIndex];
                            var otherElement = OTHER_ELEMENTS[elementIndex];
                            
                            pyHandler.debugLog("Mapped to: facies=" + facies + 
                                               " (index " + faciesIndex + "), " +
                                               "element=" + otherElement +
                                               " (index " + elementIndex + ")");
                            
                            // Call Python handler
                            pyHandler.cellDoubleClicked(facies, TARGET_ELEMENT, otherElement);
                        } catch (e) {
                            pyHandler.debugLog("Error in click handler: " + e.toString());
                        }
                    };
                    
                    pyHandler.debugLog("Click handler installed");
                };
                
                checkPlotly();
            }
            </script>
            """ % (target, facies_js, elements_js)
            
            # Generate HTML with Plotly and add webchannel script
            html_str = fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot", config={"doubleClick": False})
            html_str = html_str.replace("</head>", webchannel_js + "\n</head>")
            
            # Write to file.
            file_path = os.path.join(plots_dir, f"heatmap_{target}.html")
            with open(file_path, "w") as f:
                f.write(html_str)
            self.heatmap_files.append((os.path.abspath(file_path), target))
            print(f"Generated plot for {target} at {file_path}")

        # After generating all plots, start with the first one.
        self.current_index = 0
        self.statusLabel.setText(f"Generated {len(self.heatmap_files)} plots")
        self.load_current_plot()
        
        # Start debug timer
        self.debug_timer.start()

    def on_load_finished(self, success):
        """Callback when a page is finished loading."""
        if not success:
            print("Page load failed")
            return
            
        print("Page loaded, checking JavaScript environment...")
        self.check_js_environment()
    
    def check_js_environment(self):
        """Check the JavaScript environment for necessary components"""
        self.webView.page().runJavaScript(
            """
            (function() {
                var debug = {
                    hasPlotly: typeof Plotly !== 'undefined',
                    hasPyHandler: typeof pyHandler !== 'undefined',
                    hasPlot: document.getElementById('plot') !== null,
                    documentReady: document.readyState
                };
                return JSON.stringify(debug);
            })();
            """, 
            QWebEngineScript.ScriptWorldId.MainWorld,
            self.on_js_environment_checked
        )
    
    def on_js_environment_checked(self, result):
        """Process the JavaScript environment check results"""
        print(f"JS Environment: {result}")

    def load_current_plot(self):
        if not self.heatmap_files:
            self.statusLabel.setText("No plots available")
            return
            
        file_path, target = self.heatmap_files[self.current_index]
        self.current_target = target
        
        url = QUrl.fromLocalFile(file_path)
        self.webView.setUrl(url)
        
        self.statusLabel.setText(f"Plot {self.current_index + 1}/{len(self.heatmap_files)}: {target}")
        print(f"Loading plot: {file_path} with target {target}")

    def next_plot(self):
        if not self.heatmap_files:
            return
        self.current_index = (self.current_index + 1) % len(self.heatmap_files)
        self.load_current_plot()

    def prev_plot(self):
        if not self.heatmap_files:
            return
        self.current_index = (self.current_index - 1) % len(self.heatmap_files)
        self.load_current_plot()

    def generate_scatter_plot(self, facies, target, other):
        """Generate a scatter plot (with best-fit line) for the given facies and element pair,
           then display it in a free-standing QDialog."""
        if not self.csv_path or self.df is None:
            print("No CSV data available")
            return

        print(f"Generating scatter plot for: facies={facies}, target={target}, other={other}")
        
        # Debug info about the facies value and type
        print(f"Received facies: '{facies}' of type {type(facies)}")
        
        # Try to convert the facies value to match the DataFrame's type
        # First, check if we have type info for this facies
        if self.facies_types:
            try:
                # Special handling for numeric types
                if self.facies_type == 'int64' or self.facies_type == 'float64':
                    facies_converted = float(facies) if '.' in facies else int(facies)
                else:
                    # For other types, use the string version
                    facies_converted = str(facies)
                
                print(f"Converted facies: '{facies_converted}' of type {type(facies_converted)}")
            except (ValueError, TypeError) as e:
                print(f"Error converting facies value: {e}")
                facies_converted = facies
        else:
            # Without specific type info, try all common conversions
            facies_converted = facies
            all_facies = self.df['Facies'].unique()
            print(f"All unique facies values: {all_facies}")
            
            # Try finding the facies in different formats
            if facies not in all_facies:
                # Try as int
                try:
                    if int(float(facies)) in all_facies:
                        facies_converted = int(float(facies))
                        print(f"Found match as int: {facies_converted}")
                except:
                    pass
                    
                # Try as float
                try:
                    if float(facies) in all_facies:
                        facies_converted = float(facies)
                        print(f"Found match as float: {facies_converted}")
                except:
                    pass
                    
                # Try as string if all else fails
                if str(facies) in [str(f) for f in all_facies]:
                    matching_facies = [f for f in all_facies if str(f) == str(facies)]
                    if matching_facies:
                        facies_converted = matching_facies[0]
                        print(f"Found match as string: {facies_converted}")

        # Filter the DataFrame
        df_f = self.df[self.df['Facies'] == facies_converted]
        
        # Check for empty result and try alternatives
        if df_f.empty:
            print(f"No data for facies: {facies_converted}")
            print(f"Trying alternative lookup methods...")
            
            # Try direct string comparison
            df_f = self.df[self.df['Facies'].astype(str) == str(facies)]
            if not df_f.empty:
                print(f"Found data using string comparison")
            else:
                print(f"No data found using any method")
                return

        # Get data for the two elements.
        try:
            x_data = df_f[target]
            y_data = df_f[other]
        except KeyError:
            print(f"Columns {target} and/or {other} not found in CSV.")
            return

        print(f"Found {len(x_data)} data points for plotting")
        
        # Compute the best fit line.
        coeffs = np.polyfit(x_data, y_data, 1)
        slope, intercept = coeffs
        x_line = np.array([x_data.min(), x_data.max()])
        y_line = slope * x_line + intercept

        # Compute correlation coefficient
        r_value = np.corrcoef(x_data, y_data)[0, 1]

        # Create scatter plot figure.
        scatter_fig = go.Figure()
        scatter_fig.add_trace(go.Scatter(
            x=x_data, y=y_data, mode='markers', name='Data'
        ))
        scatter_fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines', 
            name=f'Best Fit (r = {r_value:.3f})'
        ))
        scatter_fig.update_layout(
            title=f"Scatter: {target} vs {other} for Facies {facies_converted}",
            xaxis_title=target,
            yaxis_title=other,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Create and show the dialog
        scatter_dialog = self.create_scatter_dialog(scatter_fig, target, other, facies_converted)
        scatter_dialog.exec()

    def create_scatter_dialog(self, fig, target, other, facies):
        """Create a dialog with the scatter plot directly embedded."""
        scatter_dialog = QDialog(self)
        scatter_dialog.setWindowTitle(f"Scatter Plot: {target} vs {other} (Facies {facies})")
        scatter_dialog.resize(800, 600)
        layout = QVBoxLayout(scatter_dialog)
        
        # Add a label at the top
        info_label = QLabel(f"Scatter Plot: {target} vs {other} for Facies {facies}")
        layout.addWidget(info_label)
        
        # Create the QWebEngineView
        scatter_view = QWebEngineView()
        settings = scatter_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        layout.addWidget(scatter_view)
        
        # Generate HTML directly
        scatter_html = fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot")
        
        # Add debugging script to make sure we see if Plotly is loaded
        debug_script = """
        <script>
        console.log("Scatter plot HTML loaded");
        document.addEventListener("DOMContentLoaded", function() {
            console.log("DOM loaded for scatter plot");
            if (typeof Plotly !== 'undefined') {
                console.log("Plotly is available in scatter plot");
            } else {
                console.log("Plotly NOT available in scatter plot");
                // Try to load Plotly again
                var script = document.createElement('script');
                script.src = "https://cdn.plot.ly/plotly-latest.min.js";
                script.onload = function() {
                    console.log("Plotly loaded manually");
                };
                document.head.appendChild(script);
            }
        });
        </script>
        """
        
        scatter_html = scatter_html.replace("</head>", debug_script + "</head>")
        
        # Set the HTML directly instead of loading from a file
        scatter_view.setHtml(scatter_html)
        
        # Add a load finished handler
        scatter_view.loadFinished.connect(lambda ok: print(f"Scatter plot load finished: {'success' if ok else 'failed'}"))
        
        return scatter_dialog

# ---------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())