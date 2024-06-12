"""Contains the Controller for the Ternary Trace Editor"""

from PySide6.QtCore import QObject, Signal

# Type hints
from src.views.ternary.trace.view import TernaryTraceEditorView
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.trace.tab_model import TabModel

# Instantiations
from src.controllers.ternary.trace.filter.controller import FilterEditorController
from src.controllers.ternary.trace.filter.tab_controller import FilterTabController

class TernaryTraceEditorController(QObject):

    """
    Model: Tab model (contains trace models)
    View: Trace Editor View
    """

    def __init__(
            self, 
            model: TabModel, 
            view: TernaryTraceEditorView):
        
        self.model = model
        self.view = view

        self.setup_connections()
        #self.setup_child_controllers()

    def setup_connections(self):
        self.view.select_data.valueChanged.connect(self._selected_data_event)
        self.view.convert_wtp_molar_checkbox.stateChanged.connect(self._wtp_molar_checkbox_changed_event)
        self.view.name_line_edit.textChanged.connect(self._name_changed_event)
        self.view.point_size_spinbox.valueChanged.connect(self._size_changed_event)
        self.view.select_point_shape.valueChanged.connect(self._shape_changed_event)
        self.view.color_picker.colorChanged.connect(self._color_changed_event)
        self.view.use_heatmap_checkbox.stateChanged.connect(self._heatmap_checkbox_statechanged_event)
        self.view.use_filter_checkbox.stateChanged.connect(self._filter_checkbox_statechanged_event)

        #self.view.select_data.valueChanged.connect(self.select_data_value_changed)

    def change_tab(self, trace_model: TernaryTraceEditorModel):
        # Take the values from the trace model and populate the view accordingly
        self.view.select_data.clear()
        self.view.select_data.addItems(trace_model.available_data_file_names)
        self.view.select_data.setCurrentText(trace_model.selected_data_file_name)
        self.view.convert_wtp_molar_checkbox.setChecked(trace_model.wtp_to_molar_checked)
        self.view.name_line_edit.setText(trace_model.legend_name)
        self.view.point_size_spinbox.setValue(trace_model.point_size)
        self.view.select_point_shape.setCurrentText(trace_model.selected_point_shape)
        self.view.color_picker.setColor(trace_model.color)
        self.view.use_heatmap_checkbox.setChecked(trace_model.add_heatmap_checked)
        self.view.use_filter_checkbox.setChecked(trace_model.filter_data_checked)

        # Instantiate new filter controllers each time we change a tab
        # self.view.filter_view.filter_tab_view.clear()
        # for f in trace_model.filter_tab_model.order:
        #     self.view.filter_view.filter_tab_view.add_tab_to_view(f'Filter {f}', f)
        #self.filter_tab_controller = FilterTabController(trace_model.filter_tab_model, self.view.filter_view.filter_tab_view)
        #self.filter_editor_controller = FilterEditorController(trace_model.filter_tab_model, self.view.filter_view.filter_editor_view)

    def _selected_data_event(self, value: str):
        self.model.current_tab.selected_data_file_name = value

    def _name_changed_event(self, value: str):
        self.model.current_tab.legend_name = value

    def _wtp_molar_checkbox_changed_event(self, value: int):
        self.model.current_tab.wtp_to_molar_checked = self.view.convert_wtp_molar_checkbox.isChecked()

    def _size_changed_event(self, value: int):
        self.model.current_tab.point_size = value

    def _shape_changed_event(self, value: str):
        self.model.current_tab.selected_point_shape = value

    def _color_changed_event(self, value: str):
        self.model.current_tab.color = value

    def _heatmap_checkbox_statechanged_event(self, event):
        is_checked = self.view.use_heatmap_checkbox.isChecked()
        self.model.current_tab.add_heatmap_checked = is_checked
        self.view.heatmap_view.setVisible(is_checked)

    def _filter_checkbox_statechanged_event(self, event):
        is_checked = self.view.use_filter_checkbox.isChecked()
        self.model.current_tab.filter_data_checked = is_checked
        self.view.filter_view.setVisible(is_checked)
