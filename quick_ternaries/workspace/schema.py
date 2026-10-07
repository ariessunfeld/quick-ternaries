"""Explicit public editing schema. No Qt, widgets, or arbitrary attribute access."""

from dataclasses import dataclass
import math
import re


@dataclass(frozen=True)
class Field:
    kind: str
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple = ()

    def describe(self):
        description = {k: v for k, v in {'type': self.kind, 'minimum': self.minimum,
                       'maximum': self.maximum, 'choices': list(self.choices) or None}.items() if v is not None}
        if self.kind == 'filters':
            description.update(max_items=50, item_fields={
                'filter_name': 'string', 'filter_column': 'loaded column name',
                'filter_operation': list(FILTER_OPERATIONS[1:]),
                'filter_value1': 'string; string array for is one of/is not one of',
                'filter_value2': 'string; upper numeric bound for range operations, otherwise empty'},
                required=list(FILTER_KEYS))
        elif self.kind in ('axis_scales', 'axis_formulas'):
            description.update(shape='axis name -> column name -> value',
                axes=['x_axis', 'y_axis', 'top_axis', 'left_axis', 'right_axis', 'hover_data'],
                value='finite number' if self.kind == 'axis_scales' else 'chemical formula or empty string',
                max_columns_per_axis=128)
            if self.kind == 'axis_scales':
                description.update(minimum=.01, maximum=1000)
        elif self.kind == 'errors':
            description.update(shape='column name -> absolute uncertainty', minimum=0, maximum=1e10, max_items=128)
        elif self.kind == 'color':
            description['format'] = '#RRGGBB or #AARRGGBB (alpha first)'
        return description

    def validate(self, value):
        if self.kind == 'boolean':
            valid = type(value) is bool
        elif self.kind in ('number', 'integer'):
            valid = type(value) in ((int,) if self.kind == 'integer' else (int, float))
            try:
                valid = valid and math.isfinite(value)
            except OverflowError:
                valid = False
            valid = valid and (self.minimum is None or value >= self.minimum)
            valid = valid and (self.maximum is None or value <= self.maximum)
        elif self.kind == 'strings':
            valid = (isinstance(value, list) and len(value) <= 128
                     and all(isinstance(s, str) and len(s) <= 512 for s in value)
                     and len(value) == len(set(value)))
        elif self.kind in ('axis_scales', 'axis_formulas', 'errors'):
            valid = valid_mapping(value, self.kind)
        elif self.kind == 'filters':
            valid = isinstance(value, list) and len(value) <= 50
            if valid:
                valid = all(valid_filter(v) for v in value)
        else:
            valid = isinstance(value, str) and len(value) <= 512
            if self.kind == 'color':
                valid = valid and bool(re.fullmatch(r'#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?', value))
            if self.choices:
                valid = valid and value in self.choices
        if not valid:
            raise ValueError('Value does not match the editable field schema.')
        return value.lower() if self.kind == 'color' else value


FILTER_KEYS = ('filter_name', 'filter_column', 'filter_operation', 'filter_value1', 'filter_value2')
FILTER_OPERATIONS = ('', '<', '>', '<=', '>=', '==', 'is', 'is not', 'is one of', 'is not one of',
                     'a < x < b', 'a <= x < b', 'a < x <= b', 'a <= x <= b')


def valid_filter(value):
    if not isinstance(value, dict) or set(value) != set(FILTER_KEYS):
        return False
    for key, item in value.items():
        if key == 'filter_value1' and isinstance(item, list):
            if len(item) > 128 or not all(isinstance(v, str) and len(v) <= 512 for v in item):
                return False
        elif not isinstance(item, str) or len(item) > 512:
            return False
    return value['filter_operation'] in FILTER_OPERATIONS


TEXT = Field('string')
BOOL = Field('boolean')
COLOR = Field('color')
COLUMNS = Field('strings')
NUM = Field('number', -1e10, 1e10)
SORT = Field('string', choices=('no change', 'high on top', 'low on top', 'shuffled'))
LINE = Field('string', choices=('solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot'))
TRACE_FIELDS = {
    'trace_name': TEXT, 'trace_color': COLOR, 'hide_on': BOOL,
    'point_size': Field('number', 0, 1000), 'point_on': BOOL, 'line_on': BOOL,
    'point_shape': Field('string', choices=('circle', 'square', 'diamond', 'cross', 'x',
        'triangle-up', 'triangle-down', 'triangle-left', 'triangle-right', 'pentagon', 'hexagon',
        'star', 'hexagram', 'star-triangle-up', 'star-triangle-down', 'star-square', 'star-diamond',
        'diamond-tall', 'diamond-wide', 'hourglass', 'bowtie')),
    'line_style': LINE, 'line_thickness': Field('number', 0, 100),
    'outline_color': COLOR, 'outline_thickness': Field('number', 0, 100),
    'exclude_from_legend': BOOL, 'show_advanced_settings_on': BOOL,
    'heatmap_on': BOOL, 'heatmap_use_advanced': BOOL, 'heatmap_column': TEXT,
    'heatmap_min': NUM, 'heatmap_max': NUM, 'heatmap_colorscale': TEXT,
    'heatmap_reverse_colorscale': BOOL, 'heatmap_log_transform': BOOL, 'heatmap_sort_mode': SORT,
    'heatmap_bar_orientation': Field('string', choices=('vertical', 'horizontal')),
    'heatmap_colorbar_x': Field('number', -2, 3), 'heatmap_colorbar_y': Field('number', 0, 1),
    'heatmap_colorbar_len': Field('number', .1, 1), 'heatmap_colorbar_thickness': Field('number', 1, 50),
    'sizemap_on': BOOL, 'sizemap_column': TEXT, 'sizemap_sort_mode': SORT,
    'sizemap_min': Field('number', 1, 50), 'sizemap_max': Field('number', 1.5, 50),
    'filters_on': BOOL, 'filters': Field('filters'),
    'vertical_offset_on': BOOL, 'vertical_offset_value': NUM,
    'vertical_exaggeration_on': BOOL, 'vertical_exaggeration_factor': NUM,
    'vertical_line_only': BOOL, 'vertical_line_x_value': NUM, 'min_max_normalize': BOOL,
}
PLOT_FIELDS = {
    'plot_type': Field('string', choices=('ternary', 'cartesian', 'histogram', 'zmap')),
    **{k: TEXT for k in ('title', 'x_axis_label', 'y_axis_label', 'top_vertex_label',
                         'left_vertex_label', 'right_vertex_label', 'categorical_column')},
    **{k: COLUMNS for k in ('x_axis', 'y_axis', 'top_axis', 'left_axis', 'right_axis',
                           'numerical_columns', 'hover_data')},
}


