"""Contains models representing data objects (files, libraries)"""

from typing import Dict, List, Tuple
from collections import defaultdict

import pandas as pd
from pathlib import Path

class DataFile:
    def __init__(self, filepath: str|Path, sheet: str=None, header: int=0, parse=True):
        """Parses dataframe from CSV or XLSX file, given sheet and header"""
        self.filepath: Path = Path(filepath)
        self.name: str = self.filepath.name
        self.stem: str = self.filepath.stem
        self.parent: Path = self.filepath.parent
        self.suffix: str = self.filepath.suffix
        self.sheet: str = sheet
        self.header: int = header
        if parse:
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
        if n == -1:
            return list(self.data.columns)
        return list(self.data.columns[:min(self.n_columns, n)])

class DataLibrary:
    def __init__(self):
        self.data_library: Dict[int, DataFile] = {}
        self.disambiguation_list = None

    def hash_function(self, filepath: str, sheet: str|None=None):
        return hash(f'{filepath}{sheet}') # Unique up to filepath/sheet combination

    def add_data(self, filepath: str, sheet: str|None=None, header: int=0, parse=True):
        data = DataFile(filepath, sheet, header, parse=parse)
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
        
    def get_all_filenames(self) -> List[str]:
        """Returns minimally disambiguated list of filename/sheet strings for all files in library"""
        # Step 1: Extract filenames and sheets
        name_sheet_list = [(df.name, df.sheet, df.filepath) for df in self.data_library.values()]
        
        # Step 2: Identify duplicate filenames
        name_count = defaultdict(int)
        for name, _, _ in name_sheet_list:
            name_count[(name,)] += 1
        
        # Step 3: Identify minimal disambiguating paths
        def find_minimal_prefix(paths: List[Path]) -> List[str]:
            all_parts = [path.parts[:-1] for path in paths]  # Exclude the filename part
            num_paths = len(paths)
            max_depth = max(len(parts) for parts in all_parts)
            unique_prefixes = [''] * num_paths
            ambiguous_paths = list(range(num_paths))

            for depth in range(1, max_depth + 1):
                if not ambiguous_paths:
                    break

                current_prefixes = [
                    '/'.join(all_parts[i][-depth:])
                    if i in ambiguous_paths
                    else unique_prefixes[i]
                    for i in range(num_paths)
                ]

                seen = set()
                duplicates = set()
                for i in ambiguous_paths:
                    prefix = current_prefixes[i]
                    if prefix in seen:
                        duplicates.add(prefix)
                    else:
                        seen.add(prefix)

                ambiguous_paths = [i for i in ambiguous_paths if current_prefixes[i] in duplicates]
                for i in range(num_paths):
                    if i not in ambiguous_paths:
                        unique_prefixes[i] = current_prefixes[i]

            return unique_prefixes

        disambiguation_map = defaultdict(list)
        for name, _, path in name_sheet_list:
            if name_count[(name,)] > 1:
                disambiguation_map[(name,)].append(path)

        minimal_paths = {}
        for key, paths in disambiguation_map.items():
            unique_prefixes = find_minimal_prefix(paths)
            for path, prefix in zip(paths, unique_prefixes):
                minimal_paths[(path, key)] = prefix

        # Step 4: Prepare the result list with necessary disambiguation
        result = []
        for name, sheet, path in name_sheet_list:
            if name_count[(name,)] > 1:
                disambiguated_name = f".../{minimal_paths[(path, (name,))]}/{name}"
                if sheet is not None:
                    disambiguated_name += f" | {sheet}"
                result.append((disambiguated_name, sheet, path))
            else:
                to_append = f"{name}"
                if sheet is not None:
                    to_append += f" | {sheet}"
                result.append((to_append, sheet, path))
        
        # Update the disambiguation list
        self.disambiguation_list = result
        return result
    
    def get_data_from_shortname(self, shortname: str) -> DataFile|None:
        """Returns the DataFile associated with the shortname, or None"""
        for entry in self.disambiguation_list:
            name, sheet, path = entry
            if name == shortname:
                return self.get_data(path, sheet)
        return None
    
    def list_all_datafiles(self):
        return list(self.data_library.values())



# Example usage:
if __name__ == "__main__":
    lib = DataLibrary()
    lib.add_data('/Users/username/Downloads/Mars/Docs/marsdata/data.csv', 'Sheet 1', parse=False)
    lib.add_data('/Users/username/Downloads/Venus/marsdata/data.csv', 'Sheet 2', parse=False)
    lib.add_data('/Users/username/Downloads/labdata/data.csv', 'Sheet 1', parse=False)
    lib.add_data('/Users/username/Downloads/labdata/otherdata.csv', 'Sheet 1', parse=False)
    for x in (lib.get_all_filenames()):
        print(x)