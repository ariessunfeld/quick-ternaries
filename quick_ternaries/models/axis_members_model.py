from dataclasses import dataclass, field
from PySide6.QtWidgets import QComboBox
from quick_ternaries.views.widgets import MultiFieldSelector

@dataclass
class AxisMembersModel:
    x_axis: list = field(
        default_factory=list,
        metadata={
            "label": "X Axis:",
            "widget": MultiFieldSelector,
            "plot_types": ["cartesian", "histogram"],
        },
    )
    y_axis: list = field(
        default_factory=list,
        metadata={
            "label": "Y Axis:",
            "widget": MultiFieldSelector,
            "plot_types": ["cartesian"],
        },
    )
    top_axis: list = field(
        default_factory=list,
        metadata={
            "label": "Top Apex:",
            "widget": MultiFieldSelector,
            "plot_types": ["ternary"],
        },
    )
    left_axis: list = field(
        default_factory=list,
        metadata={
            "label": "Left Apex:",
            "widget": MultiFieldSelector,
            "plot_types": ["ternary"],
        },
    )
    right_axis: list = field(
        default_factory=list,
        metadata={
            "label": "Right Apex:",
            "widget": MultiFieldSelector,
            "plot_types": ["ternary"],
        },
    )
    categorical_column: str = field(
        default_factory=str,
        metadata={
            "label": "Categorical Column:",
            "widget": QComboBox,
            "plot_types": ["zmap"],
        }
    )
    numerical_columns: list = field(
        default_factory=list,
        metadata={
            "label": "Numerical Columns:",
            "widget": MultiFieldSelector,
            "plot_types": ["zmap"]
        }
    )
    hover_data: list = field(
        default_factory=list,
        metadata={
            "label": "Hover Data:",
            "widget": MultiFieldSelector,
            "plot_types": ["ternary", "cartesian", "histogram", "zmap"],
        },
    )
