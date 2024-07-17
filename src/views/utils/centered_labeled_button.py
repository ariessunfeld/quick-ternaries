from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Signal, Qt

class LabeledButton(QWidget):
    clicked = Signal()

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.button = QPushButton(label)
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(self.clicked.emit)
        self.button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.layout.addWidget(self.button)

    def setStyleSheet(self, style):
        super().setStyleSheet(style)
        self.button.setStyleSheet(style)

    def enterEvent(self, event):
        self.setStyleSheet("background: #E0E0E0;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("background: transparent;")
        super().leaveEvent(event)
