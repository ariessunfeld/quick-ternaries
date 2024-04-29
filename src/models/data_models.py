"""Contains models representing data objects (files, libraries)"""

from typing import Dict

import pandas as pd
from pathlib import Path

class DataFile:
    def __init__(self, filepath: str|Path, sheet: str=None, header: int=0):
        """Parses dataframe from CSV or XLSX file, given sheet and header"""
        self.filepath: Path = Path(filepath)
        self.name: str = self.filepath.name
        self.stem: str = self.filepath.stem
        self.parent: Path = self.filepath.parent
        self.suffix: str = self.filepath.suffix
        self.sheet: str = sheet
        self.header: int = header
        self.data: pd.DataFrame = self.parse_data(self.filepath, sheet, header, self.suffix)
        self.n_columns = len(self.data.columns)

    def parse_data(self, filepath: Path, sheet: str, header: int, suffix: str) -> pd.DataFrame:
        if suffix == '.csv':
            return self.parse_csv(filepath, header)
        elif suffix == '.xlsx': # TODO add support for .xls if possible
            return self.parse_xlsx(filepath, sheet, header)
        else:
            raise ValueError(f'Unsupported data type: {suffix}')
        
    def parse_csv(self, filepath, header) -> pd.DataFrame:
        return pd.read_csv(filepath, header=header)
    
    def parse_xlsx(self, filepath, sheet, header) -> pd.DataFrame:
        xlsx_file = pd.ExcelFile(filepath)
        return xlsx_file.parse(sheet_name=sheet, header=header)
    
    def get_data(self) -> pd.DataFrame:
        return self.data
    
    def get_columns(self, n=-1) -> list:
        """Returns up to the first n columns of self.data. If n == -1, returns all columns"""
        if n == 1:
            return list(self.data.columns)
        return list(self.data.columns[:min(self.n_columns, n)])

class DataLibrary:
    def __init__(self):
        self.data_library: Dict[int, DataFile] = {}

    def hash_function(self, filepath: str, sheet: str|None=None):
        return hash(f'{filepath}{sheet}') # Unique up to filepath/sheet combination

    def add_data(self, filepath: str, sheet: str|None=None, header: int=0):
        data = DataFile(filepath, sheet, header)
        key = self.hash_function(filepath, sheet)
        self.data_library[key] = data

    def remove_data(self, filepath: str, sheet: str|None=None):
        key = self.hash_function(filepath, sheet)
        del self.data_library[key]

    def get_data(self, filepath: str, sheet: str|None=None) -> DataFile:
        key = self.hash_function(filepath, sheet)
        if key in self.data_library:
            return self.data_library[key]
        else:
            return None
