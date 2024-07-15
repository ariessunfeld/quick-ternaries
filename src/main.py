"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.models import AppModel
from src.views import MainWindow
from src.controllers import AppController
from src.services.app_service import AppService

def main():
    app = QApplication(sys.argv)
    
    # -----------------------------------

    # TODO replace model instantiation with loading from pickle file
    # (once everything is set up to reflect pickle-loaded state)

    app_model = AppModel()           # Model
    main_window = MainWindow()       # View
    app_service = AppService()       # Service
    app_controller = AppController(  # Controller
        app_model,
        main_window,
        app_service)

    # -----------------------------------

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    #raise NotImplementedError
