"""Contains the Controller for the Ternary Trace Editor"""

from PySide6.QtCore import QObject, Signal

from src.views.ternary.trace.view import TernaryTraceEditorView
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.trace.tab_model import TabModel


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
        self.manager = None

        self.setup_connections()

    def setup_connections(self):
        self.view.convert_wtp_molar_checkbox.stateChanged.connect(self._wtp_molar_checkbox_changed_event)
        self.view.name_line_edit.textChanged.connect(self._name_changed_event)

        #self.view.select_data.valueChanged.connect(self.select_data_value_changed)

    def change_tab(self, trace_model: TernaryTraceEditorModel):
        # Take the values from the trace model and populate the view
        self.view.select_data.clear()
        self.view.select_data.addItems(trace_model.available_data_file_names)
        self.view.select_data.setCurrentText(trace_model.selected_data_file_name)
        self.view.convert_wtp_molar_checkbox.setChecked(trace_model.wtp_to_molar_checked)
        self.view.name_line_edit.setText(trace_model.legend_name)
        self.view.point_size_spinbox.setValue(trace_model.point_size)
        #self.view.select_point_shape.addItems(trace_model.available_point_shapes)
        self.view.select_point_shape.setCurrentText(trace_model.selected_point_shape)

    def select_data_value_changed(self, seleced_data: str):
        # Look up the data file in the data library by the string
        pass
        data_file = self.manager.start_setup_model.data_library.get_data_from_shortname(seleced_data)
        # Set the current model's selected data file to this file

    def _name_changed_event(self, value: str):
        self.model.current_tab.legend_name = value

    def _wtp_molar_checkbox_changed_event(self, value: int):
        self.model.current_tab.wtp_to_molar_checked = self.view.convert_wtp_molar_checkbox.isChecked()



