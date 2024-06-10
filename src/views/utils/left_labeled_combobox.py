from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, QSizePolicy
)

class LeftLabeledComboBox(QWidget):
    """A labeled ComboBox megawidget, for combo boxes with QLabels to their left"""
    
    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        
        self.label = QLabel(label)
        self.combobox = QComboBox()
        
        # Set size policies
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.combobox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        # Ensure consistent padding
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)
        self.setLayout(self.layout)
        
    def addItems(self, items: list[str]):
        self.combobox.addItems(items)
        
    def currentText(self):
        return self.combobox.currentText()
    
    def setCurrentText(self, text: str):
        index = self.combobox.findText(text)
        if index >= 0:
            self.combobox.setCurrentIndex(index)
