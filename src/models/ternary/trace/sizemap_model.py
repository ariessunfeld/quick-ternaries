"""Represents the model for the sizemap"""

from typing import List, Optional

class SizemapModel:
    
    def __init__(
            self,
            available_columns: Optional[List[str]] = None,
            selected_column: Optional[str] = None,
            range_min: Optional[float] = None,
            range_max: Optional[float] = None,
            advanced_settings_checked: bool = False,
            log_transform_checked: bool = False,
            sorting_mode: str = 'no change'):
        
        self._available_columns = available_columns
        self._selected_column = selected_column
        self._range_min = range_min
        self._range_max = range_max
        self._advanced_settings_checked = advanced_settings_checked
        self._log_transform_checked = log_transform_checked
        self._sorting_mode = sorting_mode

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
    def advanced_settings_checked(self) -> bool:
        return self._advanced_settings_checked
    
    @advanced_settings_checked.setter
    def advanced_settings_checked(self, value: bool):
        self._advanced_settings_checked = value

    @property
    def log_transform_checked(self) -> bool:
        return self._log_transform_checked

    @log_transform_checked.setter
    def log_transform_checked(self, value: bool):
        self._log_transform_checked = value

    @property
    def sorting_mode(self) -> str:
        return self._sorting_mode
    
    @sorting_mode.setter
    def sorting_mode(self, value: str):
        self._sorting_mode = value
