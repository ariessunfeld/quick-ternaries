"""Plotly Plot Maker for Ternary diagrams"""

from typing import Dict, List, Optional

from src.models.ternary.model import TernaryModel
from src.models.ternary.setup.model import TernaryStartSetupModel, TernaryType
from src.services.ternary.trace_maker import TernaryTraceMaker

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objects import Figure, Layout

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
            ternary=dict(
                sum=100,
                aaxis=linestyle,
                baxis=linestyle,
                caxis=linestyle
            ),
            paper_bgcolor="rgba(0,0,0,0)"
        )

    @staticmethod
    def create_advanced_layout(settings) -> dict:
        axis_settings = LayoutCreator.create_axis_settings(settings)
        return dict(
            ternary=dict(
                aaxis=axis_settings,
                baxis=axis_settings,
                caxis=axis_settings,
                bgcolor=settings.background_color,
                sum=int(settings.ternary_sum)
            ),
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
            tickfont=dict(family=settings.axis_font, size=settings.axis_font_size),
            gridcolor=settings.gridline_color,
            dtick=settings.gridline_step_size,
            showgrid=True,
            ticks='outside',
            layer='below traces'
        )

class TernaryPlotMaker:
    def __init__(self):
        self.trace_maker = TernaryTraceMaker()
        self.axis_formatter = AxisFormatter()
        self.layout_creator = LayoutCreator()

    def make_plot(self, model: TernaryModel) -> Figure:
        layout = self._create_layout(model)
        traces = self._create_traces(model)
        return Figure(data=traces, layout=layout)

    def _create_layout(self, model: TernaryModel) -> Layout:
        base_layout = self.layout_creator.create_base_layout()
        layout = go.Layout(base_layout)

        if model.start_setup_model.advanced_settings_is_checked:
            advanced_layout = self.layout_creator.create_advanced_layout(model.start_setup_model.advanced_settings_model)
            layout.update(advanced_layout)

        self._add_axis_labels(layout, model)
        self._add_title(layout, model)

        return layout

    def _add_axis_labels(self, layout: Layout, model: TernaryModel):
        setup = model.start_setup_model
        ternary_type = setup.get_ternary_type()

        axis_names = {
            'top':   self._format_axis_name(setup.get_top_apex_display_name(),   ternary_type.get_top(),   model),
            'left':  self._format_axis_name(setup.get_left_apex_display_name(),  ternary_type.get_left(),  model),
            'right': self._format_axis_name(setup.get_right_apex_display_name(), ternary_type.get_right(), model)
        }

        layout.ternary.aaxis.title = axis_names['top']
        layout.ternary.baxis.title = f"<br>{axis_names['left']}"
        layout.ternary.caxis.title = f"<br>{axis_names['right']}"

    def _add_title(self, layout: Layout, model: TernaryModel):
        title = model.start_setup_model.get_title()
        ternary_type = model.start_setup_model.get_ternary_type()
        formatted_title = title.strip() or f"{ternary_type.get_short_formatted_name()} Ternary Diagram"
        layout.update(title=dict(text=formatted_title, x=0.5, y=0.95, xanchor='center', yanchor='top'))

    def _create_traces(self, model: TernaryModel) -> List[go.Scatter]:
        return [self.trace_maker.make_trace(model, trace_id)
                for trace_id in model.tab_model.order
                if trace_id != 'StartSetup']

    def _format_axis_name(self, custom_name: str, apex_columns: List[str], model: TernaryModel) -> str:
        if custom_name.strip():
            return custom_name
        if not apex_columns:
            return 'Untitled Apex'
        if model.start_setup_model.scale_apices_is_checked:
            scale_map = self.trace_maker.get_scaling_map(model)
            return self.axis_formatter.format_scaled_name(apex_columns, scale_map)
        return '+'.join(map(self.axis_formatter.format_subscripts, apex_columns))
    
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
