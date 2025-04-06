from dataclasses import dataclass, field, asdict
from typing import Dict, List
import pandas as pd
import numpy as np
from PySide6.QtWidgets import (
    QLineEdit, 
    QComboBox, 
    QDoubleSpinBox, 
    QSpinBox, 
    QCheckBox
)
from src3.views.widgets import (
    ColorButton, 
    ShapeButtonWithMenu, 
    ColorScaleDropdown
)
from src3.models.data_file_metadata_model import DataFileMetadata
from src3.models.filter_model import FilterModel
from src3.models.error_entry_model import ErrorEntryModel


@dataclass
class TraceEditorModel:
    trace_name: str = field(
        default="Default Trace",
        metadata={
            "label": "Trace Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary", "cartesian", "histogram", "zmap"],
        },
    )
    datafile: DataFileMetadata = field(
        default_factory=lambda: DataFileMetadata(file_path=""),
        metadata={
            "label": "Datafile:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian", "histogram", "zmap"],
        },
    )
    is_contour: bool = field(
        default=False,
        metadata={
            "label": None,
            "widget": None,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    trace_color: str = field(
        default="blue",
        metadata={
            "label": "Point Color:",
            "widget": ColorButton,
            "plot_types": ["ternary", "cartesian", "histogram"],
        },
    )
    outline_color: str = field(
        default='#000000',
        metadata={
            "label": "Outline Color:",
            "widget": ColorButton,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    point_shape: str = field(
        default="circle",
        metadata={
            "label": "Point Shape:",
            "widget": ShapeButtonWithMenu,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    point_size: float = field(
        default=6.0,
        metadata={
            "label": "Point Size:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    outline_thickness: int = field(
        default=1,
        metadata={
            "label": "Outline Thickness:",
            "widget": QSpinBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    convert_from_wt_to_molar: bool = field(
        default=False,
        metadata={
            "label": "Convert from wt% to molar:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    hide_on: bool = field(
        default=False,
        metadata={
            "label": "Hide (do not plot):",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    line_on: bool = field(
        default=False,
        metadata={
            "label": "Line On:",
            "widget": QCheckBox,
            "plot_types": ["cartesian"],
        },
    )
    line_style: str = field(
        default="solid",
        metadata={
            "label": "Line Style:",
            "widget": QComboBox,
            "plot_types": ["cartesian"],
        },
    )
    line_thickness: float = field(
        default=1.0,
        metadata={
            "label": "Line Thickness:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian"],
        },
    )
    heatmap_on: bool = field(
        default=False,
        metadata={
            "label": "Heatmap On:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    # New field: advanced toggle inside heatmap group.
    heatmap_use_advanced: bool = field(
        default=False,
        metadata={
            "label": "Show advanced settings:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "group": "heatmap",
            "depends_on": "heatmap_on",
        },
    )
    # Basic heatmap settings (always visible when heatmap is on)
    heatmap_column: str = field(
        default="",
        metadata={
            "label": "Heatmap Column:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap",
        },
    )
    heatmap_min: float = field(
        default=0.0,
        metadata={
            "label": "Heatmap Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap",
        },
    )
    heatmap_max: float = field(
        default=1.0,
        metadata={
            "label": "Heatmap Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap",
        },
    )
    # Advanced options – marked with "advanced": True and depend on both heatmap_on and heatmap_use_advanced.
    heatmap_colorscale: str = field(
        default="Inferno",
        metadata={
            "label": "Heatmap Colorscale:",
            "widget": ColorScaleDropdown,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True,
        },
    )
    heatmap_reverse_colorscale: bool = field(
        default=True,
        metadata={
            "label": "Reverse colorscale:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True,
        },
    )
    heatmap_log_transform: bool = field(
        default=False,
        metadata={
            "label": "Log-transform:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True,
        },
    )
    heatmap_sort_mode: str = field(
        default="no change",
        metadata={
            "label": "Heatmap Sort Mode:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True,
        },
    )
    # Advanced heatmap colorbar position & dimensions fields
    heatmap_bar_orientation: str = field(
        default="vertical",
        metadata={
            "label": "Bar orientation:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position && Dimensions",
            "advanced": True,
        },
    )
    heatmap_colorbar_x: float = field(
        default=1.1,
        metadata={
            "label": "X Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position && Dimensions",
            "advanced": True,
        },
    )
    heatmap_colorbar_y: float = field(
        default=0.5,
        metadata={
            "label": "Y Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True,
        },
    )
    heatmap_colorbar_len: float = field(
        default=0.6,
        metadata={
            "label": "Length:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True,
        },
    )
    heatmap_colorbar_thickness: float = field(
        default=18.0,
        metadata={
            "label": "Thickness:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True,
        },
    )
    sizemap_on: bool = field(
        default=False,
        metadata={
            "label": "Sizemap On:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    sizemap_column: str = field(
        default="",
        metadata={
            "label": "Sizemap Column:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap",
        },
    )
    sizemap_sort_mode: str = field(
        default="no change",
        metadata={
            "label": "Sizemap Sort Mode:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap",
        },
    )
    sizemap_min: float = field(
        default=2.0,
        metadata={
            "label": "Sizemap Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap",
        },
    )
    sizemap_max: float = field(
        default=6.0,
        metadata={
            "label": "Sizemap Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap",
        },
    )
    filters_on: bool = field(
        default=False,
        metadata={
            "label": "Filters On:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian", "histogram", "zmap"],
        },
    )
    filters: list = field(
        default_factory=list,
        metadata={
            "label": "Filters:",
            "widget": None,
            "plot_types": ["ternary", "cartesian", "histogram", "zmap"],
        },
    )
    # Contour confidence level - updated to use self-describing options
    contour_level: str = field(
        default="Contour: 1-sigma",
        metadata={
            "label": "",  # No separate label needed
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "is_contour",
        },
    )
    # Custom percentile (only visible when contour_level is "Contour: Custom percentile")
    contour_percentile: float = field(
        default=95.0,
        metadata={
            "label": "Percentile:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": [
                "is_contour",
                ("contour_level", "Contour: Custom percentile"),
            ],
        },
    )

    # New fields for contour source data
    source_point_data: Dict = field(
        default_factory=dict,
        metadata={
            "label": None,
            "widget": None,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    
    # Error entry model for component uncertainties
    error_entry_model: ErrorEntryModel = field(
        default_factory=ErrorEntryModel,
        metadata={
            "label": None,
            "widget": None,
            "plot_types": ["ternary", "cartesian"],
        },
    )
    density_contour_on: bool = field(
        default=False,
        metadata={
            "label": "Density Contour On:",
            "widget": QCheckBox,
            "plot_types": ["ternary"],
        },
    )
    density_contour_color: str = field(
        default="#000000",
        metadata={
            "label": "Contour Color:",
            "widget": ColorButton,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )
    density_contour_thickness: int = field(
        default=2,
        metadata={
            "label": "Contour Thickness:",
            "widget": QSpinBox,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )
    density_contour_percentile: float = field(
        default=68.27,
        metadata={
            "label": "Percentile:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )
    density_contour_name: str = field(
        default="",
        metadata={
            "label": "Legend Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )
    density_contour_multiple: bool = field(
        default=False,
        metadata={
            "label": "Multiple Contours:",
            "widget": QCheckBox,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )
    density_contour_percentiles: str = field(
        default="60,70,80",
        metadata={
            "label": "Percentiles (comma-separated):",
            "widget": QLineEdit,
            "plot_types": ["ternary"],
            "depends_on": ["density_contour_on", "density_contour_multiple"],
            "group": "density_contour",
        },
    )
    density_contour_line_style: str = field(
        default="solid",
        metadata={
            "label": "Line Style:",
            "widget": QComboBox,
            "plot_types": ["ternary"],
            "depends_on": "density_contour_on",
            "group": "density_contour",
        },
    )

    def to_dict(self):
        ret = asdict(self)
        # Convert source point series if necessary.
        series = ret['source_point_data'].get('series', {})
        if series and isinstance(series, pd.Series):
            ret['source_point_data']['series'] = series.to_json()
        
        # This replaces the ErrorEntryModel object with its dictionary representation
        ret['error_entry_model'] = self.error_entry_model.to_dict()
        
        return ret

    @classmethod
    def from_dict(cls, d: dict):
        """Create a model from a dictionary, with improved datafile handling."""
        # Create a copy to avoid modifying the input
        d_copy = d.copy()

        # Handle filters with proper deserialization
        if "filters" in d_copy and isinstance(d_copy["filters"], list):
            d_copy["filters"] = [
                FilterModel.from_dict(item) if isinstance(item, dict) else item
                for item in d_copy["filters"]
            ]

        # Handle datafile conversion with improved robustness
        datafile_value = d_copy.get("datafile", None)
        if isinstance(datafile_value, dict):
            d_copy["datafile"] = DataFileMetadata.from_dict(datafile_value)
        elif isinstance(datafile_value, str):
            try:
                d_copy["datafile"] = DataFileMetadata.from_display_string(datafile_value)
            except Exception:
                d_copy["datafile"] = DataFileMetadata(file_path=datafile_value)
        elif datafile_value is None:
            d_copy["datafile"] = DataFileMetadata(file_path="")

        # Handle source_point_data
        if 'source_point_data' in d_copy and isinstance(d_copy['source_point_data'], dict):
            if 'series' in d_copy['source_point_data'] and isinstance(d_copy['source_point_data']['series'], str):
                try:
                    d_copy['source_point_data']['series'] = pd.read_json(
                        d_copy['source_point_data']['series'], typ='series')
                except Exception as e:
                    print(f"Error parsing series data: {e}")
                    d_copy['source_point_data']['series'] = pd.Series()
                    
        # Handle error_entry_model
        if 'error_entry_model' in d_copy and isinstance(d_copy['error_entry_model'], dict):
            d_copy['error_entry_model'] = ErrorEntryModel.from_dict(d_copy['error_entry_model'])

        return cls(**d_copy)

    @classmethod
    def _convert_filter(cls, d: dict):
        # If the operation is multi-field and filter_value1 is a non-empty string,
        # split it into a list.
        op = d.get("filter_operation", "")
        if op in ["is one of", "is not one of"]:
            val = d.get("filter_value1", "")
            if isinstance(val, str) and val:
                d["filter_value1"] = [x.strip() for x in val.split(",")]
        return d
    
    def set_source_point(self, series: pd.Series, metadata: Dict = None):
        """
        Set the source point data for a contour trace.
        
        Args:
            series: The pandas Series containing the point data
            metadata: Optional additional metadata about the source point
        """
        if metadata is None:
            metadata = {}
            
        self.source_point_data = {
            "series": series,
            **metadata
        }
        
        # Initialize error entries for all columns in the series
        for col in series.index:
            if col not in self.error_entry_model.entries:
                # Default to using the RMSEP column if available
                err_col = f'{col} RMSEP'
                if (
                    err_col in series.index 
                    and isinstance(series[err_col], (int, float, np.number)) 
                    and not pd.isna(series[err_col])
                ):
                    default_error = series[err_col]
                    self.error_entry_model.set_error(col, default_error)
