from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QSizePolicy
)

from PySide6.QtCore import Signal

class CustomSpinBox(QDoubleSpinBox):
    def __init__(self, step_size, parent=None):
        super().__init__(parent)
        self.setSingleStep(step_size)
        self.setDecimals(1)
        self.step_size = step_size

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        steps = delta / 120
        current_value = self.value()
        self.setValue(current_value + steps * self.step_size)

class LeftLabeledSpinBox(QWidget):
    """A labeled SpinBox megawidget, for spin boxes with QLabels to their left"""

    valueChanged = Signal(float)

    def __init__(self, label: str = '', step_size: int|float = 1, parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)

        if step_size == 1:
            self.spinbox = QSpinBox()
        else:
            self.spinbox = CustomSpinBox(step_size)

        # Set size policies
        # self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # self.spinbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        # Ensure consistent padding
        # self.layout.setContentsMargins(10, 5, 10, 5)
        # self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinbox)
        self.setLayout(self.layout)

        # Connect valueChanged signal
        self.spinbox.valueChanged.connect(self.valueChanged.emit)

    def value(self):
        return self.spinbox.value()

    def setValue(self, value: int|float):
        self.spinbox.setValue(value)

    def setMaximum(self, value: int|float):
        self.spinbox.setMaximum(value)

    def setMinimum(self, value: int|float):
        self.spinbox.setMinimum(value)
