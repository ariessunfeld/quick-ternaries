"""Contains the BaseSetupView(QWidget) class, which encompasses the widgets involved in setup, and is used in the dynamic content area of the MainWindow"""

from typing import List

from src.views.utils.left_labeled_checkbox import LeftLabeledCheckbox
from src.views.utils.left_labeled_line_edit import LeftLabeledLineEdit
from src.views.ternary.setup import CustomApexSelectionView
from src.views.ternary.setup import CustomHoverDataSelectionView
from src.views.ternary.setup import LoadedDataScrollView

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QScrollArea
)

class TernaryStartSetupView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        #self.setMaximumWidth(500)

        # Scroll area to hold the content layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget to hold all the content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.scroll_area.setWidget(self.content_widget)

        # Scroll area to display filenames for loaded data
        self.loaded_data_scroll_view = LoadedDataScrollView()

        # Button to click to load data from computer
        self.button_add_data = QPushButton('Add Data')

        # Combobox to select ternary type
        self.combobox_ternary_type: QComboBox = QComboBox()

        # Menu with columns for each apex, only displayed if
        # combobox choice is "Custom"
        self.custom_apex_selection_view = CustomApexSelectionView()
        # Hide the CustomApexSelectionView at first
        self.custom_apex_selection_view.setVisible(False)

        # Line-edits for title, top apex name, left apex name,
        # right apex name
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

        # Menu for picking columns from available data for
        # displaying as metadata
        self.custom_hover_data_selection_view = \
            CustomHoverDataSelectionView()
        # Hide the CustomApexSelectionView at first
        self.custom_hover_data_selection_view.setVisible(False)

        # Add widgets to the content layout
        self.content_layout.addWidget(self.loaded_data_scroll_view)
        self.content_layout.addWidget(self.button_add_data)
        self.content_layout.addWidget(self.combobox_ternary_type)
        self.content_layout.addWidget(self.custom_apex_selection_view)
        self.content_layout.addWidget(self.labeled_line_edit_ternary_title)
        self.content_layout.addWidget(self.labeled_line_edit_top_apex_display_name)
        self.content_layout.addWidget(self.labeled_line_edit_right_apex_display_name)
        self.content_layout.addWidget(self.labeled_line_edit_left_apex_display_name)
        self.content_layout.addWidget(self.labeled_checkbox_customize_hover_data)
        self.content_layout.addWidget(self.custom_hover_data_selection_view)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def update_loaded_data_scroll_view(self, update):
        pass

    def update_custom_apex_selection_view_visibility(self, is_visible: bool):
        self.custom_apex_selection_view.setVisible(is_visible)

    def update_custom_hover_data_selection_view_visibility(self, is_visible: bool):
        self.custom_hover_data_selection_view.setVisible(is_visible)
