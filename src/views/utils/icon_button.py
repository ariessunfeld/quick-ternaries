from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QSize, Signal

class IconButton(QWidget):
    clicked = Signal()

    def __init__(self, icon_path: str, size: int = 20, hover_color: QColor=QColor(255, 0, 0), parent: QWidget = None):
        super().__init__(parent)
        
        self.icon_path = icon_path
        self.size = size
        self.default_color = QColor(0, 0, 0)
        self.hover_color = hover_color

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.button = QPushButton(self)
        self.button.setFixedSize(QSize(self.size, self.size))
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(self.clicked.emit)
        self.button.setStyleSheet('border: none; background-color: transparent;')

        self.set_icon_color(self.default_color)

        layout.addWidget(self.button)

    def set_icon_color(self, color: QColor):
        pixmap = QPixmap(self.icon_path)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        icon = QIcon(pixmap)
        self.button.setIcon(icon)
        self.button.setIconSize(QSize(self.size, self.size))

    def enterEvent(self, event):
        self.set_icon_color(self.hover_color)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.set_icon_color(self.default_color)
        super().leaveEvent(event)

    def set_default_color(self, color: QColor):
        self.default_color = color
        self.set_icon_color(self.default_color)

    def set_hover_color(self, color: QColor):
        self.hover_color = color
