"""Controller for the FilterTabView sections"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMessageBox

from src.models.ternary.trace.filter import FilterModel

if TYPE_CHECKING:
    from src.models.ternary.trace import TraceTabsPanelModel, TernaryTraceEditorModel
    from src.models.utils.data_models import DataLibrary
    from src.views.ternary.trace.filter import FilterTabView

class FilterTabController(QObject):
    
    change_filter_tab_signal = Signal(FilterModel)
    change_to_filter_setup_signal = Signal()
    trace_data_selection_handled = Signal()

    def __init__(self, model: 'TraceTabsPanelModel', view: 'FilterTabView'):
        super().__init__()
        self.model = model
        self.view = view

        self.data_library_reference = None

        self.setup_connections()

    def set_data_library_reference(self, ref: 'DataLibrary'):
        self.data_library_reference = ref

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
        if QMessageBox.question(
                self.view, 
                'Confirm Delete', 
                "Do you really want to delete this filter?") == QMessageBox.Yes:
            self.view.remove_tab_from_view(tab_id)
            self.model.current_tab.filter_tab_model.remove_filter(tab_id)
            # Always change back to start setup after deleting a filter tab
            self.change_filter_tab('StartSetup')

    def change_trace_tab(self, trace_model: 'TernaryTraceEditorModel'):
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

    def handle_trace_selected_data_event(self, value: str):
        """Update all filter models managed by this controller"""
        data_file = self.data_library_reference.get_data_from_shortname(value)
        if data_file:
            available_columns = data_file.get_columns()
            for filter_tab_id in self.model.current_tab.filter_tab_model.order:
                self.model.current_tab.filter_tab_model.filters[filter_tab_id].available_columns = available_columns
                if self.model.current_tab.filter_tab_model.filters[filter_tab_id].selected_column not in available_columns:
                    self.model.current_tab.filter_tab_model.filters[filter_tab_id].selected_column = None

        self.emit_completed_trace_selected_data_handling()

    def emit_completed_trace_selected_data_handling(self):
        self.trace_data_selection_handled.emit()


