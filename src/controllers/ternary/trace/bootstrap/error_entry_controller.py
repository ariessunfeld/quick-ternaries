"""Connects the TernaryTraceMolarConversionModel with its view"""

from PySide6.QtCore import QObject, Signal

from src.models.ternary.trace.bootstrap.error_entry_model import TernaryBootstrapErrorEntryModel
from src.models.ternary.setup.apex_scaling_model import TernaryApexScalingModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.views.ternary.setup import TernaryApexScalingView
from src.views.ternary.trace.bootstrap.error_entry_view import TernaryBootstrapErrorEntryView

class TernaryBootstrapErrorEntryController(QObject):
    
    def __init__(
            self,
            model: TraceTabsPanelModel,
            view: TernaryBootstrapErrorEntryView):
        super().__init__()

        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.textChanged.connect(self._on_view_text_changed)
    
    def _on_view_text_changed(self, column: str, error: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.update_error_value(column, error)

    def on_new_custom_column_added(self, column: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.add_column(column)
            self._refresh()

    def on_new_custom_column_removed(self, column: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.rem_column(column)
            self._refresh()

    def _refresh(self):
        current_tab = self.model.current_tab
        if current_tab:
            self.view.update_view(self.model.current_tab.error_entry_model.get_sorted_repr())
