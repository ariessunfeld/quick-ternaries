
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
    QSizePolicy,
    QSpacerItem
)

from PySide6.QtCore import Signal

class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    textChanged = Signal(str)

    def __init__(self, label:str = '', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.line_edit = QLineEdit()

        # Set size policies
        # self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        # self.line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        
        # Ensure consistent padding
        #self.layout.setContentsMargins(10, 5, 10, 5)
        #self.layout.setSpacing(10)

        self.layout.addWidget(self.label)
        #self.layout.addItem(QSpacerItem(1, 1))
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

        # Connect signals
        self.line_edit.textChanged.connect(self._emit_text_changed)

    def text(self):
        return self.line_edit.text()
    
    def setText(self, value: str):
        self.line_edit.setText(value)

    def _emit_text_changed(self, value: str):
        self.textChanged.emit(value)

    def clear(self):
        self.line_edit.clear()
