from dataclasses import fields
from typing import TYPE_CHECKING

# ---------------------------------

import pandas as pd
from PySide6.QtWidgets import (
    QGroupBox, 
    QHBoxLayout, 
    QVBoxLayout,
    QWidget, 
    QScrollArea, 
    QFormLayout,
    QVBoxLayout, 
    QComboBox, 
    QLineEdit, 
    QDoubleSpinBox, 
    QSpinBox, 
    QCheckBox, 
    QGroupBox, 
    QTableView, 
    QMessageBox,
    QHeaderView
)
from PySide6.QtCore import Qt

# ---------------------------------

from quick_ternaries.models.pandas_series_model import PandasSeriesModel
from quick_ternaries.models.filter_model import FilterModel

from quick_ternaries.views.filter_editor_view import FilterEditorView
from quick_ternaries.views.widgets import (
    ColorButton,
    DatafileSelector,
    ColorScaleDropdown,
    ShapeButtonWithMenu,
    ErrorEntryWidget,
    FilterTabWidget
)
from quick_ternaries.utils.functions import (
    get_all_columns_from_file,
    get_numeric_columns_from_dataframe
)

if TYPE_CHECKING:
    from quick_ternaries.models.trace_editor_model import TraceEditorModel



class TraceEditorView(QWidget):
    def __init__(self, model: "TraceEditorModel", parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # default
        self.widgets = {}  # Maps field names to widget instances.
        self.group_boxes = {}  # Maps group names to (group_box, layout)

        # Wrap the entire editor in a scroll area.
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.form_layout = QFormLayout(self.content)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)
        self.content.setLayout(self.form_layout)
        self.scroll.setWidget(self.content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll)
        self.setLayout(main_layout)

        self._build_ui()
        self.set_plot_type(self.current_plot_type)

    def _on_feature_enabled(self, feature_name: str, enabled: bool):
        """Initialize column when a feature like heatmap or sizemap is enabled."""
        if not enabled:
            return
            
        print(f"{feature_name} was enabled, initializing column")
        main_window = self.window()
        if not hasattr(main_window, "traceEditorController"):
            print(f"No controller found to initialize {feature_name} column")
            return
            
        controller = main_window.traceEditorController
        
        # Get the current datafile
        datafile = self.model.datafile
        if not datafile or not datafile.file_path:
            print(f"No datafile available for {feature_name} column initialization")
            return
            
        # Get the dataframe
        df = None
        try:
            df = controller.data_library.dataframe_manager.get_dataframe_by_metadata(datafile)
        except Exception as e:
            print(f"Error getting dataframe: {e}")
            
        if df is None or df.empty:
            print(f"No dataframe available for {feature_name} column initialization")
            return
            
        # Get numeric columns
        numeric_cols = get_numeric_columns_from_dataframe(df)
        if not numeric_cols:
            print(f"No numeric columns available for {feature_name}")
            return
            
        # Get the appropriate combo box
        combo_name = f"{feature_name}_column"
        combo = self.widgets.get(combo_name)
        if not combo or not isinstance(combo, QComboBox):
            print(f"No combo box found for {feature_name}_column")
            return
            
        # Initialize the model with the first numeric column
        first_column = numeric_cols[0]
        print(f"Initializing {feature_name}_column to '{first_column}'")
        
        # Block signals to prevent double-updates
        combo.blockSignals(True)
        
        # Set the model value
        setattr(self.model, combo_name, first_column)
        
        # Update the combo box
        combo.clear()
        combo.addItems(numeric_cols)
        combo.setCurrentText(first_column)
        
        combo.blockSignals(False)
        
        # For heatmap, also update min/max
        if feature_name == "heatmap":
            print("Updating heatmap min/max after initialization")
            controller._update_heatmap_min_max_for_column(first_column)

    def connect_column_change_handlers(self):
        """Connect column change signals to update min/max values."""
        # Connect heatmap column combo if it exists
        heatmap_combo = self.widgets.get("heatmap_column")
        if heatmap_combo and isinstance(heatmap_combo, QComboBox):
            main_window = self.window()
            if hasattr(main_window, "traceEditorController"):
                controller = main_window.traceEditorController
                
                # First disconnect any existing connections
                try:
                    heatmap_combo.currentTextChanged.disconnect()
                except (TypeError, RuntimeError):
                    pass  # No connections exist
                
                # Connect to controller's handler
                print("Connecting heatmap column change to min/max update")
                heatmap_combo.currentTextChanged.connect(controller._on_heatmap_column_changed)
                
                # Also ensure model gets updated
                heatmap_combo.currentTextChanged.connect(
                    lambda text: setattr(self.model, "heatmap_column", text)
                )
                
                # If heatmap is on and we have a column, update min/max immediately
                if getattr(self.model, "heatmap_on", False) and self.model.heatmap_column:
                    print(f"Initial heatmap column: {self.model.heatmap_column}")
                    controller._update_heatmap_min_max_for_column(self.model.heatmap_column)

    def connect_datafile_selector(self):
        """Ensure the datafile selector widget is properly connected to the controller."""
        datafile_selector = self.widgets.get("datafile")
        if datafile_selector and isinstance(datafile_selector, DatafileSelector):
            # Set the main window reference
            main_window = self.window()
            datafile_selector.setMainWindow(main_window)
            
            # Update available datafiles
            if hasattr(main_window, "setupMenuModel") and hasattr(main_window.setupMenuModel, "data_library"):
                all_datafiles = main_window.setupMenuModel.data_library.loaded_files
                datafile_selector.setAllDatafiles(all_datafiles)
            
            # Connect to controller if not already connected
            if hasattr(main_window, "traceEditorController"):
                # Disconnect any existing connections to avoid duplicates
                try:
                    datafile_selector.datafileChanged.disconnect()
                except (TypeError, RuntimeError):
                    pass  # No connections exist
                    
                # Connect to the controller's on_datafile_changed method
                datafile_selector.datafileChanged.connect(main_window.traceEditorController.on_datafile_changed)
                
                # Set current datafile to ensure display is correct
                datafile_selector.setDatafile(self.model.datafile)


    def update_filter_columns(self, all_cols=None):
        """Update all filter columns based on the current datafile."""
        if not hasattr(self, "filterTabWidget"):
            return
            
        # If all_cols is not provided, get them from the current datafile
        if all_cols is None:
            datafile = self.model.datafile
            if not datafile:
                return
                
            # Get datafile as proper DataFileMetadata if it's a string
            if isinstance(datafile, str):
                metadata = None
                try:
                    # Try as display string first
                    metadata = self.window().setupMenuModel.data_library.get_metadata_by_display_string(datafile)
                    if not metadata:
                        # Then try as path
                        metadata = self.window().setupMenuModel.data_library.get_metadata_by_path(datafile)
                except:
                    pass
                    
                # If we couldn't convert, just return
                if not metadata:
                    return
                datafile = metadata
                
            # Now get columns from the dataframe
            all_cols = get_all_columns_from_file(
                datafile.file_path, 
                header=datafile.header_row, 
                sheet=datafile.sheet
            )
            
        if not all_cols:
            return

        # Get the currently selected filter
        current_index = self.filterTabWidget.currentRow()
        if current_index < 0 or current_index >= len(self.model.filters):
            return

        # Update any visible filter editor
        for child in self.findChildren(FilterEditorView):
            filter_combo = child.widgets.get("filter_column")
            if filter_combo:
                # Get the current value before updating
                current_value = filter_combo.currentText()

                # Update with new items
                filter_combo.blockSignals(True)
                filter_combo.clear()
                filter_combo.addItems(all_cols)

                # Check if current value exists in the new columns
                if current_value in all_cols:
                    filter_combo.setCurrentText(current_value)
                else:
                    # If not valid, update model and UI with first column
                    if all_cols:
                        # Get the filter model for this editor
                        if hasattr(child, "filter_model"):
                            child.filter_model.filter_column = all_cols[0]
                        filter_combo.setCurrentText(all_cols[0])

                filter_combo.blockSignals(False)
                
                # Update the filter value widgets based on the new column
                child.update_filter_value_widgets()

    def _build_ui(self):
        # Clear existing state.
        self.widgets = {}
        self.group_boxes = {}
        self.subgroup_boxes = {}  # Track nested group boxes
        group_fields = {}
        subgroup_fields = {}  # Track fields that go in nested group boxes

        # Process each field in the model.
        for idx, f in enumerate(fields(self.model)):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            
            # Special handling for datafile field - replace combobox with our custom widget
            if f.name == "datafile":
                # Create our custom datafile selector widget instead of the default widget
                widget = DatafileSelector(self)
                widget.setDatafile(getattr(self.model, f.name))
                
                # Set the main window reference for access to controller
                main_window = self.window()
                widget.setMainWindow(main_window)
                
                # Get all datafiles from the data library
                if hasattr(main_window, "setupMenuModel") and hasattr(main_window.setupMenuModel, "data_library"):
                    all_datafiles = main_window.setupMenuModel.data_library.loaded_files
                    widget.setAllDatafiles(all_datafiles)
                
                # Connect the datafileChanged signal to controller
                if hasattr(main_window, "traceEditorController"):
                    widget.datafileChanged.connect(main_window.traceEditorController.on_datafile_changed)
                
                self.widgets[f.name] = widget
                self.form_layout.addRow(label_text, widget)
                continue
                
            # Normal handling for other fields
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                if f.name == "trace_name":
                    widget.textChanged.connect(
                        lambda text, fname=f.name: self._on_trace_name_changed(text)
                    )
                else:
                    widget.textChanged.connect(
                        lambda text, fname=f.name: setattr(self.model, fname, text)
                    )
            elif isinstance(widget, ColorButton):
                widget.setColor(value)
                widget.colorChanged.connect(
                    lambda color_str, fname=f.name: setattr(
                        self.model, fname, color_str
                    )
                )
            elif isinstance(widget, ColorScaleDropdown):
                # Handle our custom ColorScaleDropdown
                widget.setColorScale(value)
                widget.colorScaleChanged.connect(
                    lambda scale_str, fname=f.name: setattr(
                        self.model, fname, scale_str
                    )
                )
            elif isinstance(widget, ShapeButtonWithMenu):
                # Special handling for our custom shape buttons
                widget.setShape(value)
                widget.shapeChanged.connect(
                    lambda shape_str, fname=f.name: setattr(
                        self.model, fname, shape_str
                    )
                )
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
                widget.valueChanged.connect(
                    lambda val, fname=f.name: setattr(self.model, fname, val)
                )
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
                widget.valueChanged.connect(
                    lambda val, fname=f.name: setattr(self.model, fname, val)
                )
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
                widget.stateChanged.connect(
                    lambda state, fname=f.name: setattr(self.model, fname, bool(state))
                )
                if f.name in (
                        "heatmap_on", 
                        "sizemap_on", 
                        "density_contour_on", 
                        "custom_colorscale_on"):
                    widget.stateChanged.connect(
                        lambda _: self.set_plot_type(self.current_plot_type)
                    )
                    if f.name == 'heatmap_on':
                        widget.stateChanged.connect(
                            lambda state: self.connect_column_change_handlers() if state else None
                        )
                        widget.stateChanged.connect(
                            lambda state: self._on_feature_enabled("heatmap", bool(state))
                        )
                    elif f.name == 'sizemap_on':
                        widget.stateChanged.connect(
                            lambda state: self.connect_column_change_handlers() if state else None
                        )
                        widget.stateChanged.connect(
                            lambda state: self._on_feature_enabled("sizemap", bool(state))
                        )
                if f.name == "filters_on":
                    widget.stateChanged.connect(
                        lambda _: self._update_filters_visibility()
                    )
                if f.name == "density_contour_multiple":
                    widget.stateChanged.connect(
                        lambda state: self._update_multiple_contours_visibility(bool(state))
                    )
            elif isinstance(widget, QComboBox):
                if f.name in ["apex_red_mapping", "apex_green_mapping", "apex_blue_mapping"]:
                    widget.addItems(["top_axis", "left_axis", "right_axis"])
                    widget.setCurrentText(str(value))
                elif f.name == "line_style":
                    widget.addItems(['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'])
                elif f.name == "heatmap_sort_mode":
                    widget.addItems(
                        ["no change", "high on top", "low on top", "shuffled"]
                    )
                elif f.name == "heatmap_colorscale":
                    widget.addItems(["Viridis", "Cividis", "Plasma", "Inferno"])
                elif f.name == "sizemap_sort_mode":
                    widget.addItems(["no change", "high on top", "low on top", "shuffled"])
                elif f.name == "sizemap_scale":
                    widget.addItems(["linear", "log"])
                elif f.name == "heatmap_bar_orientation":
                    widget.addItems(["vertical", "horizontal"])
                elif f.name == "contour_level":
                    widget.addItems(["Contour: 1-sigma", "Contour: 2-sigma"])
                else:
                    widget.addItems([])
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(
                    lambda text, fname=f.name: setattr(self.model, fname, text)
                )

            # Enhanced grouping with subgrouping support
            group_name = metadata.get("group", None)
            subgroup_name = metadata.get("subgroup", None)

            if group_name and subgroup_name:
                # This field goes in a nested group box
                key = (group_name, subgroup_name)
                if key not in subgroup_fields:
                    subgroup_fields[key] = []
                subgroup_fields[key].append((f.name, label_text, widget, metadata))
            elif group_name:
                # This field goes in a regular group box
                if group_name not in group_fields:
                    group_fields[group_name] = []
                group_fields[group_name].append((f.name, label_text, widget, metadata))
            else:
                # This field goes directly in the form
                self.form_layout.addRow(label_text, widget)

        # Add contour-specific sections if this is a contour trace
        if getattr(self.model, "is_contour", False):
            # Add source point data display widget
            self.add_source_point_info()
            # Add error entry widget
            self.add_error_entry_widget()

        # Now handle group boxes and nested group boxes
        # (rest of the method remains unchanged from original)
        for group_name, field_tuples in group_fields.items():
            if group_name == "heatmap":
                # Special handling for heatmap group
                group_box = QGroupBox("Heatmap", self)
                vlayout = QVBoxLayout(group_box)

                # Create a form layout for basic fields
                basic_form = QFormLayout()
                basic_form.setLabelAlignment(Qt.AlignLeft)

                # Create an advanced container
                advanced_container = QWidget(self)
                advanced_form = QFormLayout(advanced_container)
                advanced_form.setLabelAlignment(Qt.AlignLeft)
                advanced_container.setLayout(advanced_form)
                self.advanced_heatmap_container = advanced_container

                # Process field tuples to separate basic and advanced
                toggle_tuple = None
                for fname, label_text, widget, meta in field_tuples:
                    if fname == "heatmap_use_advanced":
                        toggle_tuple = (fname, label_text, widget, meta)
                    elif meta.get("advanced", False):
                        # Only add fields without a subgroup directly to advanced form
                        if not meta.get("subgroup"):
                            advanced_form.addRow(label_text, widget)
                    else:
                        basic_form.addRow(label_text, widget)

                # Add basic form to the main layout
                vlayout.addLayout(basic_form)

                # Add the advanced toggle after basic fields
                if toggle_tuple:
                    t_fname, t_label, t_widget, t_meta = toggle_tuple
                    basic_form.addRow(t_label, t_widget)
                    # Connect the toggle to update visibility of advanced items
                    if isinstance(t_widget, QCheckBox):
                        # Disconnect any existing connections first to avoid duplicates
                        try:
                            t_widget.stateChanged.disconnect()
                        except:
                            pass
                        # Connect to our enhanced handler
                        t_widget.stateChanged.connect(
                            lambda state: self._update_advanced_visibility(bool(state))
                        )

                # Now handle any nested group boxes within the heatmap advanced section
                for (group, subgroup), sub_field_tuples in subgroup_fields.items():
                    if group == "heatmap":
                        # Create the nested group box with title from metadata
                        subgroup_title = sub_field_tuples[0][3].get(
                            "subgroup_title", subgroup.replace("_", " ").title()
                        )
                        nested_group_box = QGroupBox(subgroup_title)
                        nested_layout = QFormLayout(nested_group_box)
                        nested_layout.setLabelAlignment(Qt.AlignLeft)

                        # Add fields to the nested group box
                        for (
                            sub_fname,
                            sub_label,
                            sub_widget,
                            sub_meta,
                        ) in sub_field_tuples:
                            nested_layout.addRow(sub_label, sub_widget)

                        # Store the nested group box for visibility control
                        self.subgroup_boxes[(group, subgroup)] = nested_group_box

                        # Add the nested group box to the advanced container
                        advanced_form.addRow(nested_group_box)

                # Add the advanced container to the main layout
                vlayout.addWidget(advanced_container)

                # Set initial visibility based on model
                heatmap_use_advanced = getattr(
                    self.model, "heatmap_use_advanced", False
                )
                advanced_container.setVisible(heatmap_use_advanced)

                # Store the heatmap group box for later visibility control
                self.group_boxes["heatmap"] = (group_box, vlayout)
                self.form_layout.addRow(group_box)

                # Force nested groupbox visibility update
                self._update_advanced_visibility(heatmap_use_advanced)
            else:
                group_box = QGroupBox(group_name.capitalize(), self)
                group_layout = QFormLayout(group_box)
                group_layout.setLabelAlignment(Qt.AlignLeft)
                for fname, label_text, widget, meta in field_tuples:
                    group_layout.addRow(label_text, widget)
                self.group_boxes[group_name] = (group_box, group_layout)
                self.form_layout.addRow(group_box)

        # After processing all fields, add this code specifically for the multiple contours checkbox
        density_multiple_checkbox = self.widgets.get("density_contour_multiple")
        if density_multiple_checkbox and isinstance(density_multiple_checkbox, QCheckBox):
            # First disconnect any existing connections
            try:
                density_multiple_checkbox.stateChanged.disconnect()
            except TypeError:
                pass
            
            # Connect to both update the model and the visibility
            density_multiple_checkbox.stateChanged.connect(
                lambda state: setattr(self.model, "density_contour_multiple", bool(state))
            )
            density_multiple_checkbox.stateChanged.connect(
                lambda state: self._update_multiple_contours_visibility(bool(state))
            )

        custom_colorscale_cb = self.widgets.get("custom_colorscale_on")
        heatmap_cb = self.widgets.get("heatmap_on")

        if custom_colorscale_cb and heatmap_cb:
            custom_colorscale_cb.stateChanged.connect(
                lambda state: heatmap_cb.setChecked(False) if state else None
            )
            heatmap_cb.stateChanged.connect(
                lambda state: custom_colorscale_cb.setChecked(False) if state else None
            )

        self._build_filters_ui()

 
    def _update_multiple_contours_visibility(self, enable_multiple):
        """Update visibility of fields based on multiple contours checkbox."""
        # Ensure the model attribute is updated
        if hasattr(self.model, "density_contour_multiple"):
            self.model.density_contour_multiple = enable_multiple
        
        print(f"Model density_contour_multiple updated to: {enable_multiple}")
        
        # Get the single percentile spinbox
        percentile_spinbox = self.widgets.get("density_contour_percentile")
        
        # Get the multiple percentiles line edit
        percentiles_edit = self.widgets.get("density_contour_percentiles")
        
        # Get the form layout for the density contour group
        if "density_contour" in self.group_boxes:
            _, group_layout = self.group_boxes["density_contour"]
            if isinstance(group_layout, QVBoxLayout):
                # For QVBoxLayout, we need to find the QFormLayout inside it
                form_layout = None
                for i in range(group_layout.count()):
                    item = group_layout.itemAt(i)
                    if item and item.layout() and isinstance(item.layout(), QFormLayout):
                        form_layout = item.layout()
                        break
            else:
                # If group_layout is already a QFormLayout, use it directly
                form_layout = group_layout
            
            # Update visibility based on multiple contours setting
            if percentile_spinbox:
                percentile_spinbox.setEnabled(not enable_multiple)
                # Also toggle visibility of its label
                if form_layout:
                    label = form_layout.labelForField(percentile_spinbox)
                    if label:
                        label.setEnabled(not enable_multiple)
            
            # Toggle visibility of multiple percentiles field
            if percentiles_edit:
                percentiles_edit.setVisible(enable_multiple)
                if form_layout:
                    label = form_layout.labelForField(percentiles_edit)
                    if label:
                        label.setVisible(enable_multiple)

    def add_source_point_info(self):
        """Add a widget to display the source point data."""
        if not hasattr(self.model, "source_point_data") or not self.model.source_point_data:
            return
            
        # Get the series from the source point data
        source_data = self.model.source_point_data
        if "series" not in source_data or not isinstance(source_data["series"], pd.Series):
            return
            
        series = source_data["series"]
        
        # Create a group box for the source point info
        group_box = QGroupBox("Source Point Data")
        group_layout = QVBoxLayout(group_box)
        
        # Create a table view for the data
        table_view = QTableView()
        table_view.setModel(PandasSeriesModel(series))
        table_view.setMaximumHeight(150)
        
        # Adjust the table view
        header = table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)
        table_view.resizeRowsToContents()
        
        group_layout.addWidget(table_view)
        self.form_layout.addRow(group_box)
    
    def add_error_entry_widget(self):
        """Add the error entry widget for component uncertainties."""
        if not hasattr(self.model, "source_point_data") or not self.model.source_point_data:
            return
            
        # Get the series from the source point data
        source_data = self.model.source_point_data
        if "series" not in source_data or not isinstance(source_data["series"], pd.Series):
            return
            
        series = source_data["series"]
        
        # Create group box for error entry
        group_box = QGroupBox("Component Uncertainties")
        group_layout = QVBoxLayout(group_box)
        
        # Create and configure the error entry widget
        self.error_entry_widget = ErrorEntryWidget()
        self.error_entry_widget.update_components(series, self.model.error_entry_model)
        
        # Connect signals to update the model
        self.error_entry_widget.errorChanged.connect(self.on_error_changed)
        
        group_layout.addWidget(self.error_entry_widget)
        self.form_layout.addRow(group_box)

    def on_error_changed(self, component: str, value: float):
        """Handle when an error value is changed."""
        self.model.error_entry_model.set_error(component, value)

    def _update_advanced_visibility(self, show_advanced):
        """Update visibility of all advanced components when the toggle
        changes."""

        # First, update the main advanced container
        if hasattr(self, "advanced_heatmap_container"):
            self.advanced_heatmap_container.setVisible(show_advanced)

        # Then, update all nested groupboxes
        for (group, subgroup), nested_box in self.subgroup_boxes.items():
            if group == "heatmap":
                nested_box.setVisible(show_advanced)

                # Force visibility of all child widgets too
                for i in range(nested_box.layout().count()):
                    item = nested_box.layout().itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(show_advanced)

        # Update the model value
        if hasattr(self.model, "heatmap_use_advanced"):
            self.model.heatmap_use_advanced = show_advanced

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type.lower()
        # Process ungrouped fields.
        for f in fields(self.model):
            metadata = f.metadata
            if (
                "widget" not in metadata
                or metadata["widget"] is None
                or "group" in metadata
            ):
                continue
            widget = self.widgets.get(f.name)
            label = self.form_layout.labelForField(widget)
            visible = ("plot_types" not in metadata) or (
                self.current_plot_type in metadata["plot_types"]
            )
            if "depends_on" in metadata:
                dep = metadata["depends_on"]
                if isinstance(dep, list):
                    for d in dep:
                        if isinstance(d, str):
                            visible = visible and bool(getattr(self.model, d))
                        elif isinstance(d, tuple) and len(d) == 2:
                            # If tuple, check that dependent field equals necessary value
                            visible = visible and getattr(self.model, d[0]) == d[1]
                else:
                    visible = visible and bool(getattr(self.model, dep))
            if visible:
                widget.show()
                if label:
                    label.show()
            else:
                widget.hide()
                if label:
                    label.hide()
        # Process grouped fields with nested groupbox support
        for group_name, (group_box, _) in self.group_boxes.items():
            if group_name == "heatmap":
                heatmap_on = getattr(self.model, "heatmap_on", False)
                group_box.setVisible(heatmap_on)
                if heatmap_on:
                    # Use our dedicated method to update all advanced visibility
                    heatmap_use_advanced = getattr(
                        self.model, "heatmap_use_advanced", False
                    )
                    self._update_advanced_visibility(heatmap_use_advanced)
            else:
                group_visible = False
                for f in fields(self.model):
                    metadata = f.metadata
                    if metadata.get("group", None) != group_name:
                        continue
                    field_visible = ("plot_types" not in metadata) or (
                        self.current_plot_type in metadata["plot_types"]
                    )
                    if "depends_on" in metadata:
                        dep = metadata["depends_on"]
                        if isinstance(dep, list):
                            for d in dep:
                                field_visible = field_visible and bool(
                                    getattr(self.model, d)
                                )
                        else:
                            field_visible = field_visible and bool(
                                getattr(self.model, dep)
                            )
                    if field_visible:
                        group_visible = True
                        break
                group_box.setVisible(group_visible)
        self._update_filters_visibility()

        # Update error entry widget visibility if it exists
        if hasattr(self, 'error_entry_widget'):
            # Only show for contour traces
            try:
                self.error_entry_widget.setVisible(getattr(self.model, "is_contour", False))
            except RuntimeError as e:
                print('Encountered a runtime error trying to update error entry widget visibility')

    def update_from_model(self):
        # Special handling for datafile widget
        datafile_widget = self.widgets.get("datafile")
        if isinstance(datafile_widget, DatafileSelector):
            datafile_widget.setDatafile(self.model.datafile)
            
            # Update available datafiles list
            main_window = self.window()
            if hasattr(main_window, "setupMenuModel") and hasattr(main_window.setupMenuModel, "data_library"):
                all_datafiles = main_window.setupMenuModel.data_library.loaded_files
                datafile_widget.setAllDatafiles(all_datafiles)
        
        # Handle all other widgets as before
        for f in fields(self.model):
            metadata = f.metadata
            if "widget" not in metadata or metadata["widget"] is None or f.name == "datafile":
                continue
            widget = self.widgets.get(f.name)
            if not widget:
                continue
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                # For heatmap and sizemap columns, just add the saved value if needed
                if f.name in ["heatmap_column", "sizemap_column"] and value:
                    # Add the saved value to the combobox if it's not already there
                    if widget.findText(value) == -1 and value:
                        widget.addItem(value)
                # Now set the current text
                widget.setCurrentText(str(value))
            elif isinstance(widget, ColorButton):
                # Update the color button
                widget.setColor(value)
            elif isinstance(widget, ShapeButtonWithMenu):
                # Update the shape button
                widget.setShape(value)
            elif isinstance(widget, ColorScaleDropdown):
                # Update the color scale button
                widget.setColorScale(value)

        # Configure spinbox ranges and other properties
        if "heatmap_colorbar_x" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_x"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(-2.0, 3.0)
                spinbox.setSingleStep(0.1)

        if "heatmap_colorbar_y" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_y"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(0.0, 1.0)
                spinbox.setSingleStep(0.05)

        if "heatmap_colorbar_len" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_len"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(0.1, 1.0)
                spinbox.setSingleStep(0.05)

        if "heatmap_colorbar_thickness" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_thickness"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.0, 50.0)
                spinbox.setSingleStep(1.0)

        if "sizemap_min" in self.widgets:
            spinbox = self.widgets["sizemap_min"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.0, 50.0)
                spinbox.setSingleStep(0.5)

        if "sizemap_max" in self.widgets:
            spinbox = self.widgets["sizemap_max"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.5, 50.0)
                spinbox.setSingleStep(0.5)

        # Configure density contour spinboxes
        if "density_contour_thickness" in self.widgets:
            spinbox = self.widgets["density_contour_thickness"]
            if isinstance(spinbox, QSpinBox):
                spinbox.setRange(1, 10)
                spinbox.setSingleStep(1)
        
        if "density_contour_percentile" in self.widgets:
            spinbox = self.widgets["density_contour_percentile"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.0, 99.99)
                spinbox.setSingleStep(1.0)
                spinbox.setDecimals(2)
                spinbox.setSuffix("%")

        # Configure density contour line style combo box
        if "density_contour_line_style" in self.widgets:
            combobox = self.widgets["density_contour_line_style"]
            if isinstance(combobox, QComboBox):
                combobox.clear()
                combobox.addItems(["solid", "dash", "dot", "dashdot", "longdash"])
                if hasattr(self.model, "density_contour_line_style"):
                    combobox.setCurrentText(self.model.density_contour_line_style)
        
        # Configure spinboxes for density contours
        if "density_contour_percentile" in self.widgets:
            spinbox = self.widgets["density_contour_percentile"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.0, 99.99)
                spinbox.setSingleStep(1.0)
                spinbox.setDecimals(2)
                spinbox.setSuffix("%")
        
        if "density_contour_thickness" in self.widgets:
            spinbox = self.widgets["density_contour_thickness"]
            if isinstance(spinbox, QSpinBox):
                spinbox.setRange(1, 10)
                spinbox.setSingleStep(1)
        
        # Configure multiple contours visibility
        if hasattr(self.model, "density_contour_multiple"):
            self._update_multiple_contours_visibility(self.model.density_contour_multiple)

        # Update error entry widget if it exists
        if hasattr(self, 'error_entry_widget') and hasattr(self.model, 'source_point_data'):
            source_data = self.model.source_point_data
            if "series" in source_data and isinstance(source_data["series"], pd.Series):
                self.error_entry_widget.update_components(source_data["series"], self.model.error_entry_model)

        self.connect_datafile_selector()
        self.connect_column_change_handlers()


    def _on_trace_name_changed(self, text: str):
        self.model.trace_name = text
        if hasattr(self, "traceNameChangedCallback") and self.traceNameChangedCallback:
            self.traceNameChangedCallback(text)

    def set_model(self, new_model: "TraceEditorModel"):
        """Set a new model for the editor view."""
        self.model = new_model
        
        # Remove all existing widgets
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Rebuild UI with the new model
        self._build_ui()

        # Initialize heatmap and sizemap columns if they're enabled but not set
        for feature in ["heatmap", "sizemap"]:
            on_attribute = f"{feature}_on"
            column_attribute = f"{feature}_column"
            
            if (getattr(self.model, on_attribute, False) and 
                not getattr(self.model, column_attribute, None)):
                print(f"{feature} is enabled but column not set, initializing")
                self._on_feature_enabled(feature, True)

        # Update widgets from the model
        self.update_from_model()
        
        # Set visibility based on plot type
        self.set_plot_type(self.current_plot_type)

        # Rebuild filters UI
        self._build_filters_ui()

        self.connect_column_change_handlers()

    # --- Filters UI Methods in TraceEditorView ---
    def _build_filters_ui(self):
        if hasattr(self, "filtersGroupBox"):
            self.form_layout.removeWidget(self.filtersGroupBox)
            self.filtersGroupBox.deleteLater()
        self.filtersGroupBox = QGroupBox("Filters", self)
        filters_layout = QHBoxLayout(self.filtersGroupBox)
        self.filtersGroupBox.setLayout(filters_layout)
        self.filterTabWidget = FilterTabWidget(self)
        filters_layout.addWidget(self.filterTabWidget)
        self.filterEditorContainer = QWidget(self)
        self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
        self.filterEditorContainer.setLayout(self.filterEditorLayout)
        filters_layout.addWidget(self.filterEditorContainer)
        filter_names = (
            [f.filter_name for f in self.model.filters] if self.model.filters else []
        )
        self.filterTabWidget.set_filters(filter_names)
        if self.model.filters:
            self.currentFilterIndex = 0
            self.filterTabWidget.setCurrentRow(0)
            self._show_current_filter()
        else:
            self.currentFilterIndex = None
        self.filterTabWidget.filterSelectedCallback.connect(self.on_filter_selected)
        self.filterTabWidget.filterAddRequestedCallback.connect(
            self.on_filter_add_requested
        )
        self.filterTabWidget.filterRenamedCallback.connect(self.on_filter_renamed)
        self.filterTabWidget.filterRemoveRequestedCallback.connect(self.on_filter_remove_requested)
        self.form_layout.addRow(self.filtersGroupBox)
        self._update_filters_visibility()

    def on_filter_remove_requested(self, index: int):
        """Handle request to remove a filter."""
        if index < 0 or index >= len(self.model.filters):
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the filter '{self.model.filters[index].filter_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Remove the filter from the model
        self.model.filters.pop(index)
        
        # Update the filter tabs
        filter_names = [f.filter_name for f in self.model.filters]
        self.filterTabWidget.set_filters(filter_names)
        
        # Update the current filter index
        if self.model.filters:
            # Select the next filter, or the last one if we removed the last filter
            new_index = min(index, len(self.model.filters) - 1)
            self.currentFilterIndex = new_index
            self.filterTabWidget.setCurrentRow(new_index)
            self._show_current_filter()
        else:
            # No filters left
            self.currentFilterIndex = None
            while self.filterEditorLayout.count():
                w = self.filterEditorLayout.takeAt(0).widget()
                if w is not None:
                    w.deleteLater()

    def _show_current_filter(self):
        if self.currentFilterIndex is None or self.currentFilterIndex >= len(
            self.model.filters
        ):
            return
        if hasattr(self, "filterEditorLayout"):
            while self.filterEditorLayout.count():
                w = self.filterEditorLayout.takeAt(0).widget()
                if w is not None:
                    w.deleteLater()
        current_filter = self.model.filters[self.currentFilterIndex]
        self.currentFilterEditor = FilterEditorView(current_filter, self)
        self.filterEditorLayout.addWidget(self.currentFilterEditor)

    def on_filter_selected(self, index: int):
        if index < 0 or index >= len(self.model.filters):
            return
        self.currentFilterIndex = index
        self._show_current_filter()

    def on_filter_add_requested(self):
        new_filter = FilterModel()
        self.model.filters.append(new_filter)
        self.filterTabWidget.add_filter_tab(new_filter.filter_name)
        self.currentFilterIndex = len(self.model.filters) - 1
        self._show_current_filter()

    def on_filter_renamed(self, index: int, new_name: str):
        if index < 0 or index >= len(self.model.filters):
            return
        self.model.filters[index].filter_name = new_name
        if self.currentFilterIndex == index and hasattr(self, "currentFilterEditor"):
            self.currentFilterEditor.update_from_model()

    def _update_filters_visibility(self):
        if hasattr(self, "filtersGroupBox"):
            if getattr(self.model, "filters_on", False):
                self.filtersGroupBox.show()
            else:
                self.filtersGroupBox.hide()
