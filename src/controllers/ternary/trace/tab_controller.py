"""Controller for the Tab (trace scroll area) sections"""

from typing import List, Dict, Optional

from src.models.ternary.trace.tab_model import TabModel
from src.views.ternary.trace.trace_scroll_area import TabView
from src.views.ternary.trace.trace_scroll_area import DraggableTab

from src.models.ternary.trace.model import TernaryTraceEditorModel

from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Signal, QObject

class TabController(QObject):
    
    change_tab_signal = Signal(TernaryTraceEditorModel)

    def __init__(self, model: TabModel, view: TabView):
        super().__init__()
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):

        # Signals
        self.view.tab_changed.connect(self.change_tab)
        self.view.tab_removed.connect(self.remove_tab)

        # Mouse events
        self.view.scroll_area.setAcceptDrops(True)
        self.view.scroll_area.dragEnterEvent = self.drag_enter_event
        self.view.scroll_area.dragLeaveEvent = self.drag_leave_event
        self.view.scroll_area.dragMoveEvent = self.drag_move_event
        self.view.scroll_area.dropEvent = self.drop_event

        # Add trace button
        self.view.new_tab_button.clicked.connect(self._add_trace_button_event)

    def _add_trace_button_event(self, event: bool):
        self.add_trace()
        
    def add_trace(self, trace_model: Optional[TernaryTraceEditorModel] = None):
        if trace_model is None:
            trace_model = TernaryTraceEditorModel()
        print(f'Inside tab controller add_trace, and {trace_model=}')
        tab_id = self.model.add_trace(trace_model)
        self.view.add_trace_tab_to_view(f'Untitled {tab_id}', tab_id)
        self.change_tab(tab_id)

    def remove_tab(self, tab_id: str):
        if QMessageBox.question(self.view, 'Confirm Delete', "Do you really want to delete this trace?") == QMessageBox.Yes:
            self.view.remove_tab_from_view(tab_id)
            self.model.remove_trace(tab_id)
            self.change_tab('StartSetup') # always change back to start setup after deleting a trace tab

    def change_tab(self, tab_id: str):
        print('tab controller change_tab called')
        # Set the selected tab to the one just clicked
        self.view.set_selected_tab(tab_id)
        self.model.set_current_tab(tab_id)
        current_trace_model = self.model.get_trace(tab_id)
        print(f'{current_trace_model=}')
        self.emit_change_tab(current_trace_model)
        # Change the main window widget to trace view
        # Populate the trace view widgets with this model's info

    def emit_change_tab(self, trace_model: TernaryTraceEditorModel):
        self.change_tab_signal.emit(trace_model)

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
        if isinstance(widget, DraggableTab):
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
                               if isinstance(self.view.tab_layout.itemAt(i).widget(), DraggableTab)]
        self.model.update_order(ordered_identifiers)
