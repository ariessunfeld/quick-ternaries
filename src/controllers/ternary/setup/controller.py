"""Contains the contorller for the base setup model and view

User updates View
View signals to Controller
Controller updates Model
Model updates View

User --> View --> Controller --> Model --> View
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QObject, Signal

from src.models.ternary.setup import TernaryType

from src.controllers.ternary.setup import (
    AdvancedSettingsController,
    TernaryApexScalingController,
    CustomApexSelectionController,
    CustomHoverDataSelectionController
)

from src.utils.ternary_types import TERNARY_TYPES

if TYPE_CHECKING:
    from src.models.ternary.setup import TernaryStartSetupModel
    from src.views.ternary.setup import TernarySetupMenu


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

    def __init__(self, model: 'TernaryStartSetupModel', view: 'TernarySetupMenu'):

        super().__init__()

        # models and views are instantiated outside this class
        # hence, they get passed to the initialization method
        self.model = model
        self.view = view

        self.signaller = TernaryStartSetupControllerSignaller()
        
        self.setup_connections()

    def setup_connections(self):
        # Connect add data button to model.data_library.add_data
        #self.view.loaded_data_scroll_view.add_data_button.clicked.connect(self.load_data)

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

        # Handle changes to the advanced settings checkbox
        self.view.advanced_settings_checkbox.stateChanged.connect(self.checkbox_advanced_settings_changed)

        # Set up advanced settings connections
        self.advanced_settings_controller = AdvancedSettingsController(
            self.model.advanced_settings_model,
            self.view.advanced_settings_view)

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

    def checkbox_advanced_settings_changed(self):
        is_checked = self.view.advanced_settings_checkbox.isChecked()
        self.model.advanced_settings_is_checked = is_checked
        self.view.advanced_settings_view.setVisible(is_checked)

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
