"""Cartesian plot maker"""

from typing import Dict, List, TYPE_CHECKING

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objects import Figure, Layout

from src.services.ternary.trace_maker import TernaryTraceMaker

if TYPE_CHECKING:
    from src.models.ternary import TernaryModel


class AxisFormatter:
    @staticmethod
    def format_subscripts(oxide: str) -> str:
        if oxide.lower() == 'feot':
            return "FeO<sub>T</sub>"
        return "".join('<sub>' + x + '</sub>' if x.isnumeric() else x for x in oxide)

    @staticmethod
    def format_scaled_name(apex_columns: List[str], scale_map: Dict[str, float]) -> str:
        unique_scale_vals = sorted(set(scale_map[col] for col in apex_columns), reverse=True)
        if len(unique_scale_vals) == 1 and unique_scale_vals[0] != 1:
            return f"{unique_scale_vals[0]}&times;({'+'.join(map(AxisFormatter.format_subscripts, apex_columns))})"

        parts = []
        for val in unique_scale_vals:
            cols = [c for c in apex_columns if scale_map[c] == val]
            if val != 1:
                parts.append(f"{val}&times;({'+'.join(map(AxisFormatter.format_subscripts, cols))})")
            else:
                parts.extend(map(AxisFormatter.format_subscripts, cols))
        return '+'.join(parts)


class LayoutCreator:
    @staticmethod
    def create_base_layout() -> dict:
        linestyle = dict(ticks='outside', linecolor='grey', linewidth=1)
        return dict(
            xaxis=linestyle,
            yaxis=linestyle,
            paper_bgcolor="#ffffff",
        )

    @staticmethod
    def create_advanced_layout(settings) -> dict:
        axis_settings = LayoutCreator.create_axis_settings(settings)
        return dict(
            xaxis=axis_settings,
            yaxis=axis_settings,
            bgcolor=settings.background_color,
            title=dict(
                font=dict(
                    family=settings.title_font,
                    size=settings.title_font_size
                )
            ),
            paper_bgcolor=settings.paper_color
        )

    @staticmethod
    def create_axis_settings(settings) -> dict:
        return dict(
            title=dict(font=dict(family=settings.axis_font, size=settings.axis_font_size)),
            tickfont=dict(family=settings.tick_font, size=settings.tick_font_size),
            gridcolor=settings.gridline_color,
            showgrid=settings.show_grid,
            showticklabels=settings.show_tick_marks,
            ticks='outside' if settings.show_tick_marks else '',
            dtick=settings.gridline_step_size,
            layer='below traces'
        )


class CartesianPlotMaker:
    def __init__(self):
        self.trace_maker = TernaryTraceMaker()  # Reference remains the same
        self.axis_formatter = AxisFormatter()
        self.layout_creator = LayoutCreator()

    def make_plot(self, model: 'TernaryModel') -> go.Figure:
        layout = self._create_layout(model)
        traces = self._create_traces(model)
        return go.Figure(data=traces, layout=layout)

    def _create_layout(self, model: 'TernaryModel') -> dict:
        base_layout = self.layout_creator.create_base_layout()
        layout = go.Layout(base_layout)

        if model.start_setup_model.advanced_settings_is_checked:
            advanced_layout = self.layout_creator.create_advanced_layout(model.start_setup_model.advanced_settings_model)
            layout.update(advanced_layout)

        self._add_axis_labels(layout, model)
        self._add_title(layout, model)

        return layout

    def _add_axis_labels(self, layout: dict, model: 'TernaryModel'):
        setup = model.start_setup_model

        x_axis_name = setup.get_top_apex_display_name().strip() or 'X Axis'
        y_axis_name = setup.get_left_apex_display_name().strip() or 'Y Axis'

        layout.update(
            xaxis=dict(title=x_axis_name),
            yaxis=dict(title=y_axis_name)
        )

    def _add_title(self, layout: dict, model: 'TernaryModel'):
        title = model.start_setup_model.get_title()
        formatted_title = title.strip() or "Untitled Plot"
        layout.update(title=dict(text=formatted_title, x=0.5, y=0.95, xanchor='center', yanchor='top'))

    def _create_traces(self, model: 'TernaryModel') -> List[go.Scatter]:
        return [self.trace_maker.make_cartesian_trace(model, trace_id)
                for trace_id in model.tab_model.order
                if trace_id != 'StartSetup']

    def save_plot(self, fig: go.Figure, filepath: str, dpi: float = None):
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