from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QCheckBox, 
    QSpinBox,
    QDoubleSpinBox, 
    QLineEdit
)

from src3.views.widgets import (
    ColorScaleDropdown, 
    ColorButton
)


@dataclass
class AdvancedPlotSettingsModel:
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
            "widget": QLineEdit,
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
            "widget": QLineEdit,
            "plot_types": ["cartesian", "histogram", "ternary"],
        },
    )
