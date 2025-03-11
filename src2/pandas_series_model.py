"""Represents a single-row pandas series, for display in a QTable"""

from typing import Any
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import pandas as pd

class PandasSeriesModel(QAbstractTableModel):
    def __init__(self, series: pd.Series):
        super().__init__()
        self.series = series

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1  # Single row to represent the series

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.series)  # Number of columns is the length of the series

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self.series.iloc[index.column()])  # Single row, use column index to get value
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self.series.index[section])  # Column headers from series index
        return None
