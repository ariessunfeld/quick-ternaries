from src.models.base.trace import BaseTraceEditorModel

class CartesianTraceEditorModel(BaseTraceEditorModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # we can add more attrs here if needed