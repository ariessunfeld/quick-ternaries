"""Contains the TraceScrollArea(QWidget) class and support classes"""

"""MODEL"""

class TabModel:
    def __init__(self):
        self.traces = {}
        self.order = []
        self.tab_counter = 0

    def add_trace(self, trace_data):
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        self.traces[tab_id] = trace_data
        self.order.append(tab_id)

    def remove_trace(self, identifier):
        if identifier in self.traces:
            del self.traces[identifier]
        if identifier in self.order:
            self.order.remove(identifier)

    def get_trace(self, identifier):
        return self.traces.get(identifier)

    def update_order(self, new_order):
        self.order = new_order

    def get_all_traces(self):
        return {id: self.traces[id] for id in self.order}

"""VIEW"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QScrollArea, QStackedWidget, QMessageBox
from PySide6.QtCore import Qt, QSize, Signal, QMimeData
from PySide6.QtGui import QDrag, QPixmap

class DragTargetIndicator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(25, 5, 25, 5)
        self.setStyleSheet(
            "QLabel { background-color: #ccc; border: 1px solid black; }"
        )

class CustomTabButton(QWidget):
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
        if event.buttons() == Qt.MouseButton.LeftButton and self.identifier != "StartSetup":
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
        self.add_start_setup_tab()
        self.change_tab(0)

    def add_tab_button(self, name, identifier):
        tab_button = CustomTabButton(name, identifier)
        tab_button.tab_clicked.connect(self.tab_changed.emit)
        tab_button.tab_closed.connect(self.tab_removed.emit)
        self.tab_layout.insertWidget(self.tab_layout.count() - 1, tab_button)
        return tab_button
    
    def add_trace(self, tab_id, trace_editor):
        self.add_tab_button(f"Trace {tab_id}", tab_id)
        self.add_content_widget(trace_editor, tab_id)
        # switch to the newly created tab
        self.change_tab(self.tab_layout.count() - 2)
    
    def add_start_setup_tab(self):
        start_setup_tab = CustomTabButton("Start Setup", "StartSetup")
        start_setup_tab.tab_clicked.connect(self.tab_changed.emit)
        self.tab_layout.insertWidget(0, start_setup_tab)
        return start_setup_tab

    def add_content_widget(self, widget, identifier):
        widget.setProperty("identifier", identifier)
        self.content_stack.addWidget(widget)

    def remove_trace(self, tab):
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

    def change_tab(self, index):
        tab_button = self.tab_layout.itemAt(index).widget()
        identifier = tab_button.identifier
        for i in range(self.content_stack.count()):
            content_widget = self.content_stack.widget(i)
            if content_widget.property("identifier") == identifier:
                self.content_stack.setCurrentIndex(i)
                break

        for i in range(self.tab_layout.count()):
            tab_button = self.tab_layout.itemAt(i).widget()
            if isinstance(tab_button, CustomTabButton):
                if i == index:
                    tab_button.setStyleSheet("""font-weight: bold;
                                             background-color: lightgray;
                                             border: 1px solid gray;
                                             border-radius: 4px""")
                else:
                    tab_button.setStyleSheet("""font-weight: normal;
                                             background-color: transparent;
                                             border: 1px solid gray;
                                             border-radius: 4px;""")
    
    def get_tab_buttons(self):
        return [self.tab_layout.itemAt(i).widget() for i in range(self.tab_layout.count()) if isinstance(self.tab_layout.itemAt(i).widget(), CustomTabButton)]

    def get_current_tab_index(self):
        return self.content_stack.currentIndex()


"""CONTROLLER"""


class TabController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.view.tab_changed.connect(self.change_tab)
        self.view.tab_removed.connect(self.remove_tab)

        self.view.scroll_area.setAcceptDrops(True)
        self.view.scroll_area.dragEnterEvent = self.drag_enter_event
        self.view.scroll_area.dragLeaveEvent = self.drag_leave_event
        self.view.scroll_area.dragMoveEvent = self.drag_move_event
        self.view.scroll_area.dropEvent = self.drop_event

        self.view.new_tab_button.clicked.connect(self.add_trace)

    def add_trace(self, trace_editor = None):
        trace_editor = QWidget()  # Placeholder for actual TraceEditor
        self.model.add_trace(trace_editor)
        tab_counter = self.model.tab_counter
        tab_id = str(tab_counter)
        self.view.add_trace(tab_id, trace_editor)

    def remove_tab(self, tab):
        if QMessageBox.question(self.view, 'Confirm Delete', "Do you really want to delete this trace?") == QMessageBox.Yes:
            self.view.remove_trace(tab)
            self.model.remove_trace(tab.identifier)
            self.change_tab(max(0, self.view.get_current_tab_index() - 1))

    def change_tab(self, index):
        self.view.change_tab(index)

    def drag_enter_event(self, e):
        e.accept()

    def drag_leave_event(self, e):
        self.view._drag_target_indicator.hide()
        e.accept()

    def drag_move_event(self, e):
        index = self.find_drop_location(e)
        if index is not None:
            self.view.tab_layout.insertWidget(index, self.view._drag_target_indicator)
            e.source().hide()
            self.view._drag_target_indicator.show()
        e.accept()

    def drop_event(self, e):
        widget = e.source()
        if isinstance(widget, CustomTabButton):
            self.view._drag_target_indicator.hide()
            new_index = self.view.tab_layout.indexOf(self.view._drag_target_indicator)

            if 0 <= new_index < self.view.tab_layout.count() - 1:
                self.view.tab_layout.removeWidget(widget)
                self.view.tab_layout.insertWidget(new_index, widget)

            widget.show()
            self.update_tab_order()
            e.accept()

    def find_drop_location(self, e):
        pos = e.position()
        spacing = self.view.tab_layout.spacing() / 2

        for n in range(1, self.view.tab_layout.count() - 1):
            w = self.view.tab_layout.itemAt(n).widget()
            drop_here = (
                pos.y() >= w.y() - spacing
                and
                pos.y() <= w.y() + w.size().height() + spacing
            )
            if drop_here:
                break

        return n

    def update_tab_order(self):
        ordered_identifiers = [self.view.tab_layout.itemAt(i).widget().identifier
                               for i in range(self.view.tab_layout.count())
                               if isinstance(self.view.tab_layout.itemAt(i).widget(), CustomTabButton)]
        self.model.update_order(ordered_identifiers)

