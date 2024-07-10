from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QComboBox,
    QLabel,
    QSlider,
)

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from src.views.utils import (
    LeftLabeledSpinBox,
    LeftLabeledColorPicker,
    LeftLabeledComboBox,
    LeftLabeledFontComboBox,
    LeftLabeledSlider
)

class AdvancedSettingsView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()

        # create a container widget to hold the main layout
        self.container_widget = QWidget()
        self.container_widget.setObjectName("containerWidget") # set an object name
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)

        # add a border to the container widget
        self.container_widget.setStyleSheet("#containerWidget { border: 1px solid #1c1c1c; }")

        self.setLayout(self.main_layout)

        # background color (behind the figure)
        self.background_color = LeftLabeledColorPicker("Background Color:")

        # ternary sum
        self.ternary_sum_combo = LeftLabeledComboBox("Ternary Sum:")
        self.ternary_sum_combo.addItems(["1", "100"])

        # gridline step size
        self.gridline_step_size = LeftLabeledSpinBox("Gridline Step Size:")
        self.gridline_step_size.setMinimum(1)
        self.gridline_step_size.setMaximum(100)

        # gridline color
        self.gridline_color = LeftLabeledColorPicker("Gridline Color:")

        # paper color (background behind/outside ternary)
        self.paper_color = LeftLabeledColorPicker("Paper Color:")
        self.container_layout.addWidget(self.paper_color)

        # title font and size
        self.title_font_combo = LeftLabeledFontComboBox("Title Font:")
        self.title_font_combo.setCurrentFont(QFont("Arial"))
        self.title_font_size_spinbox = LeftLabeledSpinBox("Title Font Size:")
        self.title_font_size_spinbox.setMinimum(1)
        self.title_font_size_spinbox.setMaximum(100)

        # axis label font and size
        self.axis_font_combo = LeftLabeledFontComboBox("Axis Label Font:")
        self.axis_font_combo.setCurrentFont(QFont("Arial"))
        self.axis_font_size_spinbox = LeftLabeledSpinBox("Axis Label Font Size:")
        self.axis_font_size_spinbox.setMinimum(1)
        self.axis_font_size_spinbox.setMaximum(100)

        # add widgets to their respective layout
        self.main_layout.addWidget(self.container_widget)
        self.container_layout.addWidget(self.background_color)
        self.container_layout.addWidget(self.ternary_sum_combo)
        self.container_layout.addWidget(self.gridline_step_size)
        self.container_layout.addWidget(self.gridline_color)
        self.container_layout.addWidget(self.title_font_combo)
        self.container_layout.addWidget(self.title_font_size_spinbox)
        self.container_layout.addWidget(self.axis_font_combo)
        self.container_layout.addWidget(self.axis_font_size_spinbox)
