"""Contains the model for the Ternary Trace Editor"""

from typing import List, Optional

import pandas as pd

from src.models.utils.data_models import DataFile
from src.models.ternary.trace.heatmap_model import HeatmapModel
from src.models.ternary.trace.filter.tab_model import FilterTabsPanelModel
from src.models.ternary.trace.advanced_settings_model import AdvancedSettingsModel
from src.models.ternary.trace.bootstrap.error_entry_model import TernaryBootstrapErrorEntryModel

class TernaryTraceEditorModel:

    def __init__(
            self, 
            kind: str = 'standard',
            available_data_file_names: Optional[List[str]] = None,
            selected_data_file_name: Optional[str] = None,
            available_data_files: Optional[List[DataFile]] = None,
            selected_data_file: Optional[DataFile] = None,
            wtp_to_molar_checked: bool = False,
            tab_name: Optional[str] = None,
            legend_name: Optional[str] = None,
            point_size: int = 6,
            available_point_shapes: Optional[List[str]] = None,
            selected_point_shape: str = 'circle',
            color: Optional[str] = None,
            add_heatmap_checked: bool = False,
            filter_data_checked: bool = False,
            advanced_settings_checked: bool = False,
            heatmap_model: Optional[HeatmapModel] = None,
            filter_tab_model: Optional[FilterTabsPanelModel] = None,
            series: Optional[pd.Series] = None,
            line_thickness: Optional[float] = 1.0,
            line_style: Optional[str] = 'solid',
            selected_contour_mode: Optional[str] = '1 sigma',
            contour_level: Optional[float] = 68.0,
            error_entry_model: Optional[TernaryBootstrapErrorEntryModel] = None,
            advanced_settings_model: Optional[AdvancedSettingsModel] = None):
        
        # Direct access
        self.kind = kind
        
        if heatmap_model is None:
            self.heatmap_model = HeatmapModel()
        else:
            self.heatmap_model = heatmap_model
        
        if filter_tab_model is None:
            self.filter_tab_model = FilterTabsPanelModel()
        else:
            self.filter_tab_model = filter_tab_model
        
        if error_entry_model is None:
            self.error_entry_model = TernaryBootstrapErrorEntryModel()
        else:
            self.error_entry_model = error_entry_model

        if advanced_settings_model is None:
            self.advanced_settings_model = AdvancedSettingsModel()
        else:
            self.advanced_settings_model = advanced_settings_model

        # Controlled access
        self._available_data_file_names = available_data_file_names
        self._selected_data_file_name = selected_data_file_name
        self._available_data_files = available_data_files
        self._selected_data_file = selected_data_file
        self._wtp_to_molar_checked = wtp_to_molar_checked
        self._tab_name = tab_name
        self._legend_name = legend_name
        self._point_size = point_size
        self._available_point_shapes = available_point_shapes
        self._selected_point_shape = selected_point_shape
        self._color = color
        self._add_heatmap_checked = add_heatmap_checked
        self._filter_data_checked = filter_data_checked
        self._advanced_settings_checked = advanced_settings_checked
        self._series = series
        self._line_thickness = line_thickness
        self._line_style = line_style
        self._selected_contour_mode = selected_contour_mode
        self._contour_level = contour_level

    @property
    def available_data_file_names(self) -> Optional[List[str]]:
        return self._available_data_file_names
    
    @available_data_file_names.setter
    def available_data_file_names(self, value: Optional[List[str]]):
        self._available_data_file_names = value

    @property
    def selected_data_file_name(self) -> Optional[str]:
        return self._selected_data_file_name
    
    @selected_data_file_name.setter
    def selected_data_file_name(self, value: Optional[str]):
        self._selected_data_file_name = value
        
    @property
    def available_data_files(self) -> Optional[List[DataFile]]:
        return self._available_data_files

    @available_data_files.setter
    def available_data_files(self, value: Optional[List[DataFile]]):
        self._available_data_files = value

    @property
    def selected_data_file(self) -> Optional[DataFile]:
        return self._selected_data_file

    @selected_data_file.setter
    def selected_data_file(self, value: Optional[DataFile]):
        self._selected_data_file = value

    @property
    def wtp_to_molar_checked(self) -> bool:
        return self._wtp_to_molar_checked

    @wtp_to_molar_checked.setter
    def wtp_to_molar_checked(self, value: bool):
        self._wtp_to_molar_checked = value

    @property
    def advanced_settings_checked(self) -> bool:
        return self._advanced_settings_checked
    
    @advanced_settings_checked.setter
    def advanced_settings_checked(self, value: bool):
        self._advanced_settings_checked = value

    @property
    def tab_name(self) -> Optional[str]:
        return self._tab_name

    @tab_name.setter
    def tab_name(self, value: Optional[str]):
        self._tab_name = value

    @property
    def legend_name(self) -> Optional[str]:
        return self._legend_name

    @legend_name.setter
    def legend_name(self, value: Optional[str]):
        self._legend_name = value

    @property
    def point_size(self) -> int:
        return self._point_size

    @point_size.setter
    def point_size(self, value: int):
        self._point_size = value

    @property
    def available_point_shapes(self) -> Optional[List[str]]:
        return self._available_point_shapes

    @available_point_shapes.setter
    def available_point_shapes(self, value: Optional[List[str]]):
        self._available_point_shapes = value

    @property
    def selected_point_shape(self) -> str:
        return self._selected_point_shape

    @selected_point_shape.setter
    def selected_point_shape(self, value: str):
        self._selected_point_shape = value

    @property
    def color(self) -> Optional[str]:
        return self._color

    @color.setter
    def color(self, value: Optional[str]):
        self._color = value

    @property
    def add_heatmap_checked(self) -> bool:
        return self._add_heatmap_checked

    @add_heatmap_checked.setter
    def add_heatmap_checked(self, value: bool):
        self._add_heatmap_checked = value

    @property
    def filter_data_checked(self) -> bool:
        return self._filter_data_checked

    @filter_data_checked.setter
    def filter_data_checked(self, value: bool):
        self._filter_data_checked = value

    @property
    def series(self) -> pd.Series:
        return self._series
    
    @series.setter
    def series(self, value: pd.Series):
        self._series = value

    @property
    def line_thickness(self) -> Optional[float]:
        return self._line_thickness
    
    @line_thickness.setter
    def line_thickness(self, value: float):
        self._line_thickness = value

    @property
    def line_style(self) -> Optional[str]:
        return self._line_style
    
    @line_style.setter
    def line_style(self, value: str):
        self._line_style = value

    @property
    def selected_contour_mode(self) -> Optional[str]:
        return self._selected_contour_mode
    
    @selected_contour_mode.setter
    def selected_contour_mode(self, value: str):
        self._selected_contour_mode = value

    @property
    def contour_level(self) -> Optional[float]:
        return self._contour_level
    
    @contour_level.setter
    def contour_level(self, value: float):
        self._contour_level = value
