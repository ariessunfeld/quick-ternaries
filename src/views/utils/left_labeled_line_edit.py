
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QListWidget,
    QComboBox,
    QCheckBox
)

class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    def __init__(self, label:str = '', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.line_edit = QLineEdit()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

    def text(self):
        return self.line_edit.text()