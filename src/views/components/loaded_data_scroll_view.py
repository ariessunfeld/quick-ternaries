import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon

from src.views.utils import ListItemWidget

class DataLibraryView(QWidget):
    has_data = Signal(bool)

    ADD_FILES_ICON = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'assets',
        'icons',
        'add_files.png')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(150)
        self._setup_ui()
        self._setup_styles()
        self._emit_has_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.file_list = QListWidget()
        self._setup_add_data()

        layout.addWidget(self.file_list)
        layout.addWidget(self.add_data_button)

    def _setup_add_data(self):
        self.add_data_button = QPushButton()
        self.add_data_button.setCursor(Qt.PointingHandCursor)
        
        button_layout = QHBoxLayout(self.add_data_button)
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        # stretch to center the content
        button_layout.addStretch()
        
        add_files_icon_path = self.ADD_FILES_ICON
        icon = QIcon(add_files_icon_path)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(20, 20))
        button_layout.addWidget(icon_label)
        
        text_label = QLabel("Add Data")
        button_layout.addWidget(text_label)
        
        # stretch to center the content
        button_layout.addStretch()


    def _setup_styles(self):
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                border-bottom: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background: transparent;
                color: black;
            }
            QPushButton {
                border: 1px solid gray;
                padding: 5px;
                text-align: center;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        self.file_list.setSpacing(-10)
        self.file_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def _emit_has_data(self):
        self.has_data.emit(self.file_list.count() > 0)

    def add_item(self, title, full_path):
        list_item = QListWidgetItem(self.file_list)
        item_widget = ListItemWidget(title, full_path)
        list_item.setSizeHint(item_widget.sizeHint())
        self.file_list.addItem(list_item)
        self.file_list.setItemWidget(list_item, item_widget)
        self._emit_has_data()
        return list_item, item_widget.close_button

    def remove_item(self, item):
        self.file_list.takeItem(self.file_list.row(item))
        self._emit_has_data()

    def clear(self):
        self.file_list.clear()
        self._emit_has_data()
