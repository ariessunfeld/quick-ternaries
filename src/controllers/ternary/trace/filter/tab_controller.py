"""Controller for the FilterTabView sections"""

from typing import Optional
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox
from src.views.ternary.trace.filter.filter_tab_view import FilterTabView
from src.models.ternary.trace.filter.model import FilterModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.models.ternary.trace.model import TernaryTraceEditorModel

class FilterTabController(QObject):

    change_filter_tab_signal = Signal(FilterModel)
    change_to_filter_setup_signal = Signal()

    def __init__(self, model: TraceTabsPanelModel, view: FilterTabView):
        super().__init__()
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        # Signals
        self.view.tab_changed.connect(self.change_filter_tab)
        self.view.tab_removed.connect(self.remove_tab)
        self.view.new_tab_button.clicked.connect(lambda: self.add_filter())

    def add_filter(self, filter_model: Optional[FilterModel] = None):
        if filter_model is None:
            filter_model = FilterModel()
        tab_id = self.model.current_tab.filter_tab_model.add_filter(filter_model)
        self.view.add_tab_to_view(f'Filter {tab_id}', tab_id)
        self.change_filter_tab(tab_id)

    def remove_tab(self, tab_id: str):
        if QMessageBox.question(self.view, 'Confirm Delete', "Do you really want to delete this filter?") == QMessageBox.Yes:
            self.view.remove_tab_from_view(tab_id)
            self.model.current_tab.filter_tab_model.remove_filter(tab_id)
            self.change_filter_tab('StartSetup')  # Always change back to start setup after deleting a filter tab

    def change_trace_tab(self, trace_model: TernaryTraceEditorModel):
        self.view.clear()
        filter_tab_model = trace_model.filter_tab_model
        for identifier in filter_tab_model.order:
            name = f'Filter {identifier}'
            self.view.add_tab_to_view(name, identifier)
        self.view.set_selected_tab('StartSetup')

    def change_filter_tab(self, tab_id: str):
        if tab_id == 'StartSetup':
            # Emit back to start setup
            self.change_to_filter_setup_signal.emit()
            self.view.set_selected_tab(tab_id)
            self.model.current_tab.filter_tab_model.set_current_tab(tab_id)
        else:
            # Set the selected tab to the one just clicked visually
            self.view.set_selected_tab(tab_id)
            # Tell the model about this change
            self.model.current_tab.filter_tab_model.set_current_tab(tab_id)
            # Get the current filter model from the tab model
            current_filter_model = self.model.current_tab.filter_tab_model.get_filter(tab_id)
            # Emit a signal with the filter model
            self.emit_change_filter_tab(current_filter_model)

    def emit_change_filter_tab(self, filter_model: FilterModel):
        self.change_filter_tab_signal.emit(filter_model)
