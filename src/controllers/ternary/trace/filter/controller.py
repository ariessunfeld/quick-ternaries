"""Contains the FilterEditorController class"""

from PySide6.QtCore import QObject
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.views.ternary.trace.filter.filter_editor_view import FilterEditorView
from src.models.ternary.trace.filter.tab_model import FilterTabModel
from src.models.ternary.trace.filter.model import FilterModel

class FilterEditorController(QObject):
    def __init__(self, model: TraceTabsPanelModel, view: FilterEditorView):
        super().__init__()
        self.model = model
        self.view = view
        self.setup_connections()

    def setup_connections(self):
        self.view.filter_column_combobox.valueChanged.connect(self.on_column_changed)
        self.view.filter_operation_combobox.combobox.currentIndexChanged.connect(self.on_operation_changed)
        self.view.filter_value_line_edit.textChanged.connect(self.on_filter_value_changed)
        self.view.filter_value_a_line_edit.textChanged.connect(self.on_filter_value_a_changed)
        self.view.filter_value_b_line_edit.textChanged.connect(self.on_filter_value_b_changed)

    def change_trace_tab(self, filter_model: FilterModel):
        pass

    def change_filter_tab(self, filter_model: FilterModel):
        # Clear the filter view
        #self.view.clear()

        # Populate it accordingly
        self.view.filter_column_combobox.clear()
        self.view.filter_column_combobox.addItems(filter_model.available_columns)
        self.view.filter_column_combobox.setCurrentText(filter_model.selected_column)
        self.view.filter_operation_combobox.clear()
        self.view.filter_operation_combobox.addItems(filter_model.available_filter_operations)
        self.view.filter_operation_combobox.setCurrentText(filter_model.selected_filter_operation)
        self.view.filter_value_line_edit.setText(filter_model.filter_values)
        self.view.filter_value_a_line_edit.setText(filter_model.filter_value_a)
        self.view.filter_value_b_line_edit.setText(filter_model.filter_value_b)
        if filter_model.available_one_of_filter_values:
            self.view.available_values_list.addItems(filter_model.available_one_of_filter_values)
        self.view.add_remove_list.addItems(filter_model.selected_one_of_filter_values)

        # Update visibility based on dropdowns and types
        self.update_visibility()

    def update_visibility(self):
        is_range_operation = self.view.filter_operation_combobox.currentText() in FilterModel.NUMERICAL_RANGE
        self.view.filter_value_line_edit.setVisible(not is_range_operation)
        self.view.filter_value_a_line_edit.setVisible(is_range_operation)
        self.view.filter_value_b_line_edit.setVisible(is_range_operation)

        is_one_of_operation = self.view.filter_operation_combobox.currentText() == 'One of'
        self.view.add_remove_layout_widget.setVisible(is_one_of_operation)
        self.view.filter_value_line_edit.setVisible(not is_one_of_operation)

    def on_column_changed(self):
        trace_model: TernaryTraceEditorModel = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.selected_column = self.view.filter_column_combobox.currentText()

    def on_operation_changed(self):
        trace_model: TernaryTraceEditorModel = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.selected_filter_operation = self.view.filter_operation_combobox.currentText()
            self.update_visibility()

    def on_filter_value_changed(self):
        trace_model: TernaryTraceEditorModel = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_values = self.view.filter_value_line_edit.text()

    def on_filter_value_a_changed(self):
        trace_model: TernaryTraceEditorModel = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_value_a = self.view.filter_value_a_line_edit.text()

    def on_filter_value_b_changed(self):
        trace_model: TernaryTraceEditorModel = self.model.current_tab
        filter_tab_model = trace_model.filter_tab_model
        current_filter_tab = filter_tab_model.current_tab
        if current_filter_tab:
            current_filter_tab.filter_value_b = self.view.filter_value_b_line_edit.text()
