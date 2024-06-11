"""Contains the model for the Heatmap configuration, which is part of the Trace configuration"""

from typing import List, Optional

class HeatmapModel:
    
    def __init__(
            self,
            available_columns: Optional[List[str]] = None,
            selected_column: Optional[str] = None,
            range_min: Optional[float] = None,
            range_max: Optional[float] = None,
            log_transform_checked: bool = False):
        
        self._available_columns = available_columns
        self._selected_column = selected_column
        self._range_min = range_min
        self._range_max = range_max
        self._log_transform_checked = log_transform_checked

    @property
    def available_columns(self) -> Optional[List[str]]:
        return self._available_columns

    @available_columns.setter
    def available_columns(self, value: Optional[List[str]]):
        self._available_columns = value

    @property
    def selected_column(self) -> Optional[str]:
        return self._selected_column

    @selected_column.setter
    def selected_column(self, value: Optional[str]):
        self._selected_column = value

    @property
    def range_min(self) -> Optional[float]:
        return self._range_min

    @range_min.setter
    def range_min(self, value: Optional[float]):
        self._range_min = value

    @property
    def range_max(self) -> Optional[float]:
        return self._range_max

    @range_max.setter
    def range_max(self, value: Optional[float]):
        self._range_max = value

    @property
    def log_transform_checked(self) -> bool:
        return self._log_transform_checked

    @log_transform_checked.setter
    def log_transform_checked(self, value: bool):
        self._log_transform_checked = value
