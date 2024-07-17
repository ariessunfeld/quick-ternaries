import os

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton
)

from PySide6.QtCore import (
    Qt, QSize
)

from PySide6.QtGui import QIcon

from .icon_button import IconButton

class ListItemWidget(QWidget):
    def __init__(self, title, full_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.full_path = full_path

        self.layout = QHBoxLayout(self)

        self.set_title(title)
        self.layout.addStretch()
        self.create_close_button()

        self.setLayout(self.layout)

    def set_title(self, title):
        label = QLabel(title)
        label.setToolTip(f"File: {self.full_path}")
        self.layout.addWidget(label)

    def create_close_button(self):
        trash_can_icon_path = os.path.join(
            'src', 
            'assets', 
            'icons',
            'trash_can.png')
        self.close_button = IconButton(trash_can_icon_path)
        self.layout.addWidget(self.close_button)
