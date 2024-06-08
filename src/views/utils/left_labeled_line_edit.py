
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QListWidget,
    QComboBox,
    QCheckBox,
    QSizePolicy
)

class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    def __init__(self, label:str = '', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.line_edit = QLineEdit()

        # Set size policies
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        # Ensure consistent padding
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

    def text(self):
        return self.line_edit.text()