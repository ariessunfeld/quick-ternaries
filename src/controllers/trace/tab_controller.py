"""Controller for the Tab (trace scroll area) sections"""

from src.models.trace.tab_model import TabModel
from src.views.trace.trace_scroll_area import TabView
from src.views.trace.trace_scroll_area import CustomTabButton

from PySide6.QtWidgets import QWidget, QMessageBox

class TabController:
    def __init__(self, model: TabModel, view: TabView):
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
