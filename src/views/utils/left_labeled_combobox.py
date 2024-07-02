from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QSizePolicy
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
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)
        self.setLayout(self.layout)

        # Connect internal QComboBox signal to the new signal
        self.combobox.currentIndexChanged.connect(self.emit_value_changed)
        #self.combobox.currentTextChanged.connect(self.emit_value_changed)
        
    def addItems(self, items: list[str]):
        if items is not None:
            self.combobox.blockSignals(True)
            self.combobox.addItems(items)
            self.combobox.blockSignals(False)
        
    def currentText(self):
        return self.combobox.currentText()
    
    def setCurrentText(self, text: str, block: bool=True):
        index = self.combobox.findText(text)
        if index >= 0:
            if block:
                self.combobox.blockSignals(True)
                self.combobox.setCurrentIndex(index)
                self.combobox.blockSignals(False)
            else:
                self.combobox.setCurrentIndex(index)
        else:
            self.combobox.setCurrentIndex(0)

    def clear(self):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.blockSignals(False)

    def emit_value_changed(self, index):
        text = self.combobox.itemText(index)
        self.valueChanged.emit(text)
