"""Connects the TernaryTraceMolarConversionModel with its view"""

import pandas as pd
from PySide6.QtCore import QObject, Signal

from src.models.ternary.trace.bootstrap.error_entry_model import TernaryBootstrapErrorEntryModel
from src.models.ternary.setup.apex_scaling_model import TernaryApexScalingModel
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.trace.tab_model import TraceTabsPanelModel
from src.views.ternary.setup import TernaryApexScalingView
from src.views.ternary.trace.bootstrap.error_entry_view import TernaryBootstrapErrorEntryView

class TernaryBootstrapErrorEntryController(QObject):
    
    def __init__(
            self,
            model: TraceTabsPanelModel,
            view: TernaryBootstrapErrorEntryView):
        super().__init__()

        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        self.view.textChanged.connect(self._on_view_text_changed)
    
    def _on_view_text_changed(self, column: str, error: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.update_error_value(column, error)

    def on_new_custom_column_added(self, column: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.add_column(column)
            self._refresh()

    def on_new_custom_column_removed(self, column: str):
        current_tab = self.model.current_tab
        if current_tab:
            self.model.current_tab.error_entry_model.rem_column(column)
            self._refresh()

    def _refresh(self):
        current_tab = self.model.current_tab
        if current_tab:
            self._set_default_values(current_tab)
            self.view.update_view(self.model.current_tab.error_entry_model.get_sorted_repr())

    def _set_default_values(self, trace_model: TernaryTraceEditorModel):
        """
        Perform a case-insensitive search for '<col> RMSEP' in the df columns for each plotted column.
        If any of these columns exist, set them as the default uncertainties upon initialization.
        """
        series_df = trace_model.series.to_frame().T
        error_entry_model = trace_model.error_entry_model
        lower_case_cols = series_df.columns.str.lower()
        case_insensitive_col_mapping = dict(zip(lower_case_cols, series_df.columns))
        for col, uncertainty in error_entry_model.get_sorted_repr():
            if (not uncertainty) and ((col.lower() + " rmsep") in lower_case_cols):
                rmsep_col = case_insensitive_col_mapping[col.lower() + " rmsep"]
                default_uncertainty = series_df[rmsep_col].values[0]
                default_uncertainty = str(default_uncertainty)
                error_entry_model.update_error_value(col, default_uncertainty)
        #self._refresh()
