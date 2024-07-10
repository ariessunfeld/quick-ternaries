import re

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QColorDialog, QSizePolicy
)

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor

class LeftLabeledColorPicker(QWidget):
    """A labeled ColorPicker megawidget, for color pickers with QLabels to their left"""

    colorChanged = Signal(str)  # Will emit "rgba(...)" string

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        
        self.label = QLabel(label)
        self.color_button = QPushButton('Select Color')
        self.color_button.setCursor(Qt.PointingHandCursor)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.color_button)
        self.setLayout(self.layout)
        
        self.color_button.clicked.connect(self.open_color_dialog)
        self._color = None
        self._alpha = 255

    def open_color_dialog(self):
        initial_color = self.getQColor()
        color = QColorDialog.getColor(initial=initial_color, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.setColor(color)

    def color(self):
        return self.rgba_str()

    def getQColor(self) -> QColor:
        if self._color is None:
            return QColor(255, 255, 255, self._alpha)
        return QColor(self._color)

    def setColor(self, color:str|QColor):
        """
        Set this widget's color value.

        Arguments:
            color: A QColor object, or a string representation of the color.
                Accepted string formats:
                - RGB: "rgb(r,g,b)" where r, g, b are integers 0-255
                - RGBA: "rgba(r,g,b,a)" where r, g, b are integers 0-255 and a is a float 0-1 or integer 0-255
                - Hex: "#RRGGBB" or "#RRGGBBAA"
                - Named colors: e.g., "red", "blue", etc.

        Raises:
            ValueError: If the color argument is not a valid QColor or recognized string format.

        Note:
            If a valid color is provided, this method will update the widget's color,
            refresh the button style, and emit the colorChanged signal.
        """
        if color:
            if isinstance(color, str):
                rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color)
                
                if rgb_match:
                    r, g, b = map(int, rgb_match.groups())
                    self._color = QColor(r, g, b)
                    self._alpha = 255
                elif rgba_match:
                    r, g, b, a = rgba_match.groups()
                    self._color = QColor(int(r), int(g), int(b))
                    self._alpha = int(float(a) * 255) if '.' in a else int(a)
                else:
                    self._color = QColor(color)
                    self._alpha = self._color.alpha()
            elif isinstance(color, QColor):
                self._color = color
                self._alpha = color.alpha()
            else:
                raise ValueError("Invalid color format")

            self._color.setAlpha(self._alpha)
            self.updateButtonStyle()
            self.colorChanged.emit(self.rgba_str())

    def updateButtonStyle(self):
        rgba_str = self.rgba_str()
        self.color_button.setStyleSheet(f'background-color: {rgba_str}')
        self.color_button.setText(self._color.name() if self._color else 'Select Color')

    def rgba_str(self):
        qcolor = self.getQColor()
        return f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {qcolor.alpha() / 255:.2f})"

    @property
    def alpha(self) -> int:
        return self._alpha

    @alpha.setter
    def alpha(self, value: int):
        self._alpha = max(0, min(255, value))
        if self._color:
            self._color.setAlpha(self._alpha)
        self.updateButtonStyle()
        self.colorChanged.emit(self.rgba_str())
