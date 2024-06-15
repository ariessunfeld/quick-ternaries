from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout,  
    QLabel, 
    QPushButton,
    QToolTip
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
        label.setToolTip(f"File: {self.full_path}")  # Set the tooltip for the label
        self.layout.addWidget(label)

    def create_close_button(self):
        self.close_button = QPushButton("X")
        self.close_button.setMaximumWidth(20)
        self.layout.addWidget(self.close_button)

    # def create_info_button(self):
    #     self.info_button = QPushButton("?")
    #     self.info_button.setMaximumWidth(20)
    #     self.info_button.clicked.connect(self.show_full_path)
    #     self.layout.addWidget(self.info_button)

    def show_full_path(self):
        QToolTip.showText(self.info_button.mapToGlobal(self.info_button.rect().bottomRight()), f"File: {str(self.full_path)}")