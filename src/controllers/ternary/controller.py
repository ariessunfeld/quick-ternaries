"""Controller for the Ternary models and views"""

from typing import TYPE_CHECKING

from src.models.ternary.model import TernaryModel
from src.controllers.ternary.trace import (
    AdvancedSettingsController,
    HeatmapEditorController,
    SizemapEditorController,
    TernaryTraceEditorController,
    TernaryTraceMolarConversionController,
)

from src.controllers.components.tab_panel_controller import TabController

from src.controllers.ternary.setup import TernaryStartSetupController
from src.controllers.ternary.trace.filter import (
    FilterEditorController,
    FilterTabController
)
from src.controllers.ternary.trace.bootstrap import TernaryBootstrapErrorEntryController

if TYPE_CHECKING:
    from src.views.main_window import MainWindow
    from src.models.ternary.trace import TernaryTraceEditorModel
    from src.models.ternary.trace.filter import FilterModel

class TernaryController:
    
    def __init__(self, model: 'TernaryModel', view: 'MainWindow'):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):

        self.start_setup_controller = TernaryStartSetupController(
            self.model.start_setup_model, 
            self.view.ternary_setup_menu)
        
        self.trace_controller = TernaryTraceEditorController(
            self.model.tab_model, 
            self.view.ternary_trace_editor)
        
        self.filter_editor_controller = FilterEditorController(
            self.model.tab_model, 
            self.view.ternary_trace_editor.filter_view.filter_editor_view)
        
        self.filter_tab_controller = FilterTabController(
            self.model.tab_model, 
            self.view.ternary_trace_editor.filter_view.filter_tab_view)
        
        self.heatmap_editor_controller = HeatmapEditorController(
            self.model.tab_model, 
            self.view.ternary_trace_editor.heatmap_view)
        
        self.sizemap_editor_controller = SizemapEditorController(
            self.model.tab_model,
            self.view.ternary_trace_editor.sizemap_view)
        
        self.advanced_settings_controller = AdvancedSettingsController(
            self.model.tab_model,
            self.view.ternary_trace_editor.trace_editor_advanced_settings_view)
        
        self.molar_conversion_controller = TernaryTraceMolarConversionController(
            self.model.molar_conversion_model,
            self.view.ternary_trace_editor.molar_conversion_view)
        
        self.bootstrap_error_entry_controller = TernaryBootstrapErrorEntryController(
            self.model.tab_model,
            self.view.ternary_trace_editor.error_entry_view)
        
        # Give the child controllers access to the shared resource, data library
        self.trace_controller.set_data_library_reference(
            self.model.data_library)
        
        self.filter_editor_controller.set_data_library_reference(
            self.model.data_library)
        
        self.heatmap_editor_controller.set_data_library_reference(
            self.model.data_library)
        
        self.sizemap_editor_controller.set_data_library_reference(
            self.model.data_library)
        
        self.filter_tab_controller.set_data_library_reference(
            self.model.data_library)

        # Connect signals for when the filter tab controller says to 
        # switch between filter setup and filter editor views
        self.filter_tab_controller.change_filter_tab_signal.connect(
            self._change_filter_tab)
        
        self.filter_tab_controller.change_to_filter_setup_signal.connect(
            self._change_filter_setup_tab)

        # Make sure the heatmap updates accordingly when new data is selected for the trace
        self.trace_controller.selected_data_event.connect(
            self.heatmap_editor_controller.handle_trace_selected_data_event)
        
        # Similarly, make sure sizemap updates accordingly when new data is selected for trace
        self.trace_controller.selected_data_event.connect(
            self.sizemap_editor_controller.handle_trace_selected_data_event)

        # Make sure the filter editor updates accordingly when new data is selected for the trace
        self.trace_controller.selected_data_event.connect(
            self.filter_tab_controller.handle_trace_selected_data_event)
        
        self.filter_tab_controller.trace_data_selection_handled.connect(
            self.filter_editor_controller.update_view)

        # Connect custom apex selection add data signal to molar conversion on add data
        self.start_setup_controller.signaller.apex_column_added.connect(
            self.molar_conversion_controller.on_new_custom_column_added)
        self.start_setup_controller.signaller.apex_column_removed.connect(
            self.molar_conversion_controller.on_new_custom_column_removed)
        
        # Connect custom apex selection add data signal to error entry on add data
        self.start_setup_controller.signaller.apex_column_added.connect(
            self._on_custom_column_added)
        self.start_setup_controller.signaller.apex_column_removed.connect(
            self._on_custom_column_removed)

    def change_trace_tab(self, trace_model: 'TernaryTraceEditorModel'):

        kind = trace_model.kind

        if kind == 'standard':
            self.view.switch_to_standard_trace_view()
        elif kind == 'bootstrap':
            self.view.switch_to_bootstrap_trace_view()
            self.bootstrap_error_entry_controller.refresh_bootstrapped_trace(trace_model)
        
        # Set the available filenames/files for the trace view
        loaded_file_names = list(map(lambda x: x[0], self.model.data_library.get_all_filenames()))
        loaded_files = [self.model.data_library.get_data_from_shortname(f) for f in loaded_file_names]
        
        if trace_model.available_data_file_names is not None:
            prev_available_data_file_names = trace_model.available_data_file_names.copy()
        else:
            prev_available_data_file_names = None

        trace_model.available_data_file_names = loaded_file_names
        trace_model.available_data_files = loaded_files

        if not prev_available_data_file_names and loaded_file_names:
            trace_model.selected_data_file_name = loaded_file_names[0]
            trace_model.selected_data_file = loaded_files[0]

        if prev_available_data_file_names and not loaded_file_names:
            trace_model.selected_data_file_name = None
            trace_model.selected_data_file = None

        # Trace controller handles tab change using trace model
        # Clears current trace view fields, repopulates with information from trace model
        self.trace_controller.change_tab(trace_model)

        # If there was no data and now there is, 
        # emit that the first is selected so the heatmap can update
        if not prev_available_data_file_names and loaded_file_names: 
            self.trace_controller.selected_data_event.emit(loaded_file_names[0]) 
        
        if prev_available_data_file_names and not loaded_file_names:
            self.trace_controller.selected_data_event.emit(None)
        
        # Call the change_trace_tab() method of the filter editor controller
        self.filter_editor_controller.change_trace_tab(trace_model.filter_tab_model.current_tab)

        # Call the change_trace_tab() method of the heatmap editor controller
        self.heatmap_editor_controller.change_trace_tab(trace_model.heatmap_model)

        # Call the change_trace_tab() method of the sizemap editor controller
        self.sizemap_editor_controller.change_trace_tab(trace_model.sizemap_model)
        
        # Main window's trace view's dynamic content area switches to filter setup view (away from specific filter configuration)
        self.view.ternary_trace_editor.filter_view.switch_to_filter_setup_view()

        # Filter tab controller clears existing tab widgets, repopulates with those from trace_model.filter_tab_model
        self.filter_tab_controller.change_trace_tab(trace_model)

        self.advanced_settings_controller.change_trace_tab(trace_model.advanced_settings_model)

    def _change_filter_tab(self, filter_model: 'FilterModel'):
        # Main window's trace view's dynamic content area switches to filter view
        self.view.ternary_trace_editor.filter_view.switch_to_filter_editor_view()

        # If there is a filter model in this signal,
        if filter_model and self.model.tab_model.current_tab.selected_data_file:

            # Get the available columns from the model
            available_columns = self.model.tab_model.current_tab.selected_data_file.get_columns()

            # Set the filter model's available columns accordingly
            filter_model.available_columns = available_columns

            # Filter editor controller clears filter editor widgets and repopulates using model
            self.filter_editor_controller.change_filter_tab(filter_model)

    def _change_filter_setup_tab(self):
        self.view.ternary_trace_editor.filter_view.switch_to_filter_setup_view()

    def change_to_start_setup(self):
        self.view.switch_to_start_setup_view()

    # def _on_remove_data_signal(self, filepath_and_sheet: tuple):
    #     # Get the data from the data library
    #     # Check it against each trace's "selected data"
    #     # If match, warn user about traces that will be deleted
    #     filepath, sheet = filepath_and_sheet
    #     data_file = self.model.start_setup_model.data_library.get_data(filepath, sheet)
    #     would_be_deleted = []
    #     for tab_id in self.model.tab_model.order:
    #         trace_model = self.model.tab_model.get_trace(tab_id)
    #         if trace_model:
    #             trace_model_file = trace_model.selected_data_file
    #             if data_file == trace_model_file:
    #                 would_be_deleted.append(tab_id)
    #     fmt_list = ", ".join(would_be_deleted)

    #     # If any traces would be deleted, triple-check with user
    #     if would_be_deleted:
    #         warning_msg = f"Warning: removing this data will delete Trace(s) {fmt_list}.\n\n"
    #         warning_msg += f"To preserve these trace(s), click Cancel and change their selected data."
            
    #         # Run the special message box
    #         msg_box = QMessageBox()
    #         msg_box.setWindowTitle("Trace(s) getting deleted")
    #         msg_box.setText(warning_msg)
    #         msg_box.setIcon(QMessageBox.Question)
    #         msg_box.addButton('Delete', QMessageBox.YesRole)
    #         msg_box.addButton('Cancel', QMessageBox.NoRole)

    #         response = msg_box.exec_()

    #         if response == 5: #  'yes role' response
    #             # delete the relevant traces
    #             for tab_id in would_be_deleted:
    #                 self.tab_controller.remove_tab(tab_id, ask=False)
    #             self.start_setup_controller.on_remove_data_confirmed(filepath, sheet)
        
    #     # If no traces are going to be deleted, just go ahead after initial double-check
    #     else:
    #         self.start_setup_controller.on_remove_data_confirmed(filepath, sheet)

    def update_shared_columns(self, shared_columns: list):
        self.start_setup_controller.custom_apex_selection_controller.update_options(shared_columns)
        self.start_setup_controller.custom_hover_data_selection_controller.update_columns(shared_columns)

    def _on_custom_column_added(self, column: str):
        # Step through the tab model's order
        # For each bootstrap trace editor model, add this column to the error entry model
        order = self.model.tab_model.order.copy()
        for tab_id in order:
            if tab_id == 'StartSetup':
                continue
            trace_model = self.model.tab_model.get_trace(tab_id)
            if trace_model.kind == 'bootstrap':
                trace_model.error_entry_model.add_column(column)
                self.bootstrap_error_entry_controller.on_new_custom_column_added(column)

    def _on_custom_column_removed(self, column: str):
        # Step through the tab model's order
        # For each bootstrap trace editor model, remove this column from the error entry model
        order = self.model.tab_model.order.copy()
        for tab_id in order:
            if tab_id == 'StartSetup':
                continue
            trace_model = self.model.tab_model.get_trace(tab_id)
            if trace_model.kind == 'bootstrap':
                trace_model.error_entry_model.rem_column(column)
                self.bootstrap_error_entry_controller.on_new_custom_column_removed(column)
