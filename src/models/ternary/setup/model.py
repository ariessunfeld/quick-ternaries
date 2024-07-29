"""Contains Model for the Setup part of the GUI (part where data loading, ternary apex selection, apex display name, and title are set)"""

from typing import List

from src.models.ternary.setup import (
    CustomApexSelectionModel,
    AxisSelectionModel,
    CustomHoverDataSelectionModel,
    TernaryApexScalingModel,
    AdvancedSettingsModel
    )
from src.utils.ternary_types import TERNARY_TYPES


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

    def get_name(self) -> List[str]:
        return self.name
    
    def get_top(self) -> List[str]:
        return self.top

    def get_right(self) -> List[str]:
        return self.right
        
    def get_left(self) -> List[str]:
        return self.left
    
    def add_to_top(self, col: str):
        """Adds a column (str) to the top apex"""
        if col not in self.top:
            self.top.append(col)
            self.update_short_formatted_name()
    
    def add_to_right(self, col: str):
        """Adds a column (str) to the right apex"""
        if col not in self.right:
            self.right.append(col)
            self.update_short_formatted_name()
    
    def add_to_left(self, col: str):
        """Adds a column (str) to the left apex"""
        if col not in self.left:
            self.left.append(col)
            self.update_short_formatted_name()

    def get_short_formatted_name(self) -> str:
        """Return space-separated string with first character of each part of each apex
        
        Example: self.top = ['Al2O3', 'SiO2']; self.left = ['Cao', 'Na2O', 'K2O']; self.right = ['FeOT']
            returns: 'AS CNK F'
        """
        return "".join(s[0] if s else '' for s in self.top) + " " + \
            "".join(s[0] if s else '' for s in self.left) + " " + \
            "".join(s[0] if s else '' for s in self.right)
    
    def get_combobox_formatted_name(self) -> str:
        return "+".join(s[0] if s else '' for s in self.top) + "  " + \
            "+".join(s[0] if s else '' for s in self.left) + "  " + \
            "+".join(s[0] if s else '' for s in self.right)
    
    def update_short_formatted_name(self) -> str:
        self.formatted_name = self.get_short_formatted_name()
    
    def __str__(self):
        return str(self.__dict__)

class TernaryStartSetupModel:

    def __init__(self):
        
        self.available_ternary_types: List[TernaryType] = \
            [TernaryType(**tt) for tt in TERNARY_TYPES]
        
        self.selected_ternary_type: TernaryType = \
            self.available_ternary_types[0]
        
        self.custom_apex_selection_model = AxisSelectionModel([], [])
        self.custom_hover_data_selection_model = CustomHoverDataSelectionModel([], [])
        self.apex_scaling_model = TernaryApexScalingModel()
        self.advanced_settings_model = AdvancedSettingsModel()
        
        self.title: str = ''
        self.top_apex_display_name: str = ''
        self.right_apex_display_name: str = ''
        self.left_apex_display_name: str = ''

        self.custom_hover_data_is_checked = False
        self.scale_apices_is_checked = False
        self.advanced_settings_is_checked = False

    def get_ternary_type(self) -> TernaryType:
        return self.selected_ternary_type
    
    def set_selected_ternary_type(self, ttype: TernaryType):
        self.selected_ternary_type = ttype

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

    def get_top_apex_display_name(self) -> str:
        return self.top_apex_display_name
    
    def get_right_apex_display_name(self) -> str:
        return self.right_apex_display_name
    
    def get_left_apex_display_name(self) -> str:
        return self.left_apex_display_name

    def switch_to_cartesian(self):
        self._clear_selections()

    def switch_to_ternary(self):
        self._clear_selections()

    def _clear_selections(self):
        right_apex_cols = self.custom_apex_selection_model.right
        left_apex_cols = self.custom_apex_selection_model.left
        top_apex_cols = self.custom_apex_selection_model.top
        for col in right_apex_cols:
            self.custom_apex_selection_model.rem_from_axis(col, 'right')
        for col in left_apex_cols:
            self.custom_apex_selection_model.rem_from_axis(col, 'left')
        for col in top_apex_cols:
            self.custom_apex_selection_model.rem_from_axis(col, 'top')
