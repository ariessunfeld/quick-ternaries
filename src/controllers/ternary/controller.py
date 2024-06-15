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

        self.tab_controller.change_tab_signal.connect(self._change_trace_tab)
        self.tab_controller.change_to_start_setup_signal.connect(self._change_to_start_setup)

        self.filter_tab_controller.change_filter_tab_signal.connect(self._change_filter_tab)
        self.filter_tab_controller.change_to_filter_setup_signal.connect(self._change_filter_setup_tab)

    def _change_trace_tab(self, trace_model: TernaryTraceEditorModel):
        
        # Main window dynamic content area switches to trace view
        self.view.switch_to_trace_view()

        # Retrieve the loaded data from the start setup
        data_library = self.start_setup_controller.model.data_library
        # Isolate the filenames
        all_filenames = list(map(lambda x: x[0], data_library.get_all_filenames()))
        # Provide the trace model with the loaded data library
        trace_model.available_data_files = data_library.list_all_datafiles()
        trace_model.available_data_file_names = all_filenames
        
        # Trace controller handles tab change using trace model
        # Clears current trace view fields, repopulates with information from trace model
        self.trace_controller.change_tab(trace_model)
        
        # Call the change trace tab method of the filter editor controller
        self.filter_editor_controller.change_trace_tab(trace_model.filter_model)

        # Call the change trace tab method of the heatmap editor controller
        self.heatmap_editor_controller.change_trace_tab(trace_model.heatmap_model)
        
        # Main window's trace view's dynamic content area switches to filter setup view (away from specific filter configuration)
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_setup_view()

        # Filter tab controller clears existing tab widgets, repopulates with those from trace_model.filter_tab_model
        self.filter_tab_controller.change_trace_tab(trace_model)

    def _change_filter_tab(self, filter_model: FilterModel):
        # Main window's trace view's dynamic content area switches to filter view
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_editor_view()

        # Filter editor controller clears filter editor widgets and repopulates using model
        self.filter_editor_controller.change_filter_tab(filter_model)

    def _change_filter_setup_tab(self):
        self.view.ternary_trace_editor_view.filter_view.switch_to_filter_setup_view()

    def _change_to_start_setup(self):
        self.view.switch_to_start_setup_view()