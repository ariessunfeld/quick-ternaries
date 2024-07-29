"""View class for the Ternary custom apex selection interface"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget
)

from src.views.utils import AddRemoveList

if TYPE_CHECKING:
    from src.models.ternary.setup import AxisSelectionModel


class AxisSelectionView(QWidget):
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

    def switch_to_cartesian_view(self):
        self.add_remove_list_right_apex_columns.setVisible(False)
        self.add_remove_list_top_apex_columns.setText('X Axis')
        self.add_remove_list_left_apex_columns.setText('Y Axis')

    def switch_to_ternary_view(self):
        self.add_remove_list_right_apex_columns.setVisible(True)
        self.add_remove_list_top_apex_columns.setText('Top Apex')
        self.add_remove_list_left_apex_columns.setText('Left Apex')

    def refresh(self, model: 'AxisSelectionModel'):

        # Clear the view
        self.list_widget_available_columns.clear()
        self.add_remove_list_top_apex_columns.clear()
        self.add_remove_list_right_apex_columns.clear()
        self.add_remove_list_left_apex_columns.clear()

        # Repopulate with values from model
        self.list_widget_available_columns.addItems(model.options)
        self.add_remove_list_top_apex_columns.addItems(model.top)
        self.add_remove_list_right_apex_columns.addItems(model.right)
        self.add_remove_list_left_apex_columns.addItems(model.left)
