"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication

from src.views.main_window import MainWindow

from src.models.setup_model import BaseSetupModel
from src.controllers.setup_controller import BaseSetupController

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    # instantiate and connect models and controllers

    setup_model = BaseSetupModel()
    setup_controller = BaseSetupController(setup_model, main_window.base_setup_view)

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    #raise NotImplementedError
