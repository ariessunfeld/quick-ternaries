"""Correlation Plot (heatmap) Trace Editor Model"""

from src.models.base.trace import BaseTraceEditorModel

class CorrplotTraceEditorModel(BaseTraceEditorModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
