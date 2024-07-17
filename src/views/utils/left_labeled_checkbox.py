
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QLabel, 
    QCheckBox
)

from PySide6.QtCore import Qt, Signal

class LeftLabeledCheckbox(QWidget):
    """A labeled CheckBox megawidget, for check boxes with QLabels to their left"""

    stateChanged = Signal(int)

    def __init__(self, label:str='', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.PointingHandCursor)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)
        self.layout.addStretch(1)
        self.setLayout(self.layout)
        
        # Connect the internal checkbox's stateChanged signal to the new signal
        self.checkbox.stateChanged.connect(self.stateChanged)
        
    def isChecked(self):
        return self.checkbox.isChecked()
    
    def setChecked(self, val: bool):
        self.checkbox.setChecked(val)