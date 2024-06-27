"""View where user can enter error values for each ternary apex"""

from typing import List, Tuple

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel
)

from PySide6.QtCore import Signal

from src.views.utils import LeftLabeledLineEdit

class TernaryBootstrapTraceEditorErrorEntryView(QWidget):

    textChanged = Signal(str, str) # emits column, error
    
    def __init__(self, parent: QWidget|None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()

        # Create a container widget to hold the main layout
        self.container_widget = QWidget()
        self.container_widget.setObjectName("containerWidget")  # Set an object name
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)
        
        # add a border to the container widget
        self.container_widget.setStyleSheet("#containerWidget { border: 1px solid #1c1c1c; }")
        
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.container_widget)

        # Label widgets
        self.column_label = QLabel('Apex Column')
        self.chemical_label = QLabel('Uncertainty')

        # Label layout
        self.label_layout = QHBoxLayout()
        self.label_layout.addWidget(self.column_label)
        self.label_layout.addStretch(1)
        self.label_layout.addWidget(self.chemical_label)

        self.container_layout.addLayout(self.label_layout)

    def update_view(self, model_repr: List[Tuple[str, str]]):
        # Remove all existing widgets from the container layout
        while self.container_layout.count() > 1:  # Leave the label layout intact
            item = self.container_layout.takeAt(1)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Add new LeftLabeledLineEdits for each column and uncertainty in model_repr
        for col, uncertainty in model_repr:
            llle = LeftLabeledLineEdit(col, stretch=1)
            llle.setText(uncertainty)
            llle.textChanged.connect(lambda f, c=col: self.textChanged.emit(c, f))
            self.container_layout.addWidget(llle)
