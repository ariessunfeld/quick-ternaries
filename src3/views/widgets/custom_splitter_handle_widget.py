from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QSplitterHandle

# --------------------------------------------------------------------
# Custom Splitter Classes
# --------------------------------------------------------------------
class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.orientation = orientation
        cursor = (
            Qt.CursorShape.SplitHCursor
            if orientation == Qt.Orientation.Horizontal
            else Qt.CursorShape.SplitVCursor
        )
        self.setCursor(cursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Transparent background

        grip_color = QColor(128, 128, 128)
        painter.setBrush(grip_color)
        if self.orientation == Qt.Orientation.Horizontal:
            width = self.width()
            center_x = width // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(
                    center_x - dot_radius,
                    self.height() // 2 + i * spacing - dot_radius,
                    int(dot_radius * 2),
                    int(dot_radius * 2),
                )
        else:
            height = self.height()
            center_y = height // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(
                    self.width() // 2 + i * spacing - dot_radius,
                    center_y - dot_radius,
                    int(dot_radius * 2),
                    int(dot_radius * 2),
                )

    def enterEvent(self, event):
        cursor = (
            Qt.CursorShape.SplitHCursor
            if self.orientation == Qt.Orientation.Horizontal
            else Qt.CursorShape.SplitVCursor
        )
        self.setCursor(cursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)
