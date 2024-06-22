"""Represents state of Ternary Trace Molar Conversion panel"""

from typing import List, Tuple, Dict, Optional

from molmass import Formula, FormulaError

class TernaryTraceMolarConversionModel:
    
    def __init__(self):
        self.column_chemical_mapping = {}
    
    def add_column(self, col: str):
        # If the column isn't already in the mapping, add it to the dict
        if col not in self.column_chemical_mapping:
            text = ''
            try:
                Formula(col).mass
                text = col
            except FormulaError:
                try:
                    first_part = col.split()[0]
                    Formula(first_part).mass
                    text = first_part
                except FormulaError:
                    if first_part.lower() == 'feot':
                        text = 'FeO'
                except IndexError:
                    pass
            self.column_chemical_mapping[col] = text

    def rem_column(self, col: str):
        # If the col is already in the mapping, remove it
        if col in self.column_chemical_mapping:
            del self.column_chemical_mapping[col]
        
    def update_chemical(self, col: str, value: str):
        if col in self.column_chemical_mapping:
            self.column_chemical_mapping[col] = value

    def get_sorted_repr(self) -> List[Tuple]:
        return sorted(self.column_chemical_mapping.items())
