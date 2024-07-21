"""Contains the BaseSetupView(QWidget) class, which encompasses the widgets involved in setup, and is used in the dynamic content area of the MainWindow"""

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QListWidget,
    QComboBox,
    QCheckBox,
    QScrollArea
)
from PySide6.QtCore import Qt

from src.views.utils import (
    LeftLabeledCheckbox,
    LeftLabeledLineEdit,
    InfoButton,
    LabeledButton
)
from src.views.ternary.setup import (
    CustomApexSelectionView,
    CustomHoverDataSelectionView,
    LoadedDataScrollView,
    TernaryApexScalingView,
    AdvancedSettingsView
)

class TernaryStartSetupView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        #self.setMaximumWidth(500)

        # Widget to hold all the content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        
        # Scroll area to hold the content layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        # Scroll area to display filenames for loaded data
        self.loaded_data_scroll_view = LoadedDataScrollView()

        # Combobox to select ternary type
        self.combobox_ternary_type: QComboBox = QComboBox()
        self.combobox_ternary_type.setCursor(Qt.PointingHandCursor)

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

        self.checkbox_scale_apices_layout = QHBoxLayout()
        self.labeled_checkbox_scale_apices = \
            LeftLabeledCheckbox('Scale Ternary Apices')
        self.labeled_checkbox_scale_apices.setEnabled(False)
        text = (
            "Tip: Select the Custom ternary type and add columns to each apex\n"
            "to enable apex scaling. The default scale factor for each column is 1x."
        )
        self.scale_apices_infobutton = InfoButton(self, text)
        self.apex_scaling_view = TernaryApexScalingView()
        self.apex_scaling_view.setVisible(False)

        self.advanced_settings_checkbox = LeftLabeledCheckbox("Use Advanced Settings")
        self.advanced_settings_view = AdvancedSettingsView()
        self.advanced_settings_view.setVisible(False)

        # Add widgets to the content layout
        self.content_layout.addWidget(self.loaded_data_scroll_view)
        self.content_layout.addWidget(self.combobox_ternary_type)
        self.content_layout.addWidget(self.custom_apex_selection_view)
        self.content_layout.addWidget(self.labeled_line_edit_ternary_title)
        self.content_layout.addWidget(self.labeled_line_edit_top_apex_display_name)
        self.content_layout.addWidget(self.labeled_line_edit_left_apex_display_name)
        self.content_layout.addWidget(self.labeled_line_edit_right_apex_display_name)
        self.content_layout.addWidget(self.labeled_checkbox_customize_hover_data)
        self.content_layout.addWidget(self.custom_hover_data_selection_view)

        self.checkbox_scale_apices_layout.addWidget(self.labeled_checkbox_scale_apices)
        self.checkbox_scale_apices_layout.addWidget(self.scale_apices_infobutton, alignment=Qt.AlignRight)
        self.content_layout.addLayout(self.checkbox_scale_apices_layout)
        self.content_layout.addWidget(self.apex_scaling_view)

        self.content_layout.addWidget(self.advanced_settings_checkbox)
        self.content_layout.addWidget(self.advanced_settings_view)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

    def update_loaded_data_scroll_view(self, update):
        pass

    def update_custom_apex_selection_view_visibility(self, is_visible: bool):
        self.custom_apex_selection_view.setVisible(is_visible)

    def update_custom_hover_data_selection_view_visibility(self, is_visible: bool):
        self.custom_hover_data_selection_view.setVisible(is_visible)
        if is_visible:
            self.show_scrollbar_temporarily()
            # TODO implement scrolling
            # self.scroll_area.ensureWidgetVisible(self.custom_hover_data_selection_view)
            # self.scroll_area.repaint()

    def update_scale_apices_view_visibility(self, is_checked: bool):
        condition = \
            self.apex_scaling_view.container_layout.count() > 1 \
            and is_checked
        self.apex_scaling_view.setVisible(condition)
        if condition:
            self.show_scrollbar_temporarily()
            # TODO implement scrolling
            # self.scroll_area.ensureWidgetVisible(self.apex_scaling_view)
            # self.scroll_area.repaint()

    def show_scrollbar_temporarily(self):
        pass

    def switch_to_cartesian_view(self):
        self.custom_apex_selection_view.switch_to_cartesian_view()
        self.labeled_line_edit_left_apex_display_name.clear()
        self.labeled_line_edit_top_apex_display_name.clear()
        self.labeled_line_edit_right_apex_display_name.clear()
        self.labeled_line_edit_top_apex_display_name.setLabel('X axis (display name)')
        self.labeled_line_edit_left_apex_display_name.setLabel('Y axis (display name)')
        self.labeled_line_edit_right_apex_display_name.setVisible(False)
        self.combobox_ternary_type.setCurrentText('Custom')
        self.combobox_ternary_type.setVisible(False)
        self.advanced_settings_checkbox.setEnabled(False)

    def switch_to_ternary_view(self):
        self.custom_apex_selection_view.switch_to_ternary_view()
        self.labeled_line_edit_left_apex_display_name.clear()
        self.labeled_line_edit_top_apex_display_name.clear()
        self.labeled_line_edit_right_apex_display_name.clear()
        self.labeled_line_edit_top_apex_display_name.setLabel('Top Apex (display name)')
        self.labeled_line_edit_left_apex_display_name.setLabel('Left Apex (display name)')
        self.labeled_line_edit_right_apex_display_name.setVisible(True)
        self.combobox_ternary_type.setVisible(True)
        self.advanced_settings_checkbox.setEnabled(True)
