"""
Contains the TraceView(QWidget) class, 
which contains the widgets needed for configuring individual traces, 
and is used in the dynamic content area of the MainWindow"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout
)
class TernaryTraceEditorView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.test_label = QLabel('Hello Trace View')
        # TODO flesh out with all the existing trace configuration options,
        # and add some more if there are any in the task queue spreadsheet
        self.layout.addWidget(self.test_label)