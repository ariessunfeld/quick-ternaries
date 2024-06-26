"""Ploty Graph Objects Scatterternary Trace Maker"""

from typing import List, Dict, Tuple
import time

import plotly.graph_objects as go
import pandas as pd
import numpy as np

from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.model import TernaryModel
from src.models.ternary.setup.model import TernaryType
from src.services.utils.molar_calculator import (
    MolarMassCalculator,
    MolarMassCalculatorException
)

from src.services.utils import (
    EqualsFilterStrategy,
    OneOfFilterStrategy,
    LessEqualFilterStrategy,
    LessThanFilterStrategy,
    GreaterEqualFilterStrategy,
    GreaterThanFilterStrategy,
    LELTFilterStrategy,
    LELEFilterStrategy,
    LTLEFilterStrategy,
    LTLTFilterStrategy
)

class TraceMolarConversionException(Exception):
    """Exception raised for errors in molar conversion"""
    def __init__(self, trace_id: str, column: str, bad_formula: str, message: str):
        self.trace_id = trace_id
        self.column = column
        self.bad_formula = bad_formula
        self.message = message

class TraceFilterFloatConversionException(Exception):
    """Exception raised for errors converting filter values"""
    def __init__(self, trace_id: str, filter_id: str, message: str):
        self.trace_id = trace_id
        self.filter_id = filter_id
        self.message = message


