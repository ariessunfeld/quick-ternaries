from src.models.ternary.trace.heatmap_model import HeatmapModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.views.ternary.trace.heatmap_editor_view import TernaryHeatmapEditorView

class HeatmapEditorController:
    def __init__(self, model: TraceTabsPanelModel, view: TernaryHeatmapEditorView):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.heatmap_column_combobox.valueChanged.connect(self._on_column_changed)
        self.view.range_min_line_edit.textChanged.connect(self._on_range_min_changed)
        self.view.range_max_line_edit.textChanged.connect(self._on_range_max_changed)
        # Future connections for other parameters than user can edit,
        # like heatmap color scale, whether to reverse it, whether to log-transform

    def change_trace_tab(self, heatmap_model: HeatmapModel):
        self.view.heatmap_column_combobox.setCurrentText(heatmap_model.selected_column)
        self.view.range_min_line_edit.setText(heatmap_model.range_min)
        self.view.range_max_line_edit.setText(heatmap_model.range_max)

    def _on_column_changed(self):
        self.model.current_tab.heatmap_model.selected_column = self.view.heatmap_column_combobox.currentText()

    def _on_range_min_changed(self):
        self.model.current_tab.heatmap_model.range_min = self.view.range_min_line_edit.text()

    def _on_range_max_changed(self):
        self.model.current_tab.heatmap_model.range_max = self.view.range_max_line_edit.text()
