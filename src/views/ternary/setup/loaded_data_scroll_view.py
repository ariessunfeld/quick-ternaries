from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem
)
from PySide6.QtCore import Signal

from src.views.utils import ListItemWidget

class LoadedDataScrollView(QWidget):

    has_data = Signal(bool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.file_list = QListWidget(self)
        self.set_style()
        self.setMinimumHeight(150)

        self.layout.addWidget(self.file_list)
        self.setLayout(self.layout)

        self._emit_has_data()

    def _emit_has_data(self):
        self.has_data.emit(self.file_list.count() != 0)

    def set_style(self):
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                background-color: transparent;
            }
            QListWidget::item {
                margin: 2px;
                padding: 2px;
                margin: 6px;             
            }
            QListWidget::item:selected {
                background: transparent;
                color: black;
            }
        """)
        self.file_list.setSpacing(-10) # shrink the vertical spacing between file names

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
