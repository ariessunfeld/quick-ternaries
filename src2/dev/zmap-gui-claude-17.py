import sys
import os
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import plotly.graph_objects as go
import json
import time
import webbrowser

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QHBoxLayout, QDialog, QLabel, QComboBox, 
    QListWidget, QInputDialog, QMessageBox, QScrollArea
)
from PySide6.QtCore import QUrl, QObject, Slot, Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineSettings

# --------------------------------------------------------------------
# MultiFieldSelector Widget
# --------------------------------------------------------------------
class MultiFieldSelector(QWidget):
    """A composite widget that lets users select one or more fields.

    Displays current selections in a list with Add/Remove buttons.
    """

    selectionChanged = Signal(list)  # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_options = []
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.listWidget = QListWidget(self)
        self.listWidget.setMaximumHeight(100)
        layout.addWidget(self.listWidget)
        btn_layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        self.addButton = QPushButton("Add", self)
        self.removeButton = QPushButton("Remove", self)
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.removeButton)
        btn_layout.addStretch()
        self.addButton.clicked.connect(self.add_field)
        self.removeButton.clicked.connect(self.remove_field)

    def set_available_options(self, options):
        # Store options as list of strings
        self.available_options = [str(opt) for opt in options]

    def add_field(self):
        """Show a dialog to add a field, with better handling of empty
        options."""
        current_selected = self.get_selected_fields()
        choices = [opt for opt in self.available_options if opt not in current_selected]

        if not choices:
            print("No available choices in MultiFieldSelector.add_field()")
            QMessageBox.information(
                self,
                "No Available Fields",
                "There are no available fields to add. This may happen if there are no common columns across loaded data files.",
            )
            return

        item, ok = QInputDialog.getItem(
            self, "Select Field", "Available Fields:", choices, 0, False
        )
        if ok and item:
            self.listWidget.addItem(item)
            self.selectionChanged.emit(self.get_selected_fields())

    def remove_field(self):
        current_item = self.listWidget.currentItem()
        if current_item:
            row = self.listWidget.row(current_item)
            self.listWidget.takeItem(row)
            self.selectionChanged.emit(self.get_selected_fields())

    def get_selected_fields(self):
        """Return all currently selected fields as a list of strings."""
        return [self.listWidget.item(i).text() for i in range(self.listWidget.count())]

    def set_selected_fields(self, fields_list):
        """Set the selected fields in the list widget.

        Ensures all fields in fields_list are in available_options first.
        """
        # Clear current selections
        self.listWidget.clear()

        # Convert all fields to strings for consistency
        if not fields_list:
            return

        if isinstance(fields_list, str):
            # Handle case where a string was passed instead of a list
            fields_list = [f.strip() for f in fields_list.split(",")]

        # Make sure all values are strings
        fields_list = [str(field) for field in fields_list]

        # Make sure all fields to add are in available_options
        for field in fields_list:
            if field not in self.available_options:
                self.available_options.append(field)

        # Now add each field to the list widget
        for field in fields_list:
            self.listWidget.addItem(field)
        
        # Emit signal since we changed the selection
        self.selectionChanged.emit(fields_list)

