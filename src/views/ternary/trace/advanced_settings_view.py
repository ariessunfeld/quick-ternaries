"""Megawidget for advanced settings in the trace editor"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout
)

from src.views.utils import (
    LeftLabeledSpinBox,
    LeftLabeledColorPicker
)

class AdvancedSettingsView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()

        # Create a container widget to hold the main layout
        self.container_widget = QWidget()
        self.container_widget.setObjectName("containerWidget")  # Set an object name
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)

        # add a border to the container widget
        self.container_widget.setStyleSheet("#containerWidget { border: 1px solid #1c1c1c; }")

        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.container_widget)

        # point opacity
        self.opacity = LeftLabeledSpinBox('Opacity:')
        self.opacity.setMaximum(100)
        self.opacity.setValue(100)
        self.container_layout.addWidget(self.opacity)

        # point outline color
        self.outline_color = LeftLabeledColorPicker('Outline Color:')
        self.container_layout.addWidget(self.outline_color)

        # point outline thickness
        self.outline_thickness = LeftLabeledSpinBox('Outline Thickness:')
        self.container_layout.addWidget(self.outline_thickness)
