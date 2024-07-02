"""Ploty Graph Objects Scatterternary Trace Maker"""

import time
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import gaussian_kde

from src.models.ternary.model import TernaryModel
from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.model import TernaryModel
from src.services.utils.molar_calculator import MolarMassCalculator, MolarMassCalculatorException
from src.services.utils import (
    EqualsFilterStrategy, OneOfFilterStrategy, LessEqualFilterStrategy,
    LessThanFilterStrategy, GreaterEqualFilterStrategy, GreaterThanFilterStrategy,
    LELTFilterStrategy, LELEFilterStrategy, LTLEFilterStrategy, LTLTFilterStrategy
)
from src.services.utils.contour_utils import transform_to_cartesian, compute_kde_contours, convert_contour_to_ternary

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
    
    APEX_PATTERN = '__{apex}_{us}'
    HEATMAP_PATTERN = '__{col}_heatmap_{us}'
    SIMULATED_PATTERN = '__{col}_simulated_{us}'

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
    
    def make_trace(self, model: TernaryModel, trace_id: str) -> go.Scatterternary:
        unique_str = self._generate_unique_str()
        ternary_type = model.start_setup_model.get_ternary_type()

        # Pull the columns lists from the ternary type
        top_columns = ternary_type.get_top()
        left_columns = ternary_type.get_left()
        right_columns = ternary_type.get_right()

        # Get the trace model from the model using the trace id
        trace_model = model.tab_model.get_trace(trace_id)
        name = trace_model.legend_name
        marker = self._get_basic_marker_dict(trace_model)
        scale_apices = model.start_setup_model.scale_apices_is_checked
        scaling_map = self.get_scaling_map(model) if scale_apices else {}
        
        if trace_model.kind == 'bootstrap':
            trace_data_df = self._prepare_bootstrap_data(model, trace_model, ternary_type,
                                                         top_columns, left_columns, right_columns,
                                                         unique_str, trace_id,
                                                         marker,
                                                         scaling_map)
            mode = 'lines'
            customdata, hovertemplate = self._get_bootstrap_hover_data_and_template(trace_model, scaling_map)
            a, b, c = self._generate_contours(trace_data_df, unique_str, trace_model.contour_level)
        else:
            trace_data_df = self._prepare_standard_data(model, trace_model, ternary_type,
                                                        top_columns, left_columns, right_columns,
                                                        unique_str, trace_id,
                                                        marker,
                                                        scaling_map)
            mode = 'markers'
            customdata, hovertemplate = self._get_standard_hover_data_and_template(model, trace_model, trace_data_df, top_columns, left_columns, right_columns, scaling_map)
            a = trace_data_df[self.APEX_PATTERN.format(apex='top',   us=unique_str)]
            b = trace_data_df[self.APEX_PATTERN.format(apex='left',  us=unique_str)]
            c = trace_data_df[self.APEX_PATTERN.format(apex='right', us=unique_str)]

            indices = trace_data_df.index.to_numpy().reshape(-1, 1)
            customdata = np.hstack((customdata, indices))

        return go.Scatterternary(
            a=a, b=b, c=c, name=name, mode=mode,
            marker=marker, customdata=customdata, hovertemplate=hovertemplate, showlegend=True
        )
    
    def _prepare_standard_data(self, model:TernaryModel, trace_model:TernaryTraceEditorModel,
                               ternary_type,
                               top_columns:List[str], left_columns:List[str], right_columns:List[str],
                               unique_str:str, trace_id:str,
                               marker:dict, scaling_map:dict) -> pd.DataFrame:
        trace_data_df = trace_model.selected_data_file.get_data().copy()

        if trace_model.filter_data_checked:
            trace_data_df = self._apply_filters(trace_data_df, trace_model, trace_id)

        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)

        convert_to_molar = trace_model.wtp_to_molar_checked
        trace_data_df = self._molar_calibration(model, ternary_type,
                                                trace_data_df,
                                                top_columns, left_columns, right_columns,
                                                unique_str, trace_id,
                                                convert_to_molar)

        if trace_model.add_heatmap_checked:
            marker, trace_data_df = self._update_marker_dict_with_heatmap_config(marker, trace_model, trace_data_df, unique_str)

        return trace_data_df
    
    def _prepare_bootstrap_data(self, model:TernaryModel, trace_model:TernaryTraceEditorModel,
                                ternary_type,
                                top_columns:List[str], left_columns:List[str], right_columns:List[str],
                                unique_str:str, trace_id:str,
                                marker:dict, scaling_map:dict) -> pd.DataFrame:
        trace_data_df = trace_model.series.to_frame().T

        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
            err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr(), scaling_map)
        else:
            err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr())

        # Expand the dataframe
        N_SIM_PTS = 10_000
        trace_data_df = pd.DataFrame(np.repeat(trace_data_df.values, N_SIM_PTS, axis=0), columns=trace_data_df.columns)

        for col, err in err_repr.items():
            sim_col_fmt = self.SIMULATED_PATTERN.format(col=col, us=unique_str)
            trace_data_df[sim_col_fmt] = np.random.normal(trace_data_df[col].values[0], err, N_SIM_PTS)

        convert_to_molar = trace_model.wtp_to_molar_checked
        trace_data_df = self._molar_calibration(model, ternary_type,
                                                trace_data_df,
                                                top_columns, left_columns, right_columns,
                                                unique_str, trace_id,
                                                convert_to_molar, bootstrap=True)

        return trace_data_df
    
    def _molar_calibration(self,
                           model:TernaryModel, ternary_type,
                           trace_data_df:pd.DataFrame,
                           top_columns:List[str], left_columns:List[str], right_columns:List[str],
                           unique_str:str, trace_id:str,
                           convert_to_molar:bool, bootstrap:bool=False):
        molar_converter = MolarConverter(trace_data_df,
                                         top_columns, left_columns, right_columns,
                                         self.APEX_PATTERN,
                                         unique_str, trace_id,
                                         bootstrap)
        if convert_to_molar:
            sorted_repr = model.molar_conversion_model.get_sorted_repr()
            custom_ternary_type = (ternary_type.name == 'Custom')
            return molar_converter.molar_conversion(sorted_repr, custom_ternary_type)
        return molar_converter.nonmolar_conversion()
    
    def _generate_contours(self, trace_data_df: pd.DataFrame,
                           unique_str: str, contour_level):
        trace_data_df_for_transformation = trace_data_df[
            [self.APEX_PATTERN.format(apex='top',   us=unique_str),
             self.APEX_PATTERN.format(apex='left',  us=unique_str),
             self.APEX_PATTERN.format(apex='right', us=unique_str)]
        ]
        trace_data_cartesian = transform_to_cartesian(
            trace_data_df_for_transformation,
            self.APEX_PATTERN.format(apex='top',   us=unique_str),
            self.APEX_PATTERN.format(apex='left',  us=unique_str),
            self.APEX_PATTERN.format(apex='right', us=unique_str)
        )
        contours = compute_kde_contours(trace_data_cartesian, [self._clean_percentile(contour_level)], 100)
        first_contour = convert_contour_to_ternary(contours)[0]
        return first_contour[:, 0], first_contour[:, 1], first_contour[:, 2]
        
    def _get_standard_hover_data_and_template(
            self, 
            model: TernaryModel, trace_model: TernaryTraceEditorModel,
            trace_data_df: pd.DataFrame,
            top_columns: List[str], left_columns: List[str], right_columns: List[str],
            scale_map:dict) -> Tuple[np.array, str]:
        """
        Generates hover data and template for a standard Plotly trace.

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
            scale_map: a dictionary mapping column names to their scale factors

        Returns:
            customdata: Numpy representation of hover data columns from trace_data_df
            hovertemplate: HTML formatting for hover data.
        """
        # Collecting display names for the apices
        apex_columns = top_columns + left_columns + right_columns
        
        use_custom_hover_data = model.start_setup_model.custom_hover_data_is_checked
        # if there is custom hover data, strictly use the custom hover data selected by the user
        if use_custom_hover_data:
            hover_cols = model.start_setup_model.custom_hover_data_selection_model.get_selected_attrs()
        # if there is no custom hover data, default to the apex columns and heatmap column (if heatmap in use)
        else:
            hover_cols = apex_columns
            if trace_model.add_heatmap_checked and (trace_model.heatmap_model.selected_column not in hover_cols):
                hover_cols.append(trace_model.heatmap_model.selected_column)
            if trace_model.filter_data_checked:
                for filter_model in trace_model.filter_tab_model.get_all_filters().values():
                    if filter_model.selected_column not in hover_cols:
                        hover_cols.append(filter_model.selected_column)

        hovertemplate = "".join(
            f"<br><b>{f'{scale_map[header]}&times;' if header in scale_map and scale_map[header] != 1 else ''}{header}:</b> %{{customdata[{i}]}}"
            for i, header in enumerate(hover_cols)
        )

        # Structure hover data
        customdata = trace_data_df[hover_cols].values

        hovertemplate += "<extra></extra>" # Disable default hover text

        return customdata, hovertemplate
    
    def _get_bootstrap_hover_data_and_template(self, trace_model :TernaryTraceEditorModel, scale_map) -> Tuple[np.array, str]:
        """
        Generates hover data and template for a bootstrapped Plotly trace.

        Returns:
            customdata: Numpy representation of hover data columns from trace_data_df
            hovertemplate: HTML formatting for hover data.
        """

        err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr(), scale_map)
        hovertemplate = "".join(
            f"<br><b>{f'{scale_map[col]}&times;' if col in scale_map and scale_map[col] != 1 else ''}{col}:</b> &#177;{err_repr[col]}" 
            for col in err_repr
        )

        customdata = None
        hovertemplate += "<extra></extra>" # disable default hover text

        return customdata, hovertemplate

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
        marker = dict(
            size   = float(trace_model.point_size),
            symbol = trace_model.selected_point_shape,
            color  = trace_model.color,
            #line   = {'width': trace_model.line_thickness}
        )
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
            
        # Handle heatmap sort mode
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
            data_df = data_df.sample(frac=1)
        
        colorscale = heatmap_model.colorscale
        if heatmap_model.reverse_colorscale:
            colorscale += '_r'

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
    
    def _clean_err_repr(
            self,
            err_repr: List[Tuple[str, str]],
            scaling_map: Dict[str, float]={}) -> Dict[str, float]:
        """Returns a (scaled) representation of the errors entered by the user"""
        ret = {}
        for row in err_repr:
            col = row[0]
            err = row[1]
            err = err.strip()
            _err = []
            for ch in err:
                if ch.isdigit or (ch == '.' and ch not in _err):
                    _err.append(ch)
            _err = ''.join(_err)
            if not _err or _err == '.':
                ret[col] = None
            else:
                if scaling_map:
                    ret[col] = float(_err) * scaling_map[col]
                else:
                    ret[col] = float(_err)
        return ret

    def _clean_percentile(self, percentile: str) -> float:
        """Returns a number between 0 and 1
        
        Arguments: A string, likely between 0 and 100
        """

        try:
            percentile = float(percentile)
            if percentile > 1:
                return percentile / 100
        except ValueError as err:
            # TODO figure out how to handle gracefull
            raise ValueError from err
    
