"""Contains the Controller for the Ternary Trace Editor"""

from PySide6.QtCore import QObject, Signal

# Type hints
from src.views.ternary.trace.view import TernaryTraceEditorView
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.utils.data_models import DataLibrary

class TernaryTraceEditorController(QObject):

    """
    Model: Tab model (contains trace models)
    View: Trace Editor View
    """

    selected_data_event = Signal(str)

    def __init__(
            self, 
            model: TraceTabsPanelModel, 
            view: TernaryTraceEditorView):
        
        super().__init__()
        
        self.model = model
        self.view = view

        self.data_library_reference = None

        self.setup_connections()

    def set_data_library_reference(self, ref: DataLibrary):
        # Ideally read-only access to data library
        self.data_library_reference = ref

    def setup_connections(self):
        self.view.select_data.valueChanged.connect(self._selected_data_event)
        self.view.convert_wtp_molar_checkbox.stateChanged.connect(self._wtp_molar_checkbox_changed_event)
        self.view.name_line_edit.textChanged.connect(self._name_changed_event)
        self.view.point_size_spinbox.valueChanged.connect(self._size_changed_event)
        self.view.select_point_shape.valueChanged.connect(self._shape_changed_event)
        self.view.color_picker.colorChanged.connect(self._color_changed_event)
        self.view.use_heatmap_checkbox.stateChanged.connect(self._heatmap_checkbox_statechanged_event)
        self.view.use_filter_checkbox.stateChanged.connect(self._filter_checkbox_statechanged_event)
        self.view.advanced_settings_checkbox.stateChanged.connect(self._advanced_settings_checkbox_statechanged_event)
        self.view.sigma_dropdown.valueChanged.connect(self._selected_contour_event)
        self.view.line_thickness.valueChanged.connect(self._line_thickness_changed_event)
        self.view.percentile_edit.textChanged.connect(self._on_percentile_edit_text_changed)

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
        self.view.advanced_settings_checkbox.setChecked(trace_model.advanced_settings_checked)

        # Bootstrap config
        series = trace_model.series
        if series is not None:
            self.view.refresh_table_from_series(series)
        self.view.sigma_dropdown.setCurrentText(trace_model.selected_contour_mode, block=False)
        self.view.line_thickness.setValue(trace_model.line_thickness)
        self.view.percentile_edit.setText(str(trace_model.contour_level))
        

    def _selected_data_event(self, value: str):
        # Set the model's selected data file name to this value
        self.model.current_tab.selected_data_file_name = value
        self.model.current_tab.selected_data_file = self.data_library_reference.get_data_from_shortname(value)

        # Emit the signal so the heatmap and filter(s) can be updated
        self.selected_data_event.emit(value)

    def _name_changed_event(self, value: str):
        self.model.current_tab.legend_name = value

    def _line_thickness_changed_event(self, value: int):
        self.model.current_tab.line_thickness = value

    def _wtp_molar_checkbox_changed_event(self, value: int):
        self.model.current_tab.wtp_to_molar_checked = self.view.convert_wtp_molar_checkbox.isChecked()
        
        # Update molar conversion panel visibility
        condition = \
            self.view.molar_conversion_view.container_layout.count() > 1 \
            and self.view.convert_wtp_molar_checkbox.isChecked()
        self.view.molar_conversion_view.setVisible(
            condition)

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
        self.view.color_picker.setEnabled(not is_checked)

    def _filter_checkbox_statechanged_event(self, event):
        is_checked = self.view.use_filter_checkbox.isChecked()
        self.model.current_tab.filter_data_checked = is_checked
        self.view.filter_view.setVisible(is_checked)
    
    def _advanced_settings_checkbox_statechanged_event(self, event):
        is_checked = self.view.advanced_settings_checkbox.isChecked()
        self.model.current_tab.advanced_settings_checked = is_checked
        self.view.trace_editor_advanced_settings_view.setVisible(is_checked)

    def _selected_contour_event(self, value: str):
        self.model.current_tab.selected_contour_mode = value
        if value == 'custom':
            self.view.percentile_edit.setEnabled(True)
            self.view.percentile_edit.setText(str(self.model.current_tab.contour_level))
        elif value == '1 sigma':
            self.view.percentile_edit.setEnabled(False)
            self.view.percentile_edit.setText('68')
            self.model.current_tab.contour_level = 68.0
        elif value == '2 sigma':
            self.view.percentile_edit.setEnabled(False)
            self.view.percentile_edit.setText('95')
            self.model.current_tab.contour_level = 95.0

    def _on_percentile_edit_text_changed(self, value: str):
        self.model.current_tab.contour_level = float(value)
