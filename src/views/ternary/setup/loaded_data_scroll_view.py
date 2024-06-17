from src.views.utils.removable_list_item import ListItemWidget

from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QListWidget,
    QListWidgetItem
)


# class LoadedDataScrollView(QWidget):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.layout = QVBoxLayout(self)
#         self.file_list = QListWidget(self)
#         self.set_style()
        
#         self.layout.addWidget(self.file_list)
#         self.setLayout(self.layout)

#     def set_style(self):
#         self.file_list.setStyleSheet("""
#             QListWidget {
#                 border: 1px solid gray;
#                 background-color: transparent;
#             }
#             QListWidget::item {
#                 margin: 2px;
#                 padding: 2px;
#             }
#             QListWidget::item:selected {
#                 background: transparent;
#                 color: black;
#             }
#         """)

#     def add_item(self, title):
#         list_item = QListWidgetItem(self.file_list)
#         item_widget = ListItemWidget(title)
#         list_item.setSizeHint(item_widget.sizeHint())
#         self.file_list.addItem(list_item)
#         self.file_list.setItemWidget(list_item, item_widget)
#         return list_item, item_widget.close_button

#     def remove_item(self, item):
#         self.file_list.takeItem(self.file_list.row(item))

#     def clear(self):
#         self.file_list.clear()

class LoadedDataScrollView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.file_list = QListWidget(self)
        self.set_style()
        self.setMinimumHeight(150)
        
        self.layout.addWidget(self.file_list)
        self.setLayout(self.layout)

    def set_style(self):
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                background-color: transparent;
            }
            QListWidget::item {
                margin: 6px;
                padding: 2px;
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
        return list_item, item_widget.close_button

    def remove_item(self, item):
        self.file_list.takeItem(self.file_list.row(item))

    def clear(self):
        self.file_list.clear()
