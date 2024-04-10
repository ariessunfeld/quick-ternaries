"""Contains the TraceView(QWidget) class, which contains the widgets needed for configuring individual traces, and is used in the dynamic content area of the MainWindow"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)
class TraceView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.test_label = QLabel('Hello Trace View')
        self.layout.addWidget(self.test_label)