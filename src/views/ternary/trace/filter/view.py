"""Contains the FilterMainWidget(QWidget) view class, which encompasses the navigation panel, dynamic content area, and filter view area"""

from PySide6.QtWidgets import (
    QWidget, 
    QStackedWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel
)

from src.views.ternary.trace.filter.filter_tab_view import FilterTabView
from src.views.ternary.trace.filter.filter_editor_view import FilterEditorView

class FilterStartSetupView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout()
        label = QLabel("No filter selected")
        layout.addWidget(label)
        self.setLayout(layout)

class FilterPanelView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # Initialize components
        self.filter_tab_view = FilterTabView()
        self.filter_start_setup_view = FilterStartSetupView()
        self.filter_editor_view = FilterEditorView()

        # Dynamic Content Area
        self.dynamic_content_area = QStackedWidget()
        self.dynamic_content_area.addWidget(self.filter_start_setup_view)
        self.dynamic_content_area.addWidget(self.filter_editor_view)
        self.dynamic_content_area.setCurrentWidget(self.filter_start_setup_view)

        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.filter_tab_view, 1)
        self.main_layout.addWidget(self.dynamic_content_area, 3)

        # Set main layout
        self.setLayout(self.main_layout)

    def switch_to_filter_setup_view(self):
        self.dynamic_content_area.setCurrentWidget(self.filter_start_setup_view)
    
    def switch_to_filter_editor_view(self):
        self.dynamic_content_area.setCurrentWidget(self.filter_editor_view)
