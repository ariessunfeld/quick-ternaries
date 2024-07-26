"""Controller for the Quick Ternaries application"""

from typing import TYPE_CHECKING

from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWidgets import QMessageBox

from src.views import SettingsDialog
from src.views.utils import DeleteWarningBox

from src.controllers.ternary import TernaryController
# from src.controllers.cartesian import CartesianController
# ...

from src.controllers.components import TabController
from src.controllers.components import DataLibraryController

if TYPE_CHECKING:
    from src.models.app_state import AppModel
    from src.views.main_window import MainWindow
    from src.services.app_service import AppService

class AppController:

    TRACE_DELETION_WARNING = (
        "Warning: removing this data will delete Trace(s) {fmt_list}.\n\n"
        "To preserve the trace(s), click Cancel and change the trace selected data."
    )
    
    def __init__(self, model: 'AppModel', view: 'MainWindow', service: 'AppService'):
        self.model = model
        self.view = view
        self.service = service
        
        self.setup_connections()

    def setup_connections(self):

        # Set up child controllers --------------------

        # Set up component controllers
        self.tab_panel_controller = TabController(
            self.model.tab_model, self.view.tab_view)
        self.data_library_controller = DataLibraryController(
            self.model.data_library, self.view.data_library_view)

        # Set up plot type controllers
        self.ternary_controller = TernaryController(
            self.model.ternary_model, self.view)
        # self.cartesian_controller = CartesianController(
        #   self.model.cartesian_model, self.view)
        # ...

        # ---------------------------------------------

        # Set the current controller
        self.current_controller = self.ternary_controller

        # Connect the window's plotly interface to the web channel
        self.web_channel = QWebChannel(self.view.plot_view.page())
        self.web_channel.registerObject("plotlyInterface", self.view.plotly_interface)
        self.view.plot_view.page().setWebChannel(self.web_channel)
        
        # Preview & Save are outside the scope of specific plot controllers
        self.view.preview_button.clicked.connect(self._on_preview_clicked)
        self.view.save_button.clicked.connect(self._on_save_clicked)

        # Bootstrap is outside the scope of specific plot controllers
        self.view.bootstrap_button.clicked.connect(self._on_bootstrap_clicked)

        # Settings and Plot Type are also outside the scopy of specific plot controllers
        self.view.settings_button.clicked.connect(self._on_settings_clicked)
        self.view.plot_type_combo.currentIndexChanged.connect(self._on_plot_type_changed)
        
        self.view.tab_view.has_trace.connect(self._on_tab_view_has_trace)

        # Connect change tab signals to child controllers
        self.tab_panel_controller.change_tab_signal.connect(self.ternary_controller.change_trace_tab)
        self.tab_panel_controller.change_to_start_setup_signal.connect(self.ternary_controller.change_to_start_setup)

        # Connect data library signals
        self.view.data_library_view.has_data.connect(self._on_loaded_data_exists)
        self.data_library_controller.shared_columns_signal.connect(self._on_shared_columns_signal)
        self.data_library_controller.remove_data_signal.connect(self._on_remove_data_signal)

    def _on_preview_clicked(self):
        """Callback for Preview button click event"""
        curr_model = self.model.current_model
        url = self.service.write_html(curr_model, self.view.plot_type_combo.currentText())
        if url:
            self.view.plot_view.setUrl(url)

    def _on_save_clicked(self):
        curr_plot_type = self.view.plot_type_combo.currentText()
        curr_plot_type = curr_plot_type.lower().replace(' ', '_')
        curr_model = self.model.current_model
        plot_maker = self.service.html_makers.get(curr_plot_type).plot_maker
        fig = plot_maker.make_plot(curr_model)
        filepath, dpi = self.view.show_save_menu()
        plot_maker.save_plot(fig, filepath, dpi)

    def _on_settings_clicked(self):
        dialog = SettingsDialog(self.view)
        dialog.font_changed.connect(self.view.update_font)
        dialog.exec()

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
            # TODO make this more robust to different plot types
            top = self.model.current_model.start_setup_model.custom_apex_selection_model.get_top_apex_selected_columns()
            left = self.model.current_model.start_setup_model.custom_apex_selection_model.get_left_apex_selected_columns()
            right = self.model.current_model.start_setup_model.custom_apex_selection_model.get_right_apex_selected_columns()
            success = self.tab_panel_controller.add_bootstrap_trace(None, selected_indices, top+left+right)
            if not success:
                self.view.show_bootstrap_tutorial_gif()

    def _on_plot_type_changed(self):
        selected_plot_type = self.view.plot_type_combo.currentText()
        if selected_plot_type.lower() == 'cartesian':
            # Show popup warning user that Cartesian is a Beta feature
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Beta Feature Warning")
            msg_box.setText("The Cartesian plot type is currently in Beta and may be buggy. Do you wish to proceed?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            response = msg_box.exec()

            # Case where user is switching to Cartesian, confirmed
            if response == QMessageBox.Yes:
                self.model.ternary_model.start_setup_model.switch_to_cartesian()
                self.view.ternary_setup_menu.switch_to_cartesian_view()
                self.view.ternary_trace_editor.switch_to_cartesian_view()
                self.view.bootstrap_button.setVisible(False)
                self.view.display_blank_cartesian_plot()
                self.current_controller.start_setup_controller.custom_apex_selection_controller.refresh_view()
            else:
                # Block signals, set plot type combo back to Ternary, and unblock signals
                self.view.plot_type_combo.blockSignals(True)
                self.view.plot_type_combo.setCurrentIndex(0)
                self.view.plot_type_combo.blockSignals(False)
        elif selected_plot_type.lower() == 'ternary':
            self.model.ternary_model.start_setup_model.switch_to_ternary()
            self.view.ternary_setup_menu.switch_to_ternary_view()
            self.view.ternary_trace_editor.switch_to_ternary_view()
            self.view.bootstrap_button.setVisible(True)
            self.view.display_blank_ternary_plot()
            self.current_controller.start_setup_controller.custom_apex_selection_controller.refresh_view()
            
        #self.model.switch_current_model(selected_plot_type)
        # TODO Update the view to reflect the new model
        # This entails changing the current stacked widget in the start setup panel
        # as well as updating the tab panel with the traces from the current model
        # TODO change the app controllers current controler

    def _on_tab_view_has_trace(self, has_trace: bool):
        """Event handler for when tabs are added/removed"""
        self.view.preview_button.setEnabled(has_trace)
        self.view.save_button.setEnabled(has_trace)
        self.view.bootstrap_button.setEnabled(has_trace)
        if not has_trace:
            # TODO change this behavior for other plot modes
            # eg when in cartesian, want to call blank_cartesian() method
            self.view.display_blank_ternary_plot()

    def _on_loaded_data_exists(self, exists: bool):
        """Event handler for when data is loaded/removed"""
        self.view.tab_view.new_tab_button.setEnabled(exists)

    def _on_remove_data_signal(self, filepath_and_sheet: tuple):
        """Callback when user tries to remove data from Data Library
        
        Checks against the current traces to see which ones are using this data
        If any are, warns user that those would be deleted, and user has to confirm
        before proceeding with the delete

        If no traces are using the to-be-deleted data, user simply has to confirm intent
        """
        filepath, sheet = filepath_and_sheet
        data_file = self.model.data_library.get_data(filepath, sheet)
        would_be_deleted = []
        for tab_id in self.model.tab_model.order:
            trace_model = self.model.tab_model.get_trace(tab_id)
            if trace_model:
                trace_model_file = trace_model.selected_data_file
                if data_file == trace_model_file:
                    would_be_deleted.append(tab_id)
        fmt_list = ", ".join(would_be_deleted)

        # If any traces would be deleted, triple-check with user
        # Otherwise, just unload the data
        if would_be_deleted:
            
            msg_box = DeleteWarningBox(
                'Trace(s) Getting Deleted', 
                self.TRACE_DELETION_WARNING.format(fmt_list=fmt_list))
            response = msg_box.exec_()

            if response == 5: #  'yes role' response
                for tab_id in would_be_deleted:
                    self.tab_panel_controller.remove_tab(tab_id, ask=False)
                self.data_library_controller.remove_data(filepath, sheet)
        else:
            self.data_library_controller.remove_data(filepath, sheet)

    def _on_shared_columns_signal(self, shared_columns: list):
        """Handle the shared column signal from the data library
        
        This signal emits a List[str] with the set intersection of the
        column names from the currently loaded data

        This controller must tell its child controllers to update their shared columns
        """

        self.ternary_controller.update_shared_columns(shared_columns)
