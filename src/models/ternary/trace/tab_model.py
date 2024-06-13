"""Contains the model for the trace tab scroll area
This model contains the trace editor models for individual traces
"""

from typing import Dict, List, Optional
from src.models.ternary.trace.model import TernaryTraceEditorModel

class TraceTabsPanelModel:
    def __init__(self):
        self.traces: Dict[str,TernaryTraceEditorModel] = {}
        self.order: List[str] = []
        self.tab_counter: int = 0
        self.current_tab: Optional[TernaryTraceEditorModel] = None

    def add_trace(self, trace_model: TernaryTraceEditorModel) -> str:
        """Increments tab count to add a trace to the dict and the order
        Returns the tab_id for the just-added trace
        """
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        self.traces[tab_id] = trace_model
        self.order.append(tab_id)
        return tab_id

    def remove_trace(self, tab_id: str):
        """Removes a trace from the dict and the order"""
        if tab_id in self.traces:
            del self.traces[tab_id]
        if tab_id in self.order:
            self.order.remove(tab_id)

    def get_trace(self, tab_id: str) -> TernaryTraceEditorModel:
        """Returns a reference to a specific trace"""
        return self.traces.get(tab_id)

    def update_order(self, new_order: list):
        self.order = new_order

    def get_all_traces(self) -> Dict[str, TernaryTraceEditorModel]:
        """Returns all traces"""
        return {id: self.traces[id] for id in self.order}
    
    def set_current_tab(self, tab_id: str):
        """Points self.current_tab to traces[tab_id]"""
        self.current_tab = self.traces.get(tab_id)

    def __str__(self) -> str:
        return f"""traces: {self.traces},
order: {self.order},
tab_counter: {self.tab_counter}
"""
