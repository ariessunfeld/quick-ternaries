"""Controller for the Quick Ternaries application"""

from src.models.app_state import AppModel
from src.views.main_window import MainWindow
from src.services.app_service import AppService

from src.controllers.ternary.controller import TernaryController

from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

class AppController:
    
    def __init__(self, model: AppModel, view: MainWindow, service: AppService):
        self.model = model
        self.view = view
        self.service = service
        
        self.setup_connections()

    def setup_connections(self):
        self.ternary_controller = TernaryController(self.model.ternary_model, self.view)
        # ...
        self.current_controller = self.ternary_controller

        # Connect the window's plotly interface to the web channel
        self.web_channel = QWebChannel(self.view.plot_view.page())
        self.web_channel.registerObject("plotlyInterface", self.view.plotly_interface)
        self.view.plot_view.page().setWebChannel(self.web_channel)
        
        # Preview & Save are outside the scope of specific plot controllers
        self.view.preview_button.clicked.connect(self._on_preview_clicked)
        self.view.save_button.clicked.connect(self._on_save_clicked)
        self.view.bootstrap_button.clicked.connect(self._on_bootstrap_clicked)

        # Settings and Plot Type are also outside the scopy of specific plot controllers
        self.view.settings_button.clicked.connect(self._on_settings_clicked)
        self.view.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)

        # only allow saving and previewing if there are trace tabs
        self.ternary_controller.tab_controller.view.has_trace.connect(
            self.view.preview_button.setEnabled)
        self.ternary_controller.tab_controller.view.has_trace.connect(
            self.view.save_button.setEnabled)
        self.ternary_controller.tab_controller.view.has_trace.connect(
            self.view.bootstrap_button.setEnabled)

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

    def _on_bootstrap_clicked(self):
        # TODO get selected traces/points from plotly interface
        selected_indices = self.view.plotly_interface.get_indices()
        print(selected_indices)
        if len(selected_indices) != 1:
            pass # If not exactly one, show gif with instructions on how to bootstrap and s
        else:
            # Else, add a trace to the trace bar and switch to it and configure it
            self.current_controller.tab_controller.add_trace()
        

    def _on_plot_type_changed(self):
        selected_plot_type = self.view.plot_type_combo.currentText()
        self.model.switch_current_model(selected_plot_type)
        # TODO Update the view to reflect the new model
        # This entails changing the current stacked widget in the start setup panel
        # as well as updating the tab panel with the traces from the current model
        # TODO change the app controllers current controler







