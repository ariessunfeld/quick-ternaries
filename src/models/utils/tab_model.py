"""Contains the model for the trace tab scroll area
This model contains the trace editor models for individual traces
"""

import json
from typing import Dict, List, Optional, TYPE_CHECKING

from src.models.ternary.trace import TernaryTraceEditorModel
from src.models.cartesian.trace import CartesianTraceEditorModel
from src.models.corrplot.trace import CorrplotTraceEditorModel


class TabNode:
    """Represents a node for the tab panel model.
    
    Each node contains references to trace editor models for all plot types.
    When shared attributes are updated in one trace editor model, the changes 
    propagate to the other trace editor models. When plot-specific attributes
    are modified in one trace editor, the changes do not propagate.
    """
    def __init__(
            self, 
            tab_id: str,
            ternary_trace_model: Optional[TernaryTraceEditorModel] = None, 
            cartesian_trace_model: Optional[CartesianTraceEditorModel] = None, 
            corrplot_trace_model: Optional[CorrplotTraceEditorModel] = None, 
            # TODO
            zmap_trace_model: Optional[str] = None, 
            depth_profile_trace_model: Optional[str] = None,  
            roseplot_trace_model: Optional[str] = None, 
            area_chart_trace_model: Optional[str] = None):
        
        self.tab_id = tab_id
        self.models = {
            'ternary': ternary_trace_model or TernaryTraceEditorModel(),
            'cartesian': cartesian_trace_model or CartesianTraceEditorModel(),
            'corrplot': corrplot_trace_model or CorrplotTraceEditorModel(),
            # add other plot types here
        }
    
    def update_shared_attributes(self, **kwargs):
        """Update shared attributes across all models."""
        for model in self.models.values():
            for key, value in kwargs.items():
                if hasattr(model, key):
                    setattr(model, key, value)

    def get_model(self, plot_type: str):
        """Get the model for the specified plot type."""
        return self.models.get(plot_type)
    
    def to_json(self) -> dict:
        """Serializes the TabNode to a JSON-compatible dictionary."""
        return {
            'tab_id': self.tab_id,
            'models': {plot_type: model.to_json() for plot_type, model in self.models.items()}
        }

    @classmethod
    def from_json(cls, data: dict):
        """Deserializes the TabNode from a JSON-compatible dictionary."""
        tab_id = data['tab_id']
        models_data = data['models']
        
        # Deserialize each model based on the plot type
        ternary_trace_model = TernaryTraceEditorModel.from_json(models_data.get('ternary', {}))
        cartesian_trace_model = CartesianTraceEditorModel.from_json(models_data.get('cartesian', {}))
        corrplot_trace_model = CorrplotTraceEditorModel.from_json(models_data.get('corrplot', {}))
        # Add other plot types here
        
        return cls(
            tab_id=tab_id,
            ternary_trace_model=ternary_trace_model,
            cartesian_trace_model=cartesian_trace_model,
            corrplot_trace_model=corrplot_trace_model,
            # Add other models here
        )


class TabsPanelModel:
    def __init__(self):
        self.traces: Dict[str,'TernaryTraceEditorModel'] = {}
        self.tabs: Dict[str, TabNode] = {}
        self.order: List[str] = []
        self.tab_counter: int = 0
        self.current_tab: Optional['TernaryTraceEditorModel'] = None

    def add_trace(self, trace_model: 'TernaryTraceEditorModel') -> str:
        """Increments tab count to add a trace to the dict and the order
        Returns the tab_id for the just-added trace
        """
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        self.traces[tab_id] = trace_model
        self.order.append(tab_id)
        return tab_id
    
    def add_tab(self, tab: Optional[TabNode]) -> str:
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        if tab:
            tab.tab_id = tab_id
            self.tabs[tab_id] = tab
        else:
            self.tabs[tab_id] = TabNode(tab_id)
        self.order.append(tab_id)
        return tab_id

    def remove_trace(self, tab_id: str):
        """Removes a trace from the dict and the order"""
        if tab_id in self.traces:
            del self.traces[tab_id]
        if tab_id in self.order:
            self.order.remove(tab_id)

    def remove_tab(self, tab_id: str):
        if tab_id in self.tabs:
            del self.tabs[tab_id]
        if tab_id in self.order:
            self.order.remove(tab_id)

    def get_trace(self, tab_id: str) -> 'TernaryTraceEditorModel':
        """Returns a reference to a specific trace"""
        return self.traces.get(tab_id)
    
    def get_tab(self, tab_id: str) -> TabNode:
        """Returns a reference to a specific tab node"""
        return self.tabs.get(tab_id)

    def update_order(self, new_order: list):
        self.order = new_order

    def get_all_traces(self) -> Dict[str, 'TernaryTraceEditorModel']:
        """Returns all traces"""
        return {id: self.traces[id] for id in self.order}
    
    def get_all_tabs(self) -> Dict[str, TabNode]:
        """Returns all tabs"""
        return {id: self.tabs[id] for id in self.order}
    
    def set_current_tab(self, tab_id: str):
        """Points self.current_tab to traces[tab_id]"""
        self.current_tab = self.traces.get(tab_id)

    def __set_current_tab(self, tab_id: str):
        """Points self.current_tab to traces[tab_id]"""
        self.current_tab = self.tabs.get(tab_id)

    def to_json(self) -> dict:
        return {
            'order': self.order,
            'tab_counter': self.tab_counter,
            'tabs': {tab_id: tab.to_json() for tab_id, tab in self.tabs.items()}
        }

    @classmethod
    def from_json(cls, data: dict):
        model = cls()
        model.order = data.get('order')
        model.tab_counter = data.get('tab_counter')
        model.tabs = {tab_id: TabNode.from_json(tab_data) for tab_id, tab_data in data.get('tabs', {}).items()}
        return model

    def __str__(self) -> str:
        return json.dumps(self.to_json(), indent=4)
