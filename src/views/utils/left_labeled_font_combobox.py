from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QFontComboBox, 
    QSizePolicy
)

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

class LeftLabeledFontComboBox(QWidget):
    """A labeled font combo box megawidget, for font combo boxes with QLabels to their left"""

    valueChanged = Signal(str)

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.font_combobox = QFontComboBox()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.font_combobox)
        self.setLayout(self.layout)

        # Connect internal QComboBox signal to the new signal
        self.font_combobox.currentIndexChanged.connect(self.emit_value_changed)

    def currentText(self):
        return self.font_combobox.currentText()

    def setCurrentText(self, text: str, block: bool=True):
        index = self.font_combobox.findText(text)
        if index >= 0:
            if block:
                self.font_combobox.blockSignals(True)
                self.font_combobox.setCurrentIndex(index)
                self.font_combobox.blockSignals(False)
            else:
                self.font_combobox.setCurrentIndex(index)
        else:
            self.font_combobox.setCurrentIndex(0)

    def clear(self):
        self.font_combobox.blockSignals(True)
        self.font_combobox.clear()
        self.font_combobox.blockSignals(False)

    def emit_value_changed(self, index):
        text = self.font_combobox.itemText(index)
        self.valueChanged.emit(text)

    def setCurrentFont(self, font: QFont, block: bool = True):
        if block:
            self.font_combobox.blockSignals(True)
            self.font_combobox.setCurrentFont(font)
            self.font_combobox.blockSignals(False)
        else:
            self.font_combobox.setCurrentFont(font)
