"""Contains the MainWindow(QWidget) view class, which encompasses the navigation panel, dynamic content area, preview/save buttons, and plot view area"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QPushButton, QVBoxLayout, QWidget

class BaseSetupView(QWidget): # replace with imports of actual classes
    pass

class TraceView(QWidget):
    pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.dyanmic_content_area = QStackedWidget()

        self.base_setup_view = BaseSetupView()
        self.trace_view = TraceView()

        self.dynamic_content_area.addWidget(self.base_setup_view)
        self.dyanmic_content_area.addWidget(self.trace_view)

    def switch_to_base_setup_view(self):
        self.dyanmic_content_area.setCurrentWidget(self.base_setup_view)
    
    def switch_to_trace_view(self):
        self.dynamic_content_area.setCurrentWidget(self.trace_view)
