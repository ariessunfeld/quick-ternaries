"""Plotly Plot Maker for Ternary diagrams"""

from typing import Dict, List, Optional

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objects import Figure, Layout

from src2.ternary_trace_maker_4 import TernaryTraceMaker
from src2.axis_formatter import AxisFormatter

class LayoutCreator:
    """
    Creates and configures Plotly layouts for ternary diagrams.
    """
    
    @staticmethod
    def create_base_layout() -> dict:
        """
        Creates a basic layout configuration for a ternary plot.
        
        Returns:
            Dictionary with basic layout settings
        """
        linestyle = dict(ticks='outside', linecolor='grey', linewidth=1)
        return dict(
            ternary=dict(
                sum=100,
                aaxis=linestyle,
                baxis=linestyle,
                caxis=linestyle
            ),
            paper_bgcolor="#ececec"
        )

    @staticmethod
    def create_advanced_layout(advanced_settings) -> dict:
        """
        Creates an advanced layout configuration based on provided settings.
        
        Args:
            advanced_settings: The advanced settings model containing customization options
            
        Returns:
            Dictionary with advanced layout settings
        """
        axis_settings = LayoutCreator.create_axis_settings(advanced_settings)
        
        # Get ternary sum or default to 100
        ternary_sum = 100
        if hasattr(advanced_settings, 'ternary_sum'):
            try:
                ternary_sum = int(advanced_settings.ternary_sum)
            except (ValueError, AttributeError):
                pass
        
        return dict(
            ternary=dict(
                aaxis=axis_settings,
                baxis=axis_settings,
                caxis=axis_settings,
                # TODO refactor to make this a utility func
                bgcolor=TernaryTraceMaker()._convert_hex_to_rgba(advanced_settings.background_color) if hasattr(advanced_settings, 'background_color') else None,
                sum=ternary_sum,
            ),
            title=dict(
                font=dict(
                    family=advanced_settings.font if hasattr(advanced_settings, 'font') else 'Arial',
                    size=advanced_settings.font_size if hasattr(advanced_settings, 'font_size') else 12
                )
            ),
            paper_bgcolor=TernaryTraceMaker()._convert_hex_to_rgba(advanced_settings.paper_color) if hasattr(advanced_settings, 'paper_color') else "#FFFFFF"

        )

    @staticmethod
    def create_axis_settings(advanced_settings) -> dict:
        """
        Creates settings for ternary axes based on advanced settings.
        
        Args:
            advanced_settings: The advanced settings model containing axis customization options
            
        Returns:
            Dictionary with axis settings
        """
        return dict(
            title=dict(
                font=dict(
                    family=advanced_settings.font if hasattr(advanced_settings, 'font') else 'Arial',
                    size=advanced_settings.font_size if hasattr(advanced_settings, 'font_size') else 12
                )
            ),
            tickfont=dict(
                family=advanced_settings.font if hasattr(advanced_settings, 'font') else 'Arial',
                size=advanced_settings.font_size if hasattr(advanced_settings, 'font_size') else 10
            ),
            gridcolor=TernaryTraceMaker()._convert_hex_to_rgba(advanced_settings.grid_color) if hasattr(advanced_settings, 'grid_color') else '#888',
            showgrid=getattr(advanced_settings, 'show_grid', True),
            showticklabels=getattr(advanced_settings, 'show_tick_marks', True),
            ticks='outside' if getattr(advanced_settings, 'show_tick_marks', True) else '',
            dtick=getattr(advanced_settings, 'gridline_step_size', 10),
            layer='below traces',
        )


