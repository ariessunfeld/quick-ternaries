"""Contains the model for the Heatmap configuration, which is part of the Trace configuration"""
from typing import List, Optional

class HeatmapModel:
    
    def __init__(
            self,
            available_columns: Optional[List[str]] = None,
            selected_column: Optional[str] = None,
            range_min: Optional[float] = None,
            range_max: Optional[float] = None,
            advanced_settings_checked: bool = False,
            log_transform_checked: bool = False,
            reverse_colorscale_checked: bool = True,
            selected_colorscale: str = 'Inferno',
            colorbar_title: Optional[str] = None,
            title_position: Optional[str] = 'top',
            colorbar_length: float = 0.6,
            colorbar_thickness: float = 18,
            colorbar_x_pos: float = 1.1,
            colorbar_y_pos: float = 0.5,
            colorbar_font: str = 'Open Sans',
            colorbar_title_font_size: float = 12,
            colorbar_tick_font_size: float = 12,
            colorbar_orientation: str = 'vertical',
            sorting_mode: str = 'no change'):
        
        self._available_columns = available_columns
        self._selected_column = selected_column
        self._range_min = range_min
        self._range_max = range_max
        self._advanced_settings_checked = advanced_settings_checked
        self._log_transform_checked = log_transform_checked
        self._reverse_colorscale = reverse_colorscale_checked
        self._colorscale = selected_colorscale
        self._bar_title = colorbar_title
        self._title_position = title_position
        self._length = colorbar_length
        self._thickness = colorbar_thickness
        self._x = colorbar_x_pos
        self._y = colorbar_y_pos
        self._font = colorbar_font
        self._title_font_size = colorbar_title_font_size
        self._tick_font_size = colorbar_tick_font_size
        self._bar_orientation = colorbar_orientation
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
    def reverse_colorscale(self) -> bool:
        return self._reverse_colorscale

    @reverse_colorscale.setter
    def reverse_colorscale(self, value: bool):
        self._reverse_colorscale = value

    @property
    def colorscale(self) -> Optional[str]:
        return self._colorscale

    @colorscale.setter
    def colorscale(self, value: Optional[str]):
        self._colorscale = value

    @property
    def bar_title(self) -> Optional[str]:
        return self._bar_title

    @bar_title.setter
    def bar_title(self, value: Optional[str]):
        self._bar_title = value

    @property
    def title_position(self) -> Optional[str]:
        return self._title_position

    @title_position.setter
    def title_position(self, value: Optional[str]):
        self._title_position = value

    @property
    def length(self) -> float:
        return self._length

    @length.setter
    def length(self, value: float):
        self._length = value

    @property
    def thickness(self) -> float:
        return self._thickness

    @thickness.setter
    def thickness(self, value: float):
        self._thickness = value

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value: float):
        self._x = value

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self, value: float):
        self._y = value

    @property
    def font(self) -> float:
        return self._font

    @font.setter
    def font(self, value: str):
        self._font = value

    @property
    def title_font_size(self) -> float:
        return self._title_font_size

    @title_font_size.setter
    def title_font_size(self, value: float):
        self._title_font_size = value

    @property
    def tick_font_size(self) -> float:
        return self._tick_font_size

    @tick_font_size.setter
    def tick_font_size(self, value: float):
        self._tick_font_size = value

    @property
    def bar_orientation(self) -> str:
        return self._bar_orientation

    @bar_orientation.setter
    def bar_orientation(self, value: str):
        self._bar_orientation = value

    @property
    def sorting_mode(self) -> str:
        return self._sorting_mode
    
    @sorting_mode.setter
    def sorting_mode(self, value: str):
        self._sorting_mode = value

