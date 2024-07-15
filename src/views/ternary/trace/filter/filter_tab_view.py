from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QScrollArea,
    QStackedWidget,
    QMessageBox,
    QStyle,
    QToolButton,
    QToolTip
)
from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
)
from PySide6.QtGui import (
    QPixmap,
    QPainter,
    QCursor,
)

class FilterTab(QWidget):
    tab_clicked = Signal(str)
    tab_closed = Signal(str)

    def __init__(self, name, identifier, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.identifier = identifier

        self.setStyleSheet("background: transparent; border-radius: 10px; padding: 5px;")

        self.tab_button_layout = QHBoxLayout(self)
        self.label = QLabel(name, self)
        self.label.setStyleSheet("background: transparent;")
        self.tab_button_layout.addWidget(self.label)

        if identifier != 'StartSetup':
            self.setup_close_button()

        self.tab_button_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.tab_button_layout)
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)

    def setup_close_button(self):
        close_button = QPushButton("✕", self)
        close_button.setFixedSize(QSize(20, 20))
        close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: lightgray;
                border-radius: 10px;
            }
            QPushButton:hover {
                background-color: red;
            }
        """)
        close_button.clicked.connect(lambda: self.tab_closed.emit(self.identifier))
        self.tab_button_layout.addWidget(close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.tab_clicked.emit(self.identifier)
            self.drag_start_position = event.pos()

    def enterEvent(self, event):
        self.label.setStyleSheet("background: lightgray;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.label.setStyleSheet("background: transparent;")
        super().leaveEvent(event)


class FilterTabView(QWidget):
    """
    Megawidget containing the tab add/remove/scroll area
    """
    tab_changed = Signal(str)
    tab_removed = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.controls_layout = QHBoxLayout(self)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        # Set up the tab scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.scroll_area.setMaximumWidth(150)
        self.scroll_area.setMinimumWidth(100)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        self.tab_layout = QVBoxLayout(self.scroll_widget)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(5)
        self.tab_layout.setAlignment(Qt.AlignTop)

        # Add the "Add Filter" button to the layout
        self.new_tab_button = QPushButton("+ Add Filter")
        self.new_tab_button.setCursor(Qt.PointingHandCursor)
        self.tab_layout.addWidget(self.new_tab_button)

        # Add the scroll area to the layout
        self.controls_layout.addWidget(self.scroll_area)
        self.setLayout(self.controls_layout)

        # # initialize the view with just a start setup tab
        # self.add_start_setup_tab_to_view()
        # self.set_selected_tab('StartSetup')

    def add_tab_to_view(self, name: str, identifier: str):
        tab_button = FilterTab(name, identifier)
        tab_button.tab_clicked.connect(self.tab_changed.emit)
        tab_button.tab_closed.connect(self.tab_removed.emit)
        # insert at position n-1 to preserve the position of the Add Filter button
        self.tab_layout.insertWidget(self.tab_layout.count() - 1, tab_button)
        return tab_button

    # def add_start_setup_tab_to_view(self):
    #     start_setup_tab = FilterTab("Filter Setup", "StartSetup", hide_close_button=True)
    #     start_setup_tab.tab_clicked.connect(self.tab_changed.emit)
    #     self.tab_layout.insertWidget(0, start_setup_tab)
    #     return start_setup_tab

    def remove_tab_from_view(self, tab_id: str):
        for i in range(self.tab_layout.count()):
            tab_widget = self.tab_layout.itemAt(i).widget()
            if isinstance(tab_widget, FilterTab) and tab_widget.identifier == tab_id:
                self.tab_layout.removeWidget(tab_widget)
                tab_widget.deleteLater()
                break

    def clear(self):
        for i in range(self.tab_layout.count() - 1, -1, -1):
            tab_widget = self.tab_layout.itemAt(i).widget()
            if tab_widget is not None and isinstance(tab_widget, FilterTab) and tab_widget.identifier != 'StartSetup':
                self.tab_layout.removeWidget(tab_widget)
                tab_widget.deleteLater()

    def set_selected_tab(self, tab_id: str):
        """
        Given an identifier, set the corresponding tab appearance to "current"
        and set all others to "deselected"
        """

        # Update appearances to reflect which tab is selected
        for tab_button in self.get_tab_buttons():
            if tab_button.identifier == tab_id:
                # "current" stylesheet
                tab_button.setStyleSheet("""font-weight: bold;
                                            background-color: lightgray;
                                            border: 1px solid gray;
                                            border-radius: 4px""")
            else:
                # "non-current" stylesheet
                tab_button.setStyleSheet("""font-weight: normal;
                                            background-color: transparent;
                                            border: 1px solid gray;
                                            border-radius: 4px;""")

    def get_tab_buttons(self) -> List[FilterTab]:
        """Returns a list of filter tab widgets"""
        ret = []
        n_tabs = self.tab_layout.count()

        for i in range(n_tabs):
            item = self.tab_layout.itemAt(i).widget()
            if isinstance(item, FilterTab):
                ret.append(item)

        return ret