# ---------------------------------------------------------
# Handler exposed via QWebChannel to receive JS callbacks.
# ---------------------------------------------------------
class PlotHandler(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    @Slot(str, str, str)
    def cellDoubleClicked(self, category_value, target, other):
        print(f"Double clicked cell: {self.main_window.category_column}={category_value}, target={target}, other={other}")
        self.main_window.generate_scatter_plot(category_value, target, other)
    
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

        # Initialize file path and data variables
        self.csv_path = None
        self.heatmap_files = []
        self.current_index = 0
        self.current_target = None
        self.df = None
        self.category_column = None  # Will be set by user
        self.category_values = {}  # Will store original types
        
        # Make sure scatter plots directory exists
        self.scatter_dir = "scatter_plots"
        if not os.path.exists(self.scatter_dir):
            os.makedirs(self.scatter_dir)
        print(f"Using directory for scatter plots: {os.path.abspath(self.scatter_dir)}")

        # Create a scroll area to contain everything
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
        
        # Main container widget
        container = QWidget()
        scroll.setWidget(container)
        
        # Main layout for the container
        main_layout = QVBoxLayout(container)

        # Top control panel
        controls_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        
        # Browse file button
        file_layout = QHBoxLayout()
        controls_layout.addLayout(file_layout)
        self.btnBrowse = QPushButton("Browse CSV")
        file_layout.addWidget(self.btnBrowse)
        self.fileLabel = QLabel("No file selected")
        file_layout.addWidget(self.fileLabel)
        file_layout.addStretch()
        
        # Category column selector
        category_layout = QHBoxLayout()
        controls_layout.addLayout(category_layout)
        category_layout.addWidget(QLabel("Category Column:"))
        self.categoryCombo = QComboBox()
        category_layout.addWidget(self.categoryCombo)
        category_layout.addStretch()
        
        # Add selector for numeric fields
        controls_layout.addWidget(QLabel("Select Elements for Correlation Analysis:"))
        self.field_selector = MultiFieldSelector()
        controls_layout.addWidget(self.field_selector)
        
        # Generate button
        btn_layout = QHBoxLayout()
        controls_layout.addLayout(btn_layout)
        self.btnGenerate = QPushButton("Generate Plots")
        self.btnPrev = QPushButton("Prev")
        self.btnNext = QPushButton("Next")
        btn_layout.addWidget(self.btnGenerate)
        btn_layout.addWidget(self.btnPrev)
        btn_layout.addWidget(self.btnNext)
        btn_layout.addStretch()

        # Status label
        self.statusLabel = QLabel("No plot loaded")
        controls_layout.addWidget(self.statusLabel)

        # QWebEngineView for displaying the plots - make sure it can expand
        self.webView = QWebEngineView()
        
        # Configure WebEngine settings to allow JavaScript and external content
        settings = self.webView.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        # Add web view to main layout - it should take up all available space
        main_layout.addWidget(self.webView, 1)  # Add stretch factor to make it expand

        # Connect signals.
        self.btnBrowse.clicked.connect(self.browse_file)
        self.btnGenerate.clicked.connect(self.generate_plots)
        self.btnPrev.clicked.connect(self.prev_plot)
        self.btnNext.clicked.connect(self.next_plot)
        self.categoryCombo.currentTextChanged.connect(self.on_category_changed)
        self.field_selector.selectionChanged.connect(self.on_fields_changed)

        # Set up QWebChannel for communication from JS.
        self.channel = QWebChannel()
        self.handler = PlotHandler(self)
        self.channel.registerObject("pyHandler", self.handler)
        self.webView.page().setWebChannel(self.channel)
        
        # Connect loadFinished signal
        self.webView.loadFinished.connect(self.on_load_finished)
        
        # Disable UI elements until file is loaded
        self.update_ui_state()

    def update_ui_state(self):
        """Update UI elements based on current state"""
        has_file = self.csv_path is not None
        has_category = self.category_column is not None
        has_fields = len(self.field_selector.get_selected_fields()) > 0
        
        self.categoryCombo.setEnabled(has_file)
        self.field_selector.setEnabled(has_file)
        self.btnGenerate.setEnabled(has_file and has_category and has_fields)
        self.btnPrev.setEnabled(len(self.heatmap_files) > 0)
        self.btnNext.setEnabled(len(self.heatmap_files) > 0)

    def browse_file(self):
        # Let the user select a CSV file.
        file_name, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_name:
            self.csv_path = file_name
            print(f"Selected CSV: {self.csv_path}")
            self.fileLabel.setText(os.path.basename(self.csv_path))
            
            # Load the CSV file and populate dropdowns
            try:
                self.df = pd.read_csv(self.csv_path)
                
                # Update category dropdown with all columns
                self.categoryCombo.clear()
                for column in self.df.columns:
                    self.categoryCombo.addItem(column)
                
                # Update field selector with numeric columns
                numeric_columns = self.df.select_dtypes(include=['number']).columns.tolist()
                self.field_selector.set_available_options(numeric_columns)
                
                # Do NOT auto-select any fields
                
                # Auto-select first non-numeric column as category
                non_numeric = [col for col in self.df.columns if col not in numeric_columns]
                if non_numeric:
                    self.categoryCombo.setCurrentText(non_numeric[0])
                
                self.statusLabel.setText(f"Loaded CSV: {os.path.basename(self.csv_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading CSV", f"Failed to load CSV file: {str(e)}")
                return
            
            self.update_ui_state()

    def on_category_changed(self, column):
        """Handle category column selection change"""
        if not column or not self.df is not None:
            return
            
        self.category_column = column
        print(f"Selected category column: {self.category_column}")
        
        # Update category value types
        if self.category_column in self.df.columns:
            self.category_values = {str(value): type(value) 
                                   for value in self.df[self.category_column].unique()}
            print(f"Category values: {self.category_values}")
        
        self.update_ui_state()

    def on_fields_changed(self, fields):
        """Handle field selection changes"""
        print(f"Selected fields for correlation: {fields}")
        self.update_ui_state()

    def generate_plots(self):
        """Generate correlation heatmaps based on selected columns"""
        if not self.csv_path or self.df is None:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
            
        if not self.category_column:
            QMessageBox.warning(self, "No Category", "Please select a category column.")
            return
            
        elements = self.field_selector.get_selected_fields()
        if not elements:
            QMessageBox.warning(self, "No Elements", "Please select at least one element for correlation analysis.")
            return

        self.statusLabel.setText("Generating plots...")
        QApplication.processEvents()  # Update the UI

        # Get sorted category values.
        category_values = sorted(self.df[self.category_column].unique())

        # Group the data by category and compute pairwise Spearman correlations.
        correlations = {}
        pvals = {}
        
        # Check if we have category values
        if not category_values:
            QMessageBox.warning(self, "No Data", f"No unique values found in category column: {self.category_column}")
            return
            
        # Compute correlations for each category value
        for value in category_values:
            group = self.df[self.df[self.category_column] == value]
            data = group[elements].dropna()
            
            # Check if we have enough data points
            if len(data) < 2:
                print(f"Not enough data points for {self.category_column}={value}, skipping")
                continue
                
            try:
                corr_matrix, p_matrix = spearmanr(data)
                
                # Handle case when there's only one element
                if len(elements) == 1:
                    corr_df = pd.DataFrame([[1]], index=elements, columns=elements)
                    pval_df = pd.DataFrame([[0]], index=elements, columns=elements)
                else:
                    corr_df = pd.DataFrame(corr_matrix, index=elements, columns=elements)
                    pval_df = pd.DataFrame(p_matrix, index=elements, columns=elements)
                    
                correlations[value] = corr_df
                pvals[value] = pval_df
            except Exception as e:
                print(f"Error computing correlation for {self.category_column}={value}: {str(e)}")
                # Skip this category value
        
        # Check if we computed any valid correlations
        if not correlations:
            QMessageBox.warning(self, "No Results", "Could not compute valid correlations for any category values.")
            return

        # Ensure plots folder exists.
        plots_dir = "plots"
        if not os.path.exists(plots_dir):
            os.makedirs(plots_dir)

        # Reset heatmap files list.
        self.heatmap_files = []

        # Create one heatmap for each target element.
        for target in elements:
            other_elements = [e for e in elements if e != target]
            
            # Skip if there are no other elements
            if not other_elements:
                continue
                
            z_matrix = []
            customdata = []  # will hold [category_value, otherElement] for each cell.
            
            for other in other_elements:
                row = []
                row_custom = []
                for value in category_values:
                    # Check if correlation exists for this category value
                    if value not in correlations:
                        row.append(None)
                        row_custom.append([value, other])
                        continue
                        
                    try:
                        r = correlations[value].loc[target, other]
                        p = pvals[value].loc[target, other]
                        
                        # Only display r if significant.
                        if p <= 0.05:
                            row.append(r)
                        else:
                            row.append(None)
                            
                        row_custom.append([value, other])
                    except Exception as e:
                        print(f"Error accessing correlation for {target} vs {other} in {value}: {str(e)}")
                        row.append(None)
                        row_custom.append([value, other])
                
                z_matrix.append(row)
                customdata.append(row_custom)

            # Build the heatmap figure.
            fig = go.Figure(data=go.Heatmap(
                z=z_matrix,
                x=category_values,
                y=other_elements,
                customdata=customdata,
                colorscale='RdBu_r',  # cool-warm colorscale.
                zmin=-1,
                zmax=1,
                showscale=True,
                hoverongaps=False
            ))

            fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False)
            fig.update_xaxes(showgrid=False)
            fig.update_layout(
                title=f"Spearman's R: {target} vs Other Elements by {self.category_column}",
                xaxis_title=self.category_column,
                yaxis_title="Element",
                paper_bgcolor="white",
                plot_bgcolor="white",
                margin=dict(l=50, r=50, t=50, b=50)
            )

            # Add QWebChannel script and plot metadata
            values_js = json.dumps(category_values, default=str)  # Convert all values to strings
            elements_js = json.dumps(other_elements)
            
            webchannel_js = """
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            // Plot metadata
            var TARGET_ELEMENT = "%s";
            var CATEGORY_VALUES = %s;
            var OTHER_ELEMENTS = %s;
            var CATEGORY_COLUMN = "%s";
            
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
                            var valueIndex = Math.floor(relX * CATEGORY_VALUES.length);
                            var elementIndex = Math.floor(relY * OTHER_ELEMENTS.length);
                            
                            // Invert Y index (Plotly's Y axis goes from bottom to top)
                            elementIndex = OTHER_ELEMENTS.length - 1 - elementIndex;
                            
                            // Make sure indices are in bounds
                            valueIndex = Math.min(Math.max(valueIndex, 0), CATEGORY_VALUES.length - 1);
                            elementIndex = Math.min(Math.max(elementIndex, 0), OTHER_ELEMENTS.length - 1);
                            
                            var categoryValue = CATEGORY_VALUES[valueIndex];
                            var otherElement = OTHER_ELEMENTS[elementIndex];
                            
                            pyHandler.debugLog("Mapped to: " + CATEGORY_COLUMN + "=" + categoryValue + 
                                               " (index " + valueIndex + "), " +
                                               "element=" + otherElement +
                                               " (index " + elementIndex + ")");
                            
                            // Call Python handler
                            pyHandler.cellDoubleClicked(categoryValue, TARGET_ELEMENT, otherElement);
                        } catch (e) {
                            pyHandler.debugLog("Error in click handler: " + e.toString());
                        }
                    };
                    
                    pyHandler.debugLog("Click handler installed");
                };
                
                checkPlotly();
            }
            </script>
            """ % (target, values_js, elements_js, self.category_column)
            
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
        if self.heatmap_files:
            self.current_index = 0
            self.statusLabel.setText(f"Generated {len(self.heatmap_files)} plots")
            self.load_current_plot()
        else:
            self.statusLabel.setText("No plots generated - check console for errors")

        self.update_ui_state()

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
            0,  # World ID (0 = MainWorld)
            lambda result: print(f"JS Environment: {result}")
        )

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

    def generate_scatter_plot(self, category_value, target, other):
        """Generate a scatter plot (with best-fit line) for the given category value and element pair,
           and display it by opening the system browser."""
        if not self.csv_path or self.df is None:
            print("No CSV data available")
            return

        print(f"Generating scatter plot for: {self.category_column}={category_value}, target={target}, other={other}")
        
        # Debug info about the category value and type
        print(f"Received category value: '{category_value}' of type {type(category_value)}")
        
        # Try to convert the category value to match the DataFrame's type
        if self.category_values:
            try:
                # Special handling for numeric types
                if self.df[self.category_column].dtype == 'int64' or self.df[self.category_column].dtype == 'float64':
                    category_converted = float(category_value) if '.' in category_value else int(category_value)
                else:
                    # For other types, use the string version
                    category_converted = str(category_value)
                
                print(f"Converted category value: '{category_converted}' of type {type(category_converted)}")
            except (ValueError, TypeError) as e:
                print(f"Error converting category value: {e}")
                category_converted = category_value
        else:
            # Without specific type info, try all common conversions
            category_converted = category_value
            all_values = self.df[self.category_column].unique()
            
            # Try finding the value in different formats
            if category_value not in all_values:
                # Try as int
                try:
                    if int(float(category_value)) in all_values:
                        category_converted = int(float(category_value))
                        print(f"Found match as int: {category_converted}")
                except:
                    pass
                    
                # Try as float
                try:
                    if float(category_value) in all_values:
                        category_converted = float(category_value)
                        print(f"Found match as float: {category_converted}")
                except:
                    pass
                    
                # Try as string if all else fails
                if str(category_value) in [str(v) for v in all_values]:
                    matching_values = [v for v in all_values if str(v) == str(category_value)]
                    if matching_values:
                        category_converted = matching_values[0]
                        print(f"Found match as string: {category_converted}")

        # Filter the DataFrame
        df_f = self.df[self.df[self.category_column] == category_converted]
        
        # Check for empty result and try alternatives
        if df_f.empty:
            print(f"No data for {self.category_column}={category_converted}")
            print(f"Trying alternative lookup methods...")
            
            # Try direct string comparison
            df_f = self.df[self.df[self.category_column].astype(str) == str(category_value)]
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
            x=x_data, y=y_data, mode='markers', name='Data Points'
        ))
        scatter_fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines', 
            name=f'Best Fit (r = {r_value:.3f})'
        ))
        scatter_fig.update_layout(
            title=f"Scatter: {target} vs {other} for {self.category_column}={category_converted}",
            xaxis_title=target,
            yaxis_title=other,
            paper_bgcolor="white",
            plot_bgcolor="white",
            width=800,
            height=600,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Generate a unique filename for this plot
        safe_value = str(category_converted).replace('/', '_').replace('\\', '_')
        filename = f"scatter_{target}_{other}_{safe_value}_{int(time.time())}.html"
        filepath = os.path.join(self.scatter_dir, filename)
        
        # Write the scatter plot HTML to a file
        scatter_html = scatter_fig.to_html(include_plotlyjs=True, full_html=True)
        with open(filepath, 'w') as f:
            f.write(scatter_html)
        
        print(f"Saved scatter plot to {filepath}")

        # Open in system browser
        file_url = QUrl.fromLocalFile(os.path.abspath(filepath)).toString()
        webbrowser.open(file_url)
        print(f"Opened scatter plot in browser: {file_url}")

# ---------------------------------------------------------
# Main entry point.
# ---------------------------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())