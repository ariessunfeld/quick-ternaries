"""Contains the model for the filter tab scroll area
This model contains the filter editor models for individual filters
"""

from typing import Dict, List, Optional
from src.models.ternary.trace.filter.model import FilterModel

class FilterTabsPanelModel:
    def __init__(self):
        self.filters: Dict[str, FilterModel] = {}
        self.order: List[str] = []
        self.tab_counter: int = 0
        self.current_tab: Optional[FilterModel] = None

    def add_filter(self, filter_model: FilterModel) -> str:
        """Increments tab count to add a filter to the dict and the order
        Returns the tab_id for the just-added filter
        """
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        self.filters[tab_id] = filter_model
        self.order.append(tab_id)
        return tab_id

    def remove_filter(self, tab_id: str):
        """Removes a filter from the dict and the order"""
        if tab_id in self.filters:
            del self.filters[tab_id]
        if tab_id in self.order:
            self.order.remove(tab_id)

    def get_filter(self, tab_id: str) -> FilterModel:
        """Returns a reference to a specific filter"""
        return self.filters.get(tab_id)

    def update_order(self, new_order: list):
        self.order = new_order

    def get_all_filters(self) -> Dict[str, FilterModel]:
        """Returns all filters"""
        return {id: self.filters[id] for id in self.order}
    
    def set_current_tab(self, tab_id: str):
        """Points self.current_tab to filters[tab_id]"""
        self.current_tab = self.filters.get(tab_id)

    def __str__(self) -> str:
        filters_str = {k: str(v) for k, v in self.filters.items()}
        return f"filters: {filters_str},\norder: {self.order},\ntab_counter: {self.tab_counter}"