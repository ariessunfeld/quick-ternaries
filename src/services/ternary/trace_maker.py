"""Ploty Graph Objects Scatterternary Trace Maker"""

import time
from typing import List, Dict, Tuple, TYPE_CHECKING
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.services.ternary.exceptions import (
    BootstrapTraceContourException,
    TraceFilterFloatConversionException,
    TraceMolarConversionException,
    TraceMissingColumnException,
    FloatConversionError
)
from src.services.utils.molar_calculator import (
    MolarMassCalculator, 
    MolarMassCalculatorException
)
from src.services.utils.filter_strategies import (
    EqualsFilterStrategy, 
    OneOfFilterStrategy, 
    ExcludeOneFilterStrategy, 
    ExcludeMultipleFilterStrategy,
    LessEqualFilterStrategy, 
    LessThanFilterStrategy, 
    GreaterEqualFilterStrategy, 
    GreaterThanFilterStrategy,
    LELTFilterStrategy, 
    LELEFilterStrategy, 
    LTLEFilterStrategy, 
    LTLTFilterStrategy
)
from src.services.utils.contour_utils import (
    transform_to_cartesian, 
    compute_kde_contours, 
    convert_contour_to_ternary
)

if TYPE_CHECKING:
    from src.models.ternary import TernaryModel
    from src.models.ternary.setup import TernaryType
    from src.models.ternary.trace import TernaryTraceEditorModel

class TernaryTraceMaker:

    APEX_PATTERN = '__{apex}_{us}'
    HEATMAP_PATTERN = '__{col}_heatmap_{us}'
    SIZEMAP_PATTERN = '__{col}_sizemap_{us}'
    SIMULATED_PATTERN = '__{col}_simulated_{us}'

    N_SIMULATION_POINTS = 10_000

    def __init__(self):
        super().__init__()
        self.calculator = MolarMassCalculator()

        # TODO refactor into own class, like MolarMassCalculator
        self.operation_strategies = {
            'Equals': EqualsFilterStrategy(),
            'One of': OneOfFilterStrategy(),
            'Exclude one': ExcludeOneFilterStrategy(),
            'Exclude multiple': ExcludeMultipleFilterStrategy(),
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
    
    def make_trace(self, model: 'TernaryModel', trace_id: str) -> go.Scatterternary:
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
            marker, trace_data_df = self._prepare_bootstrap_data(
                model, 
                trace_model, 
                ternary_type,
                top_columns, 
                left_columns, 
                right_columns,
                unique_str, 
                trace_id,
                marker,
                scaling_map)
            mode = 'lines'
            customdata, hovertemplate = self._get_bootstrap_hover_data_and_template(trace_model, scaling_map)
            a, b, c = self._generate_contours(trace_id, trace_data_df, unique_str, trace_model.contour_level)
            line = dict(width=trace_model.line_thickness)
        else:
            marker, trace_data_df = self._prepare_standard_data(
                model, 
                trace_model, 
                ternary_type,
                top_columns, 
                left_columns, 
                right_columns,
                unique_str, 
                trace_id,
                marker,
                scaling_map)
            mode = 'markers'
            customdata, hovertemplate = self._get_standard_hover_data_and_template(model, trace_model, trace_data_df, top_columns, left_columns, right_columns, scaling_map)
            a = trace_data_df[self.APEX_PATTERN.format(apex='top',   us=unique_str)]
            b = trace_data_df[self.APEX_PATTERN.format(apex='left',  us=unique_str)]
            c = trace_data_df[self.APEX_PATTERN.format(apex='right', us=unique_str)]
            line = None

            indices = trace_data_df.index.to_numpy().reshape(-1, 1)
            customdata = np.hstack((customdata, indices))

        return go.Scatterternary(
            a=a, b=b, c=c, name=name, mode=mode,
            marker=marker, customdata=customdata, hovertemplate=hovertemplate, showlegend=True, line=line
        )

    def make_cartesian_trace(self, model: 'TernaryModel', trace_id: str) -> go.Scatter:
        unique_str = self._generate_unique_str()
        ternary_type = model.start_setup_model.get_ternary_type()

        # Pull the columns lists from the ternary type
        x_columns = ternary_type.get_top()
        y_columns = ternary_type.get_left()

        # Get the trace model from the model using the trace id
        trace_model = model.tab_model.get_trace(trace_id)
        name = trace_model.legend_name
        marker = self._get_basic_marker_dict(trace_model)
        scale_apices = model.start_setup_model.scale_apices_is_checked
        scaling_map = self.get_scaling_map(model) if scale_apices else {}

        if trace_model.kind == 'bootstrap':
            raise NotImplementedError
            marker, trace_data_df = self._prepare_bootstrap_data_cartesian(
                model, 
                trace_model, 
                ternary_type,
                x_columns, 
                y_columns, 
                unique_str, 
                trace_id,
                marker,
                scaling_map)
            mode = 'lines'
            customdata, hovertemplate = self._get_bootstrap_hover_data_and_template(trace_model, scaling_map)
            a, b, c = self._generate_contours(trace_id, trace_data_df, unique_str, trace_model.contour_level)
            line = dict(width=trace_model.line_thickness)
        else:
            marker, trace_data_df = self._prepare_standard_data_cartesian(
                model, 
                trace_model, 
                ternary_type,
                x_columns, 
                y_columns, 
                unique_str, 
                trace_id,
                marker,
                scaling_map)
            mode = 'markers'
            customdata, hovertemplate = self._get_standard_hover_data_and_template(model, trace_model, trace_data_df, x_columns, y_columns, [], scaling_map)
            x = trace_data_df[self.APEX_PATTERN.format(apex='top',   us=unique_str)]
            y = trace_data_df[self.APEX_PATTERN.format(apex='left',  us=unique_str)]
            line = None

            indices = trace_data_df.index.to_numpy().reshape(-1, 1)
            try:
                customdata = np.hstack((customdata, indices))
            except ValueError as err:
                # TODO handle with error message, likely came from blank apex/axis
                raise ValueError from err
            

        return go.Scatter(
            x=x, y=y, name=name, mode=mode,
            marker=marker, customdata=customdata, hovertemplate=hovertemplate, showlegend=True, line=line
        )

    def _prepare_standard_data_cartesian(
            self, 
            model:'TernaryModel', 
            trace_model:'TernaryTraceEditorModel',
            ternary_type,
            x_columns:List[str], 
            y_columns:List[str], 
            unique_str:str, 
            trace_id:str,
            marker:dict, 
            scaling_map:dict) -> pd.DataFrame:
        """
        TODO docstring
        """

        trace_data_df = trace_model.selected_data_file.get_data().copy()

        if trace_model.filter_data_checked:
            trace_data_df = self._apply_filters(trace_data_df, trace_model, trace_id)

        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)

        # TODO support molar conversion without normalization

        # return marker, trace_data_df
        heatmap_column = trace_model.heatmap_model.selected_column if trace_model.add_heatmap_checked else None
        sizemap_column = trace_model.sizemap_model.selected_column if trace_model.add_sizemap_checked else None

        if heatmap_column and sizemap_column:
            # Sort considering both heatmap and sizemap columns
            marker, trace_data_df = self._integrated_sort(marker, trace_data_df, trace_model, heatmap_column, sizemap_column, unique_str, trace_id)
        else:
            if heatmap_column:
                marker, trace_data_df = self._update_marker_dict_with_heatmap_config(
                    marker, trace_model, trace_data_df, unique_str, trace_id)
                
            if sizemap_column:
                marker, trace_data_df = self._update_marker_dict_with_sizemap_config(
                    marker, trace_model, trace_data_df, unique_str, trace_id)

        if trace_model.advanced_settings_checked:
            marker = self._update_marker_with_trace_advanced_settings(marker, trace_model)

        trace_data_df[self.APEX_PATTERN.format(apex='top', us=unique_str)] = trace_data_df[x_columns].sum(axis=1)
        trace_data_df[self.APEX_PATTERN.format(apex='left', us=unique_str)] = trace_data_df[y_columns].sum(axis=1)

        return marker, trace_data_df
    
    def _prepare_standard_data(
            self, 
            model:'TernaryModel', 
            trace_model:'TernaryTraceEditorModel',
            ternary_type,
            top_columns:List[str], 
            left_columns:List[str], 
            right_columns:List[str],
            unique_str:str, 
            trace_id:str,
            marker:dict, 
            scaling_map:dict) -> pd.DataFrame:
        """
        TODO docstring
        """
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

        # return marker, trace_data_df
        heatmap_column = trace_model.heatmap_model.selected_column if trace_model.add_heatmap_checked else None
        sizemap_column = trace_model.sizemap_model.selected_column if trace_model.add_sizemap_checked else None

        if heatmap_column and sizemap_column:
            # Sort considering both heatmap and sizemap columns
            marker, trace_data_df = self._integrated_sort(marker, trace_data_df, trace_model, heatmap_column, sizemap_column, unique_str, trace_id)
        else:
            if heatmap_column:
                marker, trace_data_df = self._update_marker_dict_with_heatmap_config(
                    marker, trace_model, trace_data_df, unique_str, trace_id)
                
            if sizemap_column:
                marker, trace_data_df = self._update_marker_dict_with_sizemap_config(
                    marker, trace_model, trace_data_df, unique_str, trace_id)

        if trace_model.advanced_settings_checked:
            marker = self._update_marker_with_trace_advanced_settings(marker, trace_model)

        return marker, trace_data_df
    
    def _prepare_bootstrap_data(
            self,
            model: 'TernaryModel',
            trace_model: 'TernaryTraceEditorModel',
            ternary_type: 'TernaryType',
            top_columns: List[str],
            left_columns: List[str],
            right_columns: List[str],
            unique_str: str,
            trace_id: str,
            marker: dict,
            scaling_map: dict) -> pd.DataFrame:
        """
        TODO docstring
        """

        # Create a dataframe from the single-row series
        trace_data_df = trace_model.series.to_frame().T

        # Apply scaling if necessary
        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
            err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr(), scaling_map)
        else:
            err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr())

        # Expand the dataframe to make room for simulated points
        trace_data_df = pd.DataFrame(
            data=np.repeat(
                trace_data_df.values, 
                self.N_SIMULATION_POINTS, 
                axis=0), 
            columns=trace_data_df.columns)

        # Fill the expanded dataframe with simulated data
        for col, err in err_repr.items():
            sim_col_fmt = self.SIMULATED_PATTERN.format(col=col, us=unique_str)
            # TODO allow users to pick other distributions besides Normal, and apply them here
            trace_data_df[sim_col_fmt] = np.random.normal(trace_data_df[col].values[0], err, self.N_SIMULATION_POINTS)

        # Check whether molar conversion is necessary
        convert_to_molar = trace_model.wtp_to_molar_checked

        # Apply molar conversion if needed, and siomple normalization if not
        trace_data_df = self._molar_calibration(
            model, 
            ternary_type,
            trace_data_df,
            top_columns, 
            left_columns, 
            right_columns,
            unique_str, 
            trace_id,
            convert_to_molar, 
            bootstrap=True)

        return marker, trace_data_df

    def _integrated_sort(
            self,
            marker: dict, 
            trace_data_df: pd.DataFrame, 
            trace_model: 'TernaryTraceEditorModel', 
            heatmap_column: str, 
            sizemap_column: str, 
            unique_str: str,
            trace_id: str):
        """Sort the dataframe considering both heatmap and sizemap columns and update marker
        
        TODO: right now there is a lot of duplicated code in thise method wrt update_marker_with_heatmap() and 
        update_marker_with_sizemap(). Need to refactor to eliminate duplicated code without compromising integrated sort
        """
        heatmap_sorted_col = self.HEATMAP_PATTERN.format(col=heatmap_column, us=unique_str)
        sizemap_sorted_col = self.SIZEMAP_PATTERN.format(col=sizemap_column, us=unique_str)

        if trace_model.heatmap_model.log_transform_checked:
            trace_data_df[heatmap_sorted_col] = trace_data_df[heatmap_column].apply(lambda x: np.log(x) if x > 0 else 0)
        else:
            trace_data_df[heatmap_sorted_col] = trace_data_df[heatmap_column]

        sizemap_model = trace_model.sizemap_model
        min_size = self._float(sizemap_model.range_min, 'sizemap minimum size', trace_id) 
        max_size = self._float(sizemap_model.range_max, 'sizemap maximum size', trace_id)
        size_range = max_size - min_size
        size_normalized = ((trace_data_df[sizemap_column] - trace_data_df[sizemap_column].min()) / 
                        (trace_data_df[sizemap_column].max() - trace_data_df[sizemap_column].min())) * size_range + min_size
        trace_data_df[sizemap_sorted_col] = size_normalized
        trace_data_df[sizemap_sorted_col].fillna(0.0, inplace=True)

        if sizemap_model.log_transform_checked:
            trace_data_df[sizemap_sorted_col] = trace_data_df[sizemap_sorted_col].apply(lambda x: np.log(x) if x > 0 else 0)

        # sort_by = []
        # if trace_model.heatmap_model.sorting_mode != 'no change':
        #     if trace_model.heatmap_model.sorting_mode in ['high on top', 'low on top']:
        #         ascending = trace_model.heatmap_model.sorting_mode == 'high on top'
        #         sort_by.append((heatmap_sorted_col, ascending))
        # if sizemap_model.sorting_mode != 'no change':
        #     sort_by.append((sizemap_sorted_col, sizemap_model.sorting_mode == 'low on top'))

        # if sort_by:
        #     sort_by_columns, ascending = zip(*sort_by)
        #     trace_data_df = trace_data_df.sort_values(by=list(sort_by_columns), ascending=list(ascending))

        # Handle heatmap sort mode
        if trace_model.heatmap_model.sorting_mode == 'no change':
            pass
        elif trace_model.heatmap_model.sorting_mode == 'high on top':
            trace_data_df = trace_data_df.sort_values(
                by=heatmap_sorted_col, 
                ascending=True)
        elif trace_model.heatmap_model.sorting_mode == 'low on top':
            trace_data_df = trace_data_df.sort_values(
                by=heatmap_sorted_col, 
                ascending=False)
        elif trace_model.heatmap_model.sorting_mode == 'shuffled':
            trace_data_df = trace_data_df.sample(frac=1)

        # Handle sizemap sort mode
        if sizemap_model.sorting_mode == 'no change':
            pass
        elif sizemap_model.sorting_mode == 'high on top':
            trace_data_df = trace_data_df.sort_values(
                by=sizemap_sorted_col, 
                ascending=True)
        elif sizemap_model.sorting_mode == 'low on top':
            trace_data_df = trace_data_df.sort_values(
                by=sizemap_sorted_col, 
                ascending=False)
        elif sizemap_model.sorting_mode == 'shuffled':
            trace_data_df = trace_data_df.sample(frac=1)

        sizeref = 2. * max(size_normalized) / (max_size**2)

        marker['size'] = trace_data_df[sizemap_sorted_col]
        marker['sizemin'] = min_size
        marker['sizeref'] = sizeref
        marker['color'] = trace_data_df[heatmap_sorted_col]
        marker['colorscale'] = trace_model.heatmap_model.colorscale
        if trace_model.heatmap_model.reverse_colorscale:
            marker['colorscale'] += '_r'
        marker['colorbar'] = dict(
            title=dict(
                text=trace_model.heatmap_model.bar_title,
                side=trace_model.heatmap_model.title_position,
                font=dict(
                    #size=float(trace_model.heatmap_model.title_font_size),
                    size=self._float(trace_model.heatmap_model.title_font_size, 'heatmap title font size', trace_id),
                    family=trace_model.heatmap_model.font
                )
            ),
            #len=float(trace_model.heatmap_model.length),
            len=self._float(trace_model.heatmap_model.length, 'heatmap length', trace_id),
            #thickness=float(trace_model.heatmap_model.thickness),
            thickness=self._float(trace_model.heatmap_model.thickness, 'heatmap thickness', trace_id),
            #x=float(trace_model.heatmap_model.x),
            x=self._float(trace_model.heatmap_model.x, 'heatmap x position', trace_id),
            #y=float(trace_model.heatmap_model.y),
            y=self._float(trace_model.heatmap_model.y, 'heatmap y position', trace_id),
            tickfont=dict(
                #size=float(trace_model.heatmap_model.tick_font_size),
                size=self._float(trace_model.heatmap_model.tick_font_size, 'heatmap tick font size', trace_id),
                family=trace_model.heatmap_model.font
            ),
            orientation='h' if trace_model.heatmap_model.bar_orientation == 'horizontal' else 'v'
        )
        #marker['cmin'] = float(trace_model.heatmap_model.range_min)
        marker['cmin'] = self._float(trace_model.heatmap_model.range_min, 'heatmap range minimum', trace_id)
        #marker['cmax'] = float(trace_model.heatmap_model.range_max)
        marker['cmax'] = self._float(trace_model.heatmap_model.range_max, 'heatmap range maximum', trace_id)

        return marker, trace_data_df
    
    def _molar_calibration(
            self,
            model:'TernaryModel', 
            ternary_type: 'TernaryType',
            trace_data_df: pd.DataFrame,
            top_columns: List[str], 
            left_columns: List[str], 
            right_columns: List[str],
            unique_str: str, 
            trace_id: str,
            convert_to_molar: bool, 
            bootstrap: bool = False):
        """
        TODO docstring
        """
        
        # Instantiate a molar converter helper object
        molar_converter = MolarConverter(
            trace_data_df,
            top_columns, 
            left_columns, 
            right_columns,
            self.APEX_PATTERN,
            unique_str, 
            trace_id,
            bootstrap)
        
        if convert_to_molar:
            sorted_repr_of_molar_conversion_model = model.molar_conversion_model.get_sorted_repr()
            custom_ternary_type = (ternary_type.name == 'Custom')
            return molar_converter.molar_conversion(
                sorted_repr_of_molar_conversion_model, custom_ternary_type)
        else:
            return molar_converter.nonmolar_conversion()
    
    def _generate_contours(
            self, 
            trace_id: str, 
            trace_data_df: pd.DataFrame,
            unique_str: str, 
            contour_level):
        """
        TODO docstring
        """

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

        success, contours = compute_kde_contours(trace_data_cartesian, [self._clean_percentile(contour_level)], 100)
        if not success:
            raise BootstrapTraceContourException(trace_id, 'Error computing contour for point')
        else:
            first_contour = convert_contour_to_ternary(contours)[0]
            return first_contour[:, 0], first_contour[:, 1], first_contour[:, 2]
        
    def _get_standard_hover_data_and_template(
            self, 
            model: 'TernaryModel', 
            trace_model: 'TernaryTraceEditorModel',
            trace_data_df: pd.DataFrame,
            top_columns: List[str], 
            left_columns: List[str], 
            right_columns: List[str],
            scale_map:dict) -> Tuple[np.array, str]:
        """
        Generates custom data for standard Plotly points and an HTML template for the hover data.

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
            customdata: Numpy representation of what information a plotted point should have
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
        
        # Construct customdata with rounded values for numeric columns and raw values for others
        customdata = []
        for header in hover_cols:
            try:
                # Try to round the column if it's numeric
                rounded_values = np.round(trace_data_df[header].values.astype(float), 4)
            except ValueError:
                # If rounding fails (e.g., for non-numeric columns), use raw values
                rounded_values = trace_data_df[header].values
            customdata.append(rounded_values)

        # Transpose customdata to match the shape expected by plotly
        customdata = np.array(customdata).T

        hovertemplate += "<extra></extra>" # Disable default hover text

        return customdata, hovertemplate
    
    def _get_bootstrap_hover_data_and_template(self, trace_model:'TernaryTraceEditorModel', scale_map) -> Tuple[np.array, str]:
        """
        Generates custom data for a bootstrapped contour and an HTML template for its hover data.

        Returns:
            customdata: Numpy representation of what information the bootstrapped contour should have
            hovertemplate: HTML formatting for hover data.
        """

        # add uncertainties
        err_repr = self._clean_err_repr(trace_model.error_entry_model.get_sorted_repr(), scale_map)
        # round to mitigate floating point error
        err_repr = {col: round(err, 4) for col, err in err_repr.items()}
        hovertemplate = "".join(
            f"<br><b>{f'{scale_map[col]}&times;' if col in scale_map and scale_map[col] != 1 else ''}{col}:</b> &#177;{err_repr[col]}" 
            for col in err_repr
        )

        # add contour levels (sigma or percentiles)
        contour_mode = trace_model.selected_contour_mode
        hovertemplate += f"<br><b>Contour:</b> {str(trace_model.contour_level) + '%' if contour_mode == 'custom' else trace_model.selected_contour_mode}"

        customdata = None
        hovertemplate += "<extra></extra>" # disable default hover text

        return customdata, hovertemplate

    def get_scaling_map(self, model: 'TernaryModel'):
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

    def _get_basic_marker_dict(self, trace_model: 'TernaryTraceEditorModel') -> dict:
        """Returns a dictionary with size, symbol, and color keys populated with values from trace"""
        marker = dict(
            size   = float(trace_model.point_size),
            symbol = trace_model.selected_point_shape,
            color  = trace_model.color
        )
        return marker
    
    def _update_marker_with_trace_advanced_settings(self, 
            marker: dict, 
            trace_model: 'TernaryTraceEditorModel') -> dict:
        
        advanced_settings_model = trace_model.advanced_settings_model

        marker.update(
            dict(
                opacity = advanced_settings_model.opacity,
                line = dict(
                    color = advanced_settings_model.outline_color,
                    width = advanced_settings_model.outline_thickness / 10
                    )
                )
        )
        return marker
    
    def _update_marker_dict_with_sizemap_config(
            self,
            marker: dict,
            trace_model: 'TernaryTraceEditorModel',
            data_df: pd.DataFrame,
            uuid: str, 
            trace_id: str) -> Tuple[dict, pd.DataFrame]:
        """Returns marker and data_df after making necessary changes for sizemap config"""

        sizemap_model = trace_model.sizemap_model
        size_column = sizemap_model.selected_column
        size_column_sorted = self.SIZEMAP_PATTERN.format(col=size_column, us=uuid)
        
        # Extract min and max sizes from range entries
        # TODO error handling for bad values
        #min_size = float(sizemap_model.range_min)
        min_size = self._float(sizemap_model.range_min, 'sizemap range minimum', trace_id)
        #max_size = float(sizemap_model.range_max)
        max_size = self._float(sizemap_model.range_max, 'sizemap range maximum', trace_id)

        # Normalize the size_column to the range [min_size, max_size]
        size_range = max_size - min_size
        size_normalized = ((data_df[size_column] - data_df[size_column].min()) / (data_df[size_column].max() - data_df[size_column].min())) * size_range + min_size
        sizeref = 2. * max(size_normalized) / (max_size**2)
        data_df[size_column_sorted] = size_normalized
        data_df[size_column_sorted].fillna(0.0, inplace=True)

        if sizemap_model.log_transform_checked:
            data_df[size_column_sorted] =\
                data_df[size_column_sorted].apply(lambda x: np.log(x) if x > 0 else 0)
            
        # Handle sizemap sort mode
        if sizemap_model.sorting_mode == 'no change':
            pass
        elif sizemap_model.sorting_mode == 'high on top':
            data_df = data_df.sort_values(
                by=size_column_sorted, 
                ascending=True)
        elif sizemap_model.sorting_mode == 'low on top':
            data_df = data_df.sort_values(
                by=size_column_sorted, 
                ascending=False)
        elif sizemap_model.sorting_mode == 'shuffled':
            data_df = data_df.sample(frac=1)

        marker['size'] = data_df[size_column_sorted]
        marker['sizemin'] = min_size
        marker['sizeref'] = sizeref

        return marker, data_df

    def _update_marker_dict_with_heatmap_config(
            self, 
            marker: dict, 
            trace_model: 'TernaryTraceEditorModel',
            data_df: pd.DataFrame,
            uuid: str, 
            trace_id: str) -> Tuple[dict, pd.DataFrame]:
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
                font=dict(
                    #size=float(heatmap_model.title_font_size),
                    size=self._float(heatmap_model.title_font_size, 'heatmap title font size', trace_id),
                    family=heatmap_model.font
                    )
                    ),
            #len=float(heatmap_model.length),
            len=self._float(heatmap_model.length, 'heatmap length', trace_id),
            #thickness=float(heatmap_model.thickness),
            thickness=self._float(heatmap_model.thickness, 'heatmap thickness', trace_id),
            # TODO add this (thickness) to view and controller
            #x=float(heatmap_model.x),
            x=self._float(heatmap_model.x, 'heatmap x position', trace_id),
            #y=float(heatmap_model.y),
            y=self._float(heatmap_model.y, 'heatmap y position', trace_id),
            tickfont=dict(
                #size=float(heatmap_model.tick_font_size),
                size=self._float(heatmap_model.tick_font_size, 'heatmap tick font size', trace_id),
                family=heatmap_model.font
                ),
            orientation='h' if heatmap_model.bar_orientation == 'horizontal' else 'v'
        )
        # TODO add error handling here for when floats fail or stuff is blank
        # TODO warn user if min >= max
        #marker['cmin'] = float(heatmap_model.range_min)
        marker['cmin'] = self._float(heatmap_model.range_min, 'heatmap range minimum', trace_id)
        #marker['cmax'] = float(heatmap_model.range_max)
        marker['cmax'] = self._float(heatmap_model.range_max, 'heatmap range maximum', trace_id)

        return marker, data_df

    def _get_trace_name(self, trace_model: 'TernaryTraceEditorModel'):
        """Extracts the trace name from the trace editor model"""
        return trace_model.legend_name
    
    def _apply_filters(
            self,
            data_df: pd.DataFrame,
            trace_model: 'TernaryTraceEditorModel',
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
            if operation in ['Equals', 'Exclude one'] or operation in ['<', '>', '≤', '≥']:
                if np.issubdtype(column_dtype, np.number):
                    try:
                        single_value = float(single_value) if single_value else None
                    except ValueError:
                        msg = "Error converting value to number."
                        raise TraceFilterFloatConversionException(trace_id, filter_id, msg)
            elif operation in ['One of', 'Exclude multiple']:
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
            else:
                raise ValueError(f'Usupported filter operation: {operation}')

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

    def _clean_percentile(self, percentile: float) -> float:
        """Returns a number between 0 and 1
        
        Arguments: A float, likely between 0 and 100
        """

        try:
            if percentile > 1:
                return percentile / 100
        except ValueError as err:
            # TODO figure out how to handle gracefull
            raise ValueError from err
        
    def _float(self, value: str, item: str=None, trace_id: str=None):
        try:
            return float(value)
        except ValueError as err:
            raise FloatConversionError(item, trace_id) from err

    
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
            try:
                self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = \
                    self.trace_data_df[[self.MOLAR_PATTERN.format(col=c, us=self.unique_str) for c in apex_cols_list]].sum(axis=1)
            except KeyError as err:
                msg = "The datafile for the specified trace is missing one or more columns required by the Plot Type"
                raise TraceMissingColumnException(self.trace_id, str(err).split('Index(')[1].split('dtype')[0].rstrip().rstrip(','), msg)
        return self.trace_data_df

    def nonmolar_conversion(self) -> pd.DataFrame:
        for apex_name, apex_cols_list in zip(['top', 'left', 'right'], 
                                             [self.top_columns, self.left_columns, self.right_columns]):
            if self.bootstrap:
                apex_cols_list = [self.SIMULATED_PATTERN.format(col=c, us=self.unique_str) for c in apex_cols_list]
            try:
                self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = \
                    self.trace_data_df[apex_cols_list].sum(axis=1)
            except KeyError as err:
                msg = "The datafile for the specified trace is missing one or more columns required by the Plot Type"
                raise TraceMissingColumnException(self.trace_id, str(err).split('Index(')[1].split('dtype')[0].rstrip().rstrip(','), msg)
        return self.trace_data_df

    def _add_molar_proportion_column(self, col: str, molar_mapping: Dict[str, str]) -> None:
        try:
            calculator = MolarMassCalculator()
            col_name = self.SIMULATED_PATTERN.format(col=col, us=self.unique_str) if self.bootstrap else col
            molar_col_name = self.MOLAR_PATTERN.format(col=col, us=self.unique_str)
            self.trace_data_df[molar_col_name] = self.trace_data_df[col_name] / calculator.get_molar_mass(molar_mapping.get(col))
        except MolarMassCalculatorException as e:
            raise TraceMolarConversionException(self.trace_id, col, molar_mapping.get(col), 'Error parsing formula for column.')
