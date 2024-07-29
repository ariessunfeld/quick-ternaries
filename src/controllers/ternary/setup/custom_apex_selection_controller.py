"""Ternary instance of the axis selection controller"""

from typing import TYPE_CHECKING, List

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from src.models.ternary.setup import CustomApexSelectionModel
    from src.views.ternary.setup import AxisSelectionView
    from src.models.ternary.setup import AxisSelectionModel

class AxisSelectionController(QObject):

    column_added_to_apices = Signal(str)
    column_removed_from_apices = Signal(str)

    def __init__(self, model: 'AxisSelectionModel', view: 'AxisSelectionView'):
        
        super().__init__()

        # models and views are instantiated outside this class
        # hence, they get passed to the initialization method
        self.model = model
        self.view = view

        self.setup_connections()
        
    def setup_connections(self):
        # Add/remove button connections
        self.view.add_remove_list_top_apex_columns.button_add.clicked.connect(self._on_btn_add_top_clicked)
        self.view.add_remove_list_top_apex_columns.button_remove.clicked.connect(self._on_btn_rem_top_clicked)
        self.view.add_remove_list_right_apex_columns.button_add.clicked.connect(self._on_btn_add_right_clicked)
        self.view.add_remove_list_right_apex_columns.button_remove.clicked.connect(self._on_btn_rem_right_clicked)
        self.view.add_remove_list_left_apex_columns.button_add.clicked.connect(self.clicked_left_apex_button_add)
        self.view.add_remove_list_left_apex_columns.button_remove.clicked.connect(self.clicked_left_apex_button_remove)

    def _on_btn_add_top_clicked(self):
        """Gets selected column from view's available_columns,
        adds to model's top_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_to_axis(col, 'top')
            self.view.refresh(self.model)
            self.column_added_to_apices.emit(col)

    def _on_btn_rem_top_clicked(self):
        """Gets selected column from view's top_apex columns,
        adds to model's available columns and removes from model's top_apex columns"""
        selected_column = self.view.add_remove_list_top_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.rem_from_axis(col, 'top')
            self.view.refresh(self.model)
            self.column_removed_from_apices.emit(col)

    def _on_btn_add_right_clicked(self):
        """Gets selected column from view's available_columns,
        adds to model's right_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_to_axis(col, 'right')
            self.view.refresh(self.model)
            self.column_added_to_apices.emit(col)

    def _on_btn_rem_right_clicked(self):
        """Gets selected column from view's right_apex columns,
        adds to model's available columns and removes from model's right_apex columns"""
        selected_column = self.view.add_remove_list_right_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.rem_from_axis(col, 'right')
            self.view.refresh(self.model)
            self.column_removed_from_apices.emit(col)

    def clicked_left_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's left_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_to_axis(col, 'left')
            self.view.refresh(self.model)
            self.column_added_to_apices.emit(col)

    def clicked_left_apex_button_remove(self):
        """Gets selected column from view's left_apex columns,
        adds to model's available columns and removes from model's left_apex columns"""
        selected_column = self.view.add_remove_list_left_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.rem_from_axis(col, 'left')
            self.view.refresh(self.model)
            self.column_removed_from_apices.emit(col)

    def update_options(self, new_options: List[str]):
        self.model.options = []

        for option in new_options:
            self.model.add_option(option)

        for option in self.model.top:
            self.model.rem_option(option)
            if option not in new_options:
                self.model.rem_from_axis(option, 'top')
                
        for option in self.model.left:
            self.model.rem_option(option)
            if option not in new_options:
                self.model.rem_from_axis(option, 'left')

        for option in self.model.right:
            self.model.rem_option(option)
            if option not in new_options:
                self.model.rem_from_axis(option, 'right')

        self.view.refresh(self.model)

    def refresh_view(self):
        """Public access to command a view refresh"""
        self.view.refresh(self.model)
