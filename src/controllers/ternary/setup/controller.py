"""Contains the contorller for the base setup model and view

User updates View
View signals to Controller
Controller updates Model
Model updates View

User --> View --> Controller --> Model --> View
"""

from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog, QWidget, QMessageBox

from src.models.ternary.setup.model import TernaryStartSetupModel
from src.views.ternary.setup.view import TernaryStartSetupView

from src.controllers.ternary.setup.custom_apex_selection_controller import CustomApexSelectionController
from src.controllers.ternary.setup.custom_hover_data_selection_controller import CustomHoverDataSelectionController

from src.utils.file_handling_utils import find_header_row_csv, find_header_row_excel
from src.utils.ternary_types import TERNARY_TYPES


class TernaryStartSetupController(QWidget):

    NO_SHARED_COLUMNS_WARNING = 'Warning: there are no shared column names across all currently loaded data.\n\n' +\
    'Custom apex selection and custom hover data selection will not work.\n\n' +\
    'Remove one or more loaded data files to increase the number of shared column names.'

    def __init__(self, model: TernaryStartSetupModel, view: TernaryStartSetupView):

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

        # Populate the ternary type combobox
        available_ternary_types = [x.name for x in self.model.available_ternary_types]
        self.view.combobox_ternary_type.addItems(available_ternary_types)

        # Handle changes to the ternary type
        self.view.combobox_ternary_type.currentTextChanged.connect(self.combobox_ternarytype_changed)

        # Handle changes to the custom hover data checkbox
        self.view.labeled_checkbox_customize_hover_data.stateChanged.connect(self.checkbox_hoverdata_changed)

        # Set up custom apex selection connections
        self.custom_apex_selection_controller = CustomApexSelectionController(
            self.model.custom_apex_selection_model, 
            self.view.custom_apex_selection_view)

        # Set up custom hover data selection connections
        self.custom_hover_data_selection_controller = CustomHoverDataSelectionController(
            self.model.custom_hover_data_selection_model,
            self.view.custom_hover_data_selection_view
        )

    def load_data(self):
        """Adds user-selected data file to model's data library

        Connected to self.view.button_add_data.clicked
        """
        filepath, _ = QFileDialog.getOpenFileName(None, "Open data file", "", "Data Files (*.csv *.xlsx)")
        if filepath:
            sheet = self.get_sheet(filepath)  # ask user to pick sheet
            header = self.get_header(filepath, sheet)  # ask user to pick header row
            self.model.data_library.add_data(filepath, sheet, header)  # add data to library
            loaded_data = self.model.data_library.get_all_filenames()  # get all loaded data
            self.view.loaded_data_scroll_view.clear()  # clear the loaded data view
            for _shortname, _sheet, _path in loaded_data:  # repopulate with disambiguated names
                list_item, close_button = self.view.loaded_data_scroll_view.add_item(_shortname, _path)
                close_button.clicked.connect(lambda _p=_path, _s=_sheet: self.remove_data(list_item, _p, _s))
            shared_columns = self.model.data_library.get_shared_columns()
            self.custom_apex_selection_controller.update_columns(shared_columns)
            self.custom_hover_data_selection_controller.update_columns(shared_columns)
            if not shared_columns:
                QMessageBox.warning(
                    self.view, 
                    'No shared columns', 
                    self.NO_SHARED_COLUMNS_WARNING)

    def remove_data(self, item, filepath, sheet):
        if QMessageBox.question(
            self.view, 
            'Confirm Delete', 
            "Do you really want to remove this data?") \
        == QMessageBox.Yes:
            self.model.data_library.remove_data(filepath, sheet)  # remove data from library
            self.view.loaded_data_scroll_view.clear()  # clear loaded data view
            loaded_data = self.model.data_library.get_all_filenames()  # repopulate from library
            for _shortname, _sheet, _path in loaded_data:
                list_item, close_button = self.view.loaded_data_scroll_view.add_item(_shortname, _path)
                close_button.clicked.connect(lambda _p=_path, _s=_sheet: self.remove_data(list_item, _p, _s))
            shared_columns = self.model.data_library.get_shared_columns()  # update custom apex selection and hoverdata
            self.custom_apex_selection_controller.update_columns(shared_columns)  # with shared columns
            self.custom_hover_data_selection_controller.update_columns(shared_columns)

    def get_sheet(self, filepath: str) -> str|None:
        """Prompts user to select a sheet name for a data file"""
        filepath = Path(filepath)
        if filepath.suffix == '.csv':
            return None
        elif filepath.suffix == '.xlsx':
            xlsx_file = pd.ExcelFile(filepath)
            sheet_names = xlsx_file.sheet_names
            if len(sheet_names) > 1:
                chosen_sheet, _ = QInputDialog.getItem(
                    self, 
                    "Select Excel Sheet", 
                    f"Choose a sheet from {Path(filepath).name}", 
                    sheet_names, 0, False)
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
        """
        Update the model so it knows the current selected ternary type
        If 'Custom' is selected, make the custom apex selection view visible
        Otherwise, ensure it is invisible
        """
        selected_ternary_type_name = self.view.combobox_ternary_type.currentText()
        selected_ternary_type = [x for x in TERNARY_TYPES if x['name'] == selected_ternary_type_name][0]
        self.model.set_selected_ternary_type(selected_ternary_type)
        if selected_ternary_type_name == 'Custom':
            self.view.update_custom_apex_selection_view_visibility(True)
        else:
            self.view.update_custom_apex_selection_view_visibility(False)

    def checkbox_hoverdata_changed(self):
        """
        Update the model so it knows the current state of the checkbox
        If checked, set Custom Hover Data Selection View to visible
        Else, set to invisible
        """
        is_checked = self.view.labeled_checkbox_customize_hover_data.isChecked()
        self.model.custom_hover_data_is_checked = is_checked
        self.view.update_custom_hover_data_selection_view_visibility(is_checked)
