from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSlider
)
from PySide6.QtCore import Signal, Qt

class LeftLabeledSlider(QWidget):
    """A labeled slider megawidget, for sliders with QLabels to their left"""

    valueChanged = Signal(int)

    def __init__(self, label: str = '', orientation: Qt.Horizontal|Qt.Vertical=Qt.Horizontal, parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.slider = QSlider(orientation)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.slider)
        self.setLayout(self.layout)

        # Connect internal QSlider signal to the new signal
        self.slider.valueChanged.connect(self.emit_value_changed)

    def value(self):
        return self.slider.value()
    
    def setValue(self, value: int, block: bool = True):
        if block:
            self.slider.blockSignals(True)
            self.slider.setValue(value)
            self.slider.blockSignals(False)
        else:
            self.slider.setValue(value)

    def minimum(self):
        return self.slider.minimum()
    
    def setMinimum(self, value: int):
        self.slider.setMinimum(value)

    def maximum(self):
        return self.slider.maximum()
    
    def setMaximum(self, value: int):
        self.slider.setMaximum(value)

    def emit_value_changed(self, value):
        self.valueChanged.emit(value)