class TernaryPlotMaker:
    """
    Creates and configures Plotly ternary diagrams based on model settings.
    """
    
    def __init__(self):
        """Initialize the plot maker with supporting objects."""
        self.trace_maker = TernaryTraceMaker()
        self.axis_formatter = AxisFormatter()
        self.layout_creator = LayoutCreator()

    def make_plot(self, setup_model, trace_models) -> Figure:
        """
        Creates a complete Plotly figure for a ternary diagram.
        
        Args:
            setup_model: The SetupMenuModel containing global plot settings
            trace_models: List of trace models
            
        Returns:
            A Plotly Figure object
        """
        layout = self._create_layout(setup_model)
        traces = self._create_traces(setup_model, trace_models)
        fig = Figure(data=traces, layout=layout)
        return fig

    def _create_layout(self, setup_model) -> Layout:
        """
        Creates the Plotly layout for the ternary diagram.
        
        Args:
            setup_model: The SetupMenuModel containing layout settings
            
        Returns:
            A Plotly Layout object
        """
        base_layout = self.layout_creator.create_base_layout()
        layout = go.Layout(base_layout)
        
        # Add advanced settings if available
        if hasattr(setup_model, 'advanced_settings'):
            advanced_layout = self.layout_creator.create_advanced_layout(setup_model.advanced_settings)
            layout.update(advanced_layout)
        
        # Add axis labels and title
        self._add_axis_labels(layout, setup_model)
        self._add_title(layout, setup_model)
        
        return layout

    def _add_axis_labels(self, layout: Layout, setup_model):
        """
        Adds formatted axis labels to the layout.
        
        Args:
            layout: The Plotly Layout object to modify
            setup_model: The SetupMenuModel containing axis settings
        """
        # Get column lists for each apex
        top_columns = setup_model.axis_members.top_axis
        left_columns = setup_model.axis_members.left_axis
        right_columns = setup_model.axis_members.right_axis
        
        # Get custom apex names if available
        top_name = setup_model.plot_labels.top_vertex_label if hasattr(setup_model.plot_labels, 'top_vertex_label') else ""
        left_name = setup_model.plot_labels.left_vertex_label if hasattr(setup_model.plot_labels, 'left_vertex_label') else ""
        right_name = setup_model.plot_labels.right_vertex_label if hasattr(setup_model.plot_labels, 'right_vertex_label') else ""
        
        # Format axis names
        axis_names = {
            'top': self._format_axis_name(top_name, top_columns, setup_model),
            'left': self._format_axis_name(left_name, left_columns, setup_model, side='left'),
            'right': self._format_axis_name(right_name, right_columns, setup_model, side='right')
        }
        
        # Update layout with axis names
        layout.ternary.aaxis.title.update(text=axis_names['top'])
        layout.ternary.baxis.title.update(text=f"<br>{axis_names['left']}")
        layout.ternary.caxis.title.update(text=f"<br>{axis_names['right']}")

    def _add_title(self, layout: Layout, setup_model):
        """
        Adds a title to the layout.
        
        Args:
            layout: The Plotly Layout object to modify
            setup_model: The SetupMenuModel containing title settings
        """
        title = setup_model.plot_labels.title if hasattr(setup_model.plot_labels, 'title') else ""
        
        # If title is empty, generate a default title
        if not title.strip():
            if hasattr(setup_model, 'get_ternary_type') and callable(setup_model.get_ternary_type):
                ternary_type = setup_model.get_ternary_type()
                title = f"{ternary_type.get_short_formatted_name()} Ternary Diagram"
            else:
                title = "Ternary Diagram"
        
        # Update layout with title
        layout.update(title=dict(text=title, x=0.5, y=0.95, xanchor='center', yanchor='top'))

    def _create_traces(self, setup_model, trace_models) -> List[go.Scatterternary]:
        """
        Creates all traces for the plot.
        
        Args:
            setup_model: The SetupMenuModel containing global settings
            trace_models: List of trace models
            
        Returns:
            List of Plotly Scatterternary objects
        """
        traces = []
        
        for trace_model in trace_models:     
            trace = self.trace_maker.make_trace(setup_model, trace_model)
            traces.append(trace)
            
        return traces

    def _format_axis_name(self, custom_name: str, apex_columns: List[str], setup_model, side: str = None) -> str:
        """
        Formats an axis name with proper subscripts and scaling.
        
        Args:
            custom_name: Custom name for the axis (if provided)
            apex_columns: List of column names for the apex
            setup_model: The SetupMenuModel containing scaling settings
            side: Which side of the triangle ('left' or 'right', for spacing)
            
        Returns:
            Formatted axis name
        """
        # Use custom name if provided
        if custom_name and custom_name.strip():
            ret = custom_name
        # Otherwise format based on columns
        elif not apex_columns:
            ret = 'Untitled Apex'
        else:
            # Check if scaling is enabled
            use_scaling = False
            if hasattr(setup_model, 'column_scaling') and hasattr(setup_model.column_scaling, 'scaling_factors'):
                scale_map = {}
                
                # Get scaling factors for top, left, and right axes
                for axis_name in ['top_axis', 'left_axis', 'right_axis']:
                    if axis_name in setup_model.column_scaling.scaling_factors:
                        scale_map.update(setup_model.column_scaling.scaling_factors[axis_name])
                
                # Only apply scaling if there are non-default (not 1.0) scale factors
                use_scaling = any(value != 1.0 for value in scale_map.values() if value is not None)
                
                if use_scaling:
                    ret = self.axis_formatter.format_scaled_name(apex_columns, scale_map)
                else:
                    ret = '+'.join(map(self.axis_formatter.format_subscripts, apex_columns))
            else:
                ret = '+'.join(map(self.axis_formatter.format_subscripts, apex_columns))
        
        # Add spacing for left/right labels to improve appearance
        if not side:
            return ret
        elif side == 'left':
            return '&nbsp;' * int(0.6 * len(ret)) + ret
        elif side == 'right':
            return ret + '&nbsp;' * int(0.6 * len(ret))
    
    def save_plot(self, fig: Figure, filepath: str, dpi: Optional[float] = None):
        """
        Saves the plot to a file.
        
        Args:
            fig: The Plotly Figure to save
            filepath: Path where the file should be saved
            dpi: Dots per inch for raster formats (optional)
        """
        # Save as interactive HTML
        if filepath.endswith('.html'):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fig.to_html())
        # Save as static image
        else:
            # Reduce marker size for better appearance in static images
            for trace in fig.data:
                if 'marker' in trace and 'size' in trace.marker:
                    # Save original size
                    original_size = trace.marker.size
                    # Reduce size for export
                    trace.marker.size = original_size / 1.8
            
            # Set scale based on DPI
            scale = 1.0
            if dpi is not None:
                scale = dpi / 72.0
                
            # Write the image
            pio.write_image(fig, filepath, scale=scale)
            
            # Restore original marker sizes
            for trace in fig.data:
                if 'marker' in trace and 'size' in trace.marker:
                    trace.marker.size = trace.marker.size * 1.8