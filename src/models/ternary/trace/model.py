"""Contains the model for the Ternary Trace Editor"""

from typing import List, Optional, TYPE_CHECKING

from src.models.ternary.trace import (
    HeatmapModel, 
    SizemapModel,
    BootstrapErrorEntryModel,
    AdvancedSettingsModel
)

from src.models.ternary.trace.filter import FilterTabsPanelModel

from src.models.base.trace import BaseTraceEditorModel

class TernaryTraceEditorModel(BaseTraceEditorModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Override the nested models with plot-specific versions
        self.heatmap_model = kwargs.get('heatmap_model') or HeatmapModel()
        self.sizemap_model = kwargs.get('sizemap_model') or SizemapModel()
        self.filter_tab_model = kwargs.get('filter_tab_model') or FilterTabsPanelModel()
        self.error_entry_model = kwargs.get('error_entry_mode') or BootstrapErrorEntryModel()
        self.advanced_settings_model = kwargs.get('advanced_settings_model') or AdvancedSettingsModel()

    def to_json(self) -> dict:
        data = super().to_json()  # Get the base class's JSON data
        # Update with any additional or overridden attributes
        data.update({
            'heatmap_model': self.heatmap_model.to_json(),
            'sizemap_model': self.sizemap_model.to_json(),
            'filter_tab_model': self.filter_tab_model.to_json(),
            'error_entry_model': self.error_entry_model.to_json(),
            'advanced_settings_model': self.advanced_settings_model.to_json()
        })
        return data
    
    @classmethod
    def from_json(cls, data: dict):
        # Deserialize the base class's data
        instance = super(TernaryTraceEditorModel, cls).from_json(data)
        
        # Override the nested models with plot-specific versions
        instance.heatmap_model = HeatmapModel.from_json(data.get('heatmap_model', {}))
        instance.sizemap_model = SizemapModel.from_json(data.get('sizemap_model', {}))
        instance.filter_tab_model = FilterTabsPanelModel.from_json(data.get('filter_tab_model', {}))
        instance.error_entry_model = BootstrapErrorEntryModel.from_json(data.get('error_entry_model', {}))
        instance.advanced_settings_model = AdvancedSettingsModel.from_json(data.get('advanced_settings_model', {}))

        return instance
