"""Base class for Hover Data Selection interface models"""

from typing import List

class BaseHoverDataSelectionModel:
    def __init__(
            self, 
            available_attrs: List[str] = None, 
            selected_attrs: List[str] = None):
        self._available_attrs = available_attrs.copy() if available_attrs else []
        self._selected_attrs = selected_attrs.copy() if selected_attrs else []

    @property
    def available_attrs(self) -> List[str]:
        return sorted(self._available_attrs)

    @available_attrs.setter
    def available_attrs(self, value: List[str]):
        self._available_attrs = value

    @property
    def selected_attrs(self) -> List[str]:
        return sorted(self._selected_attrs)

    @selected_attrs.setter
    def selected_attrs(self, value: List[str]):
        self._selected_attrs = value

    def add_available_attr(self, attr: str):
        if attr not in self._available_attrs:
            self._available_attrs.append(attr)

    def rem_available_attr(self, attr: str):
        if attr in self._available_attrs:
            self._available_attrs.remove(attr)

    def add_selected_attr(self, attr: str):
        if attr not in self._selected_attrs:
            self._selected_attrs.append(attr)

    def rem_selected_attr(self, attr: str):
        if attr in self._selected_attrs:
            self._selected_attrs.remove(attr)

    def to_json(self) -> dict:
        """Convert the model to a JSON-serializable dictionary."""
        return {
            'available_attrs': self._available_attrs,
            'selected_attrs': self._selected_attrs
        }

    @classmethod
    def from_json(cls, data: dict):
        """Create a model instance from a JSON-serializable dictionary."""
        available_attrs = data.get('available_attrs', [])
        selected_attrs = data.get('selected_attrs', [])
        return cls(available_attrs=available_attrs, selected_attrs=selected_attrs)