class MolarConverter:
    """
    If molar conversion is checked, use the specified formulae therein to perform molar conversion.
    If any of the formulae are invalid, raise a ValueError with the formula to get caught and shown to the user.
    Ideally, this would turn that part of the view red, but that's more complex. Suffices to say to user:
    Trace [trace_id] has an invalid formula for molar conversion: [bad formula]
    """

    MOLAR_PATTERN = '__{col}_molar_{us}'
    SIMULATED_PATTERN = '__{col}_simulated_{us}'

    def __init__(self, trace_data_df: pd.DataFrame,
                 top_columns: List[str], left_columns: List[str], right_columns: List[str],
                 apex_pattern: str,
                 unique_str: str,
                 trace_id: str,
                 bootstrap: bool=False):
        self.trace_data_df = trace_data_df
        self.top_columns = top_columns
        self.left_columns = left_columns
        self.right_columns = right_columns
        self.apex_pattern = apex_pattern
        self.unique_str = unique_str
        self.trace_id = trace_id
        self.bootstrap = bootstrap

    def molar_conversion(self, sorted_repr: List[Tuple[str, str]], custom_ternary_type: bool) -> pd.DataFrame:
        apex_columns = self.top_columns + self.left_columns + self.right_columns
        molar_mapping = {k: v for k, v in sorted_repr} if custom_ternary_type else {c: c for c in apex_columns}

        # add molar proportion columns for each apex column
        for col in apex_columns:
            self._add_molar_proportion_column(col, molar_mapping)

        # sum to get the apex columns
        for apex_name, apex_cols_list in zip(['top', 'left', 'right'], 
                                             [self.top_columns, self.left_columns, self.right_columns]):
            self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = \
                self.trace_data_df[[self.MOLAR_PATTERN.format(col=c, us=self.unique_str) for c in apex_cols_list]].sum(axis=1)

        return self.trace_data_df

    def nonmolar_conversion(self) -> pd.DataFrame:
        for apex_name, apex_cols_list in zip(['top', 'left', 'right'], 
                                             [self.top_columns, self.left_columns, self.right_columns]):
            if self.bootstrap:
                apex_cols_list = [self.SIMULATED_PATTERN.format(col=c, us=self.unique_str) for c in apex_cols_list]
            self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = \
                self.trace_data_df[apex_cols_list].sum(axis=1)
        return self.trace_data_df

    def _add_molar_proportion_column(self, col: str, molar_mapping: Dict[str, str]) -> None:
        try:
            calculator = MolarMassCalculator()
            col_name = self.SIMULATED_PATTERN.format(col=col, us=self.unique_str) if self.bootstrap else col
            molar_col_name = self.MOLAR_PATTERN.format(col=col, us=self.unique_str)
            self.trace_data_df[molar_col_name] = self.trace_data_df[col_name] / calculator.get_molar_mass(molar_mapping.get(col))
        except MolarMassCalculatorException as e:
            raise TraceMolarConversionException(self.trace_id, col, molar_mapping.get(col), 'Error parsing formula for column.')
