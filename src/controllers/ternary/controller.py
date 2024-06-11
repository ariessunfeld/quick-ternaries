from src.models.ternary.model import TernaryModel
from src.views.main_window import MainWindow

from src.controllers.ternary.setup.controller import TernaryStartSetupController
from src.controllers.ternary.trace.controller import TernaryTraceEditorController
from src.controllers.ternary.trace.tab_controller import TabController

from src.models.ternary.trace.model import TernaryTraceEditorModel

class TernaryController:
    
    def __init__(self, model: TernaryModel, view: MainWindow):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):

        self.start_setup_controller = TernaryStartSetupController(
            self.model.start_setup_model, self.view.ternary_start_setup_view
        )
        self.trace_controller = TernaryTraceEditorController(
            self.model.tab_model, self.view.ternary_trace_editor_view
        )
        self.tab_controller = TabController(
            self.model.tab_model, self.view.tab_view
        )

        self.tab_controller.change_tab_signal.connect(lambda tm: self.change_tab(tm))

    def change_tab(self, trace_model: TernaryTraceEditorModel):
        print('ternary change tab method called')
        self.view.switch_to_trace_view()
        self.trace_controller.change_tab(trace_model)
