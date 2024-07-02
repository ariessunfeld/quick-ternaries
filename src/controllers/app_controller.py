"""Controller for the Quick Ternaries application"""

from src.models.app_state import AppModel
from src.views.main_window import MainWindow
from src.services.app_service import AppService

from src.controllers.ternary.controller import TernaryController

from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMessageBox

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
        
        self.view.tab_view.has_trace.connect(self._on_tab_view_has_trace)

    def _on_preview_clicked(self):
        curr_model = self.model.current_model
        url = self.service.write_html(curr_model, self.view.plot_type_combo.currentText())
        if url:
            self.view.plot_view.setUrl(url)

    def _on_save_clicked(self):
        curr_model = self.model.current_model
        curr_model_name = self.model.current_model_name
        plot_maker = self.service.html_makers.get(curr_model_name).plot_maker
        fig = plot_maker.make_plot(curr_model)
        filepath, dpi = self.view.show_save_menu()
        plot_maker.save_plot(fig, filepath, dpi)

    def _on_settings_clicked(self):
        # TODO show the settings menu from the older version of the code
        # Connect it to the font size somehow (?)
        pass

    def _on_bootstrap_clicked(self):
        # TODO make this more dynamic based on plot type
        ttype = self.model.current_model.start_setup_model.get_ternary_type()
        ttype_name = ttype.name
        if ttype_name != 'Custom':
            msg = 'Please select the "Custom" ternary type from the '
            msg += 'Start Setup menu to enable bootstrapping'
            QMessageBox.information(None, 'Change ternary type', msg)
        else:
            selected_indices = self.view.plotly_interface.get_indices()
            top = self.model.current_model.start_setup_model.custom_apex_selection_model.get_top_apex_selected_columns()
            left = self.model.current_model.start_setup_model.custom_apex_selection_model.get_left_apex_selected_columns()
            right = self.model.current_model.start_setup_model.custom_apex_selection_model.get_right_apex_selected_columns()
            success = self.current_controller.tab_controller.add_bootstrap_trace(None, selected_indices, top+left+right)
            if not success:
                self.view.show_bootstrap_tutorial_gif()

    def _on_plot_type_changed(self):
        selected_plot_type = self.view.plot_type_combo.currentText()
        self.model.switch_current_model(selected_plot_type)
        # TODO Update the view to reflect the new model
        # This entails changing the current stacked widget in the start setup panel
        # as well as updating the tab panel with the traces from the current model
        # TODO change the app controllers current controler

    def _on_tab_view_has_trace(self, has_trace: bool):
        self.view.preview_button.setEnabled(has_trace)
        self.view.save_button.setEnabled(has_trace)
        self.view.bootstrap_button.setEnabled(has_trace)
        if not has_trace:
            # TODO change this behavior for other plot modes
            # eg when in cartesian, want to call blank_cartesian() method
            self.view.switch_to_blank_ternary()







