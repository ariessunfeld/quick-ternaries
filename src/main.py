"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.models.app_state import AppModel
from src.views.main_window import MainWindow
from src.controllers.app_controller import AppController

def main():
    app = QApplication(sys.argv)
    
    # -----------------------------------

    # TODO replace model instantiation with loading from pickle file
    app_model = AppModel()  # Model
    main_window = MainWindow()  # View
    app_controller = AppController(app_model, main_window)  # Controller

    # -----------------------------------

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    #raise NotImplementedError
