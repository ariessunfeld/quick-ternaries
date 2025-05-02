from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QCheckBox, 
    QSpinBox,
    QComboBox,
    QDoubleSpinBox,
    QFontComboBox
)

from quick_ternaries.views.widgets import (
    ColorScaleDropdown, 
    ColorButton
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
            "widget": ComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
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
            "widget": QFontComboBox,
            "plot_types": ["cartesian", "histogram", "ternary"],
        },
    )
