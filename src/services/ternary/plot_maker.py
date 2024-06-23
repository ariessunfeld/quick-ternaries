"""Plotly Plot Maker for Ternary diagrams"""

from src.models.ternary.model import TernaryModel
from src.models.ternary.setup.model import TernaryStartSetupModel
from src.services.ternary.trace_maker import TernaryTraceMaker

from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

class TernaryPlotMaker:
    
    def __init__(self):
        self.trace_maker = TernaryTraceMaker()

    def make_plot(self, model: TernaryModel) -> Figure:
        # Initialize a blank figure
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])

        # create a dictionary whose keys are of plotly ternary kwargs
        # which will be used to initialize a global layout for the figure 
        init_ternary = InitializeTernary(model.start_setup_model)
        base_layout = init_ternary.get_base_layout()

        # apply the layout to the blank plotly figure
        fig.update_layout(base_layout)

        
        # For each trace in the tab model's order,
        # Make the trace, add it to the figure
        for trace_id in model.tab_model.order:
            if trace_id == 'StartSetup':
                continue
            trace = self.trace_maker.make_trace(model, trace_id)
            fig.add_trace(trace)
    
        # Configure the layout of the figure as necessary
        
        return fig
    
class InitializeTernary:
    def __init__(self, start_setup: TernaryStartSetupModel):
        self.start_setup = start_setup

        self.base_layout = {}
        self.add_apex_names()
        self.add_title()

    def add_apex_names(self):
        # line_style = dict(linecolor='grey', min=0.01, linewidth=2, ticks='outside')
        top_apex_display_name   = self.start_setup.get_top_apex_display_name()
        left_apex_display_name  = self.start_setup.get_left_apex_display_name()
        right_apex_display_name = self.start_setup.get_right_apex_display_name()

        self.base_layout.update(ternary={
            'sum': 1,
            'aaxis': dict(title =   top_apex_display_name),# **line_style),
            'baxis': dict(title =  left_apex_display_name),# **line_style),
            'caxis': dict(title = right_apex_display_name),# **line_style),
            }
        )

    def add_title(self):
        title = self.start_setup.get_title()
        self.base_layout.update(
            title = dict(
                text=title,
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            )
        )

    def get_base_layout(self):
        return self.base_layout
