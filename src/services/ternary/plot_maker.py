"""Plotly Plot Maker for Ternary diagrams"""

from typing import Dict, List

from src.models.ternary.model import TernaryModel
from src.models.ternary.setup.model import TernaryStartSetupModel, TernaryType
from src.services.ternary.trace_maker import TernaryTraceMaker

import plotly.io as pio
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure
import plotly.io as pio

class TernaryPlotMaker:
    
    def __init__(self):
        self.trace_maker = TernaryTraceMaker()

    def make_plot(self, model: TernaryModel) -> Figure:
        # Initialize a blank figure
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])
        
        # Instantiate a layout
        layout = {'paper_bgcolor': 'rgba(0, 0, 0, 0)'}
        
        # Pull the title and apex display names from the start setup view
        title = model.start_setup_model.get_title()
        ternary_type = model.start_setup_model.get_ternary_type()
        top_axis_name = model.start_setup_model.get_top_apex_display_name()
        left_axis_name = model.start_setup_model.get_left_apex_display_name()
        right_axis_name = model.start_setup_model.get_right_apex_display_name()

        # Format the title and apex display names
        title = self._format_title(title, ternary_type)
        top_axis_name = self._format_top_axis_name(top_axis_name, ternary_type, model)
        left_axis_name = self._format_left_axis_name(left_axis_name, ternary_type, model)
        right_axis_name = self._format_right_axis_name(right_axis_name, ternary_type, model)

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
    
    def save_plot(self, fig: Figure, filepath: str, dpi: float|None=None):
        # Get the extension from the selected filter if the file_name has no extension
        if filepath.endswith('.html'):
            # Save interactive plot as HTML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fig.to_html())
        else:
            # Save static image with specified DPI
            for trace in fig.data:
                if 'marker' in trace and 'size' in trace.marker:
                    original_size = trace.marker.size
                    trace.marker.size = original_size / 1.8  # Halving the size

            pio.write_image(fig, filepath, scale=dpi / 72.0)

            for trace in fig.data:
                if 'marker' in trace and 'size' in trace.marker:
                    modified_size = trace.marker.size
                    trace.marker.size = 1.8 * modified_size
    
    def _format_title(self, title: str, ternary_type: TernaryType):
        """Handles blank title case, returning title as-is otherwise"""
        if title.strip() == '':
            return ternary_type.get_short_formatted_name() + ' Ternary Diagram'
        else:
            return title

    def _format_subscripts(self, oxide: str) -> str:
        """Formats numeric subscripts in a chemical formula."""
        if oxide.lower() == 'feot':  # Special case, FeOT
            return "FeO<sub>T</sub>"
        return "".join('<sub>' + x + '</sub>' if x.isnumeric() else x for x in oxide)

    def _build_str_fmt(self, apex_columns: List[str], scale_map: dict, unique_scale_vals: List[int | float]) -> str:
        """Builds the formatted string based on scaling factors and apex columns."""
        if len(unique_scale_vals) == 1 and unique_scale_vals[0] != 1:
            return f"{unique_scale_vals[0]}&times;({'+'.join(map(self._format_subscripts, apex_columns))})"

        ret = []
        for unique_val in unique_scale_vals:
            cols_with_this_val = [c for c, v in scale_map.items() if v == unique_val and c in apex_columns]
            if unique_val != 1:
                ret.append(f"{unique_val}&times;({'+'.join(map(self._format_subscripts, cols_with_this_val))})")
            else:
                ret.extend(map(self._format_subscripts, cols_with_this_val))
        return '+'.join(ret)

    def _format_axis_name(self, custom_name: str, default_name: str, apex_columns: List[str], model: TernaryModel) -> str:
        """Handles blank apex name cases, attempting to build from ternary type."""
        if custom_name.strip():
            return custom_name
        
        if not apex_columns:
            return default_name
        
        if model.start_setup_model.scale_apices_is_checked:
            scale_map = self.trace_maker.get_scaling_map(model)
            unique_scale_vals = sorted(set(scale_map[col] for col in apex_columns), reverse=True)
            return self._build_str_fmt(apex_columns, scale_map, unique_scale_vals)
        
        return '+'.join(map(self._format_subscripts, apex_columns))

    def _format_top_axis_name(self, top_name: str, ternary_type: TernaryType, model: TernaryModel) -> str:
        top_apex_columns = ternary_type.get_top()
        str_fmt = self._format_axis_name(top_name, 'Untitled Top Apex', top_apex_columns, model)
        return str_fmt
        
    def _format_left_axis_name(self, left_name: str, ternary_type: TernaryType, model: TernaryModel) -> str:
        left_apex_columns = ternary_type.get_left()
        str_fmt = self._format_axis_name(left_name, 'Untitled Left Apex', left_apex_columns, model)
        return '<br>' + '&nbsp;'*int(0.6*len(str_fmt)) + str_fmt
        
    def _format_right_axis_name(self, right_name: str, ternary_type: TernaryType, model: TernaryModel) -> str:
        right_apex_columns = ternary_type.get_right()
        str_fmt = self._format_axis_name(right_name, 'Untitled Right Apex', right_apex_columns, model)
        return '<br>' + str_fmt + '&nbsp;'*int(0.6*len(str_fmt))
        

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
