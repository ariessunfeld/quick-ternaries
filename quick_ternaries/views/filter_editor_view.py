from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QPushButton,
    QLineEdit,
    QComboBox,
    QLabel,
    QCompleter,
)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt
from dataclasses import fields

from quick_ternaries.views.widgets import FilterTabWidget, MultiFieldSelector
from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.utils.functions import get_sorted_unique_values


class FilterEditorView(QWidget):
    def __init__(self, filter_model: FilterModel, parent=None):
        super().__init__(parent)
        self.filter_model = filter_model
        self.widgets = {}
        self.form_layout = QFormLayout(self)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)
        self.setLayout(self.form_layout)
        self._build_ui()
        self.update_from_model()
        # Immediately update the value widgets based on current column and operation.
        self.update_filter_value_widgets()

        # Add a remove button at the bottom
        # TODO make this button's position more consistent
        self.remove_button = QPushButton("Remove Filter", self)
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.form_layout.addRow("", self.remove_button)

    def _on_remove_clicked(self):
        """Handle click on the remove filter button"""
        # Find the parent widget that contains FilterTabWidget
        parent_widget = self.parent()
        while parent_widget is not None:
            ftw = parent_widget.findChild(FilterTabWidget)
            if ftw is not None:
                # Get current row and emit the removal signal
                idx = ftw.currentRow()
                if idx >= 0:
                    ftw.filterRemoveRequestedCallback.emit(idx)
                break
            parent_widget = parent_widget.parent()

    def _build_ui(self):
        # Build widgets for all fields except the value widgets,
        # which will be handled dynamically.
        for f in fields(self.filter_model):
            if f.name in ["filter_value1", "filter_value2"]:
                continue  # handled dynamically later
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                widget.textChanged.connect(
                    lambda text, fname=f.name: self._on_field_changed(fname, text)
                )
            elif isinstance(widget, QComboBox):
                if f.name == "filter_column":
                    # Get columns from the current dataframe
                    main_window = self.window()
                    datafile = None
                    df = None  # Initialize dataframe variable

                    # Get the current datafile metadata from the trace editor view
                    if hasattr(main_window, "traceEditorView") and hasattr(
                        main_window.traceEditorView, "model"
                    ):
                        datafile = main_window.traceEditorView.model.datafile

                    # Get the dataframe from the dataframe manager
                    if (
                        datafile
                        and hasattr(main_window, "setupMenuModel")
                        and hasattr(main_window.setupMenuModel, "data_library")
                    ):
                        data_library = main_window.setupMenuModel.data_library
                        df = data_library.dataframe_manager.get_dataframe_by_metadata(
                            datafile
                        )

                    # If we have a dataframe, get its columns
                    if df is not None:
                        all_cols = df.columns.tolist()
                        widget.clear()
                        widget.addItems(all_cols)
                        if value and value.strip():
                            if value in all_cols:
                                widget.setCurrentText(value)
                            else:
                                widget.addItem(value)
                                widget.setCurrentText(value)
                        elif all_cols:
                            widget.setCurrentText(all_cols[0])
                            self.filter_model.filter_column = all_cols[0]
                else:
                    widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(
                    lambda text, fname=f.name: self._on_field_changed(fname, text)
                )
            self.form_layout.addRow(label_text, widget)

        # For filter_operation, update its behavior to trigger updating value widgets.
        if "filter_operation" in self.widgets:
            self.widgets["filter_operation"].currentTextChanged.connect(
                lambda text: self._on_field_changed("filter_operation", text)
            )
            self.widgets["filter_operation"].currentTextChanged.connect(
                lambda _: self.update_filter_value_widgets()
            )

        # For filter_column, update value widgets when changed.
        if "filter_column" in self.widgets:
            self.widgets["filter_column"].currentTextChanged.connect(
                lambda text: self._on_field_changed("filter_column", text)
            )
            self.widgets["filter_column"].currentTextChanged.connect(
                lambda _: self.update_filter_value_widgets()
            )

    def _on_field_changed(self, field_name, value):
        setattr(self.filter_model, field_name, value)
        if field_name == "filter_name":
            parent_widget = self.parent()
            while parent_widget is not None:
                ftw = parent_widget.findChild(FilterTabWidget)
                if ftw is not None:
                    idx = ftw.currentRow()
                    if idx >= 0:
                        ftw.update_filter_tab(idx, value)
                    break
                parent_widget = parent_widget.parent()

    def update_filter_value_widgets(self):
        """Rebuild the input widget(s) for filter_value1 (and filter_value2, if
        needed) based on the selected column's type and the chosen filter
        operation."""
        # Determine column and get the dataframe
        col = self.widgets["filter_column"].currentText()
        main_window = self.window()
        datafile = None
        df = None

        # Get the current datafile metadata from the trace editor view
        if hasattr(main_window, "traceEditorView") and hasattr(
            main_window.traceEditorView, "model"
        ):
            datafile = main_window.traceEditorView.model.datafile

        # Get the dataframe from the dataframe manager
        if (
            datafile
            and hasattr(main_window, "setupMenuModel")
            and hasattr(main_window.setupMenuModel, "data_library")
        ):
            data_library = main_window.setupMenuModel.data_library
            df = data_library.dataframe_manager.get_dataframe_by_metadata(datafile)

        # Determine if column is numeric and get unique values
        if df is not None and col in df.columns:
            numeric = col in df.select_dtypes(include=["number"]).columns
            suggestions = df[col].dropna().unique().tolist()

            # Sort suggestions
            try:
                if suggestions and numeric:
                    suggestions.sort(key=lambda x: float(x))
                else:
                    suggestions.sort(key=lambda x: str(x))
            except Exception:
                suggestions.sort(key=lambda x: str(x))
        else:
            numeric = True  # default assumption
            suggestions = []

        # Get the current filter_value1 content to preserve it
        current_value1 = self.filter_model.filter_value1

        # Ensure suggestions are strings.
        suggestions = [str(s) for s in suggestions]

        # If we have a multi-value filter, make sure all values are in suggestions
        if self.filter_model.filter_operation in ["is one of", "is not one of"]:
            if isinstance(current_value1, list):
                for val in current_value1:
                    str_val = str(val)
                    if str_val not in suggestions:
                        suggestions.append(str_val)

        # Use the saved model value for filter_operation if present.
        saved_op = self.filter_model.filter_operation

        # Update the filter_operation combo box.
        op_widget = self.widgets["filter_operation"]
        op_widget.blockSignals(True)
        op_widget.clear()
        if numeric:
            new_ops = FilterModel.ALLOWED_NUMERIC_OPERATIONS + [
                "is",
                "is not",
                "is one of",
                "is not one of",
            ]
        else:
            new_ops = ["is", "is not", "is one of", "is not one of"]
        op_widget.addItems(new_ops)
        if saved_op in new_ops:
            op_widget.setCurrentText(saved_op)
        else:
            op_widget.setCurrentIndex(0)
        op_widget.blockSignals(False)
        op = op_widget.currentText()
        # Save back the op to the model (if it changed).
        self.filter_model.filter_operation = op

        # Create new widgets for filter_value1 and filter_value2...
        # (Rest of the method remains the same as in the original code)

        # ---- Rebuild filter_value1 ----
        # Remove previous row (both label and widget) if they exist.
        if "filter_value1_label" in self.widgets:
            old_label = self.widgets.pop("filter_value1_label")
            self.form_layout.removeWidget(old_label)
            old_label.deleteLater()
        if "filter_value1" in self.widgets:
            old_widget = self.widgets.pop("filter_value1")
            self.form_layout.removeWidget(old_widget)
            old_widget.deleteLater()

        # Create new widget for filter_value1.
        if op in ["is one of", "is not one of"]:
            new_w = MultiFieldSelector(self)
            # Important: Set available options BEFORE setting selected fields
            new_w.set_available_options(suggestions)

            # Handle the saved values - ensure they're properly formatted
            saved_value = current_value1
            if isinstance(saved_value, str) and saved_value:
                saved_fields = [v.strip() for v in saved_value.split(",")]
            elif isinstance(saved_value, list):
                saved_fields = saved_value
            else:
                saved_fields = []

            # Now set the selected fields
            new_w.set_selected_fields(saved_fields)

            # Connect after initializing to avoid triggering during setup
            new_w.selectionChanged.connect(
                lambda sel: self._on_field_changed("filter_value1", sel)
            )
        else:
            new_w = QLineEdit(self)
            if numeric and op in FilterModel.ALLOWED_NUMERIC_OPERATIONS:
                new_w.setValidator(QDoubleValidator())
            else:
                completer = QCompleter(suggestions, self)
                new_w.setCompleter(completer)

            # Set the current value
            if isinstance(current_value1, list) and current_value1:
                # Convert list to comma-separated string
                new_w.setText(", ".join(str(v) for v in current_value1))
            elif current_value1:
                new_w.setText(str(current_value1))

            new_w.textChanged.connect(
                lambda text: self._on_field_changed("filter_value1", text)
            )

        # Add new row with a label.
        label1 = QLabel("Value A:", self)
        self.widgets["filter_value1_label"] = label1
        self.widgets["filter_value1"] = new_w
        self.form_layout.addRow(label1, new_w)

        # ---- Rebuild filter_value2 (only for range operations on numeric data) ----
        if "filter_value2_label" in self.widgets:
            old_label2 = self.widgets.pop("filter_value2_label")
            self.form_layout.removeWidget(old_label2)
            old_label2.deleteLater()
        if "filter_value2" in self.widgets:
            old_widget2 = self.widgets.pop("filter_value2")
            self.form_layout.removeWidget(old_widget2)
            old_widget2.deleteLater()

        if numeric and op in ["a < x < b", "a <= x < b", "a < x <= b"]:
            new_w2 = QLineEdit(self)
            new_w2.setValidator(QDoubleValidator())
            new_w2.textChanged.connect(
                lambda text: self._on_field_changed("filter_value2", text)
            )
            # Set the current value
            if self.filter_model.filter_value2:
                new_w2.setText(str(self.filter_model.filter_value2))
            label2 = QLabel("Value B:", self)
            self.widgets["filter_value2_label"] = label2
            self.widgets["filter_value2"] = new_w2
            self.form_layout.addRow(label2, new_w2)

    def update_from_model(self):
        # Update static widgets.
        for f in fields(self.filter_model):
            if f.name in ["filter_value1", "filter_value2"]:
                continue  # their widgets are handled dynamically
            widget = self.widgets.get(f.name)
            if not widget:
                continue
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
        # Now update the dynamic value widgets.
        self.update_filter_value_widgets()

        # For multi-field selectors, update the selected items.
        op = self.filter_model.filter_operation
        if op in ["is one of", "is not one of"]:
            multi_field_widget = self.widgets.get("filter_value1")
            if multi_field_widget and hasattr(
                multi_field_widget, "set_selected_fields"
            ):
                # Recalculate suggestions (must match the ones used in update_filter_value_widgets)
                col = self.widgets["filter_column"].currentText()
                main_window = self.window()
                datafile = None
                if hasattr(main_window, "traceEditorView") and hasattr(
                    main_window.traceEditorView, "model"
                ):
                    datafile = main_window.traceEditorView.model.datafile
                if datafile and datafile.file_path:
                    suggestions = get_sorted_unique_values(
                        datafile.file_path, datafile.header_row, datafile.sheet, col
                    )
                else:
                    suggestions = []
                # Normalize suggestions to strings.
                suggestions = [str(s) for s in suggestions]

                # Get the saved value.
                value = getattr(self.filter_model, "filter_value1", [])
                if isinstance(value, str) and value:
                    fields_list = [v.strip() for v in value.split(",")]
                elif isinstance(value, list):
                    fields_list = value
                else:
                    fields_list = []

                # Ensure all selected fields are in the suggestions
                for v in fields_list:
                    if v not in suggestions:
                        suggestions.append(v)

                # Update available options to include saved values
                multi_field_widget.set_available_options(suggestions)

                # Set selected fields directly
                multi_field_widget.set_selected_fields(fields_list)

    def set_filter_model(self, new_filter_model: FilterModel):
        self.filter_model = new_filter_model
        self.update_from_model()
