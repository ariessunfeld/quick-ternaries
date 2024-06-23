"""Ploty Graph Objects Scatterternary Trace Maker"""

from typing import List, Dict
import time

import plotly.graph_objects as go
import pandas as pd

from src.models.ternary.trace.model import TernaryTraceEditorModel
from src.models.ternary.model import TernaryModel
from src.models.ternary.setup.model import TernaryType
from src.services.utils.molar_calculator import (
    MolarMassCalculator,
    MolarMassCalculatorException
)

class TraceMolarConversionException(Exception):
    """Exception raised for errors in molar conversion"""
    def __init__(self, trace_id: str, column: str, bad_formula: str, message: str):
        self.trace_id = trace_id
        self.column = column
        self.bad_formula = bad_formula
        self.message = message


class TernaryTraceMaker:
    
    MOLAR_PATTERN = '__{col}_molar_{us}'
    APEX_PATTERN = '__{apex}_{us}'

    def __init__(self):
        super().__init__()
        self.calculator = MolarMassCalculator()

    def make_trace(
            self, 
            model: TernaryModel, 
            trace_id: str) -> go.Scatterternary:
        # TODO

        unique_str = self._generate_unique_str()

        # Get the start setup model from the ternary model
        ternary_type = model.start_setup_model.get_ternary_type()
        print(ternary_type)
        print(type(ternary_type))

        # If `custom`, pull out the apex values from the custom apex selection model
        if (isinstance(ternary_type, TernaryType) and ternary_type.name == 'Custom') or \
                (isinstance(ternary_type, dict) and ternary_type['name'] == 'Custom'):
            top_columns = model.start_setup_model.custom_apex_selection_model.get_top_apex_selected_columns()
            left_columns = model.start_setup_model.custom_apex_selection_model.get_left_apex_selected_columns()
            right_columns = model.start_setup_model.custom_apex_selection_model.get_right_apex_selected_columns()
        else: # otherwise pull from ternary type directly
            top_columns = ternary_type.top
            left_columns = ternary_type.left
            right_columns = ternary_type.right

        print(f"{top_columns=}")
        print(f"{left_columns=}")
        print(f"{right_columns=}")

        # Get the trace model from the model using the trace id
        trace_model = model.tab_model.get_trace(trace_id)
        print(trace_id)

        # Get the trace model's selected data (GET A COPY)
        trace_data_file = trace_model.selected_data_file
        trace_data_df = trace_data_file.get_data().copy()

        # If filters is checked, filter that data according to the filters
        # [use the filter strategies in src/utils to do this]
        use_filters = trace_model.filter_data_checked
        if use_filters:
            pass # TODO

        # If model start setup indicates any scaling needs to be done, 
        # scale the appropriate columns
        scale_apices = model.start_setup_model.scale_apices_is_checked
        if scale_apices:
            scaling_map = self._get_scaling_map(model)
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
        
        # Get the name, point size, color, shape, etc that user has specified
        name = trace_model.legend_name # TODO check that this isnt supposed to be tab_name
        point_size = float(trace_model.point_size)
        point_shape = trace_model.selected_point_shape
        point_color = trace_model.color

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

        # If `heatmap`` is checked, pull the heatmap parameters as well and configure the trace accordingly
        #   If advanced heatmap is checked, pull that info too
        #       If log-transforming heatmap, make a new column in the copy of the selected data for this data
        use_heatmap = trace_model.add_heatmap_checked
        if use_heatmap:
            pass # TODO
            advanced_heatmap = trace_model.heatmap_model.advanced_settings_checked
            if advanced_heatmap:
                pass # TODO

        return go.Scatterternary(
            a=trace_data_df[self.APEX_PATTERN.format(apex='top', us=unique_str)],
            b=trace_data_df[self.APEX_PATTERN.format(apex='left', us=unique_str)],
            c=trace_data_df[self.APEX_PATTERN.format(apex='right', us=unique_str)],
            mode='markers'
        )

    def _get_scaling_map(self, model: TernaryModel):
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
            scaling_map[col] = float(factor)
        return scaling_map

    def _apply_scale_factors(self, df: pd.DataFrame, scale_map: Dict[str, float]):
        for col, factor in scale_map.items():
            if col in df.columns.to_list():
                df[col] = factor * df[col]
        return df
    
    def _generate_unique_str(self) -> str:
        """Returns a unique string to be used in dataframe column names"""
        return str(hash(time.time()))
