from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QColorDialog,
    QSizePolicy
)

from PySide6.QtCore import Signal, Qt

class LeftLabeledColorPicker(QWidget):
    """A labeled ColorPicker megawidget, for color pickers with QLabels to their left"""

    colorChanged = Signal(str)

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.color_button = QPushButton('Select Color')
        self.color_button.setCursor(Qt.PointingHandCursor)

        # Set size policies
        # self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # self.color_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        # # Ensure consistent padding
        # self.layout.setContentsMargins(10, 5, 10, 5)
        # self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.color_button)
        self.setLayout(self.layout)

        self.color_button.clicked.connect(self.open_color_dialog)

    def open_color_dialog(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_button.setStyleSheet(f'background-color: {color.name()}')
            self.color_button.setText(color.name())
            self._color = color.name()
            self.colorChanged.emit(color.name()) # emit signal only when updated by user

    def color(self):
        return self._color

    def setColor(self, color: str):
        self.color_button.setStyleSheet(f'background-color: {color}')
        self.color_button.setText(color if color is not None else 'Select Color')
        self._color = color
