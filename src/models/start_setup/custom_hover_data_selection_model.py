from typing import List

from src.views.start_setup.custom_hover_data_selection_view import CustomHoverDataSelectionView

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