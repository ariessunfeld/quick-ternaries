from typing import List

from PySide6.QtCore import (
    Slot, QObject
)

class PlotlyInterface(QObject):
    def __init__(self):
        super().__init__()
        self.selected_indices = []

    @Slot(list)
    def receive_selected_indices(self, indices: list):
        self.selected_indices = indices

    def get_indices(self) -> List:
        return self.selected_indices.copy()
