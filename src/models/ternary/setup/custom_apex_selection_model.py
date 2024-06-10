"""Contains the model representing the custom apex selection logic, part of the BaseSetupModel"""

from typing import List

from src.views.ternary.start_setup.custom_apex_selection_view import CustomApexSelectionView

class CustomApexSelectionModel:
    def __init__(self):
        self.available_columns: List[str] = []
        self.top_apex_selected_columns: List[str] = []
        self.right_apex_selected_columns: List[str] = []
        self.left_apex_selected_columns: List[str] = []
        self.selected_column: str = ''

    def set_view(self, view: CustomApexSelectionView):
        self.view = view

    def update_view(self):
        """This is somewhat lazy. Could be optimized for speed with more specific insertions."""
        self.view.list_widget_available_columns.clear()
        self.view.add_remove_list_top_apex_columns.clear()
        self.view.add_remove_list_right_apex_columns.clear()
        self.view.add_remove_list_left_apex_columns.clear()

        self.view.list_widget_available_columns.addItems(
            self.get_available_columns())
        self.view.add_remove_list_top_apex_columns.addItems(
            self.get_top_apex_selected_columns())
        self.view.add_remove_list_right_apex_columns.addItems(
            self.get_right_apex_selected_columns())
        self.view.add_remove_list_left_apex_columns.addItems(
            self.get_left_apex_selected_columns())

    def add_available_column(self, col: str):
        if col not in self.available_columns:
            self.available_columns.append(col)
            self.update_view()
        
    def remove_available_column(self, col: str):
        if col in self.available_columns:
            self.available_columns.remove(col)
            self.update_view()
    
    def add_top_apex_column(self, col: str):
        if col not in self.top_apex_selected_columns:
            self.top_apex_selected_columns.append(col)
            self.update_view()
        
    def add_right_apex_column(self, col: str):
        if col not in self.right_apex_selected_columns:
            self.right_apex_selected_columns.append(col)
            self.update_view()

    def add_left_apex_column(self, col: str):
        if col not in self.left_apex_selected_columns:
            self.left_apex_selected_columns.append(col)
            self.update_view()

    def remove_top_apex_column(self, col: str):
        if col in self.top_apex_selected_columns:
            self.top_apex_selected_columns.remove(col)
            self.update_view()

    def remove_right_apex_column(self, col: str):
        if col in self.right_apex_selected_columns:
            self.right_apex_selected_columns.remove(col)
            self.update_view()

    def remove_left_apex_column(self, col: str):
        if col in self.left_apex_selected_columns:
            self.left_apex_selected_columns.remove(col)
            self.update_view()

    def get_available_columns(self):
        return sorted(self.available_columns)
    
    def get_top_apex_selected_columns(self):
        return sorted(self.top_apex_selected_columns)
    
    def get_right_apex_selected_columns(self):
        return sorted(self.right_apex_selected_columns)
    
    def get_left_apex_selected_columns(self):
        return sorted(self.left_apex_selected_columns)
    
    def get_selected_column(self):
        return self.selected_column
    
    def set_selected_column(self, col: str):
        self.selected_column = col
