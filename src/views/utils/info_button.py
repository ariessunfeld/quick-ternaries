from PySide6.QtWidgets import (
    QVBoxLayout, QToolButton, QToolTip, QStyle, QWidget)
from PySide6.QtGui import QCursor
from PySide6.QtCore import Qt


class InfoButton(QWidget):
    def __init__(self, main_window, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

        layout = QVBoxLayout(self)
        self.info_button = QToolButton()
        self.info_button.setCursor(Qt.PointingHandCursor)
        self.info_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.info_button.clicked.connect(lambda _ : self.show_info(msg))
        layout.addWidget(self.info_button)

    def show_info(self, msg):
        QToolTip.showText(QCursor.pos(), msg)
