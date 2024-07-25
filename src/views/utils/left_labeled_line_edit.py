from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit, 
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QDoubleValidator

class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    textChanged = Signal(str)

    def __init__(
            self, 
            label: str = '', 
            stretch: int = 0, 
            parent: QWidget|None = None,
            validate_doubles: bool = False,
            n_decimals: int = 2,
            min_double: Optional[float] = None,
            max_double: Optional[float] = None):
        """
        Initializes a (Label & Line Edit) Megawidget.

        This widget contains a QLabel and a QLineEdit, arranged horizontally.
        Optionally, the QLineEdit can be configured to only accept double values 
        within a specified range and precision.

        Arguments:
            label (str): Text to display in the label. Default is an empty string.
            stretch (int): Stretch factor for spacing between the label and the line edit. Default is 0.
            parent (QWidget or None): The parent widget. Default is None.
            validate_doubles (bool): If True, the QLineEdit will only accept double values. Default is False.
            n_decimals (int): Number of decimal places to allow if validate_doubles is True. Default is 2.
            min_double (Optional[float]): Minimum value for the double validator. Default is None.
            max_double (Optional[float]): Maximum value for the double validator. Default is None.
        """
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.line_edit = QLineEdit()

        self.layout.addWidget(self.label)
        if stretch:
            self.layout.addStretch(stretch)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

        # Set up double validation if needed
        if validate_doubles:
            double_validator = QDoubleValidator()
            double_validator.setDecimals(n_decimals)
            if min_double is not None:
                double_validator.setBottom(min_double)
            if max_double is not None:
                double_validator.setTop(max_double)
            self.line_edit.setValidator(double_validator)

        # Connect signals
        self.line_edit.textChanged.connect(self._emit_text_changed)

    def text(self):
        return self.line_edit.text()
    
    def setText(self, value: str):
        if isinstance(value, float):
            value = str(value)
        self.line_edit.setText(value)

    def setCompleter(self, value: List[str]):
        self.line_edit.setCompleter(value)

    def _emit_text_changed(self, value: str):
        self.textChanged.emit(value)

    def clear(self):
        self.line_edit.clear()

    def setLabel(self, value: str):
        self.label.setText(value)
