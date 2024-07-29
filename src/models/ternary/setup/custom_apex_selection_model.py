"""Contains the model representing the custom apex selection logic, part of the BaseSetupModel"""

from typing import List, Optional

from src.models.base.setup import BaseAxisSelectionModel

class AxisSelectionModel(BaseAxisSelectionModel):

    AXES = ['top', 'left', 'right']

    def __init__(
            self, 
            options: List[str], 
            selected: str, 
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


    

# class CustomApexSelectionModel:
#     def __init__(self):
#         self.available_columns: List[str] = []
#         self.top_apex_selected_columns: List[str] = []
#         self.right_apex_selected_columns: List[str] = []
#         self.left_apex_selected_columns: List[str] = []
#         self.selected_column: str = ''

#     # def update_view(self):
#     #     """This is somewhat lazy. Could be optimized for speed with more specific insertions."""
#     #     self.view.list_widget_available_columns.clear()
#     #     self.view.add_remove_list_top_apex_columns.clear()
#     #     self.view.add_remove_list_right_apex_columns.clear()
#     #     self.view.add_remove_list_left_apex_columns.clear()

#     #     self.view.list_widget_available_columns.addItems(
#     #         self.get_available_columns())
#     #     self.view.add_remove_list_top_apex_columns.addItems(
#     #         self.get_top_apex_selected_columns())
#     #     self.view.add_remove_list_right_apex_columns.addItems(
#     #         self.get_right_apex_selected_columns())
#     #     self.view.add_remove_list_left_apex_columns.addItems(
#     #         self.get_left_apex_selected_columns())

#     def add_available_column(self, col: str):
#         if col not in self.available_columns:
#             self.available_columns.append(col)
#             #self.update_view()
        
#     def remove_available_column(self, col: str):
#         if col in self.available_columns:
#             self.available_columns.remove(col)
#             #self.update_view()
    
#     def add_top_apex_column(self, col: str):
#         if col not in self.top_apex_selected_columns:
#             self.top_apex_selected_columns.append(col)
#             #self.update_view()
        
#     def add_right_apex_column(self, col: str):
#         if col not in self.right_apex_selected_columns:
#             self.right_apex_selected_columns.append(col)
#             #self.update_view()

#     def add_left_apex_column(self, col: str):
#         if col not in self.left_apex_selected_columns:
#             self.left_apex_selected_columns.append(col)
#             #self.update_view()

#     def remove_top_apex_column(self, col: str):
#         if col in self.top_apex_selected_columns:
#             self.top_apex_selected_columns.remove(col)
#             #self.update_view()

#     def remove_right_apex_column(self, col: str):
#         if col in self.right_apex_selected_columns:
#             self.right_apex_selected_columns.remove(col)
#             #self.update_view()

#     def remove_left_apex_column(self, col: str):
#         if col in self.left_apex_selected_columns:
#             self.left_apex_selected_columns.remove(col)
#             #self.update_view()

#     def get_available_columns(self):
#         return sorted(self.available_columns)
    
#     def get_top_apex_selected_columns(self):
#         return sorted(self.top_apex_selected_columns)
    
#     def get_right_apex_selected_columns(self):
#         return sorted(self.right_apex_selected_columns)
    
#     def get_left_apex_selected_columns(self):
#         return sorted(self.left_apex_selected_columns)
    
#     def get_selected_column(self):
#         return self.selected_column
    
#     def set_selected_column(self, col: str):
#         self.selected_column = col

# if __name__ == '__main__':
#     inst = TernaryAxisSelectionModel(['A', 'B', 'C', 'D', 'E'], 'A')
#     print(inst.options, inst.top, inst.left, inst.right)
#     inst.add_to_axis('A', 'top')
#     print(inst.options, inst.top, inst.left, inst.right)
#     inst.add_to_axis('C', 'right')
#     print(inst.options, inst.top, inst.left, inst.right)
#     inst.add_to_axis('C', 'left')
#     print(inst.options, inst.top, inst.left, inst.right)
#     inst.rem_from_axis('A', 'top')
#     print(inst.options, inst.top, inst.left, inst.right)
#     inst.rem_from_axis('C', 'top')
#     print(inst.options, inst.top, inst.left, inst.right)
