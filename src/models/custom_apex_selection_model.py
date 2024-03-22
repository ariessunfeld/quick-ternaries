"""Contains the model representing the custom apex selection logic, part of the BaseSetupModel"""

from typing import List

class CustomApexSelectionModel:
    def __init__(self):
        self.available_columns: List[str] = []
        self.top_apex_selected_columns: List[str] = []
        self.right_apex_selected_columns: List[str] = []
        self.left_apex_selected_columns: List[str] = []
        self.selected_column: str = ''

    def add_available_column(self, col: str):
        if col not in self.available_columns:
            self.available_columns.append(col)
        
    def remove_available_column(self, col: str):
        if col in self.available_columns:
            self.available_columns.remove(col)
    
    def add_top_apex_column(self, col: str):
        if col not in self.top_apex_selected_columns:
            self.top_apex_selected_columns.append(col)
        
    def add_right_apex_column(self, col: str):
        if col not in self.right_apex_selected_columns:
            self.right_apex_selected_columns.append(col)

    def add_left_apex_column(self, col: str):
        if col not in self.left_apex_selected_columns:
            self.left_apex_selected_columns.append(col)

    def remove_top_apex_column(self, col: str):
        if col in self.top_apex_columns:
            self.top_apex_selected_columns.remove(col)

    def remove_right_apex_column(self, col: str):
        if col in self.right_apex_selected_columns:
            self.right_apex_selected_columns.remove(col)

    def remove_left_apex_column(self, col: str):
        if col in self.left_apex_columns:
            self.left_apex_selected_columns.remove(col)

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
