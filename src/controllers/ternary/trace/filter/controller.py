"""Contains the FilterEditorController class"""

from typing import List

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QCompleter
import numpy as np

from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.views.ternary.trace.filter.filter_editor_view import FilterEditorView
from src.models.ternary.trace.filter.tab_model import FilterTabsPanelModel
from src.models.ternary.trace.filter.model import FilterModel
from src.models.utils.data_models import DataLibrary

class FilterEditorController(QObject):
    def __init__(self, model: TraceTabsPanelModel, view: FilterEditorView):
        super().__init__()
        self.model = model
        self.view = view
        self.data_library_reference = None

        self.setup_connections()

    def set_data_library_reference(self, ref: DataLibrary):
        # Ideally read-only access to data library
        self.data_library_reference = ref

    def setup_connections(self):
        self.view.filter_column_combobox.valueChanged.connect(self._on_column_changed)
        self.view.filter_operation_combobox.combobox.currentIndexChanged.connect(self._on_operation_changed)
        self.view.filter_value_line_edit.textChanged.connect(self._on_filter_value_changed)
        self.view.filter_value_a_line_edit.textChanged.connect(self._on_filter_value_a_changed)
        self.view.filter_value_b_line_edit.textChanged.connect(self._on_filter_value_b_changed)
        self.view.add_remove_list.button_add.clicked.connect(self._on_add_attr_button_clicked)
        self.view.add_remove_list.button_remove.clicked.connect(self._on_rem_attr_button_clicked)

    def change_trace_tab(self, filter_model: FilterModel):
        pass

    def change_filter_tab(self, filter_model: FilterModel):
        if filter_model is not None:

            completer = QCompleter(filter_model.completer_list)

            # Populate view accordingly
            self.view.filter_column_combobox.clear()
            self.view.filter_column_combobox.addItems(filter_model.available_columns)
            if filter_model.selected_column is None and filter_model.available_columns:
                filter_model.selected_column = filter_model.available_columns[0]
                self.view.filter_column_combobox.emit_value_changed(0)
            self.view.filter_column_combobox.setCurrentText(filter_model.selected_column)
            self.view.filter_operation_combobox.clear()
            self.view.filter_operation_combobox.addItems(filter_model.available_filter_operations)
            self.view.filter_operation_combobox.setCurrentText(filter_model.selected_filter_operation)
            self.view.filter_value_line_edit.setText(filter_model.filter_values)
            self.view.filter_value_a_line_edit.setText(filter_model.filter_value_a)
            self.view.filter_value_b_line_edit.setText(filter_model.filter_value_b)
            self.view.filter_value_line_edit.setCompleter(completer)
            self.view.filter_value_a_line_edit.setCompleter(completer)
            self.view.filter_value_b_line_edit.setCompleter(completer)
            if filter_model.available_one_of_filter_values:
                self.view.available_values_list.clear()
                self.view.available_values_list.addItems(sorted(filter_model.available_one_of_filter_values))
            self.view.add_remove_list.clear()
            self.view.add_remove_list.addItems(sorted(filter_model.selected_one_of_filter_values) if filter_model.selected_one_of_filter_values else None)

            # Update visibility based on dropdowns and types
            self.update_widget_visibility()
        else:
            pass

    def update_widget_visibility(self):
        is_range_operation = self.view.filter_operation_combobox.currentText() in FilterModel.NUMERICAL_RANGE
        self.view.filter_value_a_line_edit.setVisible(is_range_operation)
        self.view.filter_value_b_line_edit.setVisible(is_range_operation)

        is_one_of_operation = self.view.filter_operation_combobox.currentText() == 'One of'
        self.view.add_remove_layout_widget.setVisible(is_one_of_operation)
        self.view.filter_value_line_edit.setVisible(not is_one_of_operation and not is_range_operation)

    def update_available_operations(self, categorical=True):
        if categorical:
            self.model.current_tab.filter_tab_model.current_tab.available_filter_operations = FilterModel.CATEGORICAL_OPERATIONS
        else:
            self.model.current_tab.filter_tab_model.current_tab.available_filter_operations = FilterModel.NUMERICAL_OPERATIONS
        self.update_view()

    def update_view(self):
        """Updates the current view to reflect model state"""
        current_filter_model = self.model.current_tab.filter_tab_model.current_tab
        self.change_filter_tab(current_filter_model)

    #def update_q_completers(self, values: List[str]):

    def _on_column_changed(self):
        """Event handler for filter_column_combobox.valueChanged"""
        trace_model = self.model.current_tab  # get current trace model
        filter_tab_model = trace_model.filter_tab_model  # get current filter model
        current_filter_tab = filter_tab_model.current_tab  # from trace model
        if current_filter_tab:  # update the selected column attribute of the filter model
            current_filter_tab.selected_column = self.view.filter_column_combobox.currentText()
            if current_filter_tab.selected_column:
                #  Get the datatype of this column
                dtype = trace_model.selected_data_file.get_dtype(current_filter_tab.selected_column)
                #  Update the available operations accordingly
                if dtype == 'object':
                    self.update_available_operations()
                elif np.issubdtype(dtype, np.number):
                    self.update_available_operations(False)
                else:
                    # TODO handle this case with more nuance
                    self.update_available_operations(False)
                # Update the add/remove list
                unique_values = trace_model.selected_data_file.get_unique_values(current_filter_tab.selected_column)
                current_filter_tab.available_one_of_filter_values = unique_values.copy()
                current_filter_tab.selected_one_of_filter_values = []
                current_filter_tab.completer_list = unique_values
                self.update_view()

    def _on_operation_changed(self):
        trace_model = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.selected_filter_operation = self.view.filter_operation_combobox.currentText()
            self.update_widget_visibility()

    def _on_filter_value_changed(self):
        trace_model = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_values = self.view.filter_value_line_edit.text()

    def _on_filter_value_a_changed(self):
        trace_model = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_value_a = self.view.filter_value_a_line_edit.text()

    def _on_filter_value_b_changed(self):
        trace_model = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_value_b = self.view.filter_value_b_line_edit.text()

    def _on_add_attr_button_clicked(self):
        to_add = self.view.available_values_list.currentItem()
        if to_add is not None:
            val = to_add.text()
            self.model.current_tab.filter_tab_model.current_tab.available_one_of_filter_values.remove(val)
            self.model.current_tab.filter_tab_model.current_tab.selected_one_of_filter_values.append(val)
            self.update_view()

    def _on_rem_attr_button_clicked(self):
        to_rem = self.view.add_remove_list.currentItem()
        if to_rem is not None:
            val = to_rem.text()
            self.model.current_tab.filter_tab_model.current_tab.available_one_of_filter_values.append(val)
            self.model.current_tab.filter_tab_model.current_tab.selected_one_of_filter_values.remove(val)
            self.update_view()