def field_label(name):
    return {'trace_name': 'trace name', 'trace_color': 'trace color', 'filters': 'filters',
            'top_axis': 'top apex', 'left_axis': 'left apex', 'right_axis': 'right apex'}.get(name, name.replace('_', ' '))

TRACE_FIELDS.update({
    'convert_from_wt_to_molar': BOOL,
    'contour_level': Field('string', choices=('Contour: 1-sigma', 'Contour: 2-sigma')),
    'contour_percentile': Field('number', 0, 100),
    'density_contour_on': BOOL, 'density_contour_color': COLOR,
    'density_contour_thickness': Field('integer', 1, 100),
    'density_contour_percentile': Field('number', 1, 99.99),
    'density_contour_name': TEXT, 'density_contour_multiple': BOOL,
    'density_contour_percentiles': TEXT, 'density_contour_line_style': LINE,
    'custom_colorscale_on': BOOL,
    **{k: Field('string', choices=('top_axis', 'left_axis', 'right_axis'))
       for k in ('apex_red_mapping', 'apex_green_mapping', 'apex_blue_mapping')},
})
PLOT_FIELDS.update({
    'aspect_ratio': Field('string', choices=('Automatic', '5x3', '2x1', '1x3', '1x1')),
    'x_axis_custom_range_on': BOOL, 'x_axis_min': NUM, 'x_axis_max': NUM,
    'y_axis_custom_range_on': BOOL, 'y_axis_min': NUM, 'y_axis_max': NUM,
    'zmap_colorscale': TEXT, 'zmap_reverse_colorscale': BOOL,
    'background_color': COLOR, 'paper_color': COLOR, 'grid_color': COLOR, 'font_color': COLOR,
    'gridline_step_size': Field('integer', 1, 100), 'show_tick_marks': BOOL,
    'legend_position': Field('string', choices=('top-right', 'top-left', 'bottom-right', 'bottom-left',
        'top-center', 'bottom-center', 'center-right', 'center-left', 'center', 'custom')),
    'legend_x': Field('number', -2, 3), 'legend_y': Field('number', -2, 3),
    'legend_coordinate_reference': Field('string', choices=('paper', 'container')),
    'legend_xanchor': Field('string', choices=('left', 'center', 'right')),
    'legend_yanchor': Field('string', choices=('top', 'middle', 'bottom')),
    'legend_orientation': Field('string', choices=('vertical', 'horizontal')),
    'font_size': Field('integer', 1, 100), 'font': TEXT,
})
TRACE_FIELDS['outline_thickness'] = Field('integer', 0, 100)
TRACE_FIELDS['vertical_offset_value'] = Field('number', -10000, 10000)
TRACE_FIELDS['vertical_exaggeration_factor'] = Field('number', -10000, 10000)
TRACE_FIELDS['vertical_line_x_value'] = Field('number', -10000000, 10000000)


def valid_mapping(value, kind):
    if not isinstance(value, dict) or len(value) > 128:
        return False
    if kind in ('axis_scales', 'axis_formulas'):
        if value.keys() - {'x_axis', 'y_axis', 'top_axis', 'left_axis', 'right_axis', 'hover_data'}:
            return False
        return all(isinstance(v, dict) and len(v) <= 128 and valid_mapping(v, 'formula_values' if kind == 'axis_formulas' else 'scale_values')
                   for v in value.values())
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 512:
            return False
        if kind == 'formula_values':
            if not isinstance(item, str) or len(item) > 512:
                return False
        else:
            try:
                if type(item) not in (int, float) or not math.isfinite(item) or abs(item) > 1e10:
                    return False
                if kind == 'scale_values' and not .01 <= item <= 1000:
                    return False
                if kind == 'errors' and item < 0:
                    return False
            except OverflowError:
                return False
    return True


TRACE_FIELDS['error_entries'] = Field('errors')
PLOT_FIELDS['scaling_factors'] = Field('axis_scales')
PLOT_FIELDS['formulas'] = Field('axis_formulas')
