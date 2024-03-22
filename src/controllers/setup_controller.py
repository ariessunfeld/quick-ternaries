"""Contains the contorller for the base setup model and view

User updates View
View signals to Controller
Controller updates Model
Model updates View

User --> View --> Controller --> Model --> View
"""

from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog

from models.setup_model import BaseSetupModel
from views.setup_view import BaseSetupView
from utils.file_handling_utils import find_header_row_csv, find_header_row_excel

class BaseSetupController:
    def __init__(self, model: BaseSetupModel, view: BaseSetupView):
        
        self.model = model
        self.view = view
        
        # Connect view.button_add_data to model.data_library.add_data
        self.view.button_add_data.clicked.connect(self.load_data)

        # Connect view's lineEdits' updates to model updates
        self.view.labeled_line_edit_ternary_title.line_edit.textChanged.connect(self.title_changed)
        self.view.labeled_line_edit_top_apex_display_name.line_edit.textChanged.connect(self.top_apex_display_name_changed)
        self.view.labeled_line_edit_right_apex_display_name.line_edit.textChanged.connect(self.right_apex_display_name_changed)
        self.view.labeled_line_edit_left_apex_display_name.line_edit.textChanged.connect(self.left_apex_display_name_changed)

        # Connect view's CustomApexSelectionView add buttons to view and model updates
        self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.button_add.clicked.connect(self.top_apex_custom_add_clicked)
        self.view.custom_apex_selection_view.add_remove_list_right_apex_columns.button_add.clicked.connect(self.right_apex_custom_add_clicked)
        self.view.custom_apex_selection_view.add_remove_list_left_apex_columns.button_add.clicked.connect(self.left_apex_custom_add_clicked)

        self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.button_remove.clicked.connect(self.top_apex_custom_remove_clicked)

    def load_data(self):
        """Adds user-selected data file to model's data library
        
        Connected to self.view.button_add_data.clicked
        """
        filepath, ok = QFileDialog.getOpenFileName(None, "Open data file", "", "Data Files (*.csv *.xlsx)")
        if filepath:
            sheet = self.get_sheet(filepath)
            header = self.get_header(filepath, sheet)
            self.model.data_library.add_data(filepath, sheet, header)
            
    def get_sheet(self, filepath: str) -> str|None:
        """Prompts user to select a sheet name for a data file"""
        filepath = Path(filepath)
        if filepath.sufffix == '.csv':
            return None
        elif filepath.suffix == '.xlsx':
            xlsx_file = pd.ExcelFile(filepath)
            sheet_names = xlsx_file.sheet_names
            if len(sheet_names) > 1:
                chosen_sheet, _ = QInputDialog.getItem(self, "Select Excel Sheet", f"Choose a sheet from {Path(filepath).name}", sheet_names, 0, False)
                return chosen_sheet
            else:
                return sheet_names[0]
        else:
            raise ValueError(f"Unsupported filetype: {filepath.suffix}")
            
    def get_header(self, filepath: str, sheet: str) -> str|None:
        """Returns the user-selected header row for filepath"""
        filepath = Path(filepath)
        if filepath.suffix == '.csv':
            suggested_header = find_header_row_csv(filepath, 16)
            _df = pd.read_csv(filepath, header=0)
            return self.select_header(filepath, _df, suggested_header)
        elif filepath.suffix == '.xlsx':
            suggested_header = find_header_row_excel(filepath, 16, sheet)
            excel_file = pd.ExcelFile(filepath)
            _df = excel_file.parse(sheet, header=0)
            return self.select_header(filepath, _df, suggested_header)
        else:
            raise ValueError(f"Unsupported filetype: {filepath.suffix}")
        
    def select_header(self, filepath: str|Path|None, df: pd.DataFrame, suggested_header:int=0):
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
        chosen_header, _ = QInputDialog.getItem(  # Ask the user to pick a row
            self, "Select Header Row", 
            f"Choose a header row from {Path(filepath).name}", 
            column_info_display, suggested_header, False)
        return parse_header_val_from_choice(chosen_header)

    
    def update_text(self):
        pass
        # Connected to text-update signal from BaseSetupView
        # This is an optimistic method that would allow efficient and rapid
        # updating of ternary in GUI if there's a way to update title without
        # re-rendering (which there probably is with update_layout or something like that)
    
    def title_changed(self):
        self.model.set_title(self.view.labeled_line_edit_ternary_title.line_edit.text())

    def top_apex_display_name_changed(self):
        self.model.set_top_apex_display_name(self.view.labeled_line_edit_top_apex_display_name.line_edit.text())
    
    def right_apex_display_name_changed(self):
        self.model.set_right_apex_display_name(self.view.labeled_line_edit_right_apex_display_name.line_edit.text())
    
    def left_apex_display_name_changed(self):
        self.model.set_left_apex_display_name(self.view.labeled_line_edit_left_apex_display_name.line_edit.text())

    # TODO refactor methods below so that controller ONLY updates model, not also view
        
    def top_apex_custom_add_clicked(self):
        # Get current item
        current_item = self.view.custom_apex_selection_view.list_widget_available_columns.currentItem()
        # Make sure not None
        if current_item is None:
            return
        # Make sure not already in list
        if current_item.text() in self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.get_items():
            return
        # Get row for current item
        current_row = self.view.custom_apex_selection_view.list_widget_available_columns.row(current_item)
        # Remove item from available columns
        self.view.custom_apex_selection_view.list_widget_available_columns.takeItem(current_row)
        # Add item to top apex list
        self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.list.addItem(current_item)
        # Update model
        self.model.custom_apex_selection_model.add_top_apex_column(current_item.text())
        self.model.custom_apex_selection_model.remove_available_column(current_item.text())

    def left_apex_custom_add_clicked(self):
        # Get current item
        current_item = self.view.custom_apex_selection_view.list_widget_available_columns.currentItem()
        # Make sure not None
        if current_item is None:
            return
        # Make sure not already in list
        if current_item.text() in self.view.custom_apex_selection_view.add_remove_list_left_apex_columns.get_items():
            return
        # Get row for current item
        current_row = self.view.custom_apex_selection_view.list_widget_available_columns.row(current_item)
        # Remove item from available columns
        self.view.custom_apex_selection_view.list_widget_available_columns.takeItem(current_row)
        # Add item to left apex list
        self.view.custom_apex_selection_view.add_remove_list_left_apex_columns.list.addItem(current_item)
        # Update model
        self.model.custom_apex_selection_model.add_left_apex_column(current_item.text())
        self.model.custom_apex_selection_model.remove_available_column(current_item.text())

    def right_apex_custom_add_clicked(self):
        # Get current item
        current_item = self.view.custom_apex_selection_view.list_widget_available_columns.currentItem()
        # Make sure not None
        if current_item is None:
            return
        # Make sure not already in list
        if current_item.text() in self.view.custom_apex_selection_view.add_remove_list_right_apex_columns.get_items():
            return
        # Get row for current item
        current_row = self.view.custom_apex_selection_view.list_widget_available_columns.row(current_item)
        # Remove item from available columns
        self.view.custom_apex_selection_view.list_widget_available_columns.takeItem(current_row)
        # Add item to right apex list
        self.view.custom_apex_selection_view.add_remove_list_right_apex_columns.list.addItem(current_item)
        # Update model
        self.model.custom_apex_selection_model.add_right_apex_column(current_item.text())
        self.model.custom_apex_selection_model.remove_available_column(current_item.text())

    def top_apex_custom_remove_clicked(self):
        # Get the selected item to remove
        current_item = self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.list.currentItem()
        if current_item is not None:
            # Get row for item
            current_row = self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.list.row(current_item)
            # Remove from list using row
            self.view.custom_apex_selection_view.add_remove_list_top_apex_columns.list.takeItem(current_row)
            # Update model
            self.model.custom_apex_selection_model.remove_top_apex_column(current_item.text())
            self.model.custom_apex_selection_model.add_available_column(current_item.text())
            # Add to available columns list if not already there
            if current_item.text() not in self.view.custom_apex_selection_view.list_widget_available_columns.get_items():
                self.view.custom_apex_selection_view.list_widget_available_columns.addItem(current_item)
                # Sort available columns list
                self.view.custom_apex_selection_view.list_widget_available_columns.sortItems()
                
    