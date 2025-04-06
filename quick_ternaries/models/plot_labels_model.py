from dataclasses import dataclass, field
from PySide6.QtWidgets import QLineEdit


@dataclass
class PlotLabelsModel:
    title: str = field(
        default="",
        metadata={
            "label": "Title:",
            "widget": QLineEdit,
            "plot_types": ["cartesian", "histogram", "ternary"],
        },
    )
    x_axis_label: str = field(
        default="",
        metadata={
            "label": "X Axis Label:",
            "widget": QLineEdit,
            "plot_types": ["cartesian", "histogram"],
        },
    )
    y_axis_label: str = field(
        default="",
        metadata={
            "label": "Y Axis Label:",
            "widget": QLineEdit,
            "plot_types": ["cartesian", "histogram"],
        },
    )
    top_vertex_label: str = field(
        default="",
        metadata={
            "label": "Top Apex Display Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary"],
        },
    )
    left_vertex_label: str = field(
        default="",
        metadata={
            "label": "Left Apex Display Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary"],
        },
    )
    right_vertex_label: str = field(
        default="",
        metadata={
            "label": "Right Apex Display Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary"],
        },
    )
