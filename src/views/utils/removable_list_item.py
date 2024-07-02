from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout,  
    QLabel, 
    QPushButton,
    QToolTip
)
from PySide6.QtCore import (
    Qt
)

class ListItemWidget(QWidget):
    def __init__(self, title, full_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.full_path = full_path

        self.layout = QHBoxLayout(self)

        self.set_title(title)
        self.layout.addStretch()
        # self.create_info_button()
        self.create_close_button()

        self.setLayout(self.layout)

    def set_title(self, title):
        label = QLabel(title)
        label.setToolTip(f"File: {self.full_path}")
        self.layout.addWidget(label)

    def create_close_button(self):
        self.close_button = QPushButton("✕")
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setMaximumWidth(20)
        self.layout.addWidget(self.close_button)
