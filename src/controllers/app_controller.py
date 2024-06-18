from src.models.app_state import AppModel
from src.views.main_window import MainWindow

from src.controllers.ternary.controller import TernaryController

class AppController:

    def __init__(self, model: AppModel, view: MainWindow):
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.ternary_controller = TernaryController(self.model.ternary_model, self.view)
