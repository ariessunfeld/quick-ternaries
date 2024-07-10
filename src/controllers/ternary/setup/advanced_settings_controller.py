from PySide6.QtGui import QColor, QFont

from src.models.ternary.setup.advanced_settings_model import AdvancedSettingsModel
from src.views.ternary.setup.advanced_settings_view import AdvancedSettingsView

class AdvancedSettingsController:
    def __init__(self, model: AdvancedSettingsModel, view: AdvancedSettingsView):
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

    def _on_background_color_changed(self, color: str):
        self.model.background_color = color

    def _on_gridline_step_size_changed(self, value: int):
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

    def _on_title_font_changed(self, font: QFont):
        self.model.title_font = font

    def _on_title_font_size_changed(self, value: int):
        self.model.title_font_size = value

    def _on_axis_font_changed(self, font: QFont):
        self.model.axis_font = font

    def _on_axis_font_size_changed(self, value: int):
        self.model.axis_font_size = value

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
