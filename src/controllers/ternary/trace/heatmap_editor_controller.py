import numpy as np

from src.models.ternary.trace.heatmap_model import HeatmapModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.views.ternary.trace.heatmap_editor_view import TernaryHeatmapEditorView
from src.models.utils.data_models import DataLibrary

class HeatmapEditorController:
    def __init__(self, model: TraceTabsPanelModel, view: TernaryHeatmapEditorView):
        self.model = model
        self.view = view

        self.data_library_reference = None

        self.setup_connections()

    def setup_connections(self):
        self.view.heatmap_column_combobox.valueChanged.connect(self._on_column_changed)
        self.view.range_min_line_edit.textChanged.connect(self._on_range_min_changed)
        self.view.range_max_line_edit.textChanged.connect(self._on_range_max_changed)
        self.view.show_advanced_checkbox.stateChanged.connect(self._on_advanced_checkbox_state_changed)

        self.view.heatmap_colorscale_combobox.valueChanged.connect(self._on_colorscale_changed)
        self.view.log_transform_checkbox.stateChanged.connect(self._on_log_transform_changed)
        self.view.reverse_colorscale_checkbox.stateChanged.connect(self._on_reverse_colorscale_changed)
        self.view.title_line_edit.textChanged.connect(self._on_title_changed)
        self.view.title_position_combobox.valueChanged.connect(self._on_title_position_changed)
        self.view.len_line_edit.textChanged.connect(self._on_length_changed)
        self.view.x_line_edit.textChanged.connect(self._on_x_changed)
        self.view.y_line_edit.textChanged.connect(self._on_y_changed)
        self.view.colorbar_title_font_size_line_edit.textChanged.connect(self._on_title_font_size_changed)
        self.view.colorbar_tick_font_size_line_edit.textChanged.connect(self._on_tick_font_size_changed)
        self.view.colorbar_orientation_combobox.valueChanged.connect(self._on_orientation_changed)

    def set_data_library_reference(self, ref: DataLibrary):
        self.data_library_reference = ref

    def change_trace_tab(self, heatmap_model: HeatmapModel):
        self.view.heatmap_column_combobox.clear()
        self.view.heatmap_column_combobox.addItems(heatmap_model.available_columns)
        self.view.heatmap_column_combobox.setCurrentText(heatmap_model.selected_column)
        self.view.range_min_line_edit.setText(heatmap_model.range_min)
        self.view.range_max_line_edit.setText(heatmap_model.range_max)
        self.view.heatmap_colorscale_combobox.setCurrentText(heatmap_model.colorscale)
        self.view.log_transform_checkbox.setChecked(heatmap_model.log_transform_checked)
        self.view.reverse_colorscale_checkbox.setChecked(heatmap_model.reverse_colorscale)
        self.view.title_line_edit.setText(heatmap_model.bar_title)
        self.view.title_position_combobox.setCurrentText(heatmap_model.title_position)
        self.view.len_line_edit.setText(str(heatmap_model.length))
        self.view.x_line_edit.setText(str(heatmap_model.x))
        self.view.y_line_edit.setText(str(heatmap_model.y))
        self.view.colorbar_title_font_size_line_edit.setText(str(heatmap_model.title_font_size))
        self.view.colorbar_tick_font_size_line_edit.setText(str(heatmap_model.tick_font_size))
        self.view.colorbar_orientation_combobox.setCurrentText(heatmap_model.bar_orientation)
        self.view.show_advanced_checkbox.setChecked(heatmap_model.advanced_settings_checked)
        self.view.advanced_options_layout_widget.setVisible(heatmap_model.advanced_settings_checked)

    def _on_column_changed(self):
        self.model.current_tab.heatmap_model.selected_column = self.view.heatmap_column_combobox.currentText()
        # Get the dtype of the column
        dtype = self.model.current_tab.selected_data_file.get_dtype(self.model.current_tab.heatmap_model.selected_column)
        # If numeric, get the min and median
        if dtype == 'object':
            self.view.range_min_line_edit.clear() # this will update model too
            self.view.range_max_line_edit.clear() # this will update model too
        elif np.issubdtype(dtype, np.number):
            min_val = self.model.current_tab.selected_data_file.get_min(self.model.current_tab.heatmap_model.selected_column)
            median_val = self.model.current_tab.selected_data_file.get_median(self.model.current_tab.heatmap_model.selected_column)
            self.view.range_min_line_edit.setText(str(min_val)) # this will update model too
            self.view.range_max_line_edit.setText(str(2*median_val)) # this will update model too

    def _on_range_min_changed(self):
        self.model.current_tab.heatmap_model.range_min = self.view.range_min_line_edit.text()

    def _on_range_max_changed(self):
        self.model.current_tab.heatmap_model.range_max = self.view.range_max_line_edit.text()

    def _on_colorscale_changed(self):
        self.model.current_tab.heatmap_model.colorscale = self.view.heatmap_colorscale_combobox.currentText()

    def _on_log_transform_changed(self):
        self.model.current_tab.heatmap_model.log_transform_checked = self.view.log_transform_checkbox.isChecked()

    def _on_reverse_colorscale_changed(self):
        self.model.current_tab.heatmap_model.reverse_colorscale = self.view.reverse_colorscale_checkbox.isChecked()

    def _on_title_changed(self):
        self.model.current_tab.heatmap_model.bar_title = self.view.title_line_edit.text()

    def _on_title_position_changed(self):
        self.model.current_tab.heatmap_model.title_position = self.view.title_position_combobox.currentText()

    def _on_length_changed(self):
        self.model.current_tab.heatmap_model.length = float(self.view.len_line_edit.text())

    def _on_x_changed(self):
        self.model.current_tab.heatmap_model.x = float(self.view.x_line_edit.text())

    def _on_y_changed(self):
        self.model.current_tab.heatmap_model.y = float(self.view.y_line_edit.text())

    def _on_title_font_size_changed(self):
        self.model.current_tab.heatmap_model.title_font_size = float(self.view.colorbar_title_font_size_line_edit.text())

    def _on_tick_font_size_changed(self):
        self.model.current_tab.heatmap_model.tick_font_size = float(self.view.colorbar_tick_font_size_line_edit.text())

    def _on_orientation_changed(self):
        self.model.current_tab.heatmap_model.bar_orientation = self.view.colorbar_orientation_combobox.currentText()

    def _on_advanced_checkbox_state_changed(self):
        is_checked = self.view.show_advanced_checkbox.isChecked()
        self.view.advanced_options_layout_widget.setVisible(is_checked)
        self.model.current_tab.heatmap_model.advanced_settings_checked = is_checked

    def handle_trace_selected_data_event(self, value: str):
        """Handle case when user changes the selected data for the trace holding this heatmap"""
        # Get the data file from the data library based on the new name
        data_file = self.data_library_reference.get_data_from_shortname(value)
        if data_file:
            # Get the columns from the new data file
            available_heatmap_columns = data_file.get_columns()
            # Update the heatmap model's available columns
            self.model.current_tab.heatmap_model.available_columns = available_heatmap_columns
            # Clear the view and update it with these columns
            self.view.heatmap_column_combobox.clear()
            self.view.heatmap_column_combobox.addItems(available_heatmap_columns)
            if self.model.current_tab.heatmap_model.selected_column is not None:
                # Set the selected column if non-None
                self.view.heatmap_column_combobox.setCurrentText(self.model.current_tab.heatmap_model.selected_column)