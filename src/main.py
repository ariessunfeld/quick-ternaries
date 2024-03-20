"""Main entrypoint for ternary GUI application"""

import sys

from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    # instantiate and connect models and controllers
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    #main()
    raise NotImplementedError
