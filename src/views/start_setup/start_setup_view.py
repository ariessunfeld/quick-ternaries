"""Contains the BaseSetupView(QWidget) class, which encompasses the widgets involved in setup, and is used in the dynamic content area of the MainWindow"""

from typing import List

from src.views.utils.add_remove_list import AddRemoveList
from src.views.utils.left_labeled_checkbox import LeftLabeledCheckbox
from src.views.utils.left_labeled_line_edit import LeftLabeledLineEdit
from src.views.start_setup.custom_apex_selection_view import CustomApexSelectionView
from src.views.start_setup.custom_hover_data_selection_view import CustomHoverDataSelectionView
from src.views.start_setup.loaded_data_scroll_view import LoadedDataScrollView

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QListWidget,
    QComboBox,
    QCheckBox
)

class StartSetupView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMaximumWidth(500)

        # Scroll area to display filenames for loaded data
        self.loaded_data_scroll_view = LoadedDataScrollView()

        # Button to click to load data from computer
        self.button_add_data = QPushButton('Add Data')

        # Combobox to select ternary type
        self.combobox_ternary_type: QComboBox = QComboBox()

        # Menu with columns for each apex, only displayed if combobox choice is "Custom"
        self.custom_apex_selection_view = CustomApexSelectionView()
        self.custom_apex_selection_view.setVisible(False)  # Hide the CustomApexSelectionView at first

        # Line-edits for title, top apex name, left apex name, right apex name
        self.labeled_line_edit_ternary_title = \
            LeftLabeledLineEdit('Title:')
        self.labeled_line_edit_top_apex_display_name = \
            LeftLabeledLineEdit('Top Apex (display name):')
        self.labeled_line_edit_right_apex_display_name = \
            LeftLabeledLineEdit('Right Apex (display name):')
        self.labeled_line_edit_left_apex_display_name = \
            LeftLabeledLineEdit('Left Apex (display name):')

        # Checkbox for whether to customize the hover-over metadata
        self.labeled_checkbox_customize_hover_data = \
            LeftLabeledCheckbox('Customize Cursor-Hover Data:')
        
        # Menu for picking columns from available data for displaying as metadata
        self.custom_hover_data_selection_view = \
            CustomHoverDataSelectionView()
        self.custom_hover_data_selection_view.setVisible(False) # Hide the CustomApexSelectionView at first

        # Add widgets to the layout
        self.layout.addWidget(self.loaded_data_scroll_view)
        self.layout.addWidget(self.button_add_data)
        self.layout.addWidget(self.combobox_ternary_type)
        self.layout.addWidget(self.custom_apex_selection_view)
        self.layout.addWidget(self.labeled_line_edit_ternary_title)
        self.layout.addWidget(self.labeled_line_edit_top_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_right_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_left_apex_display_name)
        self.layout.addWidget(self.labeled_checkbox_customize_hover_data)
        self.layout.addWidget(self.custom_hover_data_selection_view)


    def update_loaded_data_scroll_view(self, update):
        pass

    def update_custom_apex_selection_view_visibility(self, is_visible: bool):
        self.custom_apex_selection_view.setVisible(is_visible)

    def update_custom_hover_data_selection_view_visibility(self, is_visible: bool):
        self.custom_hover_data_selection_view.setVisible(is_visible)
