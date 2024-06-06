"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.views.main_window import MainWindow

from src.models.start_setup.start_setup_model import StartSetupModel
from src.controllers.start_setup.start_setup_controller import StartSetupController

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    # instantiate and connect models and controllers

    start_setup_model = StartSetupModel()
    start_setup_controller = StartSetupController(start_setup_model, main_window.start_setup_view)

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    #raise NotImplementedError
