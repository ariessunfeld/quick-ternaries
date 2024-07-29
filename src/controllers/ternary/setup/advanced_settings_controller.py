from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.views.ternary.setup import AdvancedSettingsView
    from src.models.ternary.setup import TernaryAdvancedSettingsModel

class AdvancedSettingsController:
    def __init__(self, model: 'TernaryAdvancedSettingsModel', view: 'AdvancedSettingsView'):
        self.model = model
        self.view = view

        self._set_default_values()
        self.setup_connections()

    def setup_connections(self):
        self.view.paper_color.colorChanged.connect(self._on_paper_color_changed)
        self.view.background_color.colorChanged.connect(self._on_background_color_changed)
        self.view.gridline_step_size.valueChanged.connect(self._on_gridline_step_size_changed)
        self.view.ternary_sum_combo.valueChanged.connect(self._on_ternary_sum_changed)
        self.view.gridline_color.colorChanged.connect(self._on_gridline_color_changed)
        self.view.title_font_combo.valueChanged.connect(self._on_title_font_changed)
        self.view.title_font_size_spinbox.valueChanged.connect(self._on_title_font_size_changed)
        self.view.axis_font_combo.valueChanged.connect(self._on_axis_font_changed)
        self.view.axis_font_size_spinbox.valueChanged.connect(self._on_axis_font_size_changed)
        self.view.tick_font_combo.valueChanged.connect(self._on_tick_font_changed)
        self.view.tick_font_size_spinbox.valueChanged.connect(self._on_tick_font_size_changed)
        self.view.show_tick_marks.stateChanged.connect(self._on_show_tick_marks_changed)
        self.view.show_grid.stateChanged.connect(self._on_show_grid_changed)

    def _on_background_color_changed(self, color: str):
        self.model.background_color = color

    def _on_gridline_step_size_changed(self, value: int):
        if self.model.ternary_sum == "1":
            self.model.gridline_step_size = value/100
        else:
            self.model.gridline_step_size = value

    def _on_ternary_sum_changed(self, value: str):
        if value=="1":
            self.model.gridline_step_size/=100
        else:
            self.model.gridline_step_size*=100
        self.model.ternary_sum = value

    def _on_gridline_color_changed(self, color: str):
        self.model.gridline_color = color

    def _on_paper_color_changed(self, color: str):
        self.model.paper_color = color

    def _on_title_font_changed(self, font: str):
        self.model.title_font = font

    def _on_title_font_size_changed(self, value: int):
        self.model.title_font_size = value

    def _on_axis_font_changed(self, font: str):
        self.model.axis_font = font

    def _on_axis_font_size_changed(self, value: int):
        self.model.axis_font_size = value

    def _on_tick_font_changed(self, font: str):
        self.model.tick_font = font

    def _on_tick_font_size_changed(self, value: int):
        self.model.tick_font_size = value

    def _on_show_tick_marks_changed(self):
        is_checked = self.view.show_tick_marks.isChecked()
        self.model.show_tick_marks = is_checked
        self.view.tick_font_combo.setEnabled(is_checked)
        self.view.tick_font_size_spinbox.setEnabled(is_checked)

    def _on_show_grid_changed(self):
        is_checked = self.view.show_grid.isChecked()
        self.model.show_grid = is_checked
        self.view.gridline_color.setEnabled(is_checked)
        self.view.gridline_step_size.setEnabled(is_checked)

    def _set_default_values(self):
        """
        set default values for the view from the model
        """
        self.view.background_color.setColor(self.model.background_color)
        self.view.ternary_sum_combo.setCurrentText(str(self.model.ternary_sum))
        self.view.gridline_step_size.setValue(self.model.gridline_step_size)
        self.view.gridline_color.setColor(self.model.gridline_color)
        self.view.paper_color.setColor(self.model.paper_color)
        self.view.title_font_combo.setCurrentText(self.model.title_font)
        self.view.title_font_size_spinbox.setValue(self.model.title_font_size)
        self.view.axis_font_combo.setCurrentText(self.model.axis_font)
        self.view.axis_font_size_spinbox.setValue(self.model.axis_font_size)
        self.view.tick_font_combo.setCurrentText(self.model.tick_font)
        self.view.tick_font_size_spinbox.setValue(self.model.tick_font_size)
