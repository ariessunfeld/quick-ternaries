"""Plotly Plot Maker for Ternary diagrams"""

from typing import Dict, List

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
        
        # Instantiate a layout
        layout = {}
        
        # Pull the title and apex display names from the start setup view
        title = model.start_setup_model.get_title()
        top_axis_name = model.start_setup_model.get_top_apex_display_name()
        left_axis_name = model.start_setup_model.get_left_apex_display_name()
        right_axis_name = model.start_setup_model.get_right_apex_display_name()

        # Format the title and apex display names
        title = self._format_title(title, model)
        top_axis_name = self._format_top_axis_name(top_axis_name, model)
        left_axis_name = self._format_left_axis_name(left_axis_name, model)
        right_axis_name = self._format_right_axis_name(right_axis_name, model)

        # Add axis labels and title to layout
        self._add_axis_labels_to_layout(layout, top_axis_name, left_axis_name, right_axis_name)
        self._add_title_to_layout(layout, title)

        # Update the figure layout
        fig.update_layout(layout)

        # For each trace in the tab model's order,
        # Make the trace, add it to the figure
        for trace_id in model.tab_model.order:
            if trace_id == 'StartSetup':
                continue
            trace = self.trace_maker.make_trace(model, trace_id)
            fig.add_trace(trace)
    
        # Configure the layout of the figure as necessary
        
        return fig

    def _format_title(self, title: str, model: TernaryModel):
        """Handles blank title case, returning title as-is otherwise"""
        if title.strip() == '':
            return 'Untitled Ternary Diagram'
        else:
            return title

    def _format_top_axis_name(self, top_name: str, model: TernaryModel):
        """Handles blank top apex name cases, attempting to build from ternary type"""
        if top_name.strip() == '':
            top_apex_columns = model.start_setup_model.get_ternary_type().top
            if top_apex_columns:
                return '+'.join(top_apex_columns)
            else:
                return 'Untitled Top Apex'
        else:
            return top_name

    def _format_left_axis_name(self, left_name: str, model: TernaryModel):
        """Handles blank left apex name cases, attempting to build from ternary type"""
        if left_name.strip() == '':
            left_apex_columns = model.start_setup_model.get_ternary_type().left
            if left_apex_columns:
                # Add left whitespace to simulate anchoring at left apex
                str_fmt = '+'.join(left_apex_columns)
                return '<br>' + '&nbsp;'*int(1.6*len(str_fmt)) + str_fmt
            else:
                return '<br>Untitled Left Apex'
        else:
            return '<br>' + left_name
        

    def _format_right_axis_name(self, right_name: str, model: TernaryModel):
        """Handles blank right apex name cases, attempting to build from ternary type"""
        if right_name.strip() == '':
            right_apex_columns = model.start_setup_model.get_ternary_type().right
            if right_apex_columns:
                # Add right whitespace to simulate anchoring at right apex
                str_fmt = '+'.join(right_apex_columns)
                return '<br>' + str_fmt + '&nbsp;'*int(1.6*len(str_fmt))
            else:
                return '<br>Untitled Right Apex'
        else:
            return '<br>' + right_name
        

    def _add_axis_labels_to_layout(
            self, 
            layout: dict, 
            top_axis_name: str, 
            left_axis_name: str, 
            right_axis_name: str):
        """Updates `layout` in-place with axis labels and sum"""

        # Set the color, width, and tick position
        line_style = dict(linecolor='grey', linewidth=1, ticks='outside')

        # Update the layout
        layout.update(
            ternary={
                'sum': 100,
                'aaxis': dict(
                    title=top_axis_name,
                    **line_style
                ),
                'baxis': dict(
                    title=left_axis_name,
                    **line_style
                ) | dict(tickangle=60),
                'caxis': dict(
                    title=right_axis_name,
                    **line_style
                ) | dict(tickangle=-60)
            }
        )

    def _add_title_to_layout(
            self,
            layout: dict,
            title: str):
        """Updates `layout` in-place by adding title dict configuration"""
        layout.update(
            title=dict(
                text=title,
                x=0.5,
                y=0.95,
                xanchor='center',
                yanchor='top'
            )
        )
