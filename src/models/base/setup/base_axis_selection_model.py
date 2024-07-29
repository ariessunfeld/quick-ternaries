"""Base class for axis selection models"""

from typing import List, Optional


class BaseAxisSelectionModel:

    AXES = []
    
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

    def add_option(self, option: str):
        if option not in self._options:
            self._options.append(option)
    
    def rem_option(self, option: str):
        if option in self._options:
            self._options.remove(option)

    def add_to_axis(self, option: str, axis: str):
        """Adds `option` to `axis` and removes `option` from `options`"""
        if axis in self.AXES and option in self._options:
            current = getattr(self, f'_{axis}')
            if option not in current:
                setattr(self, f'_{axis}', current + [option])
                self.rem_option(option)
        else:
            raise ValueError(f'`{axis}` not a valid axis ({self.AXES}) or `{option}` not available.')

    def rem_from_axis(self, option: str, axis: str):
        """Removes `option` from `axis` and adds `option` back to `options`"""
        if axis in self.AXES:
            current = getattr(self, f'_{axis}')
            if option in current:
                current.remove(option)
                setattr(self, f'_{axis}', current)
                self.add_option(option)
        else:
            raise ValueError(f'`{axis}` not a valid axis ({self.AXES})')

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
