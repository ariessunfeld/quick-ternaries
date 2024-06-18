from src.views.utils.add_remove_list import AddRemoveList

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
)

class CustomHoverDataSelectionView(QWidget):
    """A megawidget containing the ListWidgets and buttons for custom hover data selection"""

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)

        self.list_widget_available_columns = QListWidget()
        self.add_remove_list = AddRemoveList(self, 'Hover Data')

        self.layout.addWidget(self.list_widget_available_columns)
        self.right_layout.addWidget(self.add_remove_list)
        self.layout.addWidget(self.right_layout_widget)

        self.setLayout(self.layout)

    # TODO (eventually)
    # refactor to use these single-add and single-remove
    # methods in favor of the heaevier set-methods below
    # for performance purposes
    def add_to_available_column(self, *args):
        # Should be called by model
        pass

    def add_to_selected_column(self, *args):
        pass

    def remove_from_available_column(self, *args):
        pass

    def remove_from_selected_column(self, *args):
        pass

    def set_available_columns(self, available_columns: List[str]):
        self.list_widget_available_columns.clear()
        self.list_widget_available_columns.addItems(available_columns)

    def set_selected_columns(self, selected_columns: List[str]):
        self.add_remove_list.clear()
        self.add_remove_list.addItems(selected_columns)
