from src.models.app_state import AppModel
from src.views.main_window import MainWindow
from src.services.app_service import AppService

from src.controllers.ternary.controller import TernaryController

class AppController:
    
    def __init__(self, model: AppModel, view: MainWindow, service: AppService):
        self.model = model
        self.view = view
        self.service = service
        
        self.setup_connections()

    def setup_connections(self):
        self.ternary_controller = TernaryController(self.model.ternary_model, self.view)
        
        # Preview & Save are outside the scope of specific plot controllers
        self.view.preview_button.clicked.connect(self._on_preview_clicked)
        self.view.save_button.clicked.connect(self._on_save_clicked)

        # Settings and Plot Type are also outside the scopy of specific plot controllers
        self.view.settings_button.clicked.connect(self._on_settings_clicked)
        self.view.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)

    def _on_preview_clicked(self):
        pass

    def _on_save_clicked(self):
        pass

    def _on_settings_clicked(self):
        pass

    def _on_plot_type_changed(self):
        selected_plot_type = self.view.plot_type_combo.currentText()
        self.model.switch_current_model(selected_plot_type)