class TernaryTraceMaker:
    
    MOLAR_PATTERN = '__{col}_molar_{us}'
    APEX_PATTERN = '__{apex}_{us}'
    HEATMAP_PATTERN = '__{col}_heatmap_{us}'

    def __init__(self):
        super().__init__()
        self.calculator = MolarMassCalculator()

        # TODO refactor into own class, like MolarMassCalculator
        self.operation_strategies = {
            'Equals': EqualsFilterStrategy(),
            'One of': OneOfFilterStrategy(),
            '<': LessThanFilterStrategy(),
            '>': GreaterThanFilterStrategy(),
            '≤': LessEqualFilterStrategy(),
            '≥': GreaterEqualFilterStrategy(),
            'a < x < b': LTLTFilterStrategy(),
            'a ≤ x ≤ b': LELEFilterStrategy(),
            'a ≤ x < b': LELTFilterStrategy(),
            'a < x ≤ b': LTLEFilterStrategy()
            # can add other strategies here if needed
        }

    def make_trace(
            self, 
            model: TernaryModel, 
            trace_id: str) -> go.Scatterternary:
        # TODO

        # Generate a unique string used in temporary dataframe columns
        unique_str = self._generate_unique_str()

        # Get the start setup model from the ternary model
        ternary_type = model.start_setup_model.get_ternary_type()

        # If `custom`, pull out the apex values from the custom apex selection model
        if (isinstance(ternary_type, TernaryType) and ternary_type.name == 'Custom') or \
                (isinstance(ternary_type, dict) and ternary_type['name'] == 'Custom'):
            top_columns = model.start_setup_model.custom_apex_selection_model.get_top_apex_selected_columns()
            left_columns = model.start_setup_model.custom_apex_selection_model.get_left_apex_selected_columns()
            right_columns = model.start_setup_model.custom_apex_selection_model.get_right_apex_selected_columns()
        # otherwise pull from ternary type directly
        elif (isinstance(ternary_type, TernaryType) and ternary_type.name != "Custom"): 
            top_columns = ternary_type.top
            left_columns = ternary_type.left
            right_columns = ternary_type.right
        # Janky that we need all these cases... look into how TernaryType is getting updated in startsetup model
        # This is the dict case
        else:
            top_columns = ternary_type.get('top')
            left_columns = ternary_type.get('left')
            right_columns = ternary_type.get('right')

        # Get the trace model from the model using the trace id
        trace_model = model.tab_model.get_trace(trace_id)

        # Get the trace model's selected data (GET A COPY)
        trace_data_file = trace_model.selected_data_file
        trace_data_df = trace_data_file.get_data().copy()

        # If filters is checked, filter that data according to the filters
        # [use the filter strategies in src/utils to do this]
        use_filters = trace_model.filter_data_checked
        if use_filters:
            trace_data_df = self._apply_filters(trace_data_df, trace_model, trace_id)

        # If model start setup indicates any scaling needs to be done, 
        # scale the appropriate columns
        scale_apices = model.start_setup_model.scale_apices_is_checked
        if scale_apices:
            scaling_map = self.get_scaling_map(model)
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
        
        # Get the name, point size, color, shape, etc that user has specified
        name = self._get_trace_name(trace_model)
        marker = self._get_basic_marker_dict(trace_model)

        # If molar conversion is checked, use the specified formulae therein to perform molar conversion
        # If any of the formulae are invalid, raise a ValueError with the formula to get caught and shown to user
        # Ideally this would turn that part of the view red, but that's more complex. Suffices to say to user:
        #       Trace [trace_id] has an invalid formula for molar conversion: [bad formula]
        convert_to_molar = trace_model.wtp_to_molar_checked
        if convert_to_molar:
            apex_columns = top_columns + left_columns + right_columns
            if (isinstance(ternary_type, TernaryType) and ternary_type.name == 'Custom') or \
                    (isinstance(ternary_type, dict) and ternary_type['name'] == 'Custom'):
                molar_mapping = {k:v for k,v in model.molar_conversion_model.get_sorted_repr()}
            else:
                molar_mapping = {c:c for c in apex_columns}
            for col in apex_columns:
                # add a molar proportion column for each apex column
                try:
                    trace_data_df[self.MOLAR_PATTERN.format(col=col, us=unique_str)] = \
                        trace_data_df[col] / self.calculator.get_molar_mass(molar_mapping.get(col))
                except MolarMassCalculatorException as e:
                    raise TraceMolarConversionException(trace_id, col, molar_mapping.get(col), 'Error parsing formula for column.')
            # Sum to get the apex columns
            for apex_name, apex_cols_list in zip(
                    ['top', 'left', 'right'], 
                    [top_columns, left_columns, right_columns]):
                trace_data_df[self.APEX_PATTERN.format(apex=apex_name, us=unique_str)] = \
                trace_data_df[[self.MOLAR_PATTERN.format(col=c, us=unique_str) for c in apex_cols_list]].sum(axis=1)
        else: # non-molar conversion case
            for apex_name, apex_cols_list in zip(
                    ['top', 'left', 'right'], 
                    [top_columns, left_columns, right_columns]):
                trace_data_df[self.APEX_PATTERN.format(apex=apex_name, us=unique_str)] = \
                trace_data_df[apex_cols_list].sum(axis=1)

        use_heatmap = trace_model.add_heatmap_checked
        if use_heatmap:
            marker, trace_data_df = self._update_marker_dict_with_heatmap_config(
                marker, trace_model, trace_data_df, unique_str)
            
        # Ensure this happens last (right before trace generation)
        # to avoud out-of-sync behavior between hoverdata and dataframe
        # due to sorting from heatmap operations
        hover_data, hover_template = self._get_hover_data_and_template(
            model, trace_model, trace_data_df, top_columns, left_columns, right_columns)

        return go.Scatterternary(
            a=trace_data_df[self.APEX_PATTERN.format(apex='top', us=unique_str)],
            b=trace_data_df[self.APEX_PATTERN.format(apex='left', us=unique_str)],
            c=trace_data_df[self.APEX_PATTERN.format(apex='right', us=unique_str)],
            mode='markers',
            name=name,
            marker=marker,
            customdata=hover_data,
            hovertemplate=hover_template
        )
    
    def _get_hover_data_and_template(
            self, 
            model: TernaryModel, 
            trace_model: TernaryTraceEditorModel,
            trace_data_df: pd.DataFrame,
            top_columns: List[str], 
            left_columns: List[str], 
            right_columns: List[str]) -> Tuple[np.array, str]:
        """
        Generates hover data and template for a Plotly trace.

        If custom hover data is unchecked, default hover data is provided as follows:
         - Each column used in an apex
         - Heatmap column (if used)


        Arguments:
            model: The TernaryModel containing the data and settings.
            trace_model: The TernaryTraceEditorModel for the current trace
            trace_data_df: The dataframe selected for the current trace
            top_columns: a list of string column names for the top apex
            left_columns: a list of string column names for the left apex
            right_columns: a list of string column names from the right apex

        Returns:
            hover_data: Numpy representation of hover data columns from trace_data_df
            hover_template: HTML formatting for hover data.
        """
        # Collecting display names for the apices
        apex_columns = top_columns + left_columns + right_columns
        
        # Determine if custom hover data is used
        use_custom_hover_data = model.start_setup_model.custom_hover_data_is_checked
        if use_custom_hover_data:
            # Use strictly the custom hover data selected by user if checkbox is checked
            # This includes the case where checkbox is checked but nothing is added to `selected`
            hover_cols = model.start_setup_model.custom_hover_data_selection_model.get_selected_attrs()
        else:
            # If checkbox not checked, default to the apex columns and heatmap column (if heatmap in use)
            hover_cols = apex_columns
            if trace_model.add_heatmap_checked:
                heatmap_col = trace_model.heatmap_model.selected_column
                if heatmap_col and heatmap_col not in hover_cols:
                    hover_cols += [heatmap_col]

        # Construct the hover template
        hover_template = "".join(
            f"<br><b>{header}:</b> %{{customdata[{i}]}}"
            for i, header in enumerate(hover_cols)
        )

        # Structure hover data
        hover_data = trace_data_df[hover_cols].values

        hover_template += "<extra></extra>"  # Disable default hover text

        return hover_data, hover_template

    def get_scaling_map(self, model: TernaryModel):
        """Returns a dictionary with scale factors for each column in the `Scale Apices` view"""
        scaling_info = model.start_setup_model.apex_scaling_model.get_sorted_repr()
        scaling_map = {}
        for entry in scaling_info:
            col, factor = entry
            fmt_factor = ''
            for char in factor:
                if char.isnumeric() or (char == '.' and char not in fmt_factor):
                    fmt_factor += char
            if fmt_factor == '' or fmt_factor == '.':
                factor = 1
            scaling_map[col] = float(factor) if float(factor) != int(float(factor)) else int(float(factor))
        return scaling_map

    def _apply_scale_factors(
            self, 
            df: pd.DataFrame, 
            scale_map: Dict[str, float]) -> pd.DataFrame:
        """Returns `df` after applying scale factors to each column in `scale_map`"""
        for col, factor in scale_map.items():
            if col in df.columns.to_list():
                df[col] = factor * df[col]
        return df
    
    def _generate_unique_str(self) -> str:
        """Returns a unique string to be used in dataframe column names"""
        return str(hash(time.time()))

    def _get_basic_marker_dict(self, trace_model: TernaryTraceEditorModel) -> dict:
        """Returns a dictionary with size, symbol, and color keys populated with values from trace"""
        marker = {}
        marker['size'] = float(trace_model.point_size)
        marker['symbol'] = trace_model.selected_point_shape
        marker['color'] = trace_model.color
        return marker
    
    def _update_marker_dict_with_heatmap_config(
            self, 
            marker: dict, 
            trace_model: TernaryTraceEditorModel,
            data_df: pd.DataFrame,
            uuid: str) -> Tuple[dict, pd.DataFrame]:
        """Returns makrer and data_df after making necessary changes for heatmap config"""
        # If `heatmap`` is checked, pull the heatmap parameters as well and configure the trace accordingly
        #   If advanced heatmap is checked, pull that info too
        #       If log-transforming heatmap, make a new column in the copy of the selected data for this data
        # TODO add error handling for casting everything to float
        heatmap_model = trace_model.heatmap_model
        color_column = heatmap_model.selected_column
        if heatmap_model.log_transform_checked:
            data_df[self.HEATMAP_PATTERN.format(col=color_column, us=uuid)] =\
                data_df[color_column].apply(lambda x: np.log(x) if x > 0 else 0)
        else:
            data_df[self.HEATMAP_PATTERN.format(col=color_column, us=uuid)] =\
                data_df[color_column]
            
        # sort df so that points are plotted in order from lowest
        # heatmap value abundance to highest heatmap value abundance
        # TODO add this is a default checkec option but allow users to uncheck
        if trace_model.heatmap_model.sorting_mode == 'no change':
            pass
        elif trace_model.heatmap_model.sorting_mode == 'high on top':
            data_df = data_df.sort_values(
                by=self.HEATMAP_PATTERN.format(col=color_column, us=uuid), 
                ascending=True)
        elif trace_model.heatmap_model.sorting_mode == 'low on top':
            data_df = data_df.sort_values(
                by=self.HEATMAP_PATTERN.format(col=color_column, us=uuid), 
                ascending=False)
        elif trace_model.heatmap_model.sorting_mode == 'shuffled':
            data_df = data_df.sample(frac=1).reset_index(drop=True)
        
        colorscale = heatmap_model.colorscale
        if heatmap_model.reverse_colorscale:
            colorscale += '_r'  # Assuming Plotly accepts '_r' to reverse colorscales

        marker['color'] = data_df[self.HEATMAP_PATTERN.format(col=color_column, us=uuid)]
        marker['colorscale'] = colorscale
        marker['colorbar'] = dict(
            title=dict(
                text=heatmap_model.bar_title,
                side=heatmap_model.title_position,
                font=dict(size=float(heatmap_model.title_font_size))
            ),
            len=float(heatmap_model.length),
            thickness=float(heatmap_model.thickness),
            # TODO add this (thickness) to view and controller
            x=float(heatmap_model.x),
            y=float(heatmap_model.y),
            tickfont=dict(size=float(heatmap_model.tick_font_size)),
            orientation='h' if heatmap_model.bar_orientation == 'horizontal' else 'v'
        )
        # TODO add error handling here for when floats fail or stuff is blank
        # TODO warn user if min >= max
        marker['cmin'] = float(heatmap_model.range_min)
        marker['cmax'] = float(heatmap_model.range_max)

        return marker, data_df

    def _get_trace_name(self, trace_model: TernaryTraceEditorModel):
        """Extracts the trace name from the trace editor model"""
        return trace_model.legend_name
    
    def _apply_filters(
            self, 
            data_df: pd.DataFrame, 
            trace_model: TernaryTraceEditorModel, 
            trace_id: str) -> pd.DataFrame:
        """Applies filters and returns filtered dataframe"""
        filter_order = trace_model.filter_tab_model.order
        for filter_id in filter_order:
            if filter_id == 'StartSetup':
                continue
            filter_model = trace_model.filter_tab_model.get_filter(filter_id)
            column = filter_model.selected_column
            column_dtype = trace_model.selected_data_file.get_dtype(column)
            operation = filter_model.selected_filter_operation
            selected_values = filter_model.selected_one_of_filter_values
            single_value = filter_model.filter_values
            value_a = filter_model.filter_value_a
            value_b = filter_model.filter_value_b

            # float conversion and error raising
            if operation == 'Equals' or operation in ['<', '>', '≤', '≥']:
                if np.issubdtype(column_dtype, np.number):
                    try:
                        single_value = float(single_value) if single_value else None
                    except ValueError:
                        msg = "Error converting value to number."
                        raise TraceFilterFloatConversionException(trace_id, filter_id, msg)
            elif operation == 'One of':
                if np.issubdtype(column_dtype, np.number):
                    try:
                        selected_values = [float(x) for x in selected_values] if selected_values else []
                    except ValueError:
                        msg = "Error converting value(s) to number(s)."
                        raise TraceFilterFloatConversionException(trace_id, filter_id, msg)
            elif operation in ['a < x < b', 'a ≤ x ≤ b', 'a ≤ x < b', 'a < x ≤ b']:
                if np.issubdtype(column_dtype, np.number):
                    try:
                        value_a = float(value_a) if value_a else None
                        value_b = float(value_b) if value_b else None
                    except ValueError:
                        msg = "Error converting Value A or Value B to a number."
                        raise TraceFilterFloatConversionException(trace_id, filter_id, msg)

            filter_params = {
                'column': column,
                'operation': operation,
                'value 1': single_value,
                'value a': value_a,
                'value b': value_b,
                'selected values': selected_values,
            }

            filter_strategy = self.operation_strategies.get(operation)
            data_df = filter_strategy.filter(data_df, filter_params)

        return data_df
    
