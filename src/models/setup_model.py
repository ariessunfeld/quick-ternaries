"""Contains Model for the Setup part of the GUI (part where data loading, ternary apex selection, apex display name, and title are set)"""

from typing import Dict, List

from src.models.custom_apex_selection_model import CustomApexSelectionModel
from src.models.data_models import DataFile, DataLibrary
from src.models.selection_models import HeaderRowSelectionModel, SheetSelectionModel

from src.views.start_setup.custom_hover_data_selection_view import CustomHoverDataSelectionView

class TernaryType:
    def __init__(self, name: str, top: List[str], left: List[str], right: List[str]):
        """
        Arguments:
            name: a string with the display name of the ternary type
            top: a list of chemical formulae to use for the top apex
            left: a list of chemical formulae to use for the left apex
            right: a list of chemical formulae to use for the right apex
        """
        self.name: str = name
        self.top: list = top
        self.right: list = right
        self.left: list = left
        self.formatted_name = self.get_short_formatted_name()

    def get_name(self):
        return self.name
    
    def get_top(self):
        return self.top

    def get_right(self):
        return self.right
        
    def get_left(self):
        return self.left
    
    def add_to_top(self, col: str):
        """Adds a column (str) to the top apex"""
        if col not in self.top:
            self.top.append(col)
    
    def add_to_right(self, col: str):
        """Adds a column (str) to the right apex"""
        if col not in self.right:
            self.right.append(col)
    
    def add_to_left(self, col: str):
        """Adds a column (str) to the left apex"""
        if col not in self.left:
            self.left.append(col)

    def get_short_formatted_name(self):
        """Return space-separated string with first character of each part of each apex
        
        Example: self.top = ['Al2O3', 'SiO2']; self.left = ['Cao', 'Na2O', 'K2O']; self.right = ['FeOT']
            returns: 'AS CNK F'
        """
        return "".join(s[0] for s in self.top) + " " + \
            "".join(s[0] for s in self.left) + " " + \
            "".join(s[0] for s in self.right)
    
    def get_combobox_formatted_name(self):
        return "+".join(s[0] for s in self.top) + "  " + \
            "+".join(s[0] for s in self.left) + "  " + \
            "+".join(s[0] for s in self.right)

    
class CustomHoverDataSelectionModel:
    def __init__(self, available_attrs: List[str], selected_attrs: List[str]):
        self.available_attrs = available_attrs.copy()
        self.selected_attrs = selected_attrs.copy()

    def set_view(self, view: CustomHoverDataSelectionView):
        self.view = view

    def set_selected_attrs(self, selected_attrs: List[str]):
        self.selected_attrs = selected_attrs
        self.update_view()

    def get_selected_attrs(self) -> List[str]:
        return sorted(self.selected_attrs)
    
    def set_available_attrs(self, available_attrs: List[str]):
        self.available_attrs = available_attrs
        self.update_view()

    def get_available_attrs(self) -> List[str]:
        return sorted(self.available_attrs)
    
    def add_available_attr(self, attr: str):
        if attr not in self.available_attrs:
            self.available_attrs.append(attr)
            self.update_view()

    def rem_available_attr(self, attr: str):
        if attr in self.available_attrs:
            self.available_attrs.remove(attr)
            self.update_view()

    def add_selected_attr(self, attr: str):
        if attr not in self.selected_attrs:
            self.selected_attrs.append(attr)
            self.update_view()

    def rem_selected_attr(self, attr: str):
        if attr in self.selected_attrs:
            self.selected_attrs.remove(attr)
            self.update_view()

    def update_view(self):
        """Sets the views available and selected columns"""
        self.view.set_available_columns(self.get_available_attrs())
        self.view.set_selected_columns(self.get_selected_attrs())


class StartSetupModel:

    DEFAULT_TERNARY_TYPE = ['', [], [], []]

    def __init__(self):
        self.data_library: DataLibrary = DataLibrary()
        self.ternary_type: TernaryType = TernaryType(*self.DEFAULT_TERNARY_TYPE)
        self.custom_apex_selection_model: CustomApexSelectionModel = CustomApexSelectionModel()
        self.header_row_selection_model: HeaderRowSelectionModel = HeaderRowSelectionModel([])
        self.sheet_selection_model: SheetSelectionModel = SheetSelectionModel([''])
        self.title: str = ''
        self.top_apex_display_name: str = ''
        self.right_apex_display_name: str = ''
        self.left_apex_display_name: str = ''
        self.controller = None
        self.view = None

    def set_controller(self, controller):
        self.controller = controller

    def set_view(self, view):
        self.view = view

    def get_ternary_type(self) -> TernaryType:
        return self.ternary_type
    
    def set_ternary_type(self, ttype: TernaryType):
        self.ternary_type = ttype

    def set_title(self, title: str):
        self.title = title

    def get_title(self) -> str:
        return self.title
    
    def set_top_apex_display_name(self, top_name: str):
        self.top_apex_display_name = top_name

    def set_right_apex_display_name(self, right_name: str):
        self.right_apex_display_name = right_name

    def set_left_apex_display_name(self, left_name: str):
        self.left_apex_display_name = left_name

    def get_top_apex_display_name(self):
        return self.top_apex_display_name
    
    def get_right_apex_display_name(self):
        return self.right_apex_display_name
    
    def get_left_apex_display_name(self):
        return self.left_apex_display_name

    
    
    
