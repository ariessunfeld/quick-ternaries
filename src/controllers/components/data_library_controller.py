"""Controller for the Data Library"""


from typing import Tuple, TYPE_CHECKING
from pathlib import Path
import pandas as pd

from PySide6.QtWidgets import QFileDialog, QInputDialog, QWidget, QMessageBox
from PySide6.QtCore import QObject, Signal

from src.models.ternary.setup import TernaryType

from src.controllers.ternary.setup import (
    AdvancedSettingsController,
    TernaryApexScalingController,
    CustomApexSelectionController,
    CustomHoverDataSelectionController
)

from src.utils.file_handling_utils import find_header_row_csv, find_header_row_excel
from src.utils.ternary_types import TERNARY_TYPES

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
            sheet, ok = self.get_sheet(filepath)
            if not ok: 
                return
            header, ok = self.get_header(filepath, sheet)
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
            self.custom_apex_selection_controller.update_columns(shared_columns)
            self.custom_hover_data_selection_controller.update_columns(shared_columns)
            
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

