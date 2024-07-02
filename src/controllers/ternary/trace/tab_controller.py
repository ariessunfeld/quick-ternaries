"""Controller for the Tab (trace scroll area) sections"""

from typing import Optional, List, Dict

from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.setup.model import TernaryType
from src.views.ternary.trace.trace_scroll_area import TabView
from src.views.ternary.trace.trace_scroll_area import DraggableTab

from src.models.ternary.trace.model import TernaryTraceEditorModel

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Signal, QObject

class TabController(QObject):

    change_tab_signal = Signal(TernaryTraceEditorModel)
    change_to_start_setup_signal = Signal()

    def __init__(self, model: TraceTabsPanelModel, view: TabView):
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
        tab_id = self.model.add_trace(trace_model)
        trace_model.legend_name = f'Scatter (tr {tab_id})'
        self.view.add_trace_tab_to_view(f'Scatter (tr {tab_id})', tab_id)
        self.change_tab(tab_id)

    def add_bootstrap_trace(
            self, 
            trace_model: Optional[TernaryTraceEditorModel] = None,
            selected_indices: Optional[List[Dict[str, int]]] = None,
            error_entry_cols: Optional[List[str]] = None) -> bool:
        
        curves_sorted: Dict[int: List[int]] = {-1: []}
        
        # TODO handle case where selected_indices is None
        for inner_dict in selected_indices:
            curve_number, point_index = inner_dict['curveNumber'], inner_dict['pointIndex']
            if curve_number in curves_sorted:
                curves_sorted[curve_number].append(point_index)
            else:
                curves_sorted[curve_number] = [point_index]
        max_curve_number = max(curves_sorted)
        number_of_points = len(curves_sorted[max_curve_number])
        
        if number_of_points != 1:
            return False

        # Start setup only becomes part of order after a tab is clicked
        order = self.model.order.copy()
        if 'StartSetup' in order:
            tab_id = self.model.order[1:][max_curve_number]
        else:
            tab_id = self.model.order[max_curve_number]

        # Get source model
        source_trace_model = self.model.get_trace(tab_id)

        # Extract data file from source model
        trace_data_file = source_trace_model.selected_data_file

        # TODO apply filters and heatmap sorting to copy of data file
        # ...

        # Get the series from the [filtered and sorted] data file
        series = trace_data_file.get_series(curves_sorted[max_curve_number][0])

        # Instantiate a new bootstrap trace model with data from source model
        new_trace_model = TernaryTraceEditorModel(
            kind='bootstrap', 
            series=series, 
            wtp_to_molar_checked=source_trace_model.wtp_to_molar_checked)
        
        # Populate the error model
        for col in error_entry_cols:
            new_trace_model.error_entry_model.add_column(col)

        # Get the tab ID that results from adding the new trace to the tabs model
        tab_id = self.model.add_trace(new_trace_model)

        # Add the new trace to the view and change the tab to reflect the addition
        new_trace_model.legend_name = f'Contour (tr {tab_id})'
        self.view.add_trace_tab_to_view(f'Contour (tr {tab_id})', tab_id)
        self.change_tab(tab_id)

    def remove_tab(self, tab_id: str, ask=True):
        if not ask or QMessageBox.question(
                self.view, 
                'Confirm Delete', 
                "Do you really want to delete this trace?") == QMessageBox.Yes:
            self.view.remove_tab_from_view(tab_id)
            self.model.remove_trace(tab_id)
            self.change_tab('StartSetup') # always change back to start setup after deleting a trace tab

    def change_tab(self, tab_id: str):
        if tab_id == 'StartSetup':
            # Emit signal: back to start setup
            self.change_to_start_setup_signal.emit()
            self.view.set_selected_tab(tab_id)
            self.model.set_current_tab(tab_id)
        else:
            # Set the selected tab to the one just clicked visually
            # Tell the model about this change
            # Get the current trace model from the tab model
            # Emit a signal with the trace model
            self.view.set_selected_tab(tab_id)
            self.model.set_current_tab(tab_id)
            current_trace_model = self.model.get_trace(tab_id)
            self.emit_change_tab(current_trace_model)

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
