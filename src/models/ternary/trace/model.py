"""Contains the model for the Trace"""

from typing import List, Optional
from src.models.utils.data_models import DataFile
from src.models.ternary.trace.heatmap_model import HeatmapModel
from src.models.ternary.trace.filter.model import FilterModel

class TraceModel:

    def __init__(
            self, 
            available_data_files: Optional[List[DataFile]] = None,
            selected_data_file: Optional[DataFile] = None,
            wtp_to_molar_checked: bool = True,
            tab_name: Optional[str] = None,
            legend_name: Optional[str] = None,
            point_size: int = 6,
            available_point_shapes: Optional[List[str]] = None,
            selected_point_shape: str = 'circle',
            color: Optional[str] = None,
            add_heatmap_checked: bool = False,
            filter_data_checked: bool = False,
            heatmap_model: Optional[HeatmapModel] = None,
            filter_model: Optional[FilterModel] = None):
        
        # Direct access
        self.heatmap_model = heatmap_model
        self.filter_model = filter_model

        # Controlled
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
