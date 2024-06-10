"""Contains the MainWindow(QWidget) view class, which encompasses the navigation panel, dynamic content area, preview/save buttons, and plot view area"""

import os 

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QPushButton, QVBoxLayout, QWidget,
    QHBoxLayout, QLabel, QScrollArea, QComboBox, QToolBar, QMenu, QSizePolicy
)
from PySide6.QtGui import QAction
from PySide6.QtWebEngineWidgets import QWebEngineView

from src.views.ternary.start_setup.start_setup_view import StartSetupView
from src.views.ternary.trace.trace_view import TernaryTraceEditorView
from src.views.ternary.trace.trace_scroll_area import TabView

# Disable the qt.pointer.dispatch debug messages
os.environ["QT_LOGGING_RULES"] = "qt.pointer.dispatch=false;qt.webengine.*=false"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Quick Ternaries")

        # Top Bar
        self.top_bar = QHBoxLayout()
        self.app_name_label = QLabel("Quick Ternaries")
        self.settings_button = QPushButton("Settings")
        
        # Plotting mode selection box
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Ternary", "Cartesian", "ZMap", "Depth Profile"])
        self.plot_type_combo.currentIndexChanged.connect(self.switch_plot_type)
        
        self.top_bar.addWidget(self.app_name_label)
        self.top_bar.addStretch(1)
        self.top_bar.addWidget(self.plot_type_combo)
        self.top_bar.addWidget(self.settings_button)

        # Left Scroll Area for Trace Tabs
        self.tab_view = TabView()

        # Dynamic Content Area
        self.dynamic_content_area = QStackedWidget()
        self.start_setup_view = StartSetupView()
        self.trace_view = TernaryTraceEditorView()
        # TODO eventually we will rename TraceView --> TernaryTraceView
        # We will probably also rename StartSetupView --> TernaryStartSetupView
        # We will then have classes for CartesianTraceView, ZMapTraceView, etc.
        # In these classes we can have the trace-level customization options for these other plot modes
        # This might involve a file tree refactor where now we have src.views.ternary.start_setup and src.views.ternary.trace
        # Will have to think about how we handle controllers etc, maybe the app has a "main controller" which changes for diff plot modes
        self.dynamic_content_area.addWidget(self.start_setup_view)
        self.dynamic_content_area.addWidget(self.trace_view)
        self.dynamic_content_area.setCurrentWidget(self.start_setup_view)

        # Right Area for Plotly Plot (using QWebEngineView)
        self.plot_view = QWebEngineView()
        self.plot_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Load local HTML file
        html_file_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'blank_ternary_plot.html')
        self.plot_view.setUrl(f'file://{html_file_path}')

        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.tab_view, 1)
        self.main_layout.addWidget(self.dynamic_content_area, 3)
        self.main_layout.addWidget(self.plot_view, 3)

        # Combine Top Bar and Main Layout
        self.central_layout = QVBoxLayout()
        self.central_layout.addLayout(self.top_bar)
        self.central_layout.addLayout(self.main_layout)

        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    def switch_to_start_setup_view(self):
        self.dynamic_content_area.setCurrentWidget(self.start_setup_view)
    
    def switch_to_trace_view(self):
        self.dynamic_content_area.setCurrentWidget(self.trace_view)

    def switch_plot_type(self, index):
        plot_type = self.plot_type_combo.itemText(index)
        # Logic to switch plot type goes here
        print(f"Switched to plot type: {plot_type}")
