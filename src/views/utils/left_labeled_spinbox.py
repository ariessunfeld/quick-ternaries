from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QSizePolicy
)

from PySide6.QtCore import Signal

class LeftLabeledSpinBox(QWidget):
    """A labeled SpinBox megawidget, for spin boxes with QLabels to their left"""

    valueChanged = Signal(int)

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.spinbox = QSpinBox()

        # Set size policies
        #self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        #self.spinbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Mimimum)

        # Ensure consistent padding
        # self.layout.setContentsMargins(10, 5, 10, 5)
        # self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.spinbox)
        self.setLayout(self.layout)

        # Connect valueChanged signal
        self.spinbox.valueChanged.connect(self.valueChanged)

    def value(self):
        return self.spinbox.value()

    def setValue(self, value: int):
        self.spinbox.setValue(value)
