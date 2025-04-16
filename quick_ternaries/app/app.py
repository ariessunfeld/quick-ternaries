import json
import os
from time import time
import re
import traceback
import webbrowser
from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.colors import get_colorscale
from plotly.subplots import make_subplots
import plotly.io as pio
from PySide6.QtCore import (
    Qt, 
    QUrl, 
)
from PySide6.QtGui import (
    QPalette,
    QFontDatabase,
    QDesktopServices,
    QFont
)
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quick_ternaries.services.ternary_plot_maker import TernaryPlotMaker
from quick_ternaries.services.ternary_trace_maker import (
    TernaryContourTraceMaker, 
    DensityContourMaker,
)
from quick_ternaries.services.cartesian_plot_maker import CartesianPlotMaker
from quick_ternaries.services.zmap_plot_maker import ZmapPlotMaker

from quick_ternaries.utils.functions import (
    is_valid_formula,
    validate_data_library,
    get_numeric_columns_from_dataframe,
    get_numeric_columns_from_file
)
from quick_ternaries.utils.constants import (
    ADD_TRACE_LABEL,
    SETUP_MENU_LABEL,
)
from quick_ternaries.utils.utils import (
    WorkspaceManager, 
    PlotlyInterface,
    CustomJSONEncoder,
    ZmapPlotHandler,
    ColorPalette,
)
from quick_ternaries.utils.df_manager import DataframeManager

from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel

from quick_ternaries.views.widgets import (
    CustomSplitter,
    DatafileSelector,
    ColorButton
)

from quick_ternaries.views.tab_panel_widget import TabPanel
from quick_ternaries.views.setup_menu_view import SetupMenuView
from quick_ternaries.views.trace_editor_view import TraceEditorView

