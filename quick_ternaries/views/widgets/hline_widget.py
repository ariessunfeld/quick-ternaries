from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import Qt

class HLineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(20)  # Fixed height for the widget
        self.setContentsMargins(0, 0, 0, 0)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(0, 8, self.width(), 4, QColor("#0078D7"))  # Blue line