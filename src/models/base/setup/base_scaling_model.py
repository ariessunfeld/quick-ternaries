"""Model for Axis Scaling configuration"""

from abc import ABC
from typing import List, Tuple, Dict

class BaseAxisScalingModel(ABC):
    
    def __init__(self):
        self.column_scale_mapping: Dict[str, str] = {}
    
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
    
    def to_json(self) -> dict:
        """Convert the model to a JSON-serializable dictionary."""
        return {
            'column_scale_mapping': self.column_scale_mapping
        }

    @classmethod
    def from_json(cls, data: dict):
        """Create a model instance from a JSON-serializable dictionary."""
        instance = cls()
        instance.column_scale_mapping = data.get('column_scale_mapping', {})
        return instance
