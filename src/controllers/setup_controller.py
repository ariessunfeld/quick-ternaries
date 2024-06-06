"""Contains the contorller for the base setup model and view

User updates View
View signals to Controller
Controller updates Model
Model updates View

User --> View --> Controller --> Model --> View
"""

from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog, QWidget

from src.models.setup_model import StartSetupModel, CustomHoverDataSelectionModel
from src.models.custom_apex_selection_model import CustomApexSelectionModel

from src.views.start_setup.start_setup_view import StartSetupView
from src.views.start_setup.custom_apex_selection_view import CustomApexSelectionView
from src.views.start_setup.custom_hover_data_selection_view import CustomHoverDataSelectionView

from src.controllers.custom_hover_data_selection_controller import CustomHoverDataSelectionController

from src.utils.file_handling_utils import find_header_row_csv, find_header_row_excel

class CustomApexSelectionController:
    def __init__(self, model: CustomApexSelectionModel, view: CustomApexSelectionView):
        
        # models and views are instantiated outside this class
        # hence, they get passed to the initialization method
        self.model = model
        self.view = view

        self.setup_connections()
        
    def setup_connections(self):
        # Add/remove button connections
        self.view.add_remove_list_top_apex_columns.button_add.clicked.connect(self.clicked_top_apex_button_add)
        self.view.add_remove_list_top_apex_columns.button_remove.clicked.connect(self.clicked_top_apex_button_remove)
        self.view.add_remove_list_right_apex_columns.button_add.clicked.connect(self.clicked_right_apex_button_add)
        self.view.add_remove_list_right_apex_columns.button_remove.clicked.connect(self.clicked_right_apex_button_remove)
        self.view.add_remove_list_left_apex_columns.button_add.clicked.connect(self.clicked_left_apex_button_add)
        self.view.add_remove_list_left_apex_columns.button_remove.clicked.connect(self.clicked_left_apex_button_remove)

    def clicked_top_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's top_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_top_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_top_apex_button_remove(self):
        """Gets selected column from view's top_apex columns,
        adds to model's available columns and removes from model's top_apex columns"""
        selected_column = self.view.add_remove_list_top_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_top_apex_column(col)
            self.model.add_available_column(col)

    def clicked_right_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's right_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_right_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_right_apex_button_remove(self):
        """Gets selected column from view's right_apex columns,
        adds to model's available columns and removes from model's right_apex columns"""
        selected_column = self.view.add_remove_list_right_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_right_apex_column(col)
            self.model.add_available_column(col)

    def clicked_left_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's left_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_left_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_left_apex_button_remove(self):
        """Gets selected column from view's left_apex columns,
        adds to model's available columns and removes from model's left_apex columns"""
        selected_column = self.view.add_remove_list_left_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_left_apex_column(col)
            self.model.add_available_column(col)





class StartSetupController(QWidget):
    def __init__(self, model: StartSetupModel, view: StartSetupView):
        
        super().__init__()

        # models and views are instantiated outside this class
        # hence, they get passed to the initialization method
        self.model = model
        self.view = view
        
        self.setup_connections()

    def setup_connections(self):
        # Connect view.button_add_data to model.data_library.add_data
        self.view.button_add_data.clicked.connect(self.load_data)

        # Connect view's lineEdits' updates to model updates
        self.view.labeled_line_edit_ternary_title.line_edit.textChanged.connect(self.title_changed)
        self.view.labeled_line_edit_top_apex_display_name.line_edit.textChanged.connect(self.top_apex_display_name_changed)
        self.view.labeled_line_edit_right_apex_display_name.line_edit.textChanged.connect(self.right_apex_display_name_changed)
        self.view.labeled_line_edit_left_apex_display_name.line_edit.textChanged.connect(self.left_apex_display_name_changed)

        # Handle changes to the ternary type
        self.view.combobox_ternary_type.currentTextChanged.connect(self.combobox_ternarytype_changed)

        # Set up custom apex selection connections
        self.custom_apex_selection_controller = CustomApexSelectionController(
            self.model.custom_apex_selection_model, 
            self.view.custom_apex_selection_view)
        
        self.custom_hover_data_selection_controller = CustomHoverDataSelectionController(

        )

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
        if filepath.suffix == '.csv':
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

    def combobox_ternarytype_changed(self):
        selected_ternary_type_name = self.view.combobox_ternary_type.currentText()
        selected_ternary_type = self.model.

