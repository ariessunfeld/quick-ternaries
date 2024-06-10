"""Contains the TraceScrollArea(QWidget) class and support classes"""

from typing import List

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QVBoxLayout, 
    QScrollArea, 
    QStackedWidget, 
    QMessageBox)
from PySide6.QtCore import (
    Qt, 
    QSize, 
    Signal, 
    QMimeData)
from PySide6.QtGui import (
    QDrag, 
    QPixmap)

class DragTargetIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(25, 5, 25, 5)
        self.setStyleSheet(
            "QLabel { background-color: #ccc; border: 1px solid black; }"
        )

class DraggableTab(QWidget):
    tab_clicked = Signal(int)
    tab_closed = Signal(QWidget)

    def __init__(self, name, identifier, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.identifier = identifier
    
        self.tab_button_layout = QHBoxLayout(self)
        self.label = QLabel(name, self)
        self.tab_button_layout.addWidget(self.label)

        self.setup_close_button()

        self.tab_button_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.tab_button_layout)
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)

    def setup_close_button(self):
        close_button = QPushButton("✕", self)
        close_button.setFixedSize(QSize(20, 20))
        close_button.setStyleSheet("border: none; background-color: transparent;")
        close_button.clicked.connect(lambda: self.tab_closed.emit(self))
        self.tab_button_layout.addWidget(close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.tab_clicked.emit(self.parentWidget().layout().indexOf(self))

    def mouseMoveEvent(self, event):
        if self.identifier == 'StartSetup':
            return
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            drag.setMimeData(mime)

            pixmap = QPixmap(self.size().width() * 2, self.size().height() * 2)
            pixmap.setDevicePixelRatio(2)
            self.render(pixmap)
            drag.setPixmap(pixmap)

            drag.exec(Qt.DropAction.MoveAction)
            self.show()

    def dragEnterEvent(self, event):
        event.accept()

class TabView(QWidget):
    """
    Megawidget containing the tab add/remove/scroll area
    """
    tab_changed = Signal(int)
    tab_removed = Signal(QWidget)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.content_stack = QStackedWidget()
        self.controls_layout = QHBoxLayout(self)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("border: none; ")
        self.scroll_area.setMaximumWidth(150)
        self.scroll_area.setMinimumWidth(100)

        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        self.tab_layout = QVBoxLayout(self.scroll_widget)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(5)
        self.tab_layout.setAlignment(Qt.AlignTop)

        self._drag_target_indicator = DragTargetIndicator()
        self.tab_layout.addWidget(self._drag_target_indicator)
        self._drag_target_indicator.hide()

        self.new_tab_button = QPushButton("+ Add Trace")
        self.new_tab_button.setCursor(Qt.PointingHandCursor)
        self.tab_layout.addWidget(self.new_tab_button)

        self.controls_layout.addWidget(self.scroll_area)
        self.controls_layout.addWidget(self.content_stack)
        self.setLayout(self.controls_layout)

        # initialize the view with a start setup tab
        self.add_start_setup_tab_to_view()
        self.set_selected_tab(0)

    def add_tab_to_view(self, name: str, identifier: str):
        tab_button = DraggableTab(name, identifier)
        tab_button.tab_clicked.connect(self.tab_changed.emit)
        tab_button.tab_closed.connect(self.tab_removed.emit)
        # insert at position n-1 to preserve the position of the Add Tab button
        self.tab_layout.insertWidget(self.tab_layout.count() - 1, tab_button)
        return tab_button
    
    def add_trace_tab_to_view(self, name, tab_id, trace_editor):
        self.add_tab_to_view(name, tab_id)
        self.add_content_widget(trace_editor, tab_id)
        # switch to the newly created tab
        self.set_selected_tab(self.tab_layout.count() - 2)
    
    def add_start_setup_tab_to_view(self):
        start_setup_tab = DraggableTab("Start Setup", "StartSetup")
        start_setup_tab.tab_clicked.connect(self.tab_changed.emit)
        self.tab_layout.insertWidget(0, start_setup_tab)
        return start_setup_tab

    def add_content_widget(self, widget, identifier):
        widget.setProperty("identifier", identifier)
        self.content_stack.addWidget(widget)

    def remove_tab_from_view(self, tab):
        self.tab_layout.removeWidget(tab)
        self.remove_content_widget(tab.identifier)
        tab.deleteLater()

    def remove_content_widget(self, identifier):
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if widget.property("identifier") == identifier:
                self.content_stack.removeWidget(widget)
                widget.deleteLater()
                break

    def set_selected_tab(self, index):
        """
        Given an index, get the identifier, set this widget to "current",
        update appearances of other widgets to reflect this one's current-ness
        """

        # Get the identifier from the widget
        tab_button = self.tab_layout.itemAt(index).widget()
        identifier = tab_button.identifier

        # Find the selected tab by its identifier
        for i in range(self.content_stack.count()):
            content_widget = self.content_stack.widget(i)
            if content_widget.property("identifier") == identifier:
                self.content_stack.setCurrentIndex(i)
                break

        # Update appearances to reflect which tab is selected
        for i in range(self.tab_layout.count()):
            tab_button = self.tab_layout.itemAt(i).widget()
            if isinstance(tab_button, DraggableTab):
                if i == index:
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


    def get_current_tab_index(self) -> int:
        """Returns index of current tab"""
        return self.content_stack.currentIndex()
