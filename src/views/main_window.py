"""Contains the MainWindow(QWidget) view class, which encompasses the navigation panel, dynamic content area, preview/save buttons, and plot view area"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QVBoxLayout, QWidget

from src.views.setup_view import BaseSetupView
from src.views.trace_view import TraceView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()

        self.dynamic_content_area = QStackedWidget()
        self.base_setup_view = BaseSetupView()
        self.trace_view = TraceView()

        self.dynamic_content_area.addWidget(self.base_setup_view)
        self.dynamic_content_area.addWidget(self.trace_view)

        self.dynamic_content_area.setCurrentWidget(self.base_setup_view)

        self.main_layout.addWidget(self.dynamic_content_area)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.base_setup_view.button_add_data.clicked.connect(self.switch_to_trace_view)


    def switch_to_base_setup_view(self):
        self.dynamic_content_area.setCurrentWidget(self.base_setup_view)
    
    def switch_to_trace_view(self):
        self.dynamic_content_area.setCurrentWidget(self.trace_view)
