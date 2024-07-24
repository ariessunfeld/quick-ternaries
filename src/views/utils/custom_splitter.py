"""Utilities for splitters for dragging window elements to resize""" 

from PySide6.QtWidgets import QSplitter, QSplitterHandle
from PySide6.QtGui import QPainter, QPen
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt


class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.SplitHCursor) # cursor mod

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # color and pen for drawing
        pen = QPen(QColor('#999999'))
        pen.setWidth(2)
        painter.setPen(pen)

        # vertical line
        mid_x = self.width() // 2 - 2
        painter.drawLine(mid_x, 0, mid_x, self.height())


class CustomSplitter(QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)
