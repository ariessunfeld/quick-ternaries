"""Popup window to display a gif"""


from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel
)

from PySide6.QtCore import (
    Qt, 
    QSize, 
)

from PySide6.QtGui import (
    QMovie
)


class GifPopup(QWidget):
    def __init__(self, gif_path, width, height, text, parent=None):
        super(GifPopup, self).__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.text_label = QLabel(text, self)
        self.gif_label = QLabel(self)
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(width, height))
        self.gif_label.setMovie(self.movie)
        self.gif_label.setFixedSize(width, height)

        layout = QHBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.gif_label)
        self.setLayout(layout)

        self.movie.start()
