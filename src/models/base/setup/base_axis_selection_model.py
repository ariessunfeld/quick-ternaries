"""Base class for axis selection models"""

from typing import List, Optional


class BaseAxisSelectionModel:
    def __init__(self, options: Optional[List[str]] = None, selected: str = ''):
        self._options = options or []
        self._selected = selected

    @property
    def options(self) -> List[str]:
        return sorted(self._options)
    
    @options.setter
    def options(self, value: List[str]):
        self._options = value.copy()

    @property
    def selected(self) -> str:
        return self._selected
    
    @selected.setter
    def selected(self, value: str):
        self._selected = value

    def to_json(self) -> dict:
        """Convert the model to a JSON-serializable dictionary."""
        return {
            'options': self.options,
            'selected': self.selected
        }
    
    @classmethod
    def from_json(cls, data: dict):
        """Create a model instance from a JSON-serializable dictionary."""
        return cls(data.get('options'), data.get('selected'))
