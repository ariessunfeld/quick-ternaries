"""Base class for Setup Menu models"""

from abc import ABC

from src.models.base.setup import 

class BaseSetupModel(ABC):

    def __init__(
            self, 
            title: str = '',
            custom_hover_data_checked: bool = False,
            scale_axes_checked: bool = False,
            advanced_settings_checked: bool = False,
            hover_data_selection_model:):
        
        self._title = title
        self._custom_hover_data_checked = custom_hover_data_checked
        self._scale_axes_checked = scale_axes_checked
        self._advanced_settings_checked = advanced_settings_checked

    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str):
        self._title = value

    @property
    def custom_hover_data_checked(self) -> bool:
        return self._custom_hover_data_checked
    
    @custom_hover_data_checked.setter
    def custom_hover_data_checked(self, value: bool):
        self._custom_hover_data_checked = value

    @property
    def scale_axes_checked(self) -> bool:
        return self._scale_axes_checked
    
    @scale_axes_checked.setter
    def scale_axes_checked(self, value: bool):
        self._scale_axes_checked = value

    @property
    def advanced_settings_checked(self) -> bool:
        return self._advanced_settings_checked
    
    @advanced_settings_checked.setter
    def advanced_settings_checked(self, value: bool):
        self._advanced_settings_checked = value
