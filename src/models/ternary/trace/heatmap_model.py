"""Model for the Ternary heatmap configuration panel"""

from src.models.utils.trace.heatmap_model import BaseHeatmapModel

class HeatmapModel(BaseHeatmapModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
