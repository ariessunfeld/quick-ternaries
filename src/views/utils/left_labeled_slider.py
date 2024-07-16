from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QSlider
)
from PySide6.QtCore import Signal, Qt

class LeftLabeledSlider(QWidget):
    """A labeled slider megawidget, for sliders with QLabels to their left"""

    valueChanged = Signal(int)

    def __init__(self, label: str = '', orientation: Qt.Horizontal|Qt.Vertical=Qt.Horizontal, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QHBoxLayout()
        self.slider_layout = QVBoxLayout()

        self.label = QLabel(label)
        self.slider = QSlider(orientation)

        self.main_layout.addWidget(self.label)
        self.slider_layout.addWidget(self.slider)
        self.main_layout.addLayout(self.slider_layout)
        self.setLayout(self.main_layout)

        # Connect internal QSlider signal to the new signal
        self.slider.valueChanged.connect(self.emit_value_changed)
        self.slider.valueChanged.connect(self.update_tooltip)

    def value(self):
        return self.slider.value()
    
    def setValue(self, value: int, block: bool = True):
        if block:
            self.slider.blockSignals(True)
            self.slider.setValue(value)
            self.slider.blockSignals(False)
        else:
            self.slider.setValue(value)

    @property
    def minimum(self):
        return self.slider.minimum()
    
    def setMinimum(self, value: int):
        self.slider.setMinimum(value)

    @property
    def maximum(self):
        return self.slider.maximum()
    
    def setMaximum(self, value: int):
        self.slider.setMaximum(value)

    def setRange(self, min_val: int, max_val: int):
        self.slider.setRange(min_val, max_val)

    def emit_value_changed(self, value):
        self.valueChanged.emit(value)

    def setTickPosition(self, pos: QSlider.TickPosition):
        self.slider.setTickPosition(pos)

    def setTickInterval(self, interval: int):
        self.slider.setTickInterval(interval)

    def update_tooltip(self, value):
        self.slider.setToolTip(str(value))
