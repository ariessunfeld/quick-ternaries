from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.trace.advanced_settings_model import AdvancedSettingsModel
from src.views.ternary.trace.advanced_settings_view import AdvancedSettingsView

class AdvancedSettingsController:
    def __init__(self, model: TraceTabsPanelModel, view: AdvancedSettingsView):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.opacity.valueChanged.connect(self._on_opacity_changed)
        self.view.outline_color.colorChanged.connect(self._on_outline_color_changed)
        self.view.outline_thickness.valueChanged.connect(self._on_outline_thickness_changed)

    def change_trace_tab(self, advanced_settings_model: AdvancedSettingsModel):
        self.view.opacity.setValue(advanced_settings_model.opacity)
        self.view.outline_color.setColor(advanced_settings_model.outline_color)
        self.view.outline_thickness.setValue(advanced_settings_model.outline_thickness)

    def _on_opacity_changed(self, value: int):
        self.model.current_tab.advanced_settings_model.opacity = value

    def _on_outline_color_changed(self, value: str):
        self.model.current_tab.advanced_settings_model.outline_color = value

    def _on_outline_thickness_changed(self, value: int):
        self.model.current_tab.advanced_settings_model.outline_thickness = value