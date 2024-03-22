"""Contains the models representing the sheet and header row selection logic"""

from typing import List

class SheetSelectionModel:
    """Represents the sheet selection logic when leading an xlsx file"""
    def __init__(self, sheet_names: List[str]):
        self.sheet_names = sheet_names
        self.selected_sheet_name = sheet_names[0]

    def get_selected_sheet_name(self) -> str:
        return self.selected_sheet_name
    
    def set_selected_sheet_name(self, selected_sheet: str):
        self.selected_sheet_name = selected_sheet


class HeaderRowSelectionModel:
    """Represents the header row selection logic"""
    def __init__(self, header_rows: List[int], suggested_row: int=0):
        self.header_rows = header_rows
        self.selected_header_row = suggested_row
    
    def get_selected_header_row(self) -> int:
        return self.selected_header_row
    
    def set_selected_header_row(self, row: int):
        self.selected_header_row = row