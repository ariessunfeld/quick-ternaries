"""Represents state of Ternary Apex Scaling panel"""

from typing import List, Tuple, Dict, Optional

class TernaryApexScalingModel:
    
    def __init__(self):
        self.column_scale_mapping = {}
    
    def add_column(self, col: str):
        # If the column isn't already in the mapping, add it to the dict
        if col not in self.column_scale_mapping:
            self.column_scale_mapping[col] = '1'

    def rem_column(self, col: str):
        # If the col is already in the mapping, remove it
        if col in self.column_scale_mapping:
            del self.column_scale_mapping[col]
        
    def update_scale_factor(self, col: str, value: str):
        if col in self.column_scale_mapping:
            self.column_scale_mapping[col] = value

    def get_sorted_repr(self) -> List[Tuple]:
        return sorted(self.column_scale_mapping.items())
