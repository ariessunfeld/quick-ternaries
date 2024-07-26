"""Represents state of Bootstrap editor error entry area"""

from typing import List, Tuple

class BaseBootstrapErrorEntryModel:
    
    def __init__(self):
        self.column_error_map = {}
    
    def add_column(self, col: str):
        # If the column isn't already in the mapping, add it to the dict
        if col not in self.column_error_map:
            self.column_error_map[col] = ''

    def rem_column(self, col: str):
        # If the col is already in the mapping, remove it
        if col in self.column_error_map:
            del self.column_error_map[col]
        
    def update_error_value(self, col: str, value: str):
        if col in self.column_error_map:
            self.column_error_map[col] = value

    def get_sorted_repr(self) -> List[Tuple[str, str]]:
        return sorted(self.column_error_map.items())
