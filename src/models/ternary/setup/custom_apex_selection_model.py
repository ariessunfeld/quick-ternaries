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
