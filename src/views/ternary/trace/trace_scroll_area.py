"""Contains the TraceScrollArea(QWidget) class and support classes"""

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QScrollArea)
from PySide6.QtCore import (
    Qt,
    QSize,
    Signal,
    QMimeData,
    QPoint)
from PySide6.QtGui import (
    QDrag,
    QPixmap,
    QPainter)

class DragTargetIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(25, 5, 25, 5)
        # self.setStyleSheet(
        #     "QLabel { background-color: #ccc; border: 1px solid black; }"
        # )

class DraggableTab(QWidget):
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

    def mouseMoveEvent(self, event):
        if self.identifier == 'StartSetup':
            return

        if event.buttons() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            # Create a pixmap of the label only
            pixmap = QPixmap(self.label.size())
            pixmap.fill(Qt.transparent)  # Set the background to transparent

            painter = QPainter(pixmap)
            self.label.render(painter,
                              QPoint(),
                              self.label.rect(),
                              QWidget.RenderFlag.DrawWindowBackground |
                              QWidget.RenderFlag.DrawChildren)
            painter.end()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos() - self.label.pos())

            # drag.exec(Qt.DropAction.MoveAction)
            drag.exec(Qt.MoveAction)
            self.show()

    def enterEvent(self, event):
        self.label.setStyleSheet("background: lightgray;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.label.setStyleSheet("background: transparent;")
        super().leaveEvent(event)

    def dragEnterEvent(self, event):
        event.accept()

    def dragMoveEvent(self, event):
        event.ignore()

class TabView(QWidget):
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

        # Setup a drag-and-drop indicator widget
        self._drag_target_indicator = DragTargetIndicator()
        self.tab_layout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()

        # Add the "Add Trace" button to the layout
        self.new_tab_button = QPushButton("+ Add Trace")
        self.new_tab_button.setCursor(Qt.PointingHandCursor)
        self.new_tab_button.setEnabled(False) # disable the add trace button upon initialization
        self.tab_layout.addWidget(self.new_tab_button)

        # Add the scroll area to the layout
        self.controls_layout.addWidget(self.scroll_area)
        self.setLayout(self.controls_layout)

        # initialize the view with just a start setup tab
        self.add_start_setup_tab_to_view()
        self.set_selected_tab('StartSetup')

    def add_tab_to_view(self, name: str, identifier: str):
        tab_button = DraggableTab(name, identifier)
        tab_button.tab_clicked.connect(self.tab_changed.emit)
        tab_button.tab_closed.connect(self.tab_removed.emit)
        # insert at position n-1 to preserve the position of the Add Tab button
        self.tab_layout.insertWidget(self.tab_layout.count() - 1, tab_button)
        return tab_button

    def add_trace_tab_to_view(self, name: str, tab_id: str):
        self.add_tab_to_view(name, tab_id)
        # switch to the newly created tab
        self.set_selected_tab(tab_id)

    def add_start_setup_tab_to_view(self):
        start_setup_tab = DraggableTab("<center>Start Setup</center>", "StartSetup")
        start_setup_tab.tab_clicked.connect(self.tab_changed.emit)
        self.tab_layout.insertWidget(0, start_setup_tab)
        return start_setup_tab

    def remove_tab_from_view(self, tab_id: str):
        for i in range(self.tab_layout.count()):
            tab_widget = self.tab_layout.itemAt(i).widget()
            if isinstance(tab_widget, DraggableTab) and tab_widget.identifier == tab_id:
                self.tab_layout.removeWidget(tab_widget)
                tab_widget.deleteLater()
                break

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

    def get_tab_buttons(self) -> List[DraggableTab]:
        """Returns a list of draggable tab widgets"""
        ret = []
        n_tabs = self.tab_layout.count()

        for i in range(n_tabs):
            item = self.tab_layout.itemAt(i).widget()
            if isinstance(item, DraggableTab):
                ret.append(item)

        return ret
