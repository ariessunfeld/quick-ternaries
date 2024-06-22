from typing import List

class CustomHoverDataSelectionModel:
    def __init__(self, available_attrs: List[str], selected_attrs: List[str]):
        self.available_attrs = available_attrs.copy()
        self.selected_attrs = selected_attrs.copy()

    def set_selected_attrs(self, selected_attrs: List[str]):
        self.selected_attrs = selected_attrs

    def get_selected_attrs(self) -> List[str]:
        return sorted(self.selected_attrs)

    def set_available_attrs(self, available_attrs: List[str]):
        self.available_attrs = available_attrs

    def get_available_attrs(self) -> List[str]:
        return sorted(self.available_attrs)

    def add_available_attr(self, attr: str):
        if attr not in self.available_attrs:
            self.available_attrs.append(attr)

    def rem_available_attr(self, attr: str):
        if attr in self.available_attrs:
            self.available_attrs.remove(attr)

    def add_selected_attr(self, attr: str):
        if attr not in self.selected_attrs:
            self.selected_attrs.append(attr)

    def rem_selected_attr(self, attr: str):
        if attr in self.selected_attrs:
            self.selected_attrs.remove(attr)
