"""Controller for the Ternary models and views"""

# Instantiated
from src.models.ternary.model import TernaryModel
from src.views.main_window import MainWindow
from src.controllers.ternary.setup.controller import TernaryStartSetupController
from src.controllers.ternary.trace.controller import TernaryTraceEditorController
from src.controllers.ternary.trace.tab_controller import TabController
from src.controllers.ternary.trace.filter.controller import FilterEditorController
from src.controllers.ternary.trace.filter.tab_controller import FilterTabController
from src.controllers.ternary.trace.heatmap_editor_controller import HeatmapEditorController

# For type hints
from src.models.ternary.trace.filter.model import FilterModel
from src.models.ternary.trace.model import TernaryTraceEditorModel

class TernaryController:
    
    def __init__(self, model: TernaryModel, view: MainWindow):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):

        self.start_setup_controller = TernaryStartSetupController(
            self.model.start_setup_model, self.view.ternary_start_setup_view)
        self.trace_controller = TernaryTraceEditorController(
            self.model.tab_model, self.view.ternary_trace_editor_view)
        self.tab_controller = TabController(
            self.model.tab_model, self.view.tab_view)
        self.filter_editor_controller = FilterEditorController(
            self.model.tab_model, self.view.ternary_trace_editor_view.filter_view.filter_editor_view)
        self.filter_tab_controller = FilterTabController(
            self.model.tab_model, self.view.ternary_trace_editor_view.filter_view.filter_tab_view)
        self.heatmap_editor_controller = HeatmapEditorController(
            self.model.tab_model, self.view.ternary_trace_editor_view.heatmap_view)
        
        # Give the child controllers access to the shared resource, data library
        self.trace_controller.set_data_library_reference(self.model.start_setup_model.data_library)
        self.filter_editor_controller.set_data_library_reference(self.model.start_setup_model.data_library)
        self.heatmap_editor_controller.set_data_library_reference(self.model.start_setup_model.data_library)
        self.filter_tab_controller.set_data_library_reference(self.model.start_setup_model.data_library)

        # Connect signals when the tab controller says to 
        # switch between start setup and trace tab views
        self.tab_controller.change_tab_signal.connect(self._change_trace_tab)
        self.tab_controller.change_to_start_setup_signal.connect(self._change_to_start_setup)

        # Connect signals for when the filter tab controller says to 
        # switch between filter setup and filter editor views
        self.filter_tab_controller.change_filter_tab_signal.connect(self._change_filter_tab)
        self.filter_tab_controller.change_to_filter_setup_signal.connect(self._change_filter_setup_tab)

        # Make sure the heatmap updates accordingly when new data is selected for the trace
        self.trace_controller.selected_data_event.connect(self.heatmap_editor_controller.handle_trace_selected_data_event)

        # Make sure the filter editor updates accordingly when new data is selected for the trace
        self.trace_controller.selected_data_event.connect(self.filter_tab_controller.handle_trace_selected_data_event)

        self.filter_tab_controller.trace_data_selection_handled.connect(self.filter_editor_controller.update_view)

    def _change_trace_tab(self, trace_model: TernaryTraceEditorModel):
        
        # Main window dynamic content area switches to trace view
        self.view.switch_to_trace_view()
        
        # Set the available filenames/files for the trace view
        loaded_file_names = list(map(lambda x: x[0], self.model.start_setup_model.data_library.get_all_filenames()))
        loaded_files = [self.model.start_setup_model.data_library.get_data_from_shortname(f) for f in loaded_file_names]
        prev_available_data_file_names = \
            trace_model.available_data_file_names.copy() if trace_model.available_data_file_names is not None else None
        trace_model.available_data_file_names = loaded_file_names
        trace_model.available_data_files = loaded_files

        if not prev_available_data_file_names and loaded_file_names:
            trace_model.selected_data_file_name = loaded_file_names[0]
            trace_model.selected_data_file = loaded_files[0]

        # Trace controller handles tab change using trace model
        # Clears current trace view fields, repopulates with information from trace model
        self.trace_controller.change_tab(trace_model)

        # If there was no data and now there is, emit that the first is selected so the heatmap can update
        if not prev_available_data_file_names and loaded_file_names:
            self.trace_controller.selected_data_event.emit(loaded_file_names[0])
        
        # Call the change trace tab method of the filter editor controller
        self.filter_editor_controller.change_trace_tab(trace_model.filter_tab_model.current_tab)

        # Call the change trace tab method of the heatmap editor controller
        self.heatmap_editor_controller.change_trace_tab(trace_model.heatmap_model)
        
        # Main window's trace view's dynamic content area switches to filter setup view (away from specific filter configuration)
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_setup_view()

        # Filter tab controller clears existing tab widgets, repopulates with those from trace_model.filter_tab_model
        self.filter_tab_controller.change_trace_tab(trace_model)

    def _change_filter_tab(self, filter_model: FilterModel):
        # Main window's trace view's dynamic content area switches to filter view
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_editor_view()

        # If there is a filter model in this signal,
        if filter_model:

            # Get the available columns from the model
            available_columns = self.model.tab_model.current_tab.selected_data_file.get_columns()

            # Set the filter model's available columns accordingly
            filter_model.available_columns = available_columns

            # Filter editor controller clears filter editor widgets and repopulates using model
            self.filter_editor_controller.change_filter_tab(filter_model)

    def _change_filter_setup_tab(self):
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_setup_view()

    def _change_to_start_setup(self):
        self.view.switch_to_start_setup_view()
