"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.views.main_window import MainWindow

# from src.models.ternary.setup.model import TernaryStartSetupModel
# from src.controllers.ternary.setup.controller import TernaryStartSetupController

# from src.models.ternary.trace.tab_model import TabModel
# from src.controllers.ternary.trace.tab_controller import TabController

# from src.controllers.ternary.controller import TernaryController

from src.models.app_state import AppModel
from src.controllers.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    
    # -----------------------------------

    # Right now this doesn't do anything
    app_model = AppModel()
    app_controller = AppController(app_model, main_window)

    # -----------------------------------

    # instantiate and connect models and controllers

    # start_setup_model = TernaryStartSetupModel()
    # start_setup_controller = TernaryStartSetupController(start_setup_model, main_window.ternary_start_setup_view)

    # tab_model = TabModel()
    # tab_controller = TabController(tab_model, main_window.tab_view)

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    #raise NotImplementedError
