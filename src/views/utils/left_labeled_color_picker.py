import re
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QColorDialog
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

class LeftLabeledColorPicker(QWidget):
    """A labeled ColorPicker megawidget, for color pickers with QLabels to their left"""

    colorChanged = Signal(str)  # will emit "rgba(...)" string

    def __init__(self, label: str = '', initial_color: str | QColor = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)

        self.label = QLabel(label)
        self.color_button = QPushButton('Select Color')
        self.color_button.setCursor(Qt.PointingHandCursor)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.color_button)
        self.color_button.clicked.connect(self.open_color_dialog)
        self._color = self._parse_color(initial_color) if initial_color else None
        self.updateButtonStyle()

    def open_color_dialog(self):
        initial_color = self._color or QColor(255, 255, 255)
        color = QColorDialog.getColor(initial=initial_color, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.setColor(color)

    def color(self):
        return self.rgba_str()
        
    def _parse_color(self, color: str | QColor) -> QColor:
        if isinstance(color, QColor):
            return color
        if isinstance(color, str):
            rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
            rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color)
            if rgb_match:
                return QColor(*map(int, rgb_match.groups()))
            elif rgba_match:
                r, g, b, a = rgba_match.groups()
                qcolor = QColor(int(r), int(g), int(b))
                qcolor.setAlphaF(float(a))
                return qcolor
        return QColor(color)

    def setColor(self, color: str | QColor | None):
        """Set this widget's color value."""
        if color:
            new_color = self._parse_color(color)
            if new_color != self._color:
                self._color = new_color
                self.updateButtonStyle()
                self.colorChanged.emit(self.rgba_str())
        else:
            self._color = None
            self.updateButtonStyle()

    def updateButtonStyle(self):
        self.color_button.setStyleSheet(f'background-color: {self.rgba_str()}')
        self.color_button.setText(self._color.name() if self._color else 'Select Color')

    def rgba_str(self) -> str | None:
        if self._color:
            return f"rgba({self._color.red()}, {self._color.green()}, {self._color.blue()}, {self._color.alphaF():.2f})"
        return None

    @property
    def alpha(self) -> float:
        return self._color.alphaF() if self._color else 1.0

    @alpha.setter
    def alpha(self, value: float):
        if self._color:
            self._color.setAlphaF(max(0.0, min(1.0, value)))
            self.updateButtonStyle()
            self.colorChanged.emit(self.rgba_str())
