
from typing import List, Optional

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objects import Figure, Layout

from src3.services.cartesian_trace_maker import CartesianTraceMaker

# TODO import and use the CartesianContourTraceMaker


class CartesianPlotMaker:
    """
    Creates and configures Plotly Cartesian diagrams based on model settings.
    """
    
    def __init__(self):
        """Initialize the plot maker with supporting objects."""
        self.trace_maker = CartesianTraceMaker()
    
    def make_plot(self, setup_model, trace_models) -> Figure:
        """
        Creates a complete Plotly figure for a Cartesian diagram.
        
        Args:
            setup_model: The SetupMenuModel containing global plot settings
            trace_models: List of trace models
            
        Returns:
            A Plotly Figure object
        """
        layout = self._create_layout(setup_model)
        traces = self._create_traces(setup_model, trace_models)
        return Figure(data=traces, layout=layout)

    def _create_layout(self, setup_model) -> Layout:
        """
        Creates the Plotly layout for the Cartesian diagram.
        """
        # Create base layout
        layout = go.Layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#e3ecf7",
            margin=dict(l=80, r=80, t=80, b=80),
            xaxis=dict(
                title="",
                showgrid=True,
                zeroline=True,
                showline=True,
                linecolor='#888',
                linewidth=1,
                mirror=True
            ),
            yaxis=dict(
                title="",
                showgrid=True,
                zeroline=True,
                showline=True,
                linecolor='#888',
                linewidth=1,
                mirror=True
            ),
            # legend=dict(
            #     x=1,
            #     y=1,
            #     xanchor='right',
            #     yanchor='top',
            #     bordercolor='#888',
            #     borderwidth=1
            # )
        )
        
        # Apply advanced settings if available
        if hasattr(setup_model, 'advanced_settings'):
            self._apply_advanced_settings(layout, setup_model.advanced_settings)
        
        # Add axis labels and title
        self._add_axis_labels(layout, setup_model)
        self._add_title(layout, setup_model)
        
        return layout
        
    def _apply_advanced_settings(self, layout, advanced_settings):
        """
        Applies advanced settings to the layout.
        """
        # Background colors
        if hasattr(advanced_settings, 'paper_color'):
            layout.paper_bgcolor = self._convert_hex_to_rgba(advanced_settings.paper_color)
        
        if hasattr(advanced_settings, 'background_color'):
            layout.plot_bgcolor = self._convert_hex_to_rgba(advanced_settings.background_color)
        
        # Font settings
        font_settings = dict(
            family=advanced_settings.font if hasattr(advanced_settings, 'font') else 'Arial',
            size=advanced_settings.font_size if hasattr(advanced_settings, 'font_size') else 12,
            color=advanced_settings.font_color if hasattr(advanced_settings, 'font_color') else '#000000'
        )
        
        layout.font = font_settings
        
        # Configure axis settings
        axis_settings = dict(
            showline=True,
            linecolor='#888',
            linewidth=1,
            showgrid=True,
            gridcolor=advanced_settings.grid_color if hasattr(advanced_settings, 'grid_color') else '#888',
            showticklabels=getattr(advanced_settings, 'show_tick_marks', True),
            ticks='outside' if getattr(advanced_settings, 'show_tick_marks', True) else '',
            tickfont=font_settings,
            mirror=True
        )
        
        layout.xaxis.update(axis_settings)
        layout.yaxis.update(axis_settings)
        
        # Title font
        if layout.title:
            layout.title.font = font_settings
        
        # Legend position
        # if hasattr(advanced_settings, 'legend_position'):
        #     position = advanced_settings.legend_position.lower()
        #     layout.legend.font = font_settings
            
        #     if 'top' in position:
        #         layout.legend.y = 1
        #         layout.legend.yanchor = 'top'
        #     elif 'bottom' in position:
        #         layout.legend.y = 0
        #         layout.legend.yanchor = 'bottom'
        #     else:
        #         layout.legend.y = 0.5
        #         layout.legend.yanchor = 'middle'
                
        #     if 'left' in position:
        #         layout.legend.x = 0
        #         layout.legend.xanchor = 'left'
        #     elif 'right' in position:
        #         layout.legend.x = 1
        #         layout.legend.xanchor = 'right'
        #     else:
        #         layout.legend.x = 0.5
        #         layout.legend.xanchor = 'center'
                
    def _add_axis_labels(self, layout: Layout, setup_model):
        """
        Adds formatted axis labels to the layout.
        """
        # Get column lists for each axis
        x_columns = setup_model.axis_members.x_axis
        y_columns = setup_model.axis_members.y_axis
        
        # Get custom axis labels if available
        x_label = setup_model.plot_labels.x_axis_label if hasattr(setup_model.plot_labels, 'x_axis_label') else ""
        y_label = setup_model.plot_labels.y_axis_label if hasattr(setup_model.plot_labels, 'y_axis_label') else ""
        
        # Format axis labels
        x_axis_name = self._format_axis_name(x_label, x_columns, setup_model, 'x')
        y_axis_name = self._format_axis_name(y_label, y_columns, setup_model, 'y')
        
        # Update layout with axis names
        layout.xaxis.title.text = x_axis_name
        layout.yaxis.title.text = y_axis_name
        
    def _add_title(self, layout: Layout, setup_model):
        """
        Adds a title to the layout.
        """
        title = setup_model.plot_labels.title if hasattr(setup_model.plot_labels, 'title') else ""
        
        # If title is empty, generate a default title
        if not title.strip():
            title = "Cartesian Plot"
        
        # Update layout with title
        layout.update(title=dict(text=title, x=0.5, y=0.95, xanchor='center', yanchor='top'))
        
    def _create_traces(self, setup_model, trace_models) -> List[go.Scatter]:
        """
        Creates all traces for the plot.
        """
        traces = []
        
        for trace_model in trace_models:
            try:
                trace = self.trace_maker.make_trace(setup_model, trace_model)
                traces.append(trace)
            except Exception as e:
                print(f"Error creating trace {trace_model.trace_name}: {e}")
        
        return traces
        
    def _format_axis_name(self, custom_name: str, axis_columns: List[str], setup_model, axis: str) -> str:
        """
        Formats an axis name with proper subscripts and scaling.
        """
        # Use custom name if provided
        if custom_name and custom_name.strip():
            return custom_name
        
        # Otherwise format based on columns
        if not axis_columns:
            return f'{"X" if axis == "x" else "Y"}-Axis'
        
        # Check if we have a formatter from AxisFormatter
        if hasattr(self, 'axis_formatter') and self.axis_formatter:
            # Check if scaling is enabled
            if hasattr(setup_model, 'column_scaling') and hasattr(setup_model.column_scaling, 'scaling_factors'):
                scale_map = {}
                
                # Get scaling factors for x and y axes
                axis_name = f"{axis}_axis"
                if axis_name in setup_model.column_scaling.scaling_factors:
                    scale_map.update(setup_model.column_scaling.scaling_factors[axis_name])
                
                # Only apply scaling if there are non-default scale factors
                use_scaling = any(value != 1.0 for value in scale_map.values() if value is not None)
                
                if use_scaling:
                    return self.axis_formatter.format_scaled_name(axis_columns, scale_map)
            
            # If no scaling, format with subscripts
            if hasattr(self.axis_formatter, 'format_subscripts'):
                return ' + '.join(map(self.axis_formatter.format_subscripts, axis_columns))
        
        # Default formatting: just join column names
        return ' + '.join(axis_columns)
        
    def save_plot(self, fig: Figure, filepath: str, dpi: Optional[float] = None):
        """
        Saves the plot to a file.
        """
        # Save as interactive HTML
        if filepath.endswith('.html'):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fig.to_html())
        # Save as static image
        else:
            # Reduce marker size for better appearance in static images
            for trace in fig.data:
                if hasattr(trace, 'marker') and hasattr(trace.marker, 'size'):
                    # Save original size
                    if isinstance(trace.marker.size, (int, float)):
                        trace.marker.size = trace.marker.size / 1.8
            
            # Set scale based on DPI
            scale = 1.0
            if dpi is not None:
                scale = dpi / 72.0
                
            # Write the image
            pio.write_image(fig, filepath, scale=scale)
            
            # Restore original marker sizes
            for trace in fig.data:
                if hasattr(trace, 'marker') and hasattr(trace.marker, 'size'):
                    if isinstance(trace.marker.size, (int, float)):
                        trace.marker.size = trace.marker.size * 1.8
                        
    def _convert_hex_to_rgba(self, hex_color: str) -> str:
        """Helper method to convert hex to rgba color format."""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 8:  # #AARRGGBB format
            a = int(hex_color[0:2], 16) / 255
            r = int(hex_color[2:4], 16)
            g = int(hex_color[4:6], 16)
            b = int(hex_color[6:8], 16)
            return f"rgba({r}, {g}, {b}, {a})"
        elif len(hex_color) == 6:  # #RRGGBB format
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, 1)"
        else:
            # If format not recognized, return as is
            return f"#{hex_color}"