import json
from typing import TYPE_CHECKING, List, Dict, Optional

from PySide6.QtCore import QObject, Slot
import pandas as pd
import numpy as np

from src3.models.error_entry_model import ErrorEntryModel
from src3.models.trace_editor_model import TraceEditorModel
from src3.models.setup_menu_model import SetupMenuModel

if TYPE_CHECKING:
    from src3.app import MainWindow



class WorkspaceManager:
    VERSION = "1.0"

    def __init__(self, traces: list, setup_model: "SetupMenuModel", order=None):
        self.traces = traces
        self.setup_model = setup_model
        self.order = (
            order if order is not None else [str(i) for i in range(len(traces))]
        )

    def to_dict(self) -> dict:
        """Convert workspace to a dictionary, ensuring DataframeManager is not
        included."""
        # Make a clean copy of the setup model
        setup_dict = self.setup_model.to_dict()

        # Process traces: convert each trace model to dict and ensure datafiles are clean
        traces_dicts = []
        for trace in self.traces:
            trace_dict = trace.to_dict()
            # Ensure datafile in trace doesn't contain df_id
            if "datafile" in trace_dict and isinstance(trace_dict["datafile"], dict):
                if "df_id" in trace_dict["datafile"]:
                    trace_dict["datafile"].pop("df_id")
            traces_dicts.append(trace_dict)

        return {
            "version": self.VERSION,
            "order": self.order,
            "traces": traces_dicts,
            "setup": setup_dict,
        }

    def save_to_file(self, filename: str):
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_dict(cls, d: dict):
        traces = [TraceEditorModel.from_dict(item) for item in d.get("traces", [])]
        setup = SetupMenuModel.from_dict(d.get("setup", {}))
        order = d.get("order", None)
        return cls(traces, setup, order=order)

    @classmethod
    def load_from_file(cls, filename: str):
        with open(filename, "r", encoding='utf-8') as f:
            d = json.load(f)
        return cls.from_dict(d)


class PlotlyInterface(QObject):
    def __init__(self):
        super().__init__()
        self.selected_indices = []

    @Slot(list)
    def receive_selected_indices(self, indices: list):
        self.selected_indices = indices

    def get_indices(self) -> List:
        return self.selected_indices.copy()
    

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ErrorEntryModel):
            return obj.to_dict()
        elif isinstance(obj, pd.Series):
            return obj.to_json()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.number):
            return float(obj)
        return super().default(obj)
    
class ZmapPlotHandler(QObject):
    """Handler for double-click events in Zmap plots."""
    
    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window

    @Slot(str, str, str)
    def cellDoubleClicked(self, category_value, target, other):
        """
        Handle a double-click on a Zmap cell.
        
        Args:
            category_value: The value of the categorical column
            target: The target column (x-axis)
            other: The other column (y-axis)
        """
        print(f"Double clicked cell: {self.main_window.setupMenuModel.axis_members.categorical_column}={category_value}, target={target}, other={other}")
        self.main_window.generate_scatter_plot(category_value, target, other)
    
    @Slot(str)
    def debugLog(self, message):
        """
        Handle debug messages from JavaScript.
        
        Args:
            message: The debug message
        """
        print(f"JS Debug: {message}")

class ColorPalette:
    """
    Manages a palette of colors for traces, with intelligent tracking of used colors.
    """
    # Tab10-equivalent colors as hex strings (lowercase for consistent comparisons)
    TAB10_COLORS = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
    ]

    set2_colors = [
        "#66c2a5",  # Greenish teal
        "#fc8d62",  # Soft orange
        "#8da0cb",  # Muted blue
        "#e78ac3",  # Soft pink
        "#a6d854",  # Light green
        "#ffd92f",  # Yellow
        "#e5c494",  # Beige
        "#b3b3b3",  # Gray
    ]

    dark2_colors = [
        "#1b9e77",  # Teal green
        "#d95f02",  # Burnt orange
        "#7570b3",  # Muted purple
        "#e7298a",  # Bright pink
        "#66a61e",  # Olive green
        "#e6ab02",  # Mustard yellow
        "#a6761d",  # Brown
        "#666666",  # Dark gray
    ]

    tableau_colorblind_10 = [
        "#117733",  # Dark green
        "#44AA99",  # Teal
        "#88CCEE",  # Light blue
        "#DDCC77",  # Light yellow
        "#CC6677",  # Reddish pink
        "#AA4499",  # Purple
        "#882255",  # Dark red
        "#DDDDDD",  # Light gray
        "#999933",  # Olive green
        "#332288",  # Deep blue
    ]
    
    def __init__(self):
        self.colors = self.tableau_colorblind_10.copy()
        self.used_colors = set()  # Track which colors are currently in use
    
    def next_color(self):
        """Get the next available color in the palette."""
        # Find the first unused color
        for color in self.colors:
            normalized_color = color.lower()
            if normalized_color not in self.used_colors:
                self.used_colors.add(normalized_color)
                return color
        
        # If all colors are used, pick the least recently used one and recycle it
        # For simplicity, we'll just use the first color in our list
        first_color = self.colors[0]
        return first_color
    
    def release_color(self, color):
        """Release a color back to the available pool."""
        if color:
            self.used_colors.discard(color.lower())
    
    def mark_color_used(self, color):
        """Mark a color as being used."""
        if color:
            self.used_colors.add(color.lower())
    
    def reset(self):
        """Reset all color tracking."""
        self.used_colors.clear()
    
    def sync_with_traces(self, traces):
        """Update used colors based on a list of trace models."""
        self.reset()
        for model in traces:
            is_contour = getattr(model, "is_contour", False)
            if not is_contour:  # Only track non-contour traces
                trace_color = getattr(model, "trace_color", None)
                if trace_color:
                    self.mark_color_used(trace_color)
