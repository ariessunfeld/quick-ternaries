"""Controller for the Sizemap Editor"""

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from src.models.ternary.trace import SizemapModel, TraceTabsPanelModel
    from src.models.utils.data_models import DataLibrary
    from src.views.ternary.trace.sizemap_editor_view import TernarySizemapEditorView

class SizemapEditorController:
    def __init__(self, model: 'TraceTabsPanelModel', view: 'TernarySizemapEditorView'):
        self.model = model
        self.view = view

        self.data_library_reference = None

        self.setup_connections()

    def setup_connections(self):
        self.view.sizemap_column_combobox.valueChanged.connect(self._on_column_changed)
        self.view.range_min_line_edit.textChanged.connect(self._on_range_min_changed)
        self.view.range_max_line_edit.textChanged.connect(self._on_range_max_changed)
        self.view.show_advanced_checkbox.stateChanged.connect(self._on_advanced_checkbox_state_changed)

        self.view.log_transform_checkbox.stateChanged.connect(self._on_log_transform_changed)

        self.view.no_change_radio.toggled.connect(self._on_radio_toggled)
        self.view.shuffled_radio.toggled.connect(self._on_radio_toggled)
        self.view.high_on_top_radio.toggled.connect(self._on_radio_toggled)
        self.view.low_on_top_radio.toggled.connect(self._on_radio_toggled)

    def set_data_library_reference(self, ref: 'DataLibrary'):
        self.data_library_reference = ref

    def change_trace_tab(self, sizemap_model: 'SizemapModel'):
        self.view.sizemap_column_combobox.clear()
        self.view.sizemap_column_combobox.addItems(sizemap_model.available_columns)
        self.view.sizemap_column_combobox.setCurrentText(sizemap_model.selected_column)
        self.view.range_min_line_edit.setText(sizemap_model.range_min)
        self.view.range_max_line_edit.setText(sizemap_model.range_max)
        self.view.log_transform_checkbox.setChecked(sizemap_model.log_transform_checked)
        self.view.show_advanced_checkbox.setChecked(sizemap_model.advanced_settings_checked)
        self.view.advanced_options_layout_widget.setVisible(sizemap_model.advanced_settings_checked)
        # Set the sort mode radiobutton by name
        sort_mode = sizemap_model.sorting_mode.lower().replace(' ', '_')
        getattr(self.view, f'{sort_mode}_radio').setChecked(True)

    def _on_column_changed(self):
        self.model.current_tab.sizemap_model.selected_column = self.view.sizemap_column_combobox.currentText()
        self.model.current_tab.sizemap_model.bar_title = self.view.sizemap_column_combobox.currentText()
        # Get the dtype of the column
        dtype = self.model.current_tab.selected_data_file.get_dtype(self.model.current_tab.sizemap_model.selected_column)
        # If numeric, get the min and median
        if dtype == 'object':
            self.view.range_min_line_edit.clear() # this will update model too, 
                                                  # not because view holds reference to model, 
                                                  # but because it triggers the line edit's textChanged event
            self.view.range_max_line_edit.clear()
        elif np.issubdtype(dtype, np.number):
            min_val = self.model.current_tab.selected_data_file.get_min(self.model.current_tab.sizemap_model.selected_column)
            median_val = self.model.current_tab.selected_data_file.get_median(self.model.current_tab.sizemap_model.selected_column)
            # self.view.range_min_line_edit.setText(str(min_val)) # this will update model too
            # self.view.range_max_line_edit.setText(str(2*median_val)) # this will update model too
            self.view.range_min_line_edit.setText(str(1.0))
            self.view.range_max_line_edit.setText(str(6.0))

    def _on_range_min_changed(self):
        self.model.current_tab.sizemap_model.range_min = self.view.range_min_line_edit.text()

    def _on_range_max_changed(self):
        self.model.current_tab.sizemap_model.range_max = self.view.range_max_line_edit.text()

    def _on_log_transform_changed(self):
        is_checked = self.view.log_transform_checkbox.isChecked()
        self.model.current_tab.sizemap_model.log_transform_checked = is_checked

        # Case where it was not checked and now is
        if is_checked:
            curr_range_min = self.model.current_tab.sizemap_model.range_min
            curr_range_max = self.model.current_tab.sizemap_model.range_max
            try:
                curr_range_min = self._float(curr_range_min)
                curr_range_max = self._float(curr_range_max)
                new_range_min = round(np.log(curr_range_min),2) if curr_range_min > 0 else curr_range_min
                new_range_max = round(np.log(curr_range_max),2) if curr_range_max > 0 else 0
                self.view.range_min_line_edit.setText(str(new_range_min)) # this will update model too
                self.view.range_max_line_edit.setText(str(new_range_max)) # this will update model too
            except ValueError:
                pass
        # Case where it was checked and now isn't
        # want to reset to min and 2xMedian
        else:
            min_val = self.model.current_tab.selected_data_file.get_min(self.model.current_tab.sizemap_model.selected_column)
            median_val = self.model.current_tab.selected_data_file.get_median(self.model.current_tab.sizemap_model.selected_column)
            # self.view.range_min_line_edit.setText(str(min_val)) # this will update model too
            # self.view.range_max_line_edit.setText(str(2*median_val)) # this will update model too
            self.view.range_min_line_edit.setText(str(1.0))
            self.view.range_max_line_edit.setText(str(6.0))

    def _on_advanced_checkbox_state_changed(self):
        is_checked = self.view.show_advanced_checkbox.isChecked()
        self.view.advanced_options_layout_widget.setVisible(is_checked)
        self.model.current_tab.sizemap_model.advanced_settings_checked = is_checked

    def _on_radio_toggled(self, name: str):
        self.model.current_tab.sizemap_model.sorting_mode = name.lower()
    
    def handle_trace_selected_data_event(self, value: str):
        """Handle case when user changes the selected data for the trace holding this sizemap"""
        # Get the data file from the data library based on the new name
        data_file = self.data_library_reference.get_data_from_shortname(value)
        if data_file:
            # Get the columns from the new data file
            # Only show numeric columns
            available_sizemap_columns = data_file.get_columns()
            available_sizemap_columns = [
                c for c in available_sizemap_columns if \
                    np.issubdtype(data_file.get_dtype(c), np.number)]
            # Update the sizemap model's available columns
            self.model.current_tab.sizemap_model.available_columns = available_sizemap_columns
            # Clear the view and update it with these columns
            self.view.sizemap_column_combobox.clear()
            self.view.sizemap_column_combobox.addItems(available_sizemap_columns)
            if self.model.current_tab.sizemap_model.selected_column is not None:
                # Set the selected column if non-None
                self.view.sizemap_column_combobox.setCurrentText(self.model.current_tab.sizemap_model.selected_column)
            elif len(available_sizemap_columns) > 1:
                # TODO Hacky solution, only works if > 1 item available... fix ASAP
                self.view.sizemap_column_combobox.setCurrentText(available_sizemap_columns[1], block=False)
                self.view.sizemap_column_combobox.setCurrentText(available_sizemap_columns[0], block=False)

    @staticmethod
    def _float(val: str) -> float:
        """Handles blank string case and nonnumeric cases"""
        cleaned = []
        for ch in val:
            if ch.isdigit() or (ch == '.' and ch not in cleaned) or (ch == '-' and ch not in cleaned):
                cleaned.append(ch)
        cleaned = ''.join(cleaned)
        if cleaned and cleaned != '.' and cleaned != '-':
            if float(cleaned) == int(float(cleaned)):
                return int(float(cleaned))
            else:
                return float(cleaned)
        else:
            return ''
