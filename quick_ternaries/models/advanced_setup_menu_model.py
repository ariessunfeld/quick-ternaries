from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QCheckBox, 
    QSpinBox,
    QComboBox,
    QDoubleSpinBox, 
    QLineEdit
)

from quick_ternaries.views.widgets import (
    ColorScaleDropdown, 
    ColorButton
)
from quick_ternaries.utils.legend_layout import (
    LEGEND_COORDINATE_REFERENCE_OPTIONS,
    LEGEND_ORIENTATION_OPTIONS,
    LEGEND_POSITION_OPTIONS,
    LEGEND_X_ANCHOR_OPTIONS,
    LEGEND_Y_ANCHOR_OPTIONS,
)


@dataclass
class AdvancedPlotSettingsModel:
    aspect_ratio: str = field(
        default="Automatic",
        metadata={
            "label": "Aspect Ratio:",
            "widget": QComboBox,
            "plot_types": ["cartesian"],
        },
    )
    x_axis_custom_range_on: bool = field(
        default=False,
        metadata={
            "label": "Custom X-Axis Limits:",
            "widget": QCheckBox,
            "plot_types": ["cartesian"],
        },
    )
    x_axis_min: float = field(
        default=0.0,
        metadata={
            "label": "X-Axis Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian"],
            "depends_on": "x_axis_custom_range_on",
        },
    )
    x_axis_max: float = field(
        default=1.0,
        metadata={
            "label": "X-Axis Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian"],
            "depends_on": "x_axis_custom_range_on",
        },
    )
    y_axis_custom_range_on: bool = field(
        default=False,
        metadata={
            "label": "Custom Y-Axis Limits:",
            "widget": QCheckBox,
            "plot_types": ["cartesian"],
        },
    )
    y_axis_min: float = field(
        default=0.0,
        metadata={
            "label": "Y-Axis Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian"],
            "depends_on": "y_axis_custom_range_on",
        },
    )
    y_axis_max: float = field(
        default=1.0,
        metadata={
            "label": "Y-Axis Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian"],
            "depends_on": "y_axis_custom_range_on",
        },
    )
    zmap_colorscale: str = field(
        default="RdBu",
        metadata={
            "label": "Colorscale:",
            "widget": ColorScaleDropdown,
            "plot_types": ["zmap"],
        },
    )
    zmap_reverse_colorscale: bool = field(
        default=True,
        metadata={
            "label": "Reverse colorscale:",
            "widget": QCheckBox,
            "plot_types": ["zmap"],
        },
    )
    background_color: str = field(
        default="#e3ecf7",
        metadata={
            "label": "Background Color:",
            "widget": ColorButton,
            "plot_types": ["cartesian", "histogram", "ternary", "zmap"],
        },
    )
    paper_color: str = field(
        default="#ffffff",
        metadata={
            "label": "Paper Color:",
            "widget": ColorButton,
            "plot_types": ["cartesian", "histogram", "ternary", "zmap"],
        },
    )
    grid_color: str = field(
        default="#ffffff",
        metadata={
            "label": "Grid Color:",
            "widget": ColorButton,
            "plot_types": ["cartesian", "ternary", "zmap"],
        },
    )
    font_color: str = field(
        default="#000000",
        metadata={
            "label": "Font Color:",
            "widget": ColorButton,
            "plot_types": ["cartesian", "histogram", "ternary", "zmap"],
        },
    )
    gridline_step_size: int = field(
        default=20,
        metadata={
            "label": "Grid Step Size:",
            "widget": QSpinBox,
            "plot_types": ["ternary"],
        },
    )
    show_tick_marks: bool = field(
        default=True,
        metadata={
            "label": "Show Tick Marks:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    legend_position: str = field(
        default="top-right",
        metadata={
            "label": "Legend Position:",
            "widget": QComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "options": LEGEND_POSITION_OPTIONS,
        },
    )
    legend_x: float = field(
        default=1.0,
        metadata={
            "label": "Legend X Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "depends_on": ("legend_position", "custom"),
            "minimum": -2.0,
            "maximum": 3.0,
            "single_step": 0.05,
            "decimals": 3,
        },
    )
    legend_y: float = field(
        default=1.0,
        metadata={
            "label": "Legend Y Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "depends_on": ("legend_position", "custom"),
            "minimum": -2.0,
            "maximum": 3.0,
            "single_step": 0.05,
            "decimals": 3,
        },
    )
    legend_coordinate_reference: str = field(
        default="paper",
        metadata={
            "label": "Legend Coordinate Reference:",
            "widget": QComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "depends_on": ("legend_position", "custom"),
            "options": LEGEND_COORDINATE_REFERENCE_OPTIONS,
        },
    )
    legend_xanchor: str = field(
        default="right",
        metadata={
            "label": "Legend X Anchor:",
            "widget": QComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "depends_on": ("legend_position", "custom"),
            "options": LEGEND_X_ANCHOR_OPTIONS,
        },
    )
    legend_yanchor: str = field(
        default="top",
        metadata={
            "label": "Legend Y Anchor:",
            "widget": QComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "depends_on": ("legend_position", "custom"),
            "options": LEGEND_Y_ANCHOR_OPTIONS,
        },
    )
    legend_orientation: str = field(
        default="vertical",
        metadata={
            "label": "Legend Orientation:",
            "widget": QComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
            "options": LEGEND_ORIENTATION_OPTIONS,
        },
    )
    font_size: int = field(
        default=12,
        metadata={
            "label": "Font Size:",
            "widget": QDoubleSpinBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
        },
    )
    font: str = field(
        default="Arial",
        metadata={
            "label": "Font:",
            "widget": QLineEdit,
            "plot_types": ["cartesian", "histogram", "ternary"],
        },
    )