from quick_ternaries.controllers import (
    TraceEditorController,
    SetupMenuController
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Ternaries")
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vlayout = QVBoxLayout(central_widget)
        main_vlayout.setContentsMargins(0, 0, 0, 0)

        top_banner = self._create_top_banner()
        main_vlayout.addWidget(top_banner)

        self.h_splitter = CustomSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(8)
        self.h_splitter.setStyleSheet(
            """
        QSplitter::handle {
            width: 5px;
            margin-left: 3px;
            margin-right: 3px;
        }
        """
        )
        main_vlayout.addWidget(self.h_splitter, 1)

        bottom_banner = self._create_bottom_banner()
        main_vlayout.addWidget(bottom_banner)

        # Left: TabPanel
        self.tabPanel = TabPanel()
        self.h_splitter.addWidget(self.tabPanel)

        self.zmap_plot_maker = ZmapPlotMaker()

        # Initialize color palette for new traces
        self.color_palette = ColorPalette()

        # Center: QStackedWidget to hold both TraceEditorView and SetupMenuView.
        self.centerStack = QStackedWidget()

        # Instantiate the plotly interface for handling selected points
        self.plotly_interface = PlotlyInterface()

        self.zmap_channel = QWebChannel()
        self.zmap_handler = ZmapPlotHandler(self)
        self.zmap_channel.registerObject("zmapHandler", self.zmap_handler)

        # Instantiate the setup menu view.
        self.setupMenuModel = SetupMenuModel()
        self.setupMenuModel.data_library._dataframe_manager = DataframeManager()
        self.setupMenuView = SetupMenuView(self.setupMenuModel)
        self.centerStack.addWidget(self.setupMenuView)
        self.h_splitter.addWidget(self.centerStack)

        # Instantiate the trace editor view with an initial dummy model.
        self.current_trace_model = TraceEditorModel()
        self.traceEditorView = TraceEditorView(self.current_trace_model)
        self.traceEditorController = TraceEditorController(
            self.current_trace_model,
            self.traceEditorView,
            self.setupMenuModel.data_library,
        )
        self.traceEditorView.traceNameChangedCallback = self.on_trace_name_changed
        self.centerStack.addWidget(self.traceEditorView)

        # Right: Plot Window (placeholder)
        self.plotView = QWebEngineView()
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")
        self.h_splitter.addWidget(self.plotView)

        # Set up the web channel
        self.web_channel = QWebChannel(self.plotView.page())
        self.web_channel.registerObject("plotlyInterface", self.plotly_interface)
        self.plotView.page().setWebChannel(self.web_channel)

        # Connect TabPanel callbacks
        self.tabPanel.tabSelectedCallback = self.on_tab_selected
        self.tabPanel.tabRenamedCallback = self.on_tab_renamed
        self.tabPanel.tabRemovedCallback = self.on_tab_removed
        self.tabPanel.tabAddRequestedCallback = self.create_new_tab
        self.tabPanel.duplicate_trace = self.duplicate_trace

        # Setup Menu special case
        self.setup_id = "setup-menu-id"
        self.tabPanel.id_to_widget[self.setup_id] = None

        self.current_tab_id = None

        # Start with Setup Menu selected.
        self.tabPanel.listWidget.setCurrentRow(0)
        self.current_tab_id = "setup-menu-id"
        self._show_setup_content()

        self.plotTypeSelector.currentTextChanged.connect(self.on_plot_type_changed)

        # Create and set up the Setup Menu Controller.
        self.setupController = SetupMenuController(
            self.setupMenuModel, self.setupMenuView
        )
        self.setupMenuView.set_controller(self.setupController)

        self.ternary_plot_maker = TernaryPlotMaker()
        self.ternary_contour_maker = TernaryContourTraceMaker()
        self.cartesian_plot_maker = CartesianPlotMaker()
        self.density_contour_maker = DensityContourMaker()

    def duplicate_trace(self, uid):
        """Handle the duplication of a trace."""
        if uid not in self.tabPanel.id_to_widget:
            return
            
        # Get the original model
        original_model = self.tabPanel.id_to_widget.get(uid)
        if not isinstance(original_model, TraceEditorModel):
            return
        
        # Create a deep copy of the model using the copy method
        new_model = original_model.copy()
        
        # Update the trace name
        original_name = original_model.trace_name
        new_model.trace_name = f"Copy of {original_name}"
        
        # For non-contour traces, get a new color from the palette
        if not getattr(new_model, "is_contour", False):
            new_model.trace_color = self.color_palette.next_color()
        
        # Add the new tab
        new_trace_id = self.tabPanel.add_tab(new_model.trace_name, new_model)
        
        # Save current tab data and switch to the new tab
        self._save_current_tab_data()
        self.current_tab_id = new_trace_id
        
        # Set the model in the trace editor view
        self.traceEditorView.set_model(new_model)
        self.traceEditorController.model = new_model
        self._show_trace_editor()

    def ensure_datafile_metadata(self, value):
        """Ensure value is a DataFileMetadata object."""
        if isinstance(value, DataFileMetadata):
            return value
        elif isinstance(value, str):
            # Try to convert from display string
            metadata = self.setupMenuModel.data_library.get_metadata_by_display_string(value)
            if metadata:
                return metadata
            # Try as file path
            metadata = self.setupMenuModel.data_library.get_metadata_by_path(value)
            if metadata:
                return metadata
            # Create new
            try:
                return DataFileMetadata.from_display_string(value)
            except:
                return DataFileMetadata(file_path=value)
        elif isinstance(value, dict):
            return DataFileMetadata.from_dict(value)
        else:
            # Default empty metadata
            return DataFileMetadata(file_path="")

    def validate_uncertainty_entries(self):
        """
        Validates that all contour traces have non-blank uncertainty entries.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        # Get visible contour traces
        visible_traces = self._get_visible_traces()
        contour_traces = [(uid, model) for uid, model in visible_traces if getattr(model, "is_contour", False)]
        
        if not contour_traces:
            return True  # No contour traces to validate
        
        # Track traces with missing uncertainties
        missing_uncertainties = []
        
        for uid, model in contour_traces:
            # Check if error_entry_model exists and has entries
            if not hasattr(model, "error_entry_model") or not hasattr(model.error_entry_model, "entries"):
                missing_uncertainties.append((model.trace_name, "No error model"))
                continue
            
            # Get the source point data if available
            source_data = getattr(model, "source_point_data", {})
            if "series" not in source_data or not isinstance(source_data["series"], pd.Series):
                continue
                
            series = source_data["series"]
            
            # Get relevant columns based on axis members
            relevant_columns = []
            for axis_name in ['top_axis', 'left_axis', 'right_axis']:
                if hasattr(self.setupMenuModel.axis_members, axis_name):
                    relevant_columns.extend(getattr(self.setupMenuModel.axis_members, axis_name))
            
            # Check numeric columns that should have uncertainty values
            for col in series.index:
                if col in relevant_columns and isinstance(series[col], (int, float, np.number)) and not pd.isna(series[col]):
                    # Check if this column has a valid uncertainty value
                    err_value = model.error_entry_model.get_error(col)
                    if err_value <= 0:
                        missing_uncertainties.append((model.trace_name, col))
        
        # If any missing uncertainties, show popup
        if missing_uncertainties:
            message = "Cannot render plot due to missing uncertainty values:\n\n"
            
            for trace_name, component in missing_uncertainties:
                message += f"• Trace '{trace_name}': Missing value for '{component}'\n"
            
            message += "\nPlease set uncertainty values before rendering."
            
            QMessageBox.warning(self, "Missing Uncertainty Values", message)
            return False
                
        return True

    def validate_axis_members(self):
        """
        Validates that all required axes for the current plot type have at least one column selected.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        current_plot_type = self.plotTypeSelector.currentText().lower()
        
        # Determine required axes based on plot type
        if current_plot_type == 'ternary':
            required_axes = {
                'top_axis': 'Top Apex', 
                'left_axis': 'Left Apex', 
                'right_axis': 'Right Apex'
            }
        elif current_plot_type == 'cartesian':
            required_axes = {
                'x_axis': 'X Axis', 
                'y_axis': 'Y Axis'
            }
        elif current_plot_type == 'histogram':
            required_axes = {
                'x_axis': 'X Axis'
            }
        else:
            return True  # Unknown plot type, skip validation
        
        # Check if all required axes have at least one member
        empty_axes = []
        
        for axis_name, display_name in required_axes.items():
            axis_members = getattr(self.setupMenuModel.axis_members, axis_name, [])
            if not axis_members:
                empty_axes.append(display_name)
        
        if empty_axes:
            axes_str = ', '.join(empty_axes)
            
            # Show warning popup
            QMessageBox.warning(
                self,
                "Missing Axis Data",
                f"The following axes have no columns selected: {axes_str}\n\n"
                "Please select at least one column for each axis before rendering the plot."
            )
            return False
            
        return True
        

    def setup_title(self, title: str):
        """
        Load the 'Motter Tektura' font and use it to set up the application's title label.
        The title label is configured to display the 'quick ternaries' logo which includes a
        hyperlink to the project repository.
        """
        font_path = str(Path(__file__).parent.parent / 'resources' / 'fonts' / 'Motter_Tektura_Normal.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.title_label = QLabel()
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                custom_font = QFont(font_families[0], pointSize=20)
                self.title_label.setFont(custom_font)
        self.update_title_view(title)
        self.title_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        self.title_label.setOpenExternalLinks(True)  # Allow the label to open links
        return self.title_label

    def update_title_view(self, title: str):
        """
        Update the title label hyperlink color based on the current theme.
        """
        self.title_label.setText(
            '<a href=https://github.com/ariessunfeld/quick-ternaries ' +
            f'style="color: {self.get_title_color()}; text-decoration:none;">' +
            f'{title}' +
            '</a>'
        )

    def get_title_color(self):
        """
        Determine the appropriate title color based on the current palette.
        """
        palette = self.palette()
        background_color = palette.color(QPalette.Window)
        is_dark_mode = background_color.value() < 128  # Assuming dark mode if background is dark
        return 'white' if is_dark_mode else 'black'

    def _create_top_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        # logo_label = QLabel("Quick Ternaries")
        # logo_label.setStyleSheet("font-weight: bold; font-size: 16pt;")
        logo_label = self.setup_title('Quick Ternaries')
        layout.addWidget(logo_label)
        layout.addStretch()
        self.plotTypeSelector = QComboBox()
        self.plotTypeSelector.addItems(["Ternary", "Cartesian", "Histogram", "Zmap"])
        layout.addWidget(self.plotTypeSelector)
        self.settingsButton = QPushButton("Settings")
        layout.addWidget(self.settingsButton)
        return container

    # Modify the bottom banner method to add Zmap buttons
    def _create_bottom_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)

        # Create buttons
        self.previewButton = QPushButton("Render Plot")
        self.saveButton = QPushButton("Save Workspace")
        self.loadButton = QPushButton("Load Workspace")
        self.exportButton = QPushButton("Export Plot")
        self.bootstrapButton = QPushButton("Bootstrap Point")
        
        # Add Zmap-specific buttons (initially hidden)
        self.zmapPrevButton = QPushButton("Previous ZMap")
        self.zmapNextButton = QPushButton("Next ZMap")
        self.zmapPrevButton.setVisible(False)
        self.zmapNextButton.setVisible(False)

        # Add to layout with stretch
        layout.addWidget(self.previewButton)
        layout.addWidget(self.exportButton)
        layout.addWidget(self.bootstrapButton)
        layout.addWidget(self.zmapPrevButton)
        layout.addWidget(self.zmapNextButton)
        layout.addStretch()
        layout.addWidget(self.saveButton)
        layout.addWidget(self.loadButton)

        # Connect button signals
        self.previewButton.clicked.connect(self.on_preview_clicked)
        self.saveButton.clicked.connect(self.save_workspace)
        self.loadButton.clicked.connect(self.load_workspace)
        self.bootstrapButton.clicked.connect(self.on_bootstrap_clicked)
        self.exportButton.clicked.connect(self.on_export_clicked)
        self.zmapPrevButton.clicked.connect(self.on_prev_zmap_clicked)
        self.zmapNextButton.clicked.connect(self.on_next_zmap_clicked)

        return container

    def on_prev_zmap_clicked(self):
        """Handle click on Previous ZMap button."""
        file_path = self.zmap_plot_maker.prev_plot()
        if file_path and os.path.exists(file_path):
            self.plotView.setUrl(QUrl.fromLocalFile(file_path))
            
            # Update status label if available
            if hasattr(self, 'statusLabel'):
                total_plots = len(self.zmap_plot_maker.heatmap_files)
                current_target = self.zmap_plot_maker.current_target
                self.statusLabel.setText(f"Plot {self.zmap_plot_maker.current_index + 1}/{total_plots}: {current_target}")

    def on_next_zmap_clicked(self):
        """Handle click on Next ZMap button."""
        file_path = self.zmap_plot_maker.next_plot()
        if file_path and os.path.exists(file_path):
            self.plotView.setUrl(QUrl.fromLocalFile(file_path))
            
            # Update status label if available
            if hasattr(self, 'statusLabel'):
                total_plots = len(self.zmap_plot_maker.heatmap_files)
                current_target = self.zmap_plot_maker.current_target
                self.statusLabel.setText(f"Plot {self.zmap_plot_maker.current_index + 1}/{total_plots}: {current_target}")
    
    def show_save_dialog(self):
        # Define file filters for the dropdown, adding PDF and HTML
        file_filters = (
            "PNG Files (*.png);;"
            "JPEG Files (*.jpeg);;"
            "PDF Files (*.pdf);;"
            "SVG Files (*.svg);;"
            "WEBP Files (*.webp);;"
            "HTML Files (*.html)"  # Added HTML option
        )
        # Open the save file dialog
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Plot",
            "",
            file_filters
        )

        return Path(file_path), selected_filter
    
    def generate_scatter_plot(self, category_value, target, other):
        """
        Generate a scatter plot for a double-clicked cell in the Zmap.
        
        Args:
            category_value: The value of the categorical column
            target: The target column
            other: The other column
        """
        # Get visible traces
        visible_traces = self._get_visible_traces()
        
        # Get the categorical column from the setup model
        categorical_column = self.setupMenuModel.axis_members.categorical_column
        
        if not categorical_column:
            print("No categorical column selected")
            return
        
        # Concatenate data from all traces after applying filters
        combined_df = pd.DataFrame()
        
        for uid, trace_model in visible_traces:
            # Skip traces with hiding enabled
            if getattr(trace_model, "hide_on", False):
                continue
            
            # Get the dataframe for this trace
            df = self.setupMenuModel.data_library.dataframe_manager.get_dataframe_by_metadata(trace_model.datafile)
            if df is None:
                continue
            
            # Apply filters if enabled
            if getattr(trace_model, "filters_on", False) and hasattr(trace_model, "filters"):
                # Use the ZmapPlotMaker's _apply_filters method
                filtered_df = self.zmap_plot_maker._apply_filters(df, trace_model.filters)
                if not filtered_df.empty:
                    combined_df = pd.concat([combined_df, filtered_df], ignore_index=True)
            else:
                # No filtering needed
                combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        if combined_df.empty:
            print("No data available for scatter plot")
            return
        
        # Filter to only include the selected category value
        try:
            # Try to convert category value to match the dataframe's type
            if combined_df[categorical_column].dtype == 'int64' or combined_df[categorical_column].dtype == 'float64':
                try:
                    category_converted = float(category_value) if '.' in category_value else int(category_value)
                except (ValueError, TypeError):
                    category_converted = category_value
            else:
                category_converted = category_value
            
            # Filter the dataframe
            df_f = combined_df[combined_df[categorical_column] == category_converted]
            
            # If empty result, try string comparison
            if df_f.empty:
                df_f = combined_df[combined_df[categorical_column].astype(str) == str(category_value)]
                
                # If still empty, try finding the value in different formats
                if df_f.empty:
                    all_values = combined_df[categorical_column].unique()
                    
                    # Try as int
                    try:
                        if int(float(category_value)) in all_values:
                            category_converted = int(float(category_value))
                            df_f = combined_df[combined_df[categorical_column] == category_converted]
                    except:
                        pass
                    
                    # Try as float
                    if df_f.empty:
                        try:
                            if float(category_value) in all_values:
                                category_converted = float(category_value)
                                df_f = combined_df[combined_df[categorical_column] == category_converted]
                        except:
                            pass
                    
                    # Try as string if all else fails
                    if df_f.empty and any(str(v) == str(category_value) for v in all_values):
                        matching_values = [v for v in all_values if str(v) == str(category_value)]
                        if matching_values:
                            category_converted = matching_values[0]
                            df_f = combined_df[combined_df[categorical_column] == category_converted]
        except Exception as e:
            print(f"Error filtering data: {e}")
            return
        
        if df_f.empty:
            print(f"No data for {categorical_column}={category_value}")
            return
        
        # Get data for the two elements
        try:
            x_data = df_f[target]
            y_data = df_f[other]
        except KeyError:
            print(f"Columns {target} and/or {other} not found in data")
            return
        
        print(f"Found {len(x_data)} data points for plotting")
        
        # Compute the best fit line
        try:
            coeffs = np.polyfit(x_data, y_data, 1)
            slope, intercept = coeffs
            x_line = np.array([x_data.min(), x_data.max()])
            y_line = slope * x_line + intercept
            r_value = np.corrcoef(x_data, y_data)[0, 1]
        except Exception as e:
            print(f"Error computing best fit: {e}")
            # Default values if fit fails
            slope, intercept = 0, 0
            x_line = np.array([x_data.min(), x_data.max()])
            y_line = np.zeros_like(x_line)
            r_value = 0
        
        # Create scatter plot figure
        scatter_fig = go.Figure()
        scatter_fig.add_trace(go.Scatter(
            x=x_data, y=y_data, mode='markers', name='Data Points'
        ))
        scatter_fig.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines', 
            name=f'Best Fit (r = {r_value:.3f})'
        ))
        scatter_fig.update_layout(
            title=f"Scatter: {target} vs {other} for {categorical_column}={category_converted}",
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
        filename = f"scatter_{target}_{other}_{safe_value}_{int(time())}.html"
        scatter_dir = "scatter_plots"
        
        # Make sure scatter plots directory exists
        if not os.path.exists(scatter_dir):
            os.makedirs(scatter_dir)
        
        filepath = os.path.join(scatter_dir, filename)
        
        # Write the scatter plot HTML to a file
        scatter_html = scatter_fig.to_html(include_plotlyjs=True, full_html=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(scatter_html)
        
        print(f"Saved scatter plot to {filepath}")

        # Open in system browser
        file_url = QUrl.fromLocalFile(os.path.abspath(filepath)).toString()
        webbrowser.open(file_url)
        print(f"Opened scatter plot in browser: {file_url}")

    # Add a validation method for density contour settings
    def validate_density_contour_settings(self):
        """
        Validates that all traces with density contour have sufficient data.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        # Get visible traces
        visible_traces = self._get_visible_traces()
        traces_with_issues = []
        
        for uid, model in visible_traces:
            # Skip contour traces or traces without density contour
            if getattr(model, "is_contour", False) or not getattr(model, "density_contour_on", False):
                continue
                
            # Get the dataframe for this trace
            df = self.setupMenuModel.data_library.dataframe_manager.get_dataframe_by_metadata(model.datafile)
            if df is None or df.empty:
                traces_with_issues.append((model.trace_name, "No data available"))
                continue
                
            # Apply filters if enabled
            if getattr(model, "filters_on", False) and hasattr(model, "filters"):
                filtered_df = df.copy()
                # ... apply filters ...
                if filtered_df.empty:
                    traces_with_issues.append((model.trace_name, "No data after applying filters"))
                    continue
                
                # Check if there are enough points for a meaningful contour
                if len(filtered_df) < 10:  # Arbitrary threshold
                    traces_with_issues.append((model.trace_name, f"Only {len(filtered_df)} points (minimum 10 recommended)"))
        
        # If any issues, show popup
        if traces_with_issues:
            message = "Cannot render density contours due to insufficient data:\n\n"
            
            for trace_name, issue in traces_with_issues:
                message += f"• Trace '{trace_name}': {issue}\n"
            
            message += "\nPlease ensure there are enough data points for contour generation."
            
            QMessageBox.warning(self, "Density Contour Issues", message)
            return False
                
        return True
    
    def _export_as_html_or_image(self, filepath: Path):
        """Export the current plot as a standalone HTML file."""
        try:

            # Get the current plot type
            current_plot_type = self.plotTypeSelector.currentText().lower()
            
            # Get visible traces
            visible_traces = self._get_visible_traces()
            regular_traces = [model for _, model in visible_traces if not getattr(model, "is_contour", False)]
            contour_traces = [(uid, model) for uid, model in visible_traces if getattr(model, "is_contour", False)]
            
            # Create the figure based on plot type
            if current_plot_type == 'ternary':
                fig = self.ternary_plot_maker.make_plot(self.setupMenuModel, regular_traces)
                
                # Add contour traces if any exist
                for uid, model in contour_traces:
                    contour_trace = self.ternary_contour_maker.make_trace(
                        model, self.setupMenuModel, uid
                    )
                    if contour_trace:
                        fig.add_trace(contour_trace)

                 # Add density contours for regular traces that have it enabled
                for uid, model in visible_traces:
                    # Skip bootstrap contour traces, they can't have density contours
                    if getattr(model, "is_contour", False):
                        continue
                    
                    # Check if density contour is enabled
                    if getattr(model, "density_contour_on", False):
                        print(f"Generating density contour for trace: {model.trace_name}")
                        
                        # Make sure DensityContourMaker is initialized
                        if not hasattr(self, 'density_contour_maker') or self.density_contour_maker is None:
                            print("Initializing DensityContourMaker")
                            self.density_contour_maker = DensityContourMaker()
                        
                        # Get contour traces (can now be multiple)
                        contour_traces = self.density_contour_maker.make_trace(
                            self.setupMenuModel, model, f"density-{uid}"
                        )
                        
                        if contour_traces:
                            if isinstance(contour_traces, list):
                                # Add each contour trace to the figure
                                print(f"Adding {len(contour_traces)} contour traces")
                                for trace in contour_traces:
                                    fig.add_trace(trace)
                            else:
                                # Handle case where a single trace is returned
                                print("Adding single contour trace")
                                fig.add_trace(contour_traces)
                        else:
                            print("Failed to create density contour traces")
            
            elif current_plot_type == 'cartesian':
                fig = self.cartesian_plot_maker.make_plot(self.setupMenuModel, regular_traces)
            else:
                QMessageBox.warning(
                    self, 
                    "Plot Type Not Supported", 
                    f"Exporting {current_plot_type} as HTML is not supported yet."
                )
                return

            # Get current plotView dimensions
            current_width = self.plotView.width()
            current_height = self.plotView.height()
            
            # Ensure minimum dimensions
            width = max(current_width, 300)
            height = max(current_height, 250)

            fig.update_layout(width=width, height=height)
            
            if str(filepath).lower().endswith('.html'):
                
                pio.write_html(fig, filepath)
                
                if Path(filepath).is_file():
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Plot exported as HTML to {filepath}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Export Failed",
                        f"Failed to export plot as HTML to {filepath}"
                    )

            else:

                # Get current plotView dimensions
                current_width = self.plotView.width()
                current_height = self.plotView.height()
                
                # Ensure minimum dimensions
                width = max(current_width, 300)
                height = max(current_height, 250)

                print(width, height)
                
                pio.write_image(fig, str(filepath), width=width, height=height, scale=8)

                if Path(filepath).is_file():
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Plot exported as {filepath.suffix.lstrip('.').upper()} to {filepath}"
                    )
                else:
                    QMessageBox.critical(
                        self,
                        "Export Failed",
                        f"Failed to export plot as PDF to {filepath}"
                    )
            
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export plot as HTML: {str(e)}"
            )

    def on_export_clicked(self):
        filepath, selected_filter = self.show_save_dialog()
        
        if not filepath:
            return

        self._export_as_html_or_image(filepath)

    def validate_formulas_for_molar_conversion(self):
        """
        Validates that all necessary chemical formulas are provided for traces 
        that have weight-to-molar conversion enabled.
        
        Returns:
            bool: True if validation passes, False otherwise
        """
        # Get visible traces that have weight-to-molar conversion enabled
        visible_traces = self._get_visible_traces()
        traces_needing_validation = [(uid, model) for uid, model in visible_traces 
                                    if getattr(model, "convert_from_wt_to_molar", False)]
        
        if not traces_needing_validation:
            return True  # No traces need validation
        
        # Get valid apex/axis columns
        apex_columns = {
            'top_axis': getattr(self.setupMenuModel.axis_members, 'top_axis', []),
            'left_axis': getattr(self.setupMenuModel.axis_members, 'left_axis', []),
            'right_axis': getattr(self.setupMenuModel.axis_members, 'right_axis', []),
            'x_axis': getattr(self.setupMenuModel.axis_members, 'x_axis', []),
            'y_axis': getattr(self.setupMenuModel.axis_members, 'y_axis', []),
        }
        
        # Get current formulas
        formula_model = self.setupMenuModel.chemical_formulas
        
        # Track missing or invalid formulas
        missing_formulas = []
        invalid_formulas = []
        
        # Check each trace that needs validation
        for uid, model in traces_needing_validation:
            # Get the dataframe
            df = self.setupMenuModel.data_library.dataframe_manager.get_dataframe_by_metadata(model.datafile)
            if df is None:
                continue
                
            # Check which columns need formulas
            for axis_name, columns in apex_columns.items():
                for column in columns:
                    if column in df.columns:
                        formula = formula_model.get_formula(axis_name, column)
                        
                        if not formula.strip():
                            missing_formulas.append((model.trace_name, column, axis_name))
                        elif not is_valid_formula(formula):
                            invalid_formulas.append((model.trace_name, column, formula, axis_name))
        
        # If problems found, show a warning
        if missing_formulas or invalid_formulas:
            message = "Cannot render plot with weight-to-molar conversion due to formula issues:\n\n"
            
            if missing_formulas:
                message += "Missing formulas:\n"
                for trace, column, axis in missing_formulas:
                    axis_display = axis.replace("_", " ").title()
                    message += f"• Trace '{trace}' needs formula for '{column}' on {axis_display}\n"
                message += "\n"
                
            if invalid_formulas:
                message += "Invalid formulas:\n"
                for trace, column, formula, axis in invalid_formulas:
                    axis_display = axis.replace("_", " ").title()
                    message += f"• Trace '{trace}': '{formula}' is not valid for '{column}' on {axis_display}\n"
            
            QMessageBox.warning(self, "Formula Validation Error", message)
            return False
            
        return True

    def on_preview_clicked(self):
        """Generate and display the current plot."""
        # Check if we should validate formulas (skip for Zmap)
        current_plot_type = self.plotTypeSelector.currentText().lower()
        
        # For non-Zmap plots, validate formulas
        if current_plot_type != 'zmap':
            if not self.validate_formulas_for_molar_conversion():
                return  # Don't proceed with rendering if validation fails
            
            # Add this new check for uncertainty values
            if current_plot_type in ['ternary', 'cartesian']:  # Only validate for ternary plots
                if not self.validate_uncertainty_entries():
                    return  # Don't proceed if uncertainty entries are missing
                
                if not self.validate_density_contour_settings():
                    return
            
            if not self.validate_axis_members():
                return  # Don't proceed with rendering if axis validation fails
        
        # Get visible traces
        visible_traces = self._get_visible_traces()

        print(f"Number of visible traces: {len(visible_traces)}")
        for i, (uid, model) in enumerate(visible_traces):
            print(f"Trace {i+1}: {model.trace_name}")
            print(f"  density_contour_on: {getattr(model, 'density_contour_on', False)}")
        
        if current_plot_type == 'zmap':
            # Check if we have enough data to create a zmap
            if not self.setupMenuModel.axis_members.categorical_column or not self.setupMenuModel.axis_members.numerical_columns:
                QMessageBox.warning(
                    self, 
                    "Missing Configuration",
                    "Please select a categorical column and at least one numerical column in the Setup Menu."
                )
                return
            
            # Generate the zmap plots
            success = self.zmap_plot_maker.make_plot(
                self.setupMenuModel, 
                [model for _, model in visible_traces]
            )
            
            if not success:
                QMessageBox.warning(
                    self, 
                    "Plot Generation Failed",
                    "Failed to generate Z-maps. Please check your data and configuration."
                )
                return
            
            # Get the current plot file path
            current_path = self.zmap_plot_maker.load_current_plot()
            
            if not current_path or not os.path.exists(current_path):
                QMessageBox.warning(
                    self, 
                    "File Not Found",
                    f"Could not find the plot file: {current_path}"
                )
                return
            
            # Load the plot using QUrl
            self.plotView.setUrl(QUrl.fromLocalFile(current_path))
            
            # Set the WebChannel for ZMap interactions
            self.plotView.page().setWebChannel(self.zmap_channel)
            
            # Show/hide the Zmap navigation buttons based on number of targets
            has_multiple_targets = len(self.zmap_plot_maker.heatmap_files) > 1
            self.zmapPrevButton.setVisible(has_multiple_targets)
            self.zmapNextButton.setVisible(has_multiple_targets)
            
            # Update status label if available
            if hasattr(self, 'statusLabel'):
                total_plots = len(self.zmap_plot_maker.heatmap_files)
                current_target = self.zmap_plot_maker.current_target
                self.statusLabel.setText(f"Plot {self.zmap_plot_maker.current_index + 1}/{total_plots}: {current_target}")
            
            return
        
        # For other plot types, hide Zmap buttons
        self.zmapPrevButton.setVisible(False)
        self.zmapNextButton.setVisible(False)
        
        if current_plot_type == 'ternary':
            # Handle ternary plots
            regular_traces = [model for _, model in visible_traces if not getattr(model, "is_contour", False)]
            contour_traces = [(uid, model) for uid, model in visible_traces if getattr(model, "is_contour", False)]

            # Create trace mapping to track which UI trace each plotly trace corresponds to
            trace_mapping = {}
            current_trace_index = 0
            
            # Create the basic figure with regular traces
            # fig = self.ternary_plot_maker.make_plot(self.setupMenuModel, regular_traces)
            fig = self.ternary_plot_maker.make_plot(self.setupMenuModel, [(uid, model) for uid, model in visible_traces if not getattr(model, "is_contour", False)])

            # For each regular trace, track its index in the plotly figure
            # and also track indices of any density contours it creates
            for ui_index, (uid, model) in enumerate(visible_traces):
                if getattr(model, "is_contour", False):
                    continue  # Skip contour traces here
                
                # Record mapping for this main trace
                trace_mapping[current_trace_index] = ui_index
                current_trace_index += 1  # Move to next plotly trace index
                
                # If this trace has density contours, account for them too
                if getattr(model, "density_contour_on", False):
                    # Check if it's multiple contours
                    if getattr(model, "density_contour_multiple", False):
                        percentiles_str = getattr(model, "density_contour_percentiles", "60,70,80")
                        try:
                            percentiles = [float(p.strip()) for p in percentiles_str.split(',') if p.strip()]
                            num_contours = len(percentiles) if percentiles else 3
                        except ValueError:
                            num_contours = 3
                    else:
                        num_contours = 1
                    
                    # Each contour gets its own plotly trace but maps back to the same UI trace
                    for _ in range(num_contours):
                        trace_mapping[current_trace_index] = ui_index
                        current_trace_index += 1
            
            # Add bootstrap contour traces if any exist
            for uid, model in contour_traces:
                contour_trace = self.ternary_contour_maker.make_trace(
                    model, self.setupMenuModel, uid
                )
                if contour_trace:
                    fig.add_trace(contour_trace)
                    trace_mapping[current_trace_index] = None  # Indicate this is a contour, not selectable
                    current_trace_index += 1
            
            # Add density contours for regular traces that have it enabled
            for ui_index, (uid, model) in enumerate(visible_traces):
                # Skip bootstrap contour traces, they can't have density contours
                if getattr(model, "is_contour", False):
                    continue
                
                # Check if density contour is enabled
                if getattr(model, "density_contour_on", False):
                    # Get contour traces (can now be multiple)
                    contour_traces = self.density_contour_maker.make_trace(
                        self.setupMenuModel, model, f"density-{uid}"
                    )
                    
                    if contour_traces:
                        if isinstance(contour_traces, list):
                            # Add each contour trace to the figure
                            for trace in contour_traces:
                                fig.add_trace(trace)
                        else:
                            # Handle case where a single trace is returned
                            fig.add_trace(contour_traces)
                    
            # Store the trace mapping in a global variable for bootstrap to use
            self.plotly_trace_mapping = trace_mapping
            print(f"Trace mapping: {trace_mapping}")
        
        elif current_plot_type == 'cartesian':
            # Create the figure with regular traces using cartesian plot maker
            fig = self.cartesian_plot_maker.make_plot(
                self.setupMenuModel, 
                [model for _, model in visible_traces if not getattr(model, "is_contour", False)]
            )
        
        elif current_plot_type == 'histogram':
            # TODO: Implement histogram plot maker
            QMessageBox.warning(
                self, 
                "Plot Type Not Supported", 
                "The plot type 'histogram' is not fully implemented yet."
            )
            return
        
        else:
            QMessageBox.warning(
                self, 
                "Plot Type Not Supported", 
                f"The plot type '{current_plot_type}' is not supported."
            )
            return

        # Generate HTML with plotlyInterface for ternary/cartesian plots
        html = fig.to_html()
        javascript = """
            <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                document.addEventListener("DOMContentLoaded", function() {
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.plotlyInterface = channel.objects.plotlyInterface;
                        var plotElement = document.getElementsByClassName('plotly-graph-div')[0];
                        plotElement.on('plotly_selected', function(eventData) {
                            if (eventData) {
                                var indices = eventData.points.map(function(pt) {
                                    return {traceID: pt.customdata[pt.customdata.length - 1], pointIndex: pt.customdata[pt.customdata.length - 2], curveNumber: pt.curveNumber};  // the index is the last item in customdata
                                });
                                window.plotlyInterface.receive_selected_indices(indices);
                            }
                        });
                    });
                });
            </script>
        """
        full = html + javascript
        
        fname = Path(__file__).parent / "__tmp.html"

        # Write temporary file and load it
        with open(fname, "w", encoding='utf-8') as f:
            f.write(full)
        
        self.plotView.setUrl(QUrl.fromLocalFile(fname))

    def _get_visible_traces(self):
        """
        Get a list of visible traces in the current plot.
        
        Returns:
            List of (trace_id, trace_model) tuples for visible traces.
        """
        visible_traces = []
        
        # Gather trace information in the order they appear in the tab panel
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                model = self.tabPanel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel) and not getattr(model, "hide_on", False):
                    visible_traces.append((uid, model))
        
        return visible_traces


    def on_bootstrap_clicked(self):
        """
        Handles the Bootstrap button click event.
        """
        # Get current plot type
        current_plot_type = self.plotTypeSelector.currentText().lower()

        # For now, bootstrapping is only implemented for ternary plots
        if current_plot_type != 'ternary':
            QMessageBox.warning(
                self, 
                "Bootstrapping Not Supported", 
                f"Bootstrapping is currently only supported for ternary plots."
            )
            return

        # Get selected indices from the plot
        indices = self.plotly_interface.get_indices()
        
        if not indices or len(indices) != 1:
            QMessageBox.warning(
                self, 
                "Selection Error",
                "Please select exactly one point using the lasso tool before bootstrapping."
            )
            return
        
        # Extract point information
        point_info = indices[0]
        print(f'{point_info=}')
        curve_number = point_info.get('curveNumber')
        point_index = point_info.get('pointIndex')
        # If we have source_trace_id in customdata, extract it
        source_trace_id = point_info.get('traceID')
        
        print(f"Selected point: curve={curve_number}, index={point_index}, source_id={source_trace_id}")
        
        # Extreme debugging: print all tabs to verify what we're working with
        print("All tabs in panel:")
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                model = self.tabPanel.id_to_widget.get(uid)
                is_contour = getattr(model, "is_contour", False) if model else False
                print(f"  Tab {i}: '{item.text()}', uid={uid}, is_contour={is_contour}")
        
        # Get all non-contour traces from the tab panel
        data_traces = []
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                model = self.tabPanel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel) and not getattr(model, "is_contour", False):
                    data_traces.append((uid, model))
        
        print(f"Found {len(data_traces)} data traces")
        
        # If we have a source_trace_id, use it to find the correct trace
        if source_trace_id:
            found_trace = False
            for i, (uid, model) in enumerate(data_traces):
                if uid == source_trace_id:
                    trace_uid = uid
                    trace_model = model
                    found_trace = True
                    print(f"Found source trace by ID: {model.trace_name}")
                    break
            
            if not found_trace:
                print(f"Couldn't find trace with ID {source_trace_id}, falling back to curve number")
                source_trace_id = None
        
        # If we don't have source_trace_id or couldn't find it, use curve number for backwards compatibility
        if not source_trace_id:
            if curve_number < 0 or curve_number >= len(data_traces):
                QMessageBox.warning(
                    self, 
                    "Selection Error",
                    f"Invalid curve number: {curve_number}. Please try again."
                )
                return
            
            trace_uid, trace_model = data_traces[curve_number]
        
        print(f"Selected trace for bootstrap: {trace_model.trace_name}")
        
        # Get the dataframe for this trace
        if not hasattr(trace_model, "datafile") or not trace_model.datafile:
            QMessageBox.warning(
                self, 
                "Data Error", 
                "The selected trace has no associated datafile."
            )
            return
        
        # Get the dataframe
        df = self.setupMenuModel.data_library.dataframe_manager.get_dataframe_by_metadata(
            trace_model.datafile
        )
        
        if df is None:
            QMessageBox.warning(
                self, 
                "Data Error", 
                "Could not retrieve data for the selected trace."
            )
            return
        
        # Extract the specific row from the dataframe
        # Get the row corresponding to the point index
        if point_index < len(df):
            series = df.iloc[point_index]
        else:
            QMessageBox.warning(
                self, 
                "Index Error", 
                f"Point index {point_index} is out of bounds for the dataframe."
            )
            return
        
        # Create a new trace with contour settings
        new_label = f"Contour from {trace_model.trace_name}"
        
        # Create new trace model
        model = TraceEditorModel(
            trace_name=new_label, 
            is_contour=True,
            contour_level="Contour: 1-sigma",  # Default to 1-sigma
            trace_color=trace_model.trace_color,  # Use the source trace color
            outline_thickness=2,  # Slightly thicker line for contours
            # Use the same datafile
            datafile=trace_model.datafile,
            # Use the same conversion setting
            convert_from_wt_to_molar=getattr(trace_model, "convert_from_wt_to_molar", False)
        )
        
        # Set the source point data
        model.set_source_point(series, {
            "source_trace_id": trace_uid,
            "point_index": point_index
        })
        
        # Add the new trace to the tab panel
        uid = self.tabPanel.add_tab(new_label, model)
        
        # Save current tab data and switch to the new tab
        self._save_current_tab_data()
        self.current_tab_id = uid
        
        # Set the model in the trace editor view
        self.traceEditorView.set_model(model)
        self.traceEditorController.model = model
        self._show_trace_editor()

    def on_tab_selected(self, unique_id: str):
        self._save_current_tab_data()
        self.current_tab_id = unique_id
        if unique_id == "setup-menu-id":
            self._show_setup_content()
        else:
            model = self.tabPanel.id_to_widget.get(unique_id)
            if isinstance(model, TraceEditorModel):
                # Update model first
                self.traceEditorView.set_model(model)
                self.traceEditorController.model = model
                
                # Then show the editor (which will update the UI)
                self._show_trace_editor()
            else:
                self.traceEditorView.set_model(TraceEditorModel())
                self._show_trace_editor()

    def on_tab_renamed(self, unique_id: str, new_label: str):
        if unique_id == "setup-menu-id":
            return
        model = self.tabPanel.id_to_widget.get(unique_id)
        if isinstance(model, TraceEditorModel):
            model.trace_name = new_label
        # Update the display text of the corresponding QListWidgetItem.
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if it and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                it.setText(new_label)
                break

    def on_tab_removed(self, unique_id: str):
        if unique_id == "setup-menu-id":
            return
        
        # Get the model before deletion to check if we should release its color
        model = self.tabPanel.id_to_widget.get(unique_id)
        is_contour = False
        trace_color = None

        if isinstance(model, TraceEditorModel):
            is_contour = getattr(model, "is_contour", False)
            trace_color = getattr(model, "trace_color", None)
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Only release the color if it's a non-contour trace
        if not is_contour and trace_color:
            self.color_palette.release_color(trace_color)

        if unique_id == self.current_tab_id:
            self._save_current_tab_data()
            self.current_tab_id = "setup-menu-id"
            self.tabPanel.listWidget.setCurrentRow(0)
            self._show_setup_content()

        self.tabPanel.remove_tab_by_id(unique_id)

    def create_new_tab(self):
        # Check if any data files have been loaded.
        if not self.setupMenuModel.data_library.loaded_files:
            QMessageBox.warning(self, "Warning", "Please add data first")
            return

        new_trace_number = self._find_next_trace_number()
        new_label = f"Trace {new_trace_number}"

        # Get the next color from the palette for non-contour traces
        next_color = self.color_palette.next_color()

        # Create the model with selected datafile
        model = TraceEditorModel(trace_name=new_label, trace_color=next_color)

        # Assign the first datafile from the library to the new trace
        if self.setupMenuModel.data_library.loaded_files:
            first_datafile = self.setupMenuModel.data_library.loaded_files[0]
            model.datafile = first_datafile
            
            # Pre-initialize column fields with default values from datafile
            try:
                # Get numeric columns from the datafile
                if first_datafile and first_datafile.file_path:
                    df = self.setupMenuModel.data_library.dataframe_manager.get_dataframe_by_metadata(first_datafile)
                    if df is not None and not df.empty:
                        numeric_cols = get_numeric_columns_from_dataframe(df)
                        if numeric_cols:
                            # Set default columns (even though features are off)
                            model.heatmap_column = numeric_cols[0]
                            model.sizemap_column = numeric_cols[0]
                            print(f"Pre-initialized heatmap and sizemap columns to '{numeric_cols[0]}'")
            except Exception as e:
                print(f"Error pre-initializing columns: {e}")
        
        uid = self.tabPanel.add_tab(new_label, model)
        self._save_current_tab_data()
        self.current_tab_id = uid

        # Set the model
        self.traceEditorView.set_model(model)
        self.traceEditorController.model = model
        self._show_trace_editor()

    def update_trace_datafile_options(self):
        """Update datafile combobox with display strings while preserving selection."""
        # Get the list of loaded data files
        data_files = self.setupMenuModel.data_library.loaded_files
        combobox = self.traceEditorView.widgets.get("datafile")
        
        if combobox:
            # Block signals to prevent unintended triggers
            combobox.blockSignals(True)
            
            # Get current model value to preserve
            current_metadata = self.traceEditorView.model.datafile
            if isinstance(current_metadata, str):
                # Fix: Convert string to metadata if needed
                current_metadata = self.ensure_datafile_metadata(current_metadata)
                # Update the model
                self.traceEditorView.model.datafile = current_metadata
                
            current_display_str = str(current_metadata) if current_metadata else ""
            
            # Clear existing items
            combobox.clear()
            
            # Add a display string for each metadata object
            display_strings = []
            for meta in data_files:
                display_str = str(meta)
                display_strings.append(display_str)
                combobox.addItem(display_str)
            
            # Try to select the combobox item that matches the model's datafile
            index = -1
            if current_display_str:
                index = combobox.findText(current_display_str)
                
            if index >= 0:
                combobox.setCurrentIndex(index)
            elif data_files:
                # If not found but we have files, select the first one but don't update model
                combobox.setCurrentIndex(0)
            
            # Unblock signals
            combobox.blockSignals(False)

    def _find_next_trace_number(self) -> int:
        pattern = re.compile(r"^Trace\s+(\d+)$")
        largest_number = 0
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if not it:
                continue
            text = it.text()
            match = pattern.match(text)
            if match:
                num = int(match.group(1))
                if num > largest_number:
                    largest_number = num
        return largest_number + 1

    def _save_current_tab_data(self):
        pass

    def _show_setup_content(self):
        self.centerStack.setCurrentWidget(self.setupMenuView)

    def on_trace_color_changed(self, new_color):
        """Handle when a trace's color is manually changed."""
        # Refresh our color tracking by examining all traces
        trace_models = [model for uid, model in self.tabPanel.id_to_widget.items() 
                    if uid != "setup-menu-id" and isinstance(model, TraceEditorModel)]
        self.color_palette.sync_with_traces(trace_models)

    def _show_trace_editor(self):
        self.centerStack.setCurrentWidget(self.traceEditorView)

        # Save the original model values before any updates
        model = self.traceEditorView.model
        original_heatmap_column = model.heatmap_column
        original_sizemap_column = model.sizemap_column

        # Block ALL signals during UI update
        for widget_name, widget in self.traceEditorView.widgets.items():
            if hasattr(widget, "blockSignals"):
                widget.blockSignals(True)

        # Connect to the color change signal
        color_button = self.traceEditorView.widgets.get("trace_color")
        if color_button and isinstance(color_button, ColorButton):
            # Disconnect any existing connections to avoid duplicates
            try:
                color_button.colorChanged.disconnect(self.on_trace_color_changed)
            except (TypeError, RuntimeError):
                pass  # No connection existed
            
            # Connect our handler
            color_button.colorChanged.connect(self.on_trace_color_changed)

        # Handle the datafile selector widget
        datafile_selector = self.traceEditorView.widgets.get("datafile")
        if datafile_selector and isinstance(datafile_selector, DatafileSelector):
            # Set the current datafile
            datafile_selector.setDatafile(model.datafile)
            
            # Set the main window reference
            datafile_selector.setMainWindow(self)
            
            # Set all available datafiles
            if hasattr(self.setupMenuModel, "data_library"):
                all_datafiles = self.setupMenuModel.data_library.loaded_files
                datafile_selector.setAllDatafiles(all_datafiles)

        # Process numeric columns for the current datafile
        datafile = model.datafile
        if datafile:
            # FIX: Handle case where datafile is a string instead of DataFileMetadata
            if isinstance(datafile, str):
                # Try to convert the string to DataFileMetadata
                metadata = self.setupMenuModel.data_library.get_metadata_by_display_string(datafile)
                if metadata:
                    model.datafile = metadata  # Update the model with proper object
                    datafile = metadata
                else:
                    # If can't find by display string, try to find by path
                    metadata = self.setupMenuModel.data_library.get_metadata_by_path(datafile)
                    if metadata:
                        model.datafile = metadata
                        datafile = metadata

            # Continue only if we have a valid DataFileMetadata with file_path
            if hasattr(datafile, 'file_path') and datafile.file_path:
                numeric_cols = get_numeric_columns_from_file(
                    datafile.file_path, header=datafile.header_row, sheet=datafile.sheet
                )

                # Directly update the comboboxes without triggering signals
                heatmap_combo = self.traceEditorView.widgets.get("heatmap_column")
                if heatmap_combo and isinstance(heatmap_combo, QComboBox):
                    heatmap_combo.clear()
                    heatmap_combo.addItems(numeric_cols)
                    # Add the original value if it's not in the list
                    if (
                        original_heatmap_column
                        and original_heatmap_column not in numeric_cols
                    ):
                        heatmap_combo.addItem(original_heatmap_column)
                    # Now set the combobox value to match the model
                    heatmap_combo.setCurrentText(original_heatmap_column)

                sizemap_combo = self.traceEditorView.widgets.get("sizemap_column")
                if sizemap_combo and isinstance(sizemap_combo, QComboBox):
                    sizemap_combo.clear()
                    sizemap_combo.addItems(numeric_cols)
                    # Add the original value if it's not in the list
                    if (
                        original_sizemap_column
                        and original_sizemap_column not in numeric_cols
                    ):
                        sizemap_combo.addItem(original_sizemap_column)
                    # Now set the combobox value to match the model
                    sizemap_combo.setCurrentText(original_sizemap_column)

        # Unblock signals after all updates are done
        for widget_name, widget in self.traceEditorView.widgets.items():
            if hasattr(widget, "blockSignals"):
                widget.blockSignals(False)

        # Make sure the model still has the original values
        # This is a safeguard in case any signals still fired
        model.heatmap_column = original_heatmap_column
        model.sizemap_column = original_sizemap_column

    def on_plot_type_changed(self, plot_type: str):
        plot_type_lower = plot_type.lower()
        
        # Show/hide Zmap buttons based on plot type
        is_zmap = plot_type_lower == 'zmap'
        self.zmapPrevButton.setVisible(is_zmap)
        self.zmapNextButton.setVisible(is_zmap)
        
        # Update views with new plot type
        self.traceEditorView.set_plot_type(plot_type_lower)
        self.setupMenuView.set_plot_type(plot_type_lower)

  
    def save_workspace(self):
        """Create a serializable representation of the workspace without using
        deep copying, which can preserve references to DataframeManager."""
        # Create new, clean dictionaries instead of copying objects
        traces_data = []
        order = []

        # Gather trace information
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                order.append(uid)
                model = self.tabPanel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel):
                    # Manually create a clean representation of the trace
                    trace_data = {}
                    for f in fields(model):
                        if f.name == "datafile":
                            # Manually extract datafile metadata without df_id
                            datafile = getattr(model, f.name)
                            # FIX: Handle string datafiles
                            if isinstance(datafile, DataFileMetadata):
                                trace_data["datafile"] = {
                                    "file_path": datafile.file_path,
                                    "header_row": datafile.header_row,
                                    "sheet": datafile.sheet,
                                }
                            elif isinstance(datafile, str):
                                # Try to convert from display string
                                metadata = self.setupMenuModel.data_library.get_metadata_by_display_string(datafile)
                                if metadata:
                                    trace_data["datafile"] = {
                                        "file_path": metadata.file_path,
                                        "header_row": metadata.header_row,
                                        "sheet": metadata.sheet,
                                    }
                                else:
                                    # Fallback to basic metadata
                                    trace_data["datafile"] = {
                                        "file_path": datafile,
                                        "header_row": None,
                                        "sheet": None,
                                    }
                            else:
                                # Fallback for None or other types
                                trace_data["datafile"] = {
                                    "file_path": "",
                                    "header_row": None,
                                    "sheet": None,
                                }
                        elif f.name == "filters":
                            # Handle filters list
                            filters = getattr(model, f.name)
                            filters_data = []
                            for filter_model in filters:
                                filter_data = {}
                                for filter_field in fields(filter_model):
                                    filter_data[filter_field.name] = getattr(
                                        filter_model, filter_field.name
                                    )
                                filters_data.append(filter_data)
                            trace_data[f.name] = filters_data
                        elif f.name == "error_entry_model":
                            # Handle error entry model specially
                            error_model = getattr(model, f.name)
                            if hasattr(error_model, "to_dict"):
                                trace_data[f.name] = error_model.to_dict()
                            else:
                                trace_data[f.name] = {}
                        elif f.name == "source_point_data":
                            # Handle source point data specially
                            source_data = getattr(model, f.name)
                            source_data_copy = source_data.copy() if isinstance(source_data, dict) else {}
                            
                            # Convert series to JSON if present
                            if "series" in source_data_copy and isinstance(source_data_copy["series"], pd.Series):
                                source_data_copy["series"] = source_data_copy["series"].to_json()
                                
                            trace_data[f.name] = source_data_copy
                        else:
                            # Copy other fields directly
                            trace_data[f.name] = getattr(model, f.name)
                    traces_data.append(trace_data)

        setup_data = self.setupMenuModel.to_dict()

        # Build the complete workspace data
        workspace_data = {
            "version": WorkspaceManager.VERSION,
            "order": order,
            "traces": traces_data,
            "setup": setup_data,
        }

        # Save to file
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Workspace", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, "w", encoding='utf-8') as f:
                    json.dump(workspace_data, f, indent=2, cls=CustomJSONEncoder)
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(
                    self, "Error", f"Failed to save workspace: {str(e)}"
                )

    def load_workspace(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Workspace", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                workspace = WorkspaceManager.load_from_file(filename)

                # Validate data files and get mapping for any relocated files
                file_path_mapping = validate_data_library(
                    workspace.setup_model.data_library, self
                )

                # Update all trace models with the new file paths
                for trace_model in workspace.traces:
                    if hasattr(trace_model, "datafile"):
                        # FIX: Ensure datafile is a proper DataFileMetadata object
                        if isinstance(trace_model.datafile, dict):
                            # Convert from dict to DataFileMetadata
                            trace_model.datafile = DataFileMetadata.from_dict(trace_model.datafile)
                        elif isinstance(trace_model.datafile, str):
                            # Convert from string to DataFileMetadata
                            try:
                                trace_model.datafile = DataFileMetadata.from_display_string(trace_model.datafile)
                            except Exception:
                                # Fallback to basic metadata
                                trace_model.datafile = DataFileMetadata(file_path=trace_model.datafile)
                        
                        # Now update path if needed
                        if isinstance(trace_model.datafile, DataFileMetadata):
                            old_path = trace_model.datafile.file_path
                            if old_path in file_path_mapping:
                                new_path = file_path_mapping[old_path]
                                trace_model.datafile.file_path = new_path


                # Sync the color palette with the loaded traces
                self.color_palette.sync_with_traces(workspace.traces)

                # (1) Update data_library
                self.setupMenuModel.data_library.loaded_files = (
                    []
                )  # Clear existing files
                for metadata in workspace.setup_model.data_library.loaded_files:
                    self.setupMenuModel.data_library.add_file(metadata)

                # (2) Update other sections
                for section_name in [
                    "plot_labels",
                    "axis_members",
                    "column_scaling",
                    "chemical_formulas",
                    "advanced_settings",
                ]:
                    loaded_section = getattr(workspace.setup_model, section_name)
                    current_section = getattr(self.setupMenuModel, section_name)
                    for f in fields(loaded_section):
                        setattr(
                            current_section, f.name, getattr(loaded_section, f.name)
                        )

                # Load all dataframes into memory and set up display string mapping
                for metadata in self.setupMenuModel.data_library.loaded_files:
                    # Load the dataframe - this will also set up the display string mapping
                    df_id = self.setupMenuModel.data_library.dataframe_manager.load_dataframe(metadata)
                    if df_id:
                        metadata.df_id = df_id
                    else:
                        print(f"Warning: Failed to load dataframe for {str(metadata)}")

                # Refresh the setup menu view (no need to set model since it's the same object)
                self.setupMenuView.update_from_model()
                self.setupMenuView.set_plot_type(self.setupMenuView.current_plot_type)

                # IMPORTANT: Force update of the axis options after loading
                self.setupController.update_axis_options()

                # Clear existing trace tabs (except the setup-menu)
                keys_to_remove = [
                    uid for uid in self.tabPanel.id_to_widget if uid != "setup-menu-id"
                ]
                for uid in keys_to_remove:
                    self.tabPanel.remove_tab_by_id(uid)

                # Add each loaded trace to the TabPanel
                trace_ids = []
                for trace_model in workspace.traces:
                    uid = self.tabPanel.add_tab(trace_model.trace_name, trace_model)
                    trace_ids.append((uid, trace_model))

                # IMPORTANT: Force content update before changing tab selection
                self.centerStack.setCurrentWidget(self.setupMenuView)
                # self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")

                # Now safe to update current tab state
                self.current_tab_id = "setup-menu-id"

                # Select the Setup Menu tab
                self.tabPanel.listWidget.setCurrentRow(0)

                # Process events to ensure UI is fully updated
                QApplication.processEvents()

                # Little bit redundant...
                self.tabPanel.listWidget.setCurrentRow(0)
                self.tabPanel.select_tab_by_id("setup-menu-id")
                self.tabPanel.tabSelectedCallback("setup-menu-id")
                QApplication.processEvents()

                # Reset the color palette when loading a workspace
                # self.color_palette.reset()

            # TODO fix this lazy handling
            except Exception as e:
                traceback.print_exc()
                QMessageBox.critical(
                    self, "Error", f"Failed to load workspace: {str(e)}"
                )

    def _fix_combobox_model_sync(self, combo_name, model_field_name):
        """Make sure the combobox and model value stay in sync."""
        combo = self.traceEditorView.widgets.get(combo_name)
        if combo and hasattr(self.traceEditorView.model, model_field_name):
            model_value = getattr(self.traceEditorView.model, model_field_name)

            # Force the model value into the combobox options
            if model_value and combo.findText(model_value) == -1:
                combo.addItem(model_value)

            # Set the combobox to the model value
            combo.setCurrentText(model_value)


    def on_trace_name_changed(self, new_name: str):
        """
        Update the tab name when the trace name field changes.
        Uses a flag to prevent focus loss while typing.
        """
        # Update the display text of the currently selected tab in the sidebar.
        uid = self.current_tab_id
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == uid:
                # Set the flag to indicate this is a programmatic change
                self.tabPanel.is_programmatic_change = True
                
                # Update the text
                item.setText(new_name)
                
                # Reset the flag
                self.tabPanel.is_programmatic_change = False
                break
