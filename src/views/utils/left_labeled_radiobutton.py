from PySide6.QtWidgets import QWidget, QHBoxLayout, QRadioButton, QLabel
from PySide6.QtCore import Signal

class LeftLabeledRadioButton(QWidget):
    toggled = Signal(bool)  # Expose the toggled signal

    def __init__(self, text, parent=None):
        super(LeftLabeledRadioButton, self).__init__(parent)
        self.layout = QHBoxLayout(self)

        self.label = QLabel(text)
        self.radio_button = QRadioButton()

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.radio_button)

        # Connect the internal radio button's toggled signal to the custom signal
        self.radio_button.toggled.connect(self.toggled)

    def isChecked(self):
        return self.radio_button.isChecked()

    def setChecked(self, checked):
        self.radio_button.setChecked(checked)

