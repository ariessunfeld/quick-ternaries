import sys
import os
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import plotly.graph_objects as go

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
                    hasPyHandler: typeof window.pyHandler !== 'undefined',
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
        df = pd.read_csv(self.csv_path)
        if 'Facies' not in df.columns:
            print("CSV must have a 'Facies' column.")
            self.statusLabel.setText("Error: CSV must have a 'Facies' column.")
            return

        # Get sorted facies values.
        facies_list = sorted(df['Facies'].unique())

        # Group the data by facies and compute pairwise Spearman correlations.
        correlations = {}
        pvals = {}
        for facies, group in df.groupby('Facies'):
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

            # Add QWebChannel script reference
            webchannel_js = """
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            // Target element for this plot
            var TARGET_ELEMENT = "%s";
            
            // Set up web channel connection to Python
            document.addEventListener("DOMContentLoaded", function() {
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    window.pyHandler = channel.objects.pyHandler;
                    console.log("QWebChannel established:", window.pyHandler !== undefined);
                    
                    if (window.pyHandler) {
                        window.pyHandler.debugLog("QWebChannel connected, target: " + TARGET_ELEMENT);
                    } else {
                        console.error("Failed to connect to Python handler");
                    }
                    
                    setupDoubleClick();
                });
            });
            
            // We'll use a custom double-click implementation
            function setupDoubleClick() {
                var plotDiv = document.getElementById('plot');
                if (!plotDiv) {
                    console.error("Plot div not found");
                    setTimeout(setupDoubleClick, 100);
                    return;
                }
                
                window.pyHandler.debugLog("Plot div found, setting up manual click tracking");
                
                // Track clicks manually
                var lastClickTime = 0;
                var lastPoint = null;
                
                plotDiv.addEventListener('click', function(event) {
                    var currentTime = new Date().getTime();
                    
                    if (currentTime - lastClickTime < 300 && lastPoint) {
                        // This is a double-click
                        window.pyHandler.debugLog("Double-click detected at " + event.clientX + "," + event.clientY);
                        window.pyHandler.debugLog("Last point: " + JSON.stringify(lastPoint));
                        
                        if (lastPoint && lastPoint.customdata) {
                            var facies = lastPoint.customdata[0];
                            var otherElement = lastPoint.customdata[1];
                            window.pyHandler.debugLog("Double-clicked: " + facies + ", " + TARGET_ELEMENT + ", " + otherElement);
                            
                            if (window.pyHandler) {
                                window.pyHandler.cellDoubleClicked(facies, TARGET_ELEMENT, otherElement);
                            }
                        }
                        
                        // Reset to prevent triple-click
                        lastClickTime = 0;
                        lastPoint = null;
                        
                    } else {
                        // This is a first click
                        lastClickTime = currentTime;
                        
                        // We need to use Plotly's event handling to get the data point
                        if (typeof Plotly !== 'undefined') {
                            var plotlyDiv = document.getElementById('plot');
                            window.pyHandler.debugLog("Plotly is available");
                            
                            // Store the event for potential double-click
                            var pointInfo = null;
                            
                            try {
                                // Get Plotly points data at click position
                                var rect = plotlyDiv.getBoundingClientRect();
                                var x = event.clientX - rect.left;
                                var y = event.clientY - rect.top;
                                
                                // Use Plotly's hover API to find the data point
                                Plotly.Fx.hover('plot', [
                                    { xval: x, yval: y }
                                ]);
                                
                                // Get the hover data from the plot
                                var hoverData = document.querySelector('.hovertext');
                                if (hoverData) {
                                    window.pyHandler.debugLog("Hover data found: " + hoverData.textContent);
                                    
                                    // Extract data from the hover label
                                    // For now, we'll use this to determine if we're on a cell
                                    lastPoint = { hovering: true };
                                    
                                    // This is a simplification - in real code, you'd parse the hover text
                                    // to extract facies and other elements, or use the position to lookup
                                    // the data in your original matrix
                                    
                                    // For demo, we'll rely on click position - this is very crude
                                    // but demonstrates the principle
                                    var xaxis = plotlyDiv._fullLayout.xaxis;
                                    var yaxis = plotlyDiv._fullLayout.yaxis;
                                    
                                    var dataX = xaxis.p2d(x);
                                    var dataY = yaxis.p2d(y);
                                    
                                    window.pyHandler.debugLog("Data coordinates: " + dataX + ", " + dataY);
                                    
                                    // Now map these to your facies list and other_elements
                                    // This is placeholder code - you'll need to adapt to your data
                                    var faciesIndex = Math.floor(dataX);
                                    var elementIndex = Math.floor(dataY);
                                    
                                    // Custom data access attempt
                                    try {
                                        var plotData = plotlyDiv.data[0];
                                        if (plotData && plotData.customdata) {
                                            // Try to map to closest cell
                                            var cols = plotData.x.length;
                                            var rows = plotData.y.length;
                                            
                                            // Normalize to indices
                                            var colIdx = Math.min(Math.max(Math.round(faciesIndex), 0), cols-1);
                                            var rowIdx = Math.min(Math.max(Math.round(elementIndex), 0), rows-1);
                                            
                                            // Get custom data
                                            lastPoint = {
                                                customdata: plotData.customdata[rowIdx][colIdx]
                                            };
                                            
                                            window.pyHandler.debugLog("Found customdata: " + 
                                                JSON.stringify(lastPoint.customdata));
                                        }
                                    } catch (e) {
                                        window.pyHandler.debugLog("Error accessing customdata: " + e);
                                    }
                                } else {
                                    window.pyHandler.debugLog("No hover data found");
                                    lastPoint = null;
                                }
                            } catch (e) {
                                window.pyHandler.debugLog("Error in click processing: " + e);
                                lastPoint = null;
                            }
                        } else {
                            window.pyHandler.debugLog("Plotly not available for click processing");
                            lastPoint = null;
                        }
                    }
                });
                
                window.pyHandler.debugLog("Manual click tracking set up");
            }
            
            // Start setup when document is ready
            if (document.readyState === "complete") {
                window.pyHandler.debugLog("Document already complete");
            } else {
                window.pyHandler.debugLog("Document not ready, waiting for load");
            }
            </script>
            """ % target
            
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
                    hasPyHandler: typeof window.pyHandler !== 'undefined',
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
        
        # If needed, we could inject additional JavaScript here based on the result

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
        if not self.csv_path:
            return

        print(f"Generating scatter plot for: facies={facies}, target={target}, other={other}")

        # Read the CSV and filter by facies.
        df = pd.read_csv(self.csv_path)
        df_f = df[df['Facies'] == facies]
        if df_f.empty:
            print(f"No data for facies: {facies}")
            return

        # Get data for the two elements.
        try:
            x_data = df_f[target]
            y_data = df_f[other]
        except KeyError:
            print(f"Columns {target} and/or {other} not found in CSV.")
            return

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
            title=f"Scatter: {target} vs {other} for Facies {facies}",
            xaxis_title=target,
            yaxis_title=other,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Write the scatter plot to an HTML file.
        plots_dir = "plots"
        scatter_file = os.path.join(plots_dir, "scatter_temp.html")
        scatter_html = scatter_fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot")
        with open(scatter_file, "w") as f:
            f.write(scatter_html)

        # Open a new dialog with a QWebEngineView to show the scatter plot.
        scatter_dialog = QDialog(self)
        scatter_dialog.setWindowTitle(f"Scatter Plot: {target} vs {other} (Facies {facies})")
        layout = QVBoxLayout(scatter_dialog)
        
        # Add a label at the top
        info_label = QLabel(f"Scatter Plot: {target} vs {other} for Facies {facies}")
        layout.addWidget(info_label)
        
        scatter_view = QWebEngineView()
        
        # Configure WebEngine settings for the scatter view
        settings = scatter_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        layout.addWidget(scatter_view)
        scatter_view.setUrl(QUrl.fromLocalFile(os.path.abspath(scatter_file)))
        
        scatter_dialog.resize(800, 600)
        scatter_dialog.exec()

# ---------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())