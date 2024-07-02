"""Contains the contorller for the base setup model and view

User updates View
View signals to Controller
Controller updates Model
Model updates View

User --> View --> Controller --> Model --> View
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog, QWidget, QMessageBox
from PySide6.QtCore import QObject, Signal

from src.models.ternary.setup.model import TernaryStartSetupModel, TernaryType
from src.views.ternary.setup.view import TernaryStartSetupView

from src.controllers.ternary.setup.custom_apex_selection_controller import CustomApexSelectionController
from src.controllers.ternary.setup.custom_hover_data_selection_controller import CustomHoverDataSelectionController
from src.controllers.ternary.setup.apex_scaling_controller import TernaryApexScalingController

from src.utils.file_handling_utils import find_header_row_csv, find_header_row_excel
from src.utils.ternary_types import TERNARY_TYPES


class TernaryStartSetupControllerSignaller(QObject):

    remove_data_signal = Signal(tuple)

    apex_column_added = Signal(str)
    apex_column_removed = Signal(str)

    def __init__(self):
        super().__init__()
    


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

        self.signaller = TernaryStartSetupControllerSignaller()
        
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

        # Handle changes to the scale apices checkbox
        self.view.labeled_checkbox_scale_apices.stateChanged.connect(self.checkbox_scale_apices_changed)

        # Set up custom apex selection connections
        self.custom_apex_selection_controller = CustomApexSelectionController(
            self.model.custom_apex_selection_model, 
            self.view.custom_apex_selection_view)
        
        # Set up custom hover data selection connections
        self.custom_hover_data_selection_controller = CustomHoverDataSelectionController(
            self.model.custom_hover_data_selection_model,
            self.view.custom_hover_data_selection_view)

        # Thread the custom apex selection signals through this controller
        self.custom_apex_selection_controller.column_added_to_apices.connect(
            lambda s: self.signaller.apex_column_added.emit(s))
        self.custom_apex_selection_controller.column_removed_from_apices.connect(
            lambda s: self.signaller.apex_column_removed.emit(s))
        
        # Connect custom apex add/remove to updating ternary type
        self.custom_apex_selection_controller.column_added_to_apices.connect(
            self._set_custom_ternary_type)
        self.custom_apex_selection_controller.column_removed_from_apices.connect(
            self._set_custom_ternary_type)
        
        # Set up apex scaling controller and connections
        self.apex_scaling_controller = TernaryApexScalingController(
            self.model.apex_scaling_model,
            self.view.apex_scaling_view)
        
        self.signaller.apex_column_added.connect(self.apex_scaling_controller.on_new_custom_column_added)
        self.signaller.apex_column_added.connect(self.checkbox_scale_apices_changed)
        self.signaller.apex_column_removed.connect(self.apex_scaling_controller.on_new_custom_column_removed)
        self.signaller.apex_column_removed.connect(self.checkbox_scale_apices_changed)

    def load_data(self):
        """Adds user-selected data file to model's data library

        Connected to self.view.button_add_data.clicked
        """
        filepath, ok = QFileDialog.getOpenFileName(None, "Open data file", "", "Data Files (*.csv *.xlsx)")
        if filepath:
            sheet, ok = self.get_sheet(filepath)  # ask user to pick sheet
            if not ok: return
            header, ok = self.get_header(filepath, sheet)  # ask user to pick header row
            if not ok: return
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

    def remove_data(self, item, filepath: str, sheet: str):
        """Callback when user tries to remove data
        Prompts user to double-check; if user says okay, emits signal
        Signal gets caught by ternary controller which checks if traces need to be deleted
        """
        if QMessageBox.question(
            self.view, 
            'Confirm Delete', 
            "Do you really want to remove this data?") \
        == QMessageBox.Yes:
            # Signal so the ternary controller can see
            self.signaller.remove_data_signal.emit((filepath, sheet))

    def on_remove_data_confirmed(self, filepath: str, sheet: str):
        # Gets triggered by ternary controller
        self.model.data_library.remove_data(filepath, sheet)  # remove data from library
        self.view.loaded_data_scroll_view.clear()  # clear loaded data view
        loaded_data = self.model.data_library.get_all_filenames()  # repopulate from library
        for _shortname, _sheet, _path in loaded_data:
            list_item, close_button = self.view.loaded_data_scroll_view.add_item(_shortname, _path)
            close_button.clicked.connect(lambda _p=_path, _s=_sheet: self.remove_data(list_item, _p, _s))
        shared_columns = self.model.data_library.get_shared_columns()  # update custom apex selection and hoverdata
        self.custom_apex_selection_controller.update_columns(shared_columns)  # with shared columns
        self.custom_hover_data_selection_controller.update_columns(shared_columns)

    def get_sheet(self, filepath: str) -> Tuple[str|None, bool]:
        """Prompts user to select a sheet name for a data file"""
        filepath = Path(filepath)
        if filepath.suffix == '.csv':
            return None, True
        elif filepath.suffix == '.xlsx':
            xlsx_file = pd.ExcelFile(filepath)
            sheet_names = xlsx_file.sheet_names
            if len(sheet_names) > 1:
                chosen_sheet, ok = QInputDialog.getItem(
                    None, 
                    "Select Excel Sheet", 
                    f"Choose a sheet from {Path(filepath).name}", 
                    sheet_names, 0, False)
                return chosen_sheet, ok
            else:
                return sheet_names[0], True
        else:
            raise ValueError(f"Unsupported filetype: {filepath.suffix}")
            
    def get_header(self, filepath: str, sheet: str) -> Tuple[str|None, bool]:
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
        
    def select_header(
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
            column_info_display, suggested_header, False)
        return parse_header_val_from_choice(chosen_header), ok

    
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
        if selected_ternary_type_name == 'Custom':
            self._set_custom_ternary_type()
            self.view.update_custom_apex_selection_view_visibility(True)
            self.view.labeled_checkbox_scale_apices.setEnabled(True)
            self.view.update_scale_apices_view_visibility(self.view.labeled_checkbox_scale_apices.isChecked())
        else:
            selected_ternary_type = [x for x in TERNARY_TYPES if x['name'] == selected_ternary_type_name][0]
            selected_ternary_type = TernaryType(**selected_ternary_type)
            self.model.set_selected_ternary_type(selected_ternary_type)
            self.view.update_custom_apex_selection_view_visibility(False)
            self.view.labeled_checkbox_scale_apices.setEnabled(False)
            self.view.labeled_checkbox_scale_apices.setChecked(False)
            self.view.update_scale_apices_view_visibility(self.view.labeled_checkbox_scale_apices.isChecked())

    def checkbox_hoverdata_changed(self):
        """
        Update the model so it knows the current state of the checkbox
        If checked, set Custom Hover Data Selection View to visible
        Else, set to invisible
        """
        is_checked = self.view.labeled_checkbox_customize_hover_data.isChecked()
        self.model.custom_hover_data_is_checked = is_checked
        self.view.update_custom_hover_data_selection_view_visibility(is_checked)

    def checkbox_scale_apices_changed(self):
        is_checked = self.view.labeled_checkbox_scale_apices.isChecked()
        self.model.scale_apices_is_checked = is_checked
        self.view.update_scale_apices_view_visibility(is_checked)

    def _set_custom_ternary_type(self):
        self.model.set_selected_ternary_type(
            TernaryType(
                **{
                    'name': 'Custom',
                    'top': self.model.custom_apex_selection_model.get_top_apex_selected_columns(),
                    'left': self.model.custom_apex_selection_model.get_left_apex_selected_columns(),
                    'right': self.model.custom_apex_selection_model.get_right_apex_selected_columns()
                }
            )
        )
