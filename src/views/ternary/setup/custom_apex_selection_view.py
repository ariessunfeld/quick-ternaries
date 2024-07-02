
from src.views.utils.add_remove_list import AddRemoveList

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QListWidget,
)

class CustomApexSelectionView(QWidget):
    """A megawidget containing the ListWidgets and buttons for custom apex selection"""

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)
        
        self.list_widget_available_columns = QListWidget()
        self.add_remove_list_top_apex_columns = AddRemoveList(self, 'Top Apex')
        self.add_remove_list_right_apex_columns = AddRemoveList(self, 'Right Apex')
        self.add_remove_list_left_apex_columns = AddRemoveList(self, 'Left Apex')

        self.layout.addWidget(self.list_widget_available_columns)
        self.right_layout.addWidget(self.add_remove_list_top_apex_columns)
        self.right_layout.addWidget(self.add_remove_list_left_apex_columns)
        self.right_layout.addWidget(self.add_remove_list_right_apex_columns)
        self.layout.addWidget(self.right_layout_widget)

    def refresh(self, model):
        self.list_widget_available_columns.clear()
        self.add_remove_list_top_apex_columns.clear()
        self.add_remove_list_right_apex_columns.clear()
        self.add_remove_list_left_apex_columns.clear()

        self.list_widget_available_columns.addItems(
            model.get_available_columns())
        self.add_remove_list_top_apex_columns.addItems(
            model.get_top_apex_selected_columns())
        self.add_remove_list_right_apex_columns.addItems(
            model.get_right_apex_selected_columns())
        self.add_remove_list_left_apex_columns.addItems(
            model.get_left_apex_selected_columns())
