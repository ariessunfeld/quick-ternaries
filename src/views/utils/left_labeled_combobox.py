from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox, 
    QSizePolicy
)

from PySide6.QtCore import Signal

class LeftLabeledComboBox(QWidget):
    """A labeled ComboBox megawidget, for combo boxes with QLabels to their left"""
    
    valueChanged = Signal(str)

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.combobox = QComboBox()

        # # Set size policies
        # self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        # self.combobox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        # # Ensure consistent padding
        # self.layout.setContentsMargins(10, 5, 10, 5)
        # self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)
        self.setLayout(self.layout)

        # Connect internal QComboBox signal to the new signal
        self.combobox.currentIndexChanged.connect(self.emit_value_changed)

    def addItems(self, items: list[str]):
        if items is not None:
            self.combobox.blockSignals(True)
            self.combobox.addItems(items)
            self.combobox.blockSignals(False)

    def currentText(self):
        return self.combobox.currentText()

    def setCurrentText(self, text: str):
        index = self.combobox.findText(text)
        if index >= 0:
            self.combobox.setCurrentIndex(index)

    def clear(self):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.blockSignals(False)

    def emit_value_changed(self, index):
        text = self.combobox.itemText(index)
        self.valueChanged.emit(text)
