from dataclasses import fields

from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QListWidget,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from src3.views.widgets import (
    ColorButton,
    ColorScaleDropdown,
    ColumnScalingWidget,
    FormulaInputWidget,
    MultiFieldSelector,
)
from src3.views.dialogs import (
    HeaderSelectionDialog,
    SheetSelectionDialog,
)
from src3.models.data_file_metadata_model import DataFileMetadata
from src3.models.trace_editor_model import TraceEditorModel
from src3.utils.functions import get_sheet_names

if TYPE_CHECKING:
    from src3.models.setup_menu_model import SetupMenuModel
    from src3.controllers.setup_menu_controller import SetupMenuController

class SetupMenuView(QWidget):
    def __init__(self, model: "SetupMenuModel", parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # Default plot type
        self.controller = None  # Will be set later by the main window
        self.section_widgets = {}  # To hold per‑section widget mappings
        
        # Wrap all contents in a scroll area for vertical scrolling
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.scroll.setWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content.setLayout(self.content_layout)

        # Data Library Section
        self.dataLibraryWidget = QWidget(self)
        data_library_layout = QVBoxLayout(self.dataLibraryWidget)
        self.dataLibraryWidget.setLayout(data_library_layout)
        data_library_label = QLabel("Loaded Data:")
        data_library_layout.addWidget(data_library_label)
        self.dataLibraryList = QListWidget(self)
        self.dataLibraryList.setMaximumHeight(150)
        data_library_layout.addWidget(self.dataLibraryList)
        btn_layout = QHBoxLayout()
        self.addDataButton = QPushButton("Add Data", self)
        self.removeDataButton = QPushButton("Remove Data", self)
        btn_layout.addWidget(self.addDataButton)
        btn_layout.addWidget(self.removeDataButton)
        data_library_layout.addLayout(btn_layout)
        self.addDataButton.clicked.connect(self.add_data_file)
        self.removeDataButton.clicked.connect(self.remove_data_file)
        self.content_layout.addWidget(self.dataLibraryWidget)

        # Axis Members Section
        self.axisMembersWidget = self.build_form_section(
            self.model.axis_members, "axis_members"
        )
        self.content_layout.addWidget(self.axisMembersWidget)

        # Plot Labels Section
        self.plotLabelsWidget = self.build_form_section(
            self.model.plot_labels, "plot_labels"
        )
        self.content_layout.addWidget(self.plotLabelsWidget)

        # Column Scaling Section
        self.columnScalingWidget = QWidget(self)
        column_scaling_layout = QVBoxLayout(self.columnScalingWidget)
        self.columnScalingWidget.setLayout(column_scaling_layout)
        self.scalingWidget = ColumnScalingWidget(self)
        column_scaling_layout.addWidget(self.scalingWidget)
        self.content_layout.addWidget(self.columnScalingWidget)

        # Connect scaling widget signals
        self.scalingWidget.scaleChanged.connect(self.on_scale_changed)

        # Chemical Formula Section - NEW
        self.chemicalFormulaWidget = QWidget(self)
        formula_layout = QVBoxLayout(self.chemicalFormulaWidget)
        self.chemicalFormulaWidget.setLayout(formula_layout)
        self.formulaWidget = FormulaInputWidget(self)
        formula_layout.addWidget(self.formulaWidget)
        self.content_layout.addWidget(self.chemicalFormulaWidget)

        # Connect formula widget signals
        self.formulaWidget.formulaChanged.connect(self.on_formula_changed)

        # Advanced Settings Section
        self.advancedSettingsWidget = self.build_form_section(
            self.model.advanced_settings, "advanced_settings"
        )
        self.content_layout.addWidget(self.advancedSettingsWidget)

        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.scroll)
        self.setLayout(outer_layout)

        # Initialize to default plot type
        self.set_plot_type(self.current_plot_type)

        # Update the widgets with initial values
        self.update_scaling_widget()
        self.update_formula_widget()

    def on_formula_changed(self, axis_name, column_name, formula):
        """Handle when a formula is changed in the formula widget."""
        self.model.chemical_formulas.set_formula(axis_name, column_name, formula)

    def update_formula_widget(self):
        """Update all axes in the formula widget."""
        # Get valid axes for the current plot type
        valid_axes = self.get_valid_axes_for_current_plot_type()

        # First, clear the formula widget completely
        self.formulaWidget.clear()

        # Update only the valid axes
        for axis_name in valid_axes:
            self.update_formula_widget_for_axis(axis_name)

    def update_formula_widget_for_axis(self, axis_name):
        """Update a single axis in the formula widget."""
        # Get the selected columns for this axis
        axis_widget = self.section_widgets.get("axis_members", {}).get(axis_name)
        if isinstance(axis_widget, MultiFieldSelector):
            columns = axis_widget.get_selected_fields()

            # Get the current formulas for this axis
            current_formulas = self.model.chemical_formulas.formulas.get(
                axis_name, {}
            )

            # Update the formula widget
            self.formulaWidget.update_columns(axis_name, columns, current_formulas)

    def set_controller(self, controller: "SetupMenuController"):
        self.controller = controller

    def build_form_section(self, section_model, model_attr_name):
        widget = QWidget(self)
        form_layout = QFormLayout(widget)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        widget.setLayout(form_layout)
        # Store the form layout so we can later access labels.
        if not hasattr(self, "section_form_layouts"):
            self.section_form_layouts = {}
        self.section_form_layouts[model_attr_name] = form_layout
        self.section_widgets[model_attr_name] = {}
        for f in fields(section_model):
            metadata = f.metadata
            if (
                "label" not in metadata
                or "widget" not in metadata
                or metadata["widget"] is None
            ):
                continue
            widget_cls = metadata["widget"]
            label_text = metadata["label"]
            field_widget = widget_cls(self)
            value = getattr(section_model, f.name)
            if isinstance(field_widget, QLineEdit):
                field_widget.setText(str(value))
                field_widget.textChanged.connect(
                    lambda text, fname=f.name, m=section_model: setattr(m, fname, text)
                )
            elif isinstance(field_widget, ColorButton):
                field_widget.setColor(value)
                field_widget.colorChanged.connect(
                    lambda color_str, fname=f.name, m=section_model: setattr(
                        m, fname, color_str
                    )
                )
            elif isinstance(field_widget, ColorScaleDropdown):
                field_widget.setColorScale(value)
                field_widget.colorScaleChanged.connect(
                    lambda color_str, fname=f.name, m=section_model: setattr(
                        m, fname, color_str
                    )
                )
            elif isinstance(field_widget, QDoubleSpinBox):
                field_widget.setValue(float(value))
                field_widget.valueChanged.connect(
                    lambda val, fname=f.name, m=section_model: setattr(m, fname, val)
                )
            elif isinstance(field_widget, QSpinBox):
                field_widget.setValue(int(value))
                field_widget.valueChanged.connect(
                    lambda val, fname=f.name, m=section_model: setattr(m, fname, val)
                )
            elif isinstance(field_widget, QCheckBox):
                field_widget.setChecked(bool(value))
                field_widget.stateChanged.connect(
                    lambda state, fname=f.name, m=section_model: setattr(
                        m, fname, bool(state)
                    )
                )
            elif isinstance(field_widget, QComboBox):
                field_widget.addItems([])
                field_widget.setCurrentText(str(value))
                field_widget.currentTextChanged.connect(
                    lambda text, fname=f.name, m=section_model: setattr(m, fname, text)
                )
            elif isinstance(field_widget, MultiFieldSelector):
                field_widget.set_selected_fields(value)
                # Connect selectionChanged to update the model and scaling widget
                # field_widget.setMaximumHeight(100)
                field_widget.selectionChanged.connect(
                    lambda sel, fname=f.name, m=section_model: self.on_field_selection_changed(
                        fname, sel, m
                    )
                )
            form_layout.addRow(label_text, field_widget)
            self.section_widgets[model_attr_name][f.name] = field_widget
        return widget

    # Update the existing on_field_selection_changed method
    def on_field_selection_changed(self, field_name, selection, model):
        """Handle when a field selection changes in axis members."""
        # Update the model
        setattr(model, field_name, selection)

        # Clean up any scaling factors for columns no longer selected
        self.model.column_scaling.clean_unused_scales(field_name, selection)
        
        # Clean up any formulas for columns no longer selected
        self.model.chemical_formulas.clean_unused_formulas(field_name, selection)

        # Update the widgets for this axis
        self.update_scaling_widget_for_axis(field_name)
        self.update_formula_widget_for_axis(field_name)

    def on_scale_changed(self, axis_name, column_name, scale_factor):
        """Handle when a scale factor is changed in the scaling widget."""
        self.model.column_scaling.set_scale(axis_name, column_name, scale_factor)

    def get_valid_axes_for_current_plot_type(self):
        """Return a list of axis names valid for the current plot type."""
        valid_axes = []

        axis_members = self.model.axis_members
        for f in fields(axis_members):
            metadata = f.metadata
            if (
                "plot_types" in metadata
                and self.current_plot_type in metadata["plot_types"]
            ):
                valid_axes.append(f.name)

        return valid_axes


    def update_scaling_widget(self):
        """Update all axes in the scaling widget."""
        # Get valid axes for the current plot type
        valid_axes = self.get_valid_axes_for_current_plot_type()

        # First, clear the scaling widget completely
        self.scalingWidget.clear()

        # Update only the valid axes
        for axis_name in valid_axes:
            self.update_scaling_widget_for_axis(axis_name)

    def update_scaling_widget_for_axis(self, axis_name):
        """Update a single axis in the scaling widget."""
        # Get the selected columns for this axis
        axis_widget = self.section_widgets.get("axis_members", {}).get(axis_name)
        if isinstance(axis_widget, MultiFieldSelector):
            columns = axis_widget.get_selected_fields()

            # Get the current scale factors for this axis
            current_scales = self.model.column_scaling.scaling_factors.get(
                axis_name, {}
            )

            # Update the scaling widget
            self.scalingWidget.update_columns(axis_name, columns, current_scales)

    def set_plot_type(self, plot_type: str):
        """
        Update widget visibility and values based on the selected plot type.
        
        Args:
            plot_type: The new plot type (ternary, cartesian, histogram, zmap)
        """
        self.current_plot_type = plot_type
        
        # First update visibility of all form fields based on plot type
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            form_layout = self.section_form_layouts.get(section)
            for fname, field_widget in widgets.items():
                # Retrieve metadata for this field.
                metadata = None
                for f in fields(section_model):
                    if f.name == fname:
                        metadata = f.metadata
                        break
                if metadata is None:
                    continue
                show_field = (
                    "plot_types" in metadata
                    and self.current_plot_type in metadata["plot_types"]
                )
                if show_field:
                    field_widget.show()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.show()
                    
                    # For newly visible fields that are comboboxes, ensure values are set correctly
                    if self.current_plot_type == 'zmap' and isinstance(field_widget, QComboBox) and fname == 'categorical_column':
                        # Get the current value from the model
                        current_value = getattr(section_model, fname, "")
                        
                        # Ensure the combobox has this value if present
                        if current_value and field_widget.findText(current_value) == -1:
                            field_widget.blockSignals(True)
                            field_widget.addItem(current_value)
                            field_widget.blockSignals(False)
                        
                        # Set the current text to match the model
                        if current_value:
                            field_widget.blockSignals(True)
                            field_widget.setCurrentText(current_value)
                            field_widget.blockSignals(False)

                    if self.current_plot_type == 'zmap' and isinstance(field_widget, ColorScaleDropdown) and fname == 'zmap_colorscale':
                        # Get the current value from the model
                        current_value = getattr(section_model, fname, "")
                        
                        # Set the current text to match the model
                        if current_value:
                            field_widget.blockSignals(True)
                            field_widget.setColorScale(current_value)
                            field_widget.blockSignals(False)
                else:
                    field_widget.hide()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.hide()

        # Show/hide the column scaling widget based on plot type
        scaling_plot_types = ["cartesian", "histogram", "ternary"]
        if self.current_plot_type in scaling_plot_types:
            self.columnScalingWidget.show()
            # Update with the correct axes for this plot type
            self.update_scaling_widget()
        else:
            self.columnScalingWidget.hide()

        # Show/hide the chemical formula widget based on plot type
        formula_plot_types = ["cartesian", "ternary"]
        if self.current_plot_type in formula_plot_types:
            self.chemicalFormulaWidget.show()
            # Update with the correct axes for this plot type
            self.update_formula_widget()
        else:
            self.chemicalFormulaWidget.hide()

    def add_data_file(self):
        """Modified add_data_file method to use DataframeManager with display strings."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File", "", "Data Files (*.csv *.xlsx)"
        )
        if file_path:
            metadata = None
            if file_path.endswith(".csv"):
                header, ok = HeaderSelectionDialog.getHeader(self, file_path)
                if not ok:
                    return  # User cancelled header selection
                metadata = DataFileMetadata(file_path=file_path, header_row=header)
            elif file_path.endswith(".xlsx"):
                sheets = get_sheet_names(file_path)
                if len(sheets) > 1:
                    sheet, ok = SheetSelectionDialog.getSheet(self, file_path, sheets)
                    if not ok:
                        return  # User cancelled sheet selection
                else:
                    sheet = sheets[0] if sheets else None
                header, ok = HeaderSelectionDialog.getHeader(
                    self, file_path, sheet=sheet
                )
                if not ok:
                    return  # User cancelled header selection
                metadata = DataFileMetadata(
                    file_path=file_path, header_row=header, sheet=sheet
                )
            else:
                # If not CSV or XLSX, simply create a basic metadata object with file_path
                metadata = DataFileMetadata(file_path=file_path)

            # Add the file to the data library
            if self.model.data_library.add_file(metadata):
                # Display the metadata with the full display string
                self.dataLibraryList.addItem(str(metadata))
                if self.controller:
                    self.controller.update_axis_options()
            else:
                QMessageBox.warning(
                    self, "Error", f"Failed to load data from {file_path}"
                )

    def remove_data_file(self):
        """Modified remove_data_file method to use display strings."""
        current_item = self.dataLibraryList.currentItem()
        if current_item:
            display_str = current_item.text()

            # Check for dependent traces
            main_window = self.window()  # Retrieve the main window
            dependent_traces = []
            if hasattr(main_window, "tabPanel"):
                # Iterate over all trace models stored in the tab panel
                for uid, model in main_window.tabPanel.id_to_widget.items():
                    if (
                        model is not None
                        and isinstance(model, TraceEditorModel)
                        and str(model.datafile) == display_str
                    ):
                        dependent_traces.append((uid, model.trace_name))

            # If there are dependent traces, warn the user
            if dependent_traces:
                # Handle warnings and trace removal...
                # TODO implement something here!
                pass

            # Now remove the data file using the new method
            row = self.dataLibraryList.row(current_item)
            self.dataLibraryList.takeItem(row)
            self.model.data_library.remove_file(display_str)

            if self.controller:
                self.controller.update_axis_options()

    def update_from_model(self):
        """Update all widgets from the model, ensuring comboboxes have the correct options."""
        # Update custom Data Library list
        self.dataLibraryList.clear()
        for meta in self.model.data_library.loaded_files:
            # self.dataLibraryList.addItem(meta.file_path)
            self.dataLibraryList.addItem(str(meta))
            
        # Update each section built by build_form_section
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            for fname, field_widget in widgets.items():
                for f in fields(section_model):
                    if f.name == fname:
                        value = getattr(section_model, fname)
                        if isinstance(field_widget, QLineEdit):
                            field_widget.setText(str(value))
                        elif isinstance(field_widget, QDoubleSpinBox):
                            field_widget.setValue(float(value))
                        elif isinstance(field_widget, QCheckBox):
                            field_widget.setChecked(bool(value))
                        elif isinstance(field_widget, QComboBox):
                            # Special handling for comboboxes to ensure model value is in the list
                            # Block signals to prevent triggering any side effects
                            field_widget.blockSignals(True)
                            
                            # For categorical_column and similar comboboxes, make sure value is in list
                            if value and field_widget.findText(str(value)) == -1:
                                field_widget.addItem(str(value))
                            
                            # Now set the current text
                            if value:
                                field_widget.setCurrentText(str(value))
                                
                            field_widget.blockSignals(False)
                        elif isinstance(field_widget, MultiFieldSelector):
                            field_widget.set_selected_fields(value)
                        elif isinstance(field_widget, ColorButton):
                            field_widget.setColor(value)
                        elif isinstance(field_widget, ColorScaleDropdown):
                            field_widget.setColorScale(value)
                        elif isinstance(field_widget, QSpinBox):
                            field_widget.setValue(int(value))
                        break

        # Update the column scaling widget
        self.update_scaling_widget()
        
        # Update the chemical formula widget
        self.update_formula_widget()
