import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr
import plotly.graph_objects as go
import json
import os

from src3.utils.functions import util_convert_hex_to_rgba

class ZmapPlotMaker:
    """
    Creates Z-maps (correlation heatmaps) that show the strength of correlation 
    between one numerical column and all others, across different values of a categorical column.
    """
    
    def __init__(self):
        self.current_index = 0
        self.heatmap_files = []  # List of (file_path, target_element) tuples
        self.current_target = None
        
        # Ensure plots directory exists
        self.plots_dir = "plots"
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
    
    def make_plot(self, setup_model, traces):
        """
        Generate the Z-map plot based on the setup model and active traces.
        
        Args:
            setup_model: The SetupMenuModel containing plot configuration
            traces: List of trace models to include in the plot
            
        Returns:
            bool: True if plots were generated successfully
        """
        # Get the categorical column and numerical columns from the setup model
        categorical_column = setup_model.axis_members.categorical_column
        numerical_columns = setup_model.axis_members.numerical_columns
        
        if not categorical_column or not numerical_columns:
            print("Missing configuration - please select a categorical column and numerical columns")
            return False
        
        # Concatenate data from all traces after applying filters
        combined_df = self._concat_filtered_dataframes(setup_model, traces)
        
        if combined_df.empty:
            print("No data available after filtering")
            return False
        
        # Generate correlation heatmaps
        success = self._generate_heatmaps(combined_df, categorical_column, numerical_columns, setup_model)
        
        if not success:
            print("Failed to generate heatmaps")
            return False
        
        # Set the initial plot to show
        if self.heatmap_files:
            self.current_index = 0
            self.current_target = self.heatmap_files[0][1]
            return True
            
        return False
    
    def _concat_filtered_dataframes(self, setup_model, traces):
        """
        Concatenate dataframes from all traces after applying filters.
        
        Args:
            setup_model: The SetupMenuModel containing the DataLibraryModel
            traces: List of trace models to include
            
        Returns:
            pd.DataFrame: Combined dataframe with all filtered data
        """
        dataframes = []
        
        for trace in traces:
            # Skip traces with hiding enabled
            if getattr(trace, "hide_on", False):
                continue
                
            # Get the dataframe for this trace
            df = setup_model.data_library.dataframe_manager.get_dataframe_by_metadata(trace.datafile)
            if df is None:
                continue
                
            # Apply filters if enabled
            if getattr(trace, "filters_on", False) and hasattr(trace, "filters"):
                filtered_df = self._apply_filters(df, trace.filters)
                if not filtered_df.empty:
                    dataframes.append(filtered_df)
            else:
                # No filtering needed
                dataframes.append(df)
        
        # Combine all dataframes
        if not dataframes:
            return pd.DataFrame()
            
        return pd.concat(dataframes, ignore_index=True)
    
    def _apply_filters(self, df, filters):
        """
        Apply a list of filters to a dataframe.
        
        Args:
            df: The dataframe to filter
            filters: List of FilterModel objects
            
        Returns:
            pd.DataFrame: Filtered dataframe
        """
        filtered_df = df.copy()
        
        for filter_model in filters:
            column = filter_model.filter_column
            operation = filter_model.filter_operation
            value1 = filter_model.filter_value1
            value2 = filter_model.filter_value2
            
            if column not in filtered_df.columns:
                continue
                
            # Apply the filter based on operation
            # TODO fix this by making the filters an enum rather than checking on strings
            if operation == "<":
                filtered_df = filtered_df[filtered_df[column] < float(value1)]
            elif operation == ">":
                filtered_df = filtered_df[filtered_df[column] > float(value1)]
            elif operation == "<=":
                filtered_df = filtered_df[filtered_df[column] <= float(value1)]
            elif operation == ">=":
                filtered_df = filtered_df[filtered_df[column] >= float(value1)]
            elif operation == "==":
                filtered_df = filtered_df[filtered_df[column] == float(value1)]
            elif operation == "is":
                filtered_df = filtered_df[filtered_df[column] == value1]
            elif operation == "is not":
                filtered_df = filtered_df[filtered_df[column] != value1]
            elif operation == "is one of":
                if isinstance(value1, list):
                    filtered_df = filtered_df[filtered_df[column].isin(value1)]
                else:
                    # If value1 is a string, split by comma
                    values = [v.strip() for v in str(value1).split(",")]
                    filtered_df = filtered_df[filtered_df[column].isin(values)]
            elif operation == "is not one of":
                if isinstance(value1, list):
                    filtered_df = filtered_df[~filtered_df[column].isin(value1)]
                else:
                    # If value1 is a string, split by comma
                    values = [v.strip() for v in str(value1).split(",")]
                    filtered_df = filtered_df[~filtered_df[column].isin(values)]
            elif operation == "a < x < b":
                filtered_df = filtered_df[(filtered_df[column] > float(value1)) & 
                                         (filtered_df[column] < float(value2))]
            elif operation == "a <= x < b":
                filtered_df = filtered_df[(filtered_df[column] >= float(value1)) & 
                                         (filtered_df[column] < float(value2))]
            elif operation == "a < x <= b":
                filtered_df = filtered_df[(filtered_df[column] > float(value1)) & 
                                         (filtered_df[column] <= float(value2))]
            elif operation == "a <= x <= b":
                filtered_df = filtered_df[(filtered_df[column] >= float(value1)) & 
                                         (filtered_df[column] <= float(value2))]
        
        return filtered_df
    
    def _generate_heatmaps(self, df, category_column, numerical_columns, setup_model):
        """
        Generate correlation heatmaps between each numerical column and all others,
        across different values of the categorical column. Writes HTML files to disk.
        
        Args:
            df: The dataframe containing the data
            category_column: The name of the categorical column
            numerical_columns: List of numerical column names
            setup_model: The setup model containing styling information
            
        Returns:
            bool: True if at least one heatmap was generated
        """
        # Clear existing heatmap files list
        self.heatmap_files = []
        
        if not numerical_columns:
            return False
            
        # Get sorted category values
        category_values = sorted(df[category_column].unique())
        
        if not category_values:
            return False
            
        # Compute correlations for each category value
        correlations = {}
        pvals = {}
        
        for value in category_values:
            group = df[df[category_column] == value]
            data = group[numerical_columns].dropna()
            
            # Check if we have enough data points
            if len(data) < 2:
                print(f"Not enough data points for {category_column}={value}, skipping")
                continue
                
            try:
                corr_matrix, p_matrix = spearmanr(data)
                
                # Handle case when there's only one element
                if len(numerical_columns) == 1:
                    corr_df = pd.DataFrame([[1]], index=numerical_columns, columns=numerical_columns)
                    pval_df = pd.DataFrame([[0]], index=numerical_columns, columns=numerical_columns)
                else:
                    corr_df = pd.DataFrame(corr_matrix, index=numerical_columns, columns=numerical_columns)
                    pval_df = pd.DataFrame(p_matrix, index=numerical_columns, columns=numerical_columns)
                    
                correlations[value] = corr_df
                pvals[value] = pval_df
            except Exception as e:
                print(f"Error computing correlation for {category_column}={value}: {str(e)}")
        
        # Check if we computed any valid correlations
        if not correlations:
            return False
        
        # Create one heatmap for each target element
        for target in numerical_columns:
            other_elements = [e for e in numerical_columns if e != target]
            
            # Skip if there are no other elements
            if not other_elements:
                continue
                
            z_matrix = []
            customdata = []  # will hold [category_value, otherElement] for each cell
            
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
                        
                        # Only display r if significant
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

            advanced = setup_model.advanced_settings
            colorscale = getattr(advanced, 'zmap_colorscale', 'RdBu')
            reverse = getattr(advanced, 'zmap_reverse_colorscale', True)
            if reverse:
                colorscale += '_r'
            

            # Build the heatmap figure
            fig = go.Figure(data=go.Heatmap(
                z=z_matrix,
                x=category_values,
                y=other_elements,
                customdata=customdata,
                colorscale=colorscale,
                zmin=-1,
                zmax=1,
                showscale=True,
                hoverongaps=False
            ))

            # Apply styling from setup model
            self._apply_styling(fig, setup_model)
            
            fig.update_layout(
                title=f"Spearman's R: {target} vs Other Elements by {category_column}",
                xaxis_title=category_column,
                yaxis_title="Element",
                margin=dict(l=50, r=50, t=50, b=50)
            )

            values_js = json.dumps(category_values, default=str)
            elements_js = json.dumps(other_elements)
            
            webchannel_js = """
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            // Plot metadata
            var TARGET_ELEMENT = "%s";
            var CATEGORY_VALUES = %s;
            var OTHER_ELEMENTS = %s;
            var CATEGORY_COLUMN = "%s";
            
            // Variables to store hover data
            var lastHoverData = null;
            
            // Set up web channel connection to Python
            var zmapHandler;
            new QWebChannel(qt.webChannelTransport, function(channel) {
                zmapHandler = channel.objects.zmapHandler;
                console.log("QWebChannel established", zmapHandler !== undefined);
                
                if (zmapHandler) {
                    try {
                        zmapHandler.debugLog("QWebChannel connected for " + TARGET_ELEMENT);
                    } catch (e) {
                        console.error("Error calling debugLog:", e);
                    }
                    
                    // Set up the hover and click handlers once QWebChannel is ready
                    document.addEventListener("DOMContentLoaded", setupHandlers);
                    // Also try immediately in case DOM is already loaded
                    if (document.readyState === "complete") {
                        setupHandlers();
                    }
                }
            });
            
            // Function to create hover and click handlers
            function setupHandlers() {
                if (!zmapHandler) {
                    console.error("zmapHandler not available");
                    setTimeout(setupHandlers, 100);
                    return;
                }
                
                try {
                    zmapHandler.debugLog("Setting up handlers");
                } catch (e) {
                    console.error("Error calling debugLog:", e);
                }
                
                // Get the plot div
                var plotDiv = document.getElementById('plot');
                if (!plotDiv) {
                    console.error("Plot div not found");
                    setTimeout(setupHandlers, 100);
                    return;
                }
                
                // Wait for Plotly to be fully loaded
                var checkPlotly = function() {
                    if (typeof Plotly === 'undefined' || !plotDiv._fullLayout) {
                        setTimeout(checkPlotly, 50);
                        return;
                    }
                    
                    // Set up hover event handler to capture hover data
                    plotDiv.on('plotly_hover', function(data) {
                        // Store the hover points for later use
                        lastHoverData = data.points[0];
                    });
                    
                    // Set up click handler for double-clicks
                    var lastClickTime = 0;
                    plotDiv.onclick = function(event) {
                        var currentTime = new Date().getTime();
                        var isDoubleClick = (currentTime - lastClickTime < 300);
                        lastClickTime = currentTime;
                        
                        if (!isDoubleClick) return; // Only process double-clicks
                        
                        try {
                            if (lastHoverData) {
                                // Use the hover data to get exact cell coordinates
                                zmapHandler.debugLog("Using hover data for click: " + 
                                                  "x=" + lastHoverData.x + ", " +
                                                  "y=" + lastHoverData.y);
                                
                                // These values are directly from Plotly's hover data
                                var categoryValue = lastHoverData.x;
                                var otherElement = lastHoverData.y;
                                
                                zmapHandler.debugLog("Double-clicked cell: " + CATEGORY_COLUMN + "=" + categoryValue + 
                                                  ", element=" + otherElement);
                                
                                // Call Python handler with the exact data from the hover
                                zmapHandler.cellDoubleClicked(categoryValue, TARGET_ELEMENT, otherElement);
                            } else {
                                // Fallback to position-based detection if no hover data
                                zmapHandler.debugLog("No hover data available for click, using position");
                                
                                // Get plot layout info for coordinate conversion
                                var layout = plotDiv._fullLayout;
                                var plotArea = {
                                    left: layout.margin.l,
                                    top: layout.margin.t,
                                    width: layout.width - layout.margin.l - layout.margin.r,
                                    height: layout.height - layout.margin.t - layout.margin.b
                                };
                                
                                // Get mouse position relative to plot
                                var rect = plotDiv.getBoundingClientRect();
                                var x = event.clientX - rect.left;
                                var y = event.clientY - rect.top;
                                
                                zmapHandler.debugLog("Click position: " + x + ", " + y);
                                
                                // Check if click is inside the actual plot area
                                if (x < plotArea.left || x > (plotArea.left + plotArea.width) ||
                                    y < plotArea.top || y > (plotArea.top + plotArea.height)) {
                                    zmapHandler.debugLog("Click outside plot area");
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
                                
                                zmapHandler.debugLog("Mapped to: " + CATEGORY_COLUMN + "=" + categoryValue + 
                                                  " (index " + valueIndex + "), " +
                                                  "element=" + otherElement +
                                                  " (index " + elementIndex + ")");
                                
                                // Call Python handler
                                zmapHandler.cellDoubleClicked(categoryValue, TARGET_ELEMENT, otherElement);
                            }
                        } catch (e) {
                            zmapHandler.debugLog("Error in click handler: " + e.toString());
                        }
                    };
                    
                    zmapHandler.debugLog("Handlers installed successfully");
                };
                
                checkPlotly();
            }
            </script>
            """ % (target, values_js, elements_js, category_column)
            
            # Generate HTML with Plotly and add webchannel script
            html_str = fig.to_html(include_plotlyjs=True, full_html=True, div_id="plot", config={"doubleClick": False})
            html_str = html_str.replace("</head>", webchannel_js + "\n</head>")
            
            # Write to file
            file_path = os.path.join(self.plots_dir, f"heatmap_{target}.html")
            with open(file_path, "w") as f:
                f.write(html_str)
            
            # Add to heatmap files list
            self.heatmap_files.append((os.path.abspath(file_path), target))
            print(f"Generated plot for {target} at {file_path}")
        
        return len(self.heatmap_files) > 0
    
    def _apply_styling(self, fig, setup_model):
        """
        Apply styling to the figure based on the setup model.
        
        Args:
            fig: The plotly figure to style
            setup_model: The SetupMenuModel containing styling info
        """
        # Get styling settings from the advanced settings
        advanced = setup_model.advanced_settings

        # Apply background colors
        fig.update_layout(
            paper_bgcolor=util_convert_hex_to_rgba(advanced.paper_color),
            plot_bgcolor=util_convert_hex_to_rgba(advanced.background_color),
        )
        
        # Apply font settings
        fig.update_layout(
            font=dict(
                family=advanced.font,
                size=advanced.font_size,
                color=util_convert_hex_to_rgba(advanced.font_color)
            )
        )
        
        # Apply grid color
        fig.update_xaxes(gridcolor=util_convert_hex_to_rgba(advanced.grid_color), gridwidth=1)
        fig.update_yaxes(gridcolor=util_convert_hex_to_rgba(advanced.grid_color), gridwidth=1)
        
        # Apply tick mark settings
        if hasattr(advanced, 'show_tick_marks'):
            fig.update_xaxes(showticklabels=advanced.show_tick_marks)
            fig.update_yaxes(showticklabels=advanced.show_tick_marks)
    
    def load_current_plot(self):
        """Load the current plot from file."""
        if not self.heatmap_files:
            print("No plots available")
            return None
        
        file_path, target = self.heatmap_files[self.current_index]
        self.current_target = target
        
        print(f"Loading plot: {file_path} with target {target}")
        
        return file_path
    
    def next_plot(self):
        """Move to the next plot in the sequence."""
        if not self.heatmap_files:
            return None
        self.current_index = (self.current_index + 1) % len(self.heatmap_files)
        return self.load_current_plot()
    
    def prev_plot(self):
        """Move to the previous plot in the sequence."""
        if not self.heatmap_files:
            return None
        self.current_index = (self.current_index - 1) % len(self.heatmap_files)
        return self.load_current_plot()
