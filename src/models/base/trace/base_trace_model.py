"""Base class for Trace Editor Models"""

from abc import ABC
from typing import List, Optional, TYPE_CHECKING

import pandas as pd

from src.models.utils.trace import (
    HeatmapModel, 
    SizemapModel, 
    BootstrapErrorEntryModel
)
from src.models.utils.data_models import DataFile
from src.models.utils.trace.filter import FilterTabsPanelModel

from src import __version__


class BaseTraceEditorModel(ABC):

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
            add_sizemap_checked: bool = False,
            filter_data_checked: bool = False,
            advanced_settings_checked: bool = False,
            heatmap_model: Optional[HeatmapModel] = None,
            sizemap_model: Optional[SizemapModel] = None,
            filter_tab_model: Optional[FilterTabsPanelModel] = None,
            series: Optional[pd.Series] = None,
            line_thickness: Optional[float] = 2.0,
            line_style: Optional[str] = 'solid',
            selected_contour_mode: Optional[str] = '1 sigma',
            contour_level: Optional[float] = 68.0,
            error_entry_model: Optional[BootstrapErrorEntryModel] = None):
        
        # Direct access
        self.kind = kind
        self.heatmap_model = heatmap_model or HeatmapModel()
        self.sizemap_model = sizemap_model or SizemapModel()
        self.filter_tab_model = filter_tab_model or FilterTabsPanelModel()
        self.error_entry_model = error_entry_model or BootstrapErrorEntryModel()

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
        self._add_sizemap_checked = add_sizemap_checked
        self._filter_data_checked = filter_data_checked
        self._advanced_settings_checked = advanced_settings_checked
        self._series = series
        self._line_thickness = line_thickness
        self._line_style = line_style
        self._selected_contour_mode = selected_contour_mode
        self._contour_level = contour_level

    def to_json(self) -> dict:
        return {
            'version': __version__,
            'kind': self.kind,
            'available_data_file_names': self._available_data_file_names,
            'selected_data_file_name': self._selected_data_file_name,
            'available_data_files': [df.to_json() for df in self._available_data_files] if self._available_data_files else None,
            'selected_data_file': self._selected_data_file.to_json() if self._selected_data_file else None,
            'wtp_to_molar_checked': self._wtp_to_molar_checked,
            'tab_name': self._tab_name,
            'legend_name': self._legend_name,
            'point_size': self._point_size,
            'available_point_shapes': self._available_point_shapes,
            'selected_point_shape': self._selected_point_shape,
            'color': self._color,
            'add_heatmap_checked': self._add_heatmap_checked,
            'add_sizemap_checked': self._add_sizemap_checked,
            'filter_data_checked': self._filter_data_checked,
            'advanced_settings_checked': self._advanced_settings_checked,
            'heatmap_model': self.heatmap_model.to_json(),
            'sizemap_model': self.sizemap_model.to_json(),
            'filter_tab_model': self.filter_tab_model.to_json(),
            'series': self._series.to_json() if self._series is not None else None,
            'line_thickness': self._line_thickness,
            'line_style': self._line_style,
            'selected_contour_mode': self._selected_contour_mode,
            'contour_level': self._contour_level,
            'error_entry_model': self.error_entry_model.to_json()
        }
    
    @classmethod
    def from_json(cls, data: dict):
        available_data_files = [DataFile.from_json(df) for df in data.get('available_data_files', [])] if data.get('available_data_files') else None
        selected_data_file = DataFile.from_json(data.get('selected_data_file')) if data.get('selected_data_file') else None
        series = pd.read_json(data.get('series')) if data.get('series') is not None else None

        return cls(
            kind=data.get('kind', 'standard'),
            available_data_file_names=data.get('available_data_file_names'),
            selected_data_file_name=data.get('selected_data_file_name'),
            available_data_files=available_data_files,
            selected_data_file=selected_data_file,
            wtp_to_molar_checked=data.get('wtp_to_molar_checked', False),
            tab_name=data.get('tab_name'),
            legend_name=data.get('legend_name'),
            point_size=data.get('point_size', 6),
            available_point_shapes=data.get('available_point_shapes'),
            selected_point_shape=data.get('selected_point_shape', 'circle'),
            color=data.get('color'),
            add_heatmap_checked=data.get('add_heatmap_checked', False),
            add_sizemap_checked=data.get('add_sizemap_checked', False),
            filter_data_checked=data.get('filter_data_checked', False),
            advanced_settings_checked=data.get('advanced_settings_checked', False),
            heatmap_model=HeatmapModel.from_json(data.get('heatmap_model', {})),
            sizemap_model=SizemapModel.from_json(data.get('sizemap_model', {})),
            filter_tab_model=FilterTabsPanelModel.from_json(data.get('filter_tab_model', {})),
            series=series,
            line_thickness=data.get('line_thickness', 2.0),
            line_style=data.get('line_style', 'solid'),
            selected_contour_mode=data.get('selected_contour_mode', '1 sigma'),
            contour_level=data.get('contour_level', 68.0),
            error_entry_model=BootstrapErrorEntryModel.from_json(data.get('error_entry_model', {}))
        )

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
    def available_data_files(self) -> Optional[List['DataFile']]:
        return self._available_data_files

    @available_data_files.setter
    def available_data_files(self, value: Optional[List['DataFile']]):
        self._available_data_files = value

    @property
    def selected_data_file(self) -> Optional['DataFile']:
        return self._selected_data_file

    @selected_data_file.setter
    def selected_data_file(self, value: Optional['DataFile']):
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
    def add_sizemap_checked(self) -> bool:
        return self._add_sizemap_checked

    @add_sizemap_checked.setter
    def add_sizemap_checked(self, value: bool):
        self._add_sizemap_checked = value

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
