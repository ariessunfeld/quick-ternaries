
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QLabel, 
    QCheckBox
)

class LeftLabeledCheckbox(QWidget):
    """A labeled CheckBox megawidget, for check boxes with QLabels to their left"""

    def __init__(self, label:str='', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.checkbox = QCheckBox()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)
        self.setLayout(self.layout)

    def isChecked(self):
        return self.checkbox.isChecked()