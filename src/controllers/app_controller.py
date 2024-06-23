"""Controller for the Quick Ternaries application"""

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
        # TODO Get the current model from the AppModel
        # Hand it off to service layer to make HTML
        # Update view's html path for the QWebEngine with the new HTML
        curr_model = self.model.current_model
        url = self.service.write_html(curr_model, self.view.plot_type_combo.currentText())
        if url:
            self.view.plot_view.setUrl(url)

    def _on_save_clicked(self):
        # TODO same as _on_preview_clicked
        # but with the additional step that we
        # show the user a popup with choices for filetype and resolution
        # and then save the plot according to their chosen specifications
        pass

    def _on_settings_clicked(self):
        # TODO show the settings menu from the older version of the code
        # Connect it to the font size somehow (?)
        pass
        

    def _on_plot_type_changed(self):
        selected_plot_type = self.view.plot_type_combo.currentText()
        self.model.switch_current_model(selected_plot_type)
        # TODO Update the view to reflect the new model
        # This entails changing the current stacked widget in the start setup panel
        # as well as updating the tab panel with the traces from the current model







