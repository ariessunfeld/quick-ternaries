"""Controller for the Data Library"""


from typing import Tuple, TYPE_CHECKING
from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PySide6.QtCore import QObject, Signal

from src.utils.file_handling_utils import find_header_row_csv, find_header_row_excel

if TYPE_CHECKING:
    from src.models.utils import DataLibrary
    from src.views.components import DataLibraryView

class DataLibraryController(QObject):

    remove_data_signal = Signal(tuple)
    shared_columns_signal = Signal(list)

    NO_SHARED_COLUMNS_WARNING = (
        'Warning: there are no shared column names across all currently loaded' 
        ' data.\n\nCustom apex selection and custom hover data selection will '
        'not work.\n\nRemove one or more loaded data files to increase the num'
        'ber of shared column names.'
    )

    def __init__(self, model: 'DataLibrary', view: 'DataLibraryView'):
        super().__init__()

        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.add_data_button.clicked.connect(self._on_add_data_clicked)

    def _on_add_data_clicked(self, event):
        self._load_data()

    def _load_data(self):
        """Adds user-selected data file to model's data library

        Connected to self.loaded_data_scroll_view.add_data_button.clicked
        """
        filepath, ok = QFileDialog.getOpenFileName(
            None, 
            "Open data file", 
            "", 
            "Data Files (*.csv *.xlsx)")
        if filepath:
            sheet, ok = self._get_sheet(filepath)
            if not ok: 
                return
            header, ok = self._get_header(filepath, sheet)
            if not ok: 
                return
            self.model.add_data(filepath, sheet, header)  # add data to library
            
            loaded_data = self.model.get_all_filenames()  # get all loaded data
            self.view.clear()  # clear the loaded data view
            
            for _shortname, _sheet, _path in loaded_data:  # repopulate with disambiguated names
                list_item, close_button = self.view.add_item(_shortname, _path)
                close_button.clicked.connect(lambda _p=_path, _s=_sheet: self._remove_data(list_item, _p, _s))
            
            shared_columns = self.model.get_shared_columns()
            
            # TODO emit some signal with these columns
            self.shared_columns_signal.emit(shared_columns)
            # self.custom_apex_selection_controller.update_columns(shared_columns)
            # self.custom_hover_data_selection_controller.update_columns(shared_columns)
            
            if not shared_columns:
                QMessageBox.warning(
                    self.view, 
                    'No shared columns', 
                    self.NO_SHARED_COLUMNS_WARNING)
                
    def _remove_data(self, item, filepath: str, sheet: str):
        """
        Callback when user tries to remove data

        Prompts user to double-check; if user says okay, emits signal.
        Signal gets caught by ternary controller which checks if traces need to be deleted
        """
        if QMessageBox.question(
            self.view, 
            'Confirm Delete', 
            "Do you really want to remove this data?") \
        == QMessageBox.Yes:
            # Signal so the ternary controller can see
            self.remove_data_signal.emit((filepath, sheet))

    def _get_sheet(self, filepath: str) -> Tuple[str|None, bool]:
        """Prompts user to select a sheet name for a data file"""
        filepath = Path(filepath)
        if filepath.suffix.lower() == '.csv':
            return None, True
        elif filepath.suffix.lower() == '.xlsx':
            xlsx_file = pd.ExcelFile(filepath)
            sheet_names = xlsx_file.sheet_names
            if len(sheet_names) > 1:
                chosen_sheet, ok = QInputDialog.getItem(
                    None, 
                    "Select Excel Sheet", 
                    f"Choose a sheet from {Path(filepath).name}", 
                    sheet_names, 
                    0, 
                    False)
                return chosen_sheet, ok
            else:
                return sheet_names[0], True
        else:
            raise ValueError(f"Unsupported filetype: {filepath.suffix}")
        
    def _get_header(self, filepath: str, sheet: str) -> Tuple[str|None, bool]:
        """Returns the user-selected header row for filepath"""
        filepath = Path(filepath)
        if filepath.suffix.lower() == '.csv':
            suggested_header = find_header_row_csv(filepath, 16)
            _df = pd.read_csv(filepath, header=0)
            return self._select_header(filepath, _df, suggested_header)
        elif filepath.suffix.lower() == '.xlsx':
            suggested_header = find_header_row_excel(filepath, 16, sheet)
            excel_file = pd.ExcelFile(filepath)
            _df = excel_file.parse(sheet, header=0)
            return self._select_header(filepath, _df, suggested_header)
        else:
            raise ValueError(f"Unsupported filetype: {filepath.suffix}")
        
    def _select_header(
            self, 
            filepath: str|Path|None, 
            df: pd.DataFrame, 
            suggested_header: int=0) -> Tuple[str|None, bool]:
        """Prompts user to select a header row for filepath"""
        
        def parse_header_val_from_choice(choice: str):
            """Utility function for parsing user choice from input dialog repr"""
            # choices are 1-index for readability
            return int(choice.split('|')[0].split()[1].strip()) - 1
        
        max_columns_to_display = 8 # to display in input dialog
        max_rows_to_display = 16

        column_info = {} # integer keys, list[str] values
        first_row = list(df.columns)  # Get the columns for the first row
        first_row = first_row[:min(len(first_row), max_columns_to_display)]
        column_info[0] = first_row  # Store them in the dictionary
        for row in range(min(max_rows_to_display, len(df))):  # Get the columns for the next few rows
            colnames =  list(df.iloc[row])
            column_info[row+1] = colnames[:min(max_columns_to_display, len(colnames))]
        column_info_display = [  # Format the column/row pairs for display
            f'Row {k+1} | Columns: {", ".join(str(c) for c in v)}' for k, v in sorted(column_info.items())]
        chosen_header, ok = QInputDialog.getItem(  # Ask the user to pick a row
            None, 
            "Select Header Row", 
            f"Choose a header row from {Path(filepath).name}", 
            column_info_display, 
            suggested_header, 
            False)
        return parse_header_val_from_choice(chosen_header), ok

    def remove_data(self, filepath: str, sheet: str):
        """Public method for removing data
        
        Gets called by parent controller when user confirms removal intent
        """
        self.model.data_library.remove_data(filepath, sheet)
        self.view.clear()
        loaded_data = self.model.get_all_filenames()
        for _shortname, _sheet, _path in loaded_data:
            list_item, close_button = self.view.add_item(_shortname, _path)
            close_button.clicked.connect(lambda _p=_path, _s=_sheet: self._remove_data(list_item, _p, _s))
        shared_columns = self.model.get_shared_columns()  # update custom apex selection and hoverdata
        
        # TODO emit signal here rather than performing direct update
        self.shared_columns_signal.emit(shared_columns)
        # self.custom_apex_selection_controller.update_columns(shared_columns)  # with shared columns
        # self.custom_hover_data_selection_controller.update_columns(shared_columns)
