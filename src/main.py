"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.models import AppModel
from src.views import MainWindow
from src.controllers import AppController
from src.services.app_service import AppService

from src.utils import exception_handler

def main():
    sys.excepthook = exception_handler
    app = QApplication(sys.argv)
    
    # -----------------------------------

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
