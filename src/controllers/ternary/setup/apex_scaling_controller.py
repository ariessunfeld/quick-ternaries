"""Connects the TernaryTraceMolarConversionModel with its view"""

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject

if TYPE_CHECKING:
    from src.models.ternary.setup import TernaryAxisScalingModel
    from src.views.ternary.setup import TernaryApexScalingView

class TernaryApexScalingController(QObject):
    
    def __init__(
            self,
            model: 'TernaryAxisScalingModel',
            view: 'TernaryApexScalingView'):
        super().__init__()

        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.textChanged.connect(self._on_view_text_changed)
    
    def _on_view_text_changed(self, column: str, formula: str):
        self.model.update_scale_factor(column, formula)
        #self._refresh()

    def on_new_custom_column_added(self, column: str):
        self.model.add_column(column)
        self._refresh()

    def on_new_custom_column_removed(self, column: str):
        self.model.rem_column(column)
        self._refresh()

    def _refresh(self):
        self.view.update_view(self.model.get_sorted_repr())
