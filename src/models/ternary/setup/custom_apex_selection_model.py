"""Contains the model representing the custom apex selection logic, part of the BaseSetupModel"""

from typing import List, Optional

from src.models.base.setup import BaseAxisSelectionModel

class TernaryAxisSelectionModel(BaseAxisSelectionModel):

    AXES = ['top', 'left', 'right']

    def __init__(
            self, 
            options: Optional[List[str]] = None, 
            selected: str = '', 
            top: Optional[List[str]] = None, 
            left: Optional[List[str]] = None, 
            right: Optional[List[str]] = None):
        super().__init__(options, selected)

        self._top = top or []
        self._left = left or []
        self._right = right or []

    @property
    def top(self) -> List[str]:
        return sorted(self._top)
    
    @top.setter
    def top(self, value: Optional[List[str]]):
        self._top = value.copy()
        
    @property
    def left(self) -> List[str]:
        return sorted(self._left)
    
    @left.setter
    def left(self, value: Optional[List[str]]):
        self._left = value.copy()

    @property
    def right(self) -> List[str]:
        return sorted(self._right)
    
    @right.setter
    def right(self, value: Optional[List[str]]):
        self._right = value.copy()

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
