"""Plotly Plot Maker for Ternary diagrams"""

from src.models.ternary.model import TernaryModel
from src.services.ternary.trace_maker import TernaryTraceMaker

from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

class TernaryPlotMaker:
    
    def __init__(self):
        self.trace_maker = TernaryTraceMaker()

    def make_plot(self, model: TernaryModel) -> Figure:
        # Initialize a figure
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])
        
        # For each trace in the tab model's order,
        # Make the trace, add it to the figure
        for trace_id in model.tab_model.order:
            if trace_id == 'StartSetup':
                continue
            trace = self.trace_maker.make_trace(model, trace_id)
            fig.add_trace(trace)

        # Configure the layout of the figure as necessary
        
        return fig
