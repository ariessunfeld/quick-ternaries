import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
import plotly.graph_objects as go

from quick_ternaries.services.molar_mass_calculator import MolarMassCalculator
from quick_ternaries.services.filters import (
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

from quick_ternaries.utils.functions import (
    util_convert_hex_to_rgba,
    format_scale_factor
)
from quick_ternaries.models.error_entry_model import ErrorEntryModel
from quick_ternaries.utils.contour_utils import (
    compute_kde_contours, 
)

if TYPE_CHECKING:
    from quick_ternaries.models.setup_menu_model import SetupMenuModel
    from quick_ternaries.models.trace_editor_model import TraceEditorModel


class CartesianContourException(Exception):
    """Exception raised when there's an error generating contours for a Cartesian trace."""
    def __init__(self, trace_id, message):
        self.trace_id = trace_id
        self.message = message
        super().__init__(f"Error in trace {trace_id}: {message}")

class CartesianContourTraceMaker:
    """
    Creates Plotly Scatter traces for bootstrap contours in Cartesian diagrams.
    This class handles specifically the contour generation logic for Cartesian plots.
    """
    
    # Pattern constants for column naming
    AXIS_PATTERN = '__{axis}_scaled_sum_{us}'
    SIMULATED_PATTERN = '__{col}_simulated_{us}'
    
    # Number of simulation points for bootstrap
    N_SIMULATION_POINTS = 10_000
    
    def __init__(self):
        """Initialize the Cartesian contour trace maker."""
        self.calculator = MolarMassCalculator()

    def make_trace(self, model, setup_model, trace_id: str) -> go.Scatter:
        """
        Creates a Plotly Scatter trace for a bootstrap contour.
        
        Args:
            model: The TraceEditorModel for the contour trace
            setup_model: The SetupMenuModel containing global plot settings
            trace_id: Unique identifier for the trace
            
        Returns:
            A Plotly Scatter trace object representing the contour
        """
        # Check if this is a contour trace
        if not getattr(model, "is_contour", False):
            raise ValueError(f"Trace {trace_id} is not a contour trace")
            
        # Check if source point data is available
        if not hasattr(model, "source_point_data") or not model.source_point_data:
            raise ValueError(f"Trace {trace_id} has no source point data")
            
        # Get the series from the source point data
        source_data = model.source_point_data
        if "series" not in source_data or not isinstance(source_data["series"], pd.Series):
            raise ValueError(f"Trace {trace_id} has invalid source point data")
            
        series = source_data["series"]
        
        unique_str = self._generate_unique_str()
        
        # Get column lists for x and y axes
        x_columns = self._get_axis_columns(setup_model, 'x_axis')
        y_columns = self._get_axis_columns(setup_model, 'y_axis')
        
        # Get scaling maps if needed
        if hasattr(setup_model, 'column_scaling') and hasattr(setup_model.column_scaling, 'scaling_factors'):
            scaling_map = self._get_scaling_map(setup_model)
        else:
            scaling_map = {}
        
        # Prepare trace name
        name = model.trace_name
        
        # Prepare the bootstrap data for contour generation
        marker, trace_data_df = self._prepare_bootstrap_data(
            model,
            setup_model,
            x_columns,
            y_columns,
            unique_str,
            trace_id,
            scaling_map,
            series
        )
        
        # Determine contour confidence level
        contour_level = model.contour_level
        if contour_level == "Contour: 1-sigma":
            contour_level = "68.27"  # 1-sigma = 68.27%
        elif contour_level == "Contour: 2-sigma":
            contour_level = "95.45"  # 2-sigma = 95.45%
        else:
            # Use custom percentile if defined
            contour_level = str(model.contour_percentile)
        
        # Generate contours
        x, y = self._generate_contours(trace_id, trace_data_df, unique_str, contour_level)
        
        # Get hover data and template
        customdata, hovertemplate = self._get_bootstrap_hover_data_and_template(model, scaling_map)
        
        # Set line properties
        line = dict(
            width=model.outline_thickness, 
            color=self._convert_hex_to_rgba(model.outline_color)
        )
        
        # Create the trace
        return go.Scatter(
            x=x, y=y,
            name=name,
            mode='lines',
            marker=marker,
            customdata=customdata,
            hovertemplate=hovertemplate,
            showlegend=not getattr(model, "exclude_from_legend", False),
            line=line,
            fill='toself'  # Add fill to create a closed contour
        )
    def _get_axis_columns(self, setup_model, axis_name):
        """Get the list of columns for a specific axis from the setup model."""
        if hasattr(setup_model, 'axis_members') and hasattr(setup_model.axis_members, axis_name):
            return getattr(setup_model.axis_members, axis_name)
        return []
    
    def _get_scaling_map(self, setup_model):
        """Returns a dictionary with scale factors for each column."""
        scaling_map = {}
        
        if hasattr(setup_model, 'column_scaling') and hasattr(setup_model.column_scaling, 'scaling_factors'):
            # Merge axis scaling factors
            axes = ['x_axis', 'y_axis']
            for axis in axes:
                if axis in setup_model.column_scaling.scaling_factors:
                    scaling_map.update(setup_model.column_scaling.scaling_factors[axis])
        
        return scaling_map
    
    def _prepare_bootstrap_data(
            self,
            model,
            setup_model,
            x_columns: List[str],
            y_columns: List[str],
            unique_str: str,
            trace_id: str,
            scaling_map: dict,
            series: pd.Series) -> Tuple[dict, pd.DataFrame]:
        """
        Prepare data for bootstrap contour generation.
        
        Args:
            model: The TraceEditorModel for this trace
            setup_model: The global setup model
            x_columns: List of columns for x axis
            y_columns: List of columns for y axis
            unique_str: Unique string for column naming
            trace_id: Trace identifier
            scaling_map: Dictionary of column scaling factors
            series: The pandas Series containing the point data
            
        Returns:
            Tuple of (marker dict, processed dataframe)
        """
        # Create a dataframe from the series
        trace_data_df = series.to_frame().T
        
        # Apply scaling if necessary
        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
            err_repr = self._generate_error_repr(model, series, scaling_map)
        else:
            err_repr = self._generate_error_repr(model, series)
        
        # Expand the dataframe to make room for simulated points
        trace_data_df = pd.DataFrame(
            data=np.repeat(
                trace_data_df.values, 
                self.N_SIMULATION_POINTS, 
                axis=0), 
            columns=trace_data_df.columns)
        
        # Fill the expanded dataframe with simulated data
        for col, err in err_repr.items():
            if col in trace_data_df.columns:
                sim_col_fmt = self.SIMULATED_PATTERN.format(col=col, us=unique_str)
                # Normal distribution simulation
                trace_data_df[sim_col_fmt] = np.random.normal(
                    trace_data_df[col].values[0], err, self.N_SIMULATION_POINTS)
        
        # Apply molar conversion if needed
        convert_to_molar = getattr(model, 'convert_from_wt_to_molar', False)
        
        # Call appropriate conversion method
        if convert_to_molar:
            trace_data_df = self._molar_calibration(
                setup_model,
                trace_data_df,
                x_columns,
                y_columns,
                unique_str,
                trace_id,
                convert_to_molar,
                bootstrap=True
            )
        else:
            # Simple summation for non-molar conversion
            for axis_name, axis_cols_list in zip(['x', 'y'], [x_columns, y_columns]):
                axis_cols_sim = [self.SIMULATED_PATTERN.format(col=c, us=unique_str) for c in axis_cols_list]
                try:
                    trace_data_df[self.AXIS_PATTERN.format(axis=axis_name, us=unique_str)] = \
                        trace_data_df[axis_cols_sim].sum(axis=1)
                except KeyError as err:
                    # Handle missing columns error
                    missing = [x for x in axis_cols_sim if x not in trace_data_df.columns]
                    raise Exception(f"Missing simulated columns: {missing}") from err
        
        # Create a basic marker dict
        marker = self._get_basic_marker_dict(model)
        
        return marker, trace_data_df
    
    def _generate_error_repr(self, model, series: pd.Series, scaling_map: Dict[str, float]=None) -> Dict[str, float]:
        """
        Generate error representation for bootstrap simulation using the error values from the model.
        
        Args:
            model: The trace model containing error settings
            series: The series containing point data
            scaling_map: Optional dictionary of scaling factors
            
        Returns:
            Dictionary mapping column names to error values
        """
        err_dict = {}
        
        # Use error values from the model
        if hasattr(model, "error_entry_model") and isinstance(model.error_entry_model, ErrorEntryModel):
            error_model = model.error_entry_model
            
            for col in series.index:
                if isinstance(series[col], (int, float, np.number)) and not pd.isna(series[col]):
                    # Get error from the model
                    err = error_model.get_error(col)
                    
                    # Apply scaling if provided
                    if scaling_map and col in scaling_map:
                        err *= scaling_map[col]
                        
                    err_dict[col] = err
        else:
            # Fallback to default error model if no error entry model
            for col, val in series.items():
                if isinstance(val, (int, float, np.number)) and not pd.isna(val):
                    # Simple error model: 5% of the value or 0.05, whichever is larger
                    err = max(abs(val) * 0.05, 0.05)
                    
                    # Apply scaling if provided
                    if scaling_map and col in scaling_map:
                        err *= scaling_map[col]
                        
                    err_dict[col] = err
        
        return err_dict
    
    def _molar_calibration(
            self,
            setup_model,
            trace_data_df: pd.DataFrame,
            x_columns: List[str],
            y_columns: List[str],
            unique_str: str,
            trace_id: str,
            convert_to_molar: bool,
            bootstrap: bool = True):
        """
        Convert weight percentages to molar proportions.
        """
        # Create a simplified MolarConverter for this function
        class MolarConverter:
            def __init__(self, df, x_cols, y_cols, axis_pattern, unique_str, calculator):
                self.df = df
                self.x_cols = x_cols
                self.y_cols = y_cols
                self.axis_pattern = axis_pattern
                self.unique_str = unique_str
                self.calculator = calculator
                self.SIMULATED_PATTERN = '__{col}_simulated_{us}'
                self.MOLAR_PATTERN = '__{col}_molar_{us}'
                
            def molar_conversion(self, formula_map=None):
                """Convert to molar proportions using chemical formulas."""
                axis_columns = self.x_cols + self.y_cols
                
                # Default to using column name as formula if no map provided
                if formula_map is None:
                    formula_map = {c: c for c in axis_columns}
                
                # Process each axis
                for axis_name, cols in zip(['x', 'y'], [self.x_cols, self.y_cols]):
                    molar_cols = []
                    
                    for col in cols:
                        if col in formula_map:
                            formula = formula_map[col]
                            
                            # For bootstrap, use simulated columns
                            sim_col = self.SIMULATED_PATTERN.format(col=col, us=self.unique_str)
                            if sim_col in self.df.columns:
                                try:
                                    molar_mass = self.calculator.get_molar_mass(formula)
                                    molar_col = self.MOLAR_PATTERN.format(col=col, us=self.unique_str)
                                    self.df[molar_col] = self.df[sim_col] / molar_mass
                                    molar_cols.append(molar_col)
                                except Exception as e:
                                    print(f"Warning: Error calculating molar mass for {formula}: {e}")
                    
                    # Sum molar values for the axis
                    if molar_cols:
                        self.df[self.axis_pattern.format(axis=axis_name, us=self.unique_str)] = \
                            self.df[molar_cols].sum(axis=1)
                    else:
                        # If no molar columns, use zeros
                        self.df[self.axis_pattern.format(axis=axis_name, us=self.unique_str)] = 0
                
                return self.df
                
            def nonmolar_conversion(self):
                """Simple normalization without molar conversion."""
                for axis_name, cols in zip(['x', 'y'], [self.x_cols, self.y_cols]):
                    # For bootstrap, use simulated columns
                    sim_cols = [self.SIMULATED_PATTERN.format(col=c, us=self.unique_str) for c in cols]
                    self.df[self.axis_pattern.format(axis=axis_name, us=self.unique_str)] = \
                        self.df[sim_cols].sum(axis=1)
                return self.df
        
        # Create converter instance
        converter = MolarConverter(
            trace_data_df,
            x_columns,
            y_columns,
            self.AXIS_PATTERN,
            unique_str,
            self.calculator
        )
        
        # Get formula mappings from setup model if available
        formula_map = None
        if hasattr(setup_model, 'chemical_formulas') and hasattr(setup_model.chemical_formulas, 'formulas'):
            formula_map = {}
            for axis_name, axis_cols in zip(
                ['x_axis', 'y_axis'],
                [x_columns, y_columns]
            ):
                if axis_name in setup_model.chemical_formulas.formulas:
                    for col, formula in setup_model.chemical_formulas.formulas[axis_name].items():
                        if col in x_columns + y_columns:
                            formula_map[col] = formula
        
        # Use molar conversion or simple normalization
        if convert_to_molar:
            return converter.molar_conversion(formula_map)
        else:
            return converter.nonmolar_conversion()

    def _generate_contours(
            self, 
            trace_id: str, 
            trace_data_df: pd.DataFrame,
            unique_str: str, 
            contour_level: str):
        """
        Generate contour data from the simulated points.
        
        Args:
            trace_id: Identifier for the trace
            trace_data_df: DataFrame with simulated points data
            unique_str: Unique string for column naming
            contour_level: Contour level (percentile) as a string
            
        Returns:
            tuple: (x, y) coordinates for the contour
        """
        try:
            # Extract x and y coordinates
            x_col = self.AXIS_PATTERN.format(axis='x', us=unique_str)
            y_col = self.AXIS_PATTERN.format(axis='y', us=unique_str)
            
            # Extract the coordinates as numpy arrays
            x_values = trace_data_df[x_col].values
            y_values = trace_data_df[y_col].values
            
            # Standardize the data to have similar scales - this helps the KDE algorithm
            x_mean, x_std = np.mean(x_values), np.std(x_values)
            y_mean, y_std = np.mean(y_values), np.std(y_values)
            
            x_values_std = (x_values - x_mean) / x_std
            y_values_std = (y_values - y_mean) / y_std
            
            # Create standardized points array
            cartesian_points_std = np.column_stack([x_values_std, y_values_std])
            
            # Compute contours on standardized data
            percentile = self._clean_percentile(contour_level)
            success, contours_std = compute_kde_contours(cartesian_points_std, [percentile], 150)
            
            if not success or not contours_std or len(contours_std) == 0:
                # Fallback to an elliptical contour if KDE fails
                theta = np.linspace(0, 2*np.pi, 100)
                x_circle_std = np.cos(theta)
                y_circle_std = np.sin(theta)
                
                # Transform back to original scale
                x_circle = x_circle_std * x_std + x_mean
                y_circle = y_circle_std * y_std + y_mean
                
                return x_circle, y_circle
            
            # Process contour segments to find the best one
            all_segments = []
            for contour_level in contours_std:
                for segment in contour_level:
                    if len(segment) >= 10:  # Only consider segments with sufficient points
                        all_segments.append(segment)
            
            if not all_segments:
                # Fallback to an elliptical contour if no valid segments
                theta = np.linspace(0, 2*np.pi, 100)
                x_circle_std = np.cos(theta)
                y_circle_std = np.sin(theta)
                
                # Transform back to original scale
                x_circle = x_circle_std * x_std + x_mean
                y_circle = y_circle_std * y_std + y_mean
                
                return x_circle, y_circle
            
            # Find the largest contour segment
            best_segment = max(all_segments, key=len)
            
            # Transform back to original scale
            x_coords_std = best_segment[:, 0]
            y_coords_std = best_segment[:, 1]
            
            x_coords = x_coords_std * x_std + x_mean
            y_coords = y_coords_std * y_std + y_mean
            
            # Ensure the contour is properly closed (essential for fill='toself')
            if not np.allclose(best_segment[0], best_segment[-1]):
                x_coords = np.append(x_coords, x_coords[0])
                y_coords = np.append(y_coords, y_coords[0])
                
            return x_coords, y_coords
        
        except Exception as e:
            # Provide a fallback for any exceptions
            print(f"Error generating contour for trace {trace_id}: {str(e)}")
            theta = np.linspace(0, 2*np.pi, 100)
            radius = 0.05 * max(np.std(x_values), np.std(y_values))
            x_circle = np.mean(x_values) + radius * np.cos(theta)
            y_circle = np.mean(y_values) + radius * np.sin(theta)
            return x_circle, y_circle
    
    def _get_bootstrap_hover_data_and_template(self, model, scale_map) -> Tuple[Optional[np.ndarray], str]:
        """
        Generates hover data and template for bootstrap contours.
        
        Args:
            model: The trace model
            scale_map: Dictionary of scaling factors
            
        Returns:
            Tuple of (customdata array, hovertemplate string)
        """
        # Construct hover template for the contour
        contour_mode = model.contour_level
        
        # Format contour level for display
        if contour_mode == "Contour: 1-sigma":
            display_level = "1-sigma (68.27%)"
        elif contour_mode == "Contour: 2-sigma":
            display_level = "2-sigma (95.45%)"
        else:
            # Custom percentile
            display_level = f"{model.contour_percentile}%"
        
        hovertemplate = f"<b>Contour:</b> {display_level}<br><br>"
        
        # Add trace name if available
        if hasattr(model, 'trace_name') and model.trace_name:
            hovertemplate += f"<b>Trace:</b> {model.trace_name}<br>"
        
        # Add component uncertainties if available
        if hasattr(model, 'error_entry_model') and isinstance(model.error_entry_model, ErrorEntryModel):
            hovertemplate += "<br><b>Component Uncertainties:</b><br>"
            
            sorted_entries = model.error_entry_model.get_sorted_repr()
            for component, error in sorted_entries:
                # Apply scaling if available
                scale_factor = scale_map.get(component, 1.0) if scale_map else 1.0
                display_component = f"{component}"
                if scale_factor != 1.0:
                    display_component = f"{scale_factor}× {component}"
                
                hovertemplate += f"{display_component}: ±{error}<br>"
        
        # Add standard footer to remove default hover text
        hovertemplate += "<extra></extra>"
        
        # No customdata for contours - they use the template directly
        return None, hovertemplate
    
    def _get_basic_marker_dict(self, model) -> dict:
        """
        Returns a dictionary with basic marker properties.
        """
        # For contours, we use a simplified marker since we're using lines mode
        marker = {}
        
        # Use trace color for marker if defined
        if hasattr(model, 'trace_color'):
            marker['color'] = self._convert_hex_to_rgba(model.trace_color)
        
        return marker

    def _apply_scale_factors(
            self,
            df: pd.DataFrame,
            scale_map: Dict[str, float]) -> pd.DataFrame:
        """
        Applies scale factors to columns in the DataFrame.
        """
        # Create a copy to avoid modifying the original
        scaled_df = df.copy()
        
        # Apply scaling to each column in the map
        for col, factor in scale_map.items():
            if col in scaled_df.columns:
                scaled_df[col] = factor * scaled_df[col]
                
        return scaled_df

    def _clean_percentile(self, percentile: str) -> float:
        """
        Converts a percentile string to a float between 0 and 1.
        """
        try:
            value = float(percentile)
            # If percentile is greater than 1, assume it's 0-100 scale and convert to 0-1
            if value > 1:
                return value / 100
            return value
        except ValueError:
            # Default to 0.95 (95%) if conversion fails
            return 0.95

    def _generate_unique_str(self) -> str:
        """Generates a unique string for column naming based on timestamp."""
        return str(hash(time.time()))

    def _convert_hex_to_rgba(self, hex_color: str) -> str:
        """
        Convert a hex color string to rgba format.
        """
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
            # If format is not recognized, return the original color
            return f"#{hex_color}"

class CartesianTraceMaker:
    """
    Creates Plotly Scatter traces for Cartesian diagrams based on the provided
    setup and trace models.
    """
    
    SCALED_COLUMN_PATTERN = '__{col}_scaled_{axis}_{us}'
    HEATMAP_PATTERN = '__{col}_heatmap_{us}'
    SIZEMAP_PATTERN = '__{col}_sizemap_{us}'
    
    def __init__(self):
        """Initialize the trace maker with filter strategies and molar calculator."""
        # Reuse the same calculator from TernaryTraceMaker
        if 'MolarMassCalculator' in globals():
            self.calculator = MolarMassCalculator()
        else:
            # If not available, create a dummy one that will be replaced later
            self.calculator = None
        
        # Filter strategies mapping - same as TernaryTraceMaker
        self.operation_strategies = {
            'is': EqualsFilterStrategy(),
            '==': EqualsFilterStrategy(),
            'is one of': OneOfFilterStrategy(),
            'is not': ExcludeOneFilterStrategy(),
            'is not one of': ExcludeMultipleFilterStrategy(),
            '<': LessThanFilterStrategy(),
            '>': GreaterThanFilterStrategy(),
            '<=': LessEqualFilterStrategy(),
            '>=': GreaterEqualFilterStrategy(),
            'a < x < b': LTLTFilterStrategy(),
            'a <= x <= b': LELEFilterStrategy(),
            'a <= x < b': LELTFilterStrategy(),
            'a < x <= b': LTLEFilterStrategy()
        }
    
    def make_trace(self, setup_model, trace_model) -> go.Scatter:
        """
        Creates a Plotly Scatter trace based on the provided setup and trace models.
        
        Args:
            setup_model: The SetupMenuModel containing global plot settings
            trace_model: The TraceEditorModel containing trace-specific settings
            
        Returns:
            A Plotly Scatter trace object
        """
        unique_str = self._generate_unique_str()
        
        # Get the column lists for x and y axes
        x_columns = setup_model.axis_members.x_axis
        y_columns = setup_model.axis_members.y_axis
        
        # Basic trace properties
        name = trace_model.trace_name
        marker = self._get_basic_marker_dict(trace_model)
        
        # Get scaling maps for each axis
        scaling_maps = self._get_scaling_maps(setup_model)
        
        # Prepare the data for plotting
        marker, trace_data_df = self._prepare_data(
            setup_model, 
            trace_model,
            x_columns, 
            y_columns,
            unique_str,
            marker,
            scaling_maps
        )
        
        # Get hover data and template
        customdata, hovertemplate = self._get_hover_data_and_template(
            setup_model, 
            trace_model, 
            trace_data_df,
            x_columns, 
            y_columns,
            scaling_maps
        )
        
        # Get the x and y data (scaled sums)
        x = trace_data_df[f'__x_scaled_sum_{unique_str}']
        y = trace_data_df[f'__y_scaled_sum_{unique_str}']
        
        # # Create mode based on trace settings
        # mode = 'markers'
        # if getattr(trace_model, 'line_on', False):
        #     mode += '+lines'

        # Apply min-max normalization if enabled
        if getattr(trace_model, "min_max_normalize", False):
            # x = self._normalize_values(x)
            y = self._normalize_values(y)

        # Apply vertical offset if enabled (after min-max normalization)
        if getattr(trace_model, "vertical_offset_on", False):
            offset_value = getattr(trace_model, "vertical_offset_value", 0.0)
            y = y + offset_value
        
        # Determine the mode based on point_on and line_on settings
        mode = ''
        if getattr(trace_model, 'point_on', True):
            mode += 'markers'
        
        if getattr(trace_model, 'line_on', False):
            if mode:
                mode += '+lines'
            else:
                mode = 'lines'
        
        # If both options are turned off, default to markers
        if not mode:
            mode = 'markers'
        
        # Line settings if enabled
        line = None
        if getattr(trace_model, 'line_on', False):
            line = {
                'color': self._convert_hex_to_rgba(trace_model.trace_color),
                'width': trace_model.line_thickness,
                'dash': trace_model.line_style
            }
        
        # Create the Scatter trace
        return go.Scatter(
            x=x, y=y,
            name=name,
            mode=mode,
            marker=marker,
            line=line,
            customdata=customdata,
            hovertemplate=hovertemplate,
            showlegend=not getattr(trace_model, "exclude_from_legend", False),
        )
    
    def _normalize_values(self, values):
        """Normalize values to range [0, 1] using min-max scaling."""
        if len(values) <= 1:
            return values
        min_val = values.min()
        max_val = values.max()
        if max_val > min_val:
            return (values - min_val) / (max_val - min_val)
        return values  # Return original if max=min to avoid division by zero

    def _make_vertical_line_trace(self, trace_model) -> go.Scatter:
        """
        Create a vertical line trace at a specific x value.
        
        Args:
            trace_model: The TraceEditorModel containing trace settings
            
        Returns:
            A Plotly Scatter trace representing a vertical line
        """
        # Get the x value where the vertical line should be drawn
        x_value = getattr(trace_model, "vertical_line_x_value", 0.0)
        
        # Create line style based on trace settings
        line = {
            'color': self._convert_hex_to_rgba(trace_model.trace_color),
            'width': trace_model.line_thickness,
            'dash': trace_model.line_style
        }
        
        # Create the trace with a vertical line spanning the entire y-axis
        return go.Scatter(
            x=[x_value, x_value],  # Same x-value for both points
            y=[0, 1],              # Spans from 0 to 1 in normalized coordinates
            name=trace_model.trace_name,
            mode='lines',
            line=line,
            showlegend=not getattr(trace_model, "exclude_from_legend", False),
            hoverinfo='x',         # Only show x-value on hover
        )
    
    def _get_scaling_maps(self, setup_model) -> Dict[str, Dict[str, float]]:
        """
        Extracts scaling maps for axes from the setup model.
        """
        scaling_maps = {
            'x': {},
            'y': {},
            'all': {}  # For backward compatibility and columns not in specific axis
        }
        
        # Check if column scaling is available
        if not hasattr(setup_model, 'column_scaling') or not hasattr(setup_model.column_scaling, 'scaling_factors'):
            return scaling_maps
        
        scaling_factors = setup_model.column_scaling.scaling_factors
        
        # Map model axis names to our axis names
        axis_to_axis = {
            'x_axis': 'x',
            'y_axis': 'y',
            'hover_data': 'all'
        }
        
        # Extract scaling factors for each axis
        for axis_name, columns_dict in scaling_factors.items():
            if axis_name in axis_to_axis:
                axis_mapped = axis_to_axis[axis_name]
                for column, factor in columns_dict.items():
                    scaling_maps[axis_mapped][column] = factor
                    # Also add to 'all' for backward compatibility
                    scaling_maps['all'][column] = factor
        
        return scaling_maps
    
    def _prepare_data(self, setup_model, trace_model, x_columns, y_columns, 
                  unique_str, marker, scaling_maps) -> Tuple[dict, pd.DataFrame]:
        """
        Prepares the data for plotting by applying filters, scaling, and configuring markers.
        
        Args:
            setup_model: The SetupMenuModel containing global settings
            trace_model: The TraceEditorModel containing trace settings
            x_columns: List of columns for the x axis
            y_columns: List of columns for the y axis
            unique_str: Unique string for column naming
            marker: Base marker dictionary
            scaling_maps: Dictionary mapping axis names to column scaling dictionaries
            
        Returns:
            tuple: (marker, dataframe)
        """
        # Get the dataframe using the DataframeManager
        if not hasattr(setup_model, 'data_library'):
            raise ValueError("Setup model must have a data_library attribute")
            
        # Get the dataframe for this trace using the metadata
        trace_data_df = setup_model.data_library.dataframe_manager.get_dataframe_by_metadata(trace_model.datafile)
        
        if trace_data_df is None:
            raise ValueError(f"Failed to load data for trace: {trace_model.trace_name}")
            
        # Make a copy to avoid modifying the original
        trace_data_df = trace_data_df.copy()
        
        # Apply filters if enabled
        if trace_model.filters_on:
            trace_data_df = self._apply_filters(trace_data_df, trace_model)
        
        # Apply scaling with axis-specific factors
        trace_data_df = self._apply_axis_specific_scaling(
            trace_data_df,
            x_columns,
            y_columns,
            scaling_maps,
            unique_str
        )
        
        # Apply molar conversion if enabled
        if trace_model.convert_from_wt_to_molar:
            trace_data_df = self._perform_molar_conversion(
                trace_data_df,
                setup_model,
                x_columns,
                y_columns,
                unique_str
            )
        else:
            # Sum the scaled columns for each axis
            for axis_name, axis_cols_list in zip(['x', 'y'], [x_columns, y_columns]):
                # Use the scaled column names
                scaled_cols = [
                    self.SCALED_COLUMN_PATTERN.format(col=col, axis=axis_name, us=unique_str)
                    for col in axis_cols_list
                ]
                
                # Sum the scaled columns
                if scaled_cols:
                    trace_data_df[f'__{axis_name}_scaled_sum_{unique_str}'] = \
                        trace_data_df[scaled_cols].sum(axis=1)
                else:
                    # Handle empty column lists
                    trace_data_df[f'__{axis_name}_scaled_sum_{unique_str}'] = 0
        
        # Configure markers based on heatmap and sizemap settings
        if trace_model.heatmap_on and trace_model.sizemap_on:
            # Sort and style considering both heatmap and sizemap columns
            marker, trace_data_df = self._integrated_sort(
                marker,
                trace_data_df,
                trace_model,
                unique_str
            )
        else:
            if trace_model.heatmap_on:
                marker, trace_data_df = self._update_marker_with_heatmap(
                    marker,
                    trace_model,
                    trace_data_df,
                    unique_str
                )
            
            if trace_model.sizemap_on:
                marker, trace_data_df = self._update_marker_with_sizemap(
                    marker,
                    trace_model,
                    trace_data_df,
                    unique_str
                )

        # Add outline to markers if sizemap is not enabled
        if not trace_model.sizemap_on:
            marker.update(
                dict(
                    line = dict(
                        color = self._convert_hex_to_rgba(trace_model.outline_color),
                        width = trace_model.outline_thickness / 10
                    )
                )
            )
        
        return marker, trace_data_df


    def _apply_filters(self, data_df: pd.DataFrame, trace_model) -> pd.DataFrame:
        """
        Applies filters to the dataframe.
        
        Args:
            data_df: The dataframe to filter
            trace_model: The TraceEditorModel containing filter settings
            
        Returns:
            The filtered dataframe
        """
        # If filters are not enabled or no filters exist, return original dataframe
        if not trace_model.filters_on or not trace_model.filters:
            return data_df
        
        # Make a copy to avoid modifying the original
        filtered_df = data_df.copy()
        
        # Track filters with issues for reporting
        filter_issues = []
        
        # Apply each filter in sequence
        for filter_obj in trace_model.filters:
            # Skip if filter is not configured properly
            if not hasattr(filter_obj, 'filter_column') or not hasattr(filter_obj, 'filter_operation'):
                filter_issues.append(f"Filter '{getattr(filter_obj, 'filter_name', 'Unknown')}' is missing required attributes")
                continue
            
            column = filter_obj.filter_column
            operation = filter_obj.filter_operation
            
            # Skip if column not in dataframe
            if column not in filtered_df.columns:
                filter_issues.append(f"Column '{column}' not found for filter '{filter_obj.filter_name}'")
                continue
            
            # Get column data type
            column_dtype = filtered_df[column].dtype
            is_numeric = pd.api.types.is_numeric_dtype(column_dtype)
            
            # Prepare filter parameters
            filter_params = {
                'column': column,
                'operation': operation,
            }
            
            try:
                # Single value operations
                if operation in ['==', '<', '>', '<=', '>=', 'is', 'is not']:
                    value = filter_obj.filter_value1
                    if is_numeric and value:
                        try:
                            value = float(value)
                        except ValueError:
                            raise ValueError(f"Cannot convert '{value}' to a number for filter '{filter_obj.filter_name}'")
                    filter_params['value 1'] = value
                    
                # Multi-value operations
                elif operation in ['is one of', 'is not one of']:
                    values = filter_obj.filter_value1
                    # Handle both list and string cases
                    if isinstance(values, str):
                        values = [v.strip() for v in values.split(',') if v.strip()]
                    elif not isinstance(values, list):
                        values = [values] if values else []
                    
                    if is_numeric and values:
                        try:
                            values = [float(v) for v in values]
                        except ValueError:
                            raise ValueError(f"Cannot convert one or more values to numbers for filter '{filter_obj.filter_name}'")
                    
                    filter_params['selected values'] = values
                    
                # Range operations
                elif operation in ['a < x < b', 'a <= x <= b', 'a <= x < b', 'a < x <= b']:
                    if not is_numeric:
                        raise ValueError(f"Cannot apply range operation '{operation}' to non-numeric column '{column}'")
                    
                    value_a = filter_obj.filter_value1
                    value_b = filter_obj.filter_value2
                    
                    try:
                        if value_a:
                            value_a = float(value_a)
                        if value_b:
                            value_b = float(value_b)
                    except ValueError:
                        raise ValueError(f"Cannot convert range values to numbers for filter '{filter_obj.filter_name}'")
                    
                    filter_params['value a'] = value_a
                    filter_params['value b'] = value_b
                    
                else:
                    raise ValueError(f"Unsupported filter operation: '{operation}'")
                
                # Apply the filter using appropriate strategy
                filter_strategy = self.operation_strategies.get(operation)
                if filter_strategy:
                    try:
                        # Apply filter and handle empty result case
                        result_df = filter_strategy.filter(filtered_df, filter_params)
                        if len(result_df) > 0:
                            filtered_df = result_df
                        else:
                            print(f"Warning: Filter '{filter_obj.filter_name}' resulted in zero rows")
                    except Exception as e:
                        raise ValueError(f"Error applying filter '{filter_obj.filter_name}': {str(e)}")
                else:
                    filter_issues.append(f"No strategy found for operation '{operation}' in filter '{filter_obj.filter_name}'")
                    
            except ValueError as e:
                filter_issues.append(str(e))
        
        # Log filter issues if any
        if filter_issues:
            print("Filter application issues:")
            for issue in filter_issues:
                print(f"  - {issue}")
        
        return filtered_df
    
    def _apply_axis_specific_scaling(self, df, x_columns, y_columns, 
                                    scaling_maps, unique_str) -> pd.DataFrame:
        """
        Applies axis-specific scaling to columns and creates scaled columns.
        """
        # Process each axis
        for axis_name, axis_cols_list in zip(['x', 'y'], [x_columns, y_columns]):
            # Get scaling map for this axis
            axis_scale_map = scaling_maps.get(axis_name, {})
            
            # Create scaled columns for each axis column
            for col in axis_cols_list:
                # Get the scale factor (default to 1.0)
                scale_factor = axis_scale_map.get(col, 1.0)
                
                # Create a scaled column
                scaled_col_name = self.SCALED_COLUMN_PATTERN.format(
                    col=col, axis=axis_name, us=unique_str
                )
                df[scaled_col_name] = df[col] * scale_factor
        
        return df
        
    def _get_basic_marker_dict(self, trace_model) -> dict:
        """
        Returns a dictionary with basic marker properties.
        """
        # Get the color from trace_model
        color = trace_model.trace_color
        
        # Convert hex color with alpha to rgba format if needed
        if color.startswith('#'):
            color = self._convert_hex_to_rgba(color)
            
        marker = dict(
            size=float(trace_model.point_size),
            symbol=trace_model.point_shape,
            color=color
        )
        
        # Add outline if specified
        if hasattr(trace_model, 'outline_thickness') and hasattr(trace_model, 'outline_color'):
            marker['line'] = dict(
                color=self._convert_hex_to_rgba(trace_model.outline_color),
                width=trace_model.outline_thickness / 10
            )
            
        return marker
        
    def _convert_hex_to_rgba(self, hex_color: str) -> str:
        """
        Convert a hex color string to rgba format.
        Handles hex formats: #RGB, #RGBA, #RRGGBB, #AARRGGBB
        
        Args:
            hex_color: Hex color string
            
        Returns:
            rgba color string
        """
        return util_convert_hex_to_rgba(hex_color)
    
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        if len(hex_color) == 8:  # #AARRGGBB format from ColorButton
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
        
        elif len(hex_color) == 4:  # #RGBA format
            r = int(hex_color[0] + hex_color[0], 16)
            g = int(hex_color[1] + hex_color[1], 16)
            b = int(hex_color[2] + hex_color[2], 16)
            a = int(hex_color[3] + hex_color[3], 16) / 255
            return f"rgba({r}, {g}, {b}, {a})"
        
        elif len(hex_color) == 3:  # #RGB format
            r = int(hex_color[0] + hex_color[0], 16)
            g = int(hex_color[1] + hex_color[1], 16)
            b = int(hex_color[2] + hex_color[2], 16)
            return f"rgba({r}, {g}, {b}, 1)"
        
        else:
            # If the format is not recognized, return the original color
            return f"#{hex_color}"
            
    def _generate_unique_str(self) -> str:
        """
        Generates a unique string to use in column names.
        """
        return str(hash(time.time()))
    
    def _update_marker_with_heatmap(self, marker: dict, trace_model, 
                              data_df: pd.DataFrame, unique_str: str) -> Tuple[dict, pd.DataFrame]:
        """
        Updates the marker dictionary with heatmap configuration.
        
        Args:
            marker: The marker dictionary to update
            trace_model: The TraceEditorModel containing heatmap settings
            data_df: The dataframe containing the data
            unique_str: Unique string for column naming
            
        Returns:
            tuple: (updated marker, updated dataframe)
        """
        color_column = trace_model.heatmap_column
        heatmap_sorted_col = self.HEATMAP_PATTERN.format(col=color_column, us=unique_str)
        
        # Copy the column
        data_df[heatmap_sorted_col] = data_df[color_column].copy()
        
        # Apply log transform if enabled
        if hasattr(trace_model, 'heatmap_log_transform') and trace_model.heatmap_log_transform:
            data_df[heatmap_sorted_col] = data_df[color_column].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Apply sorting
        if trace_model.heatmap_sort_mode == 'high on top':
            data_df = data_df.sort_values(
                by=heatmap_sorted_col,
                ascending=True
            )
        elif trace_model.heatmap_sort_mode == 'low on top':
            data_df = data_df.sort_values(
                by=heatmap_sorted_col,
                ascending=False
            )
        elif trace_model.heatmap_sort_mode == 'shuffled':
            data_df = data_df.sample(frac=1)
        
        # Configure marker properties
        colorscale = trace_model.heatmap_colorscale
        if hasattr(trace_model, 'heatmap_reverse_colorscale') and trace_model.heatmap_reverse_colorscale:
            colorscale += '_r'
        
        # Set color values from dataframe
        marker['color'] = data_df[heatmap_sorted_col]
        marker['colorscale'] = colorscale
        
        # Configure colorbar
        marker['colorbar'] = dict(
            title=dict(
                text=color_column,
                side=trace_model.heatmap_title_position if hasattr(trace_model, 'heatmap_title_position') else 'right',
                font=dict(
                    size=float(trace_model.heatmap_title_font_size) if hasattr(trace_model, 'heatmap_title_font_size') else 12,
                    family=trace_model.heatmap_font if hasattr(trace_model, 'heatmap_font') else 'Arial'
                )
            ),
            len=float(trace_model.heatmap_colorbar_len),
            thickness=float(trace_model.heatmap_colorbar_thickness),
            x=float(trace_model.heatmap_colorbar_x),
            y=float(trace_model.heatmap_colorbar_y),
            tickfont=dict(
                size=float(trace_model.heatmap_tick_font_size) if hasattr(trace_model, 'heatmap_tick_font_size') else 10,
                family=trace_model.heatmap_font if hasattr(trace_model, 'heatmap_font') else 'Arial'
            ),
            orientation='h' if hasattr(trace_model, 'heatmap_bar_orientation') and trace_model.heatmap_bar_orientation == 'horizontal' else 'v'
        )
        
        # Set min and max values
        marker['cmin'] = float(trace_model.heatmap_min)
        marker['cmax'] = float(trace_model.heatmap_max)
        
        return marker, data_df

    def _update_marker_with_sizemap(self, marker: dict, trace_model, 
                                data_df: pd.DataFrame, unique_str: str) -> Tuple[dict, pd.DataFrame]:
        """
        Updates the marker dictionary with sizemap configuration.
        
        Args:
            marker: The marker dictionary to update
            trace_model: The TraceEditorModel containing sizemap settings
            data_df: The dataframe containing the data
            unique_str: Unique string for column naming
            
        Returns:
            tuple: (updated marker, updated dataframe)
        """
        size_column = trace_model.sizemap_column
        size_column_sorted = self.SIZEMAP_PATTERN.format(col=size_column, us=unique_str)
        
        # Extract min and max sizes
        min_size = float(trace_model.sizemap_min)
        max_size = float(trace_model.sizemap_max)
        
        # Copy the column
        data_df[size_column_sorted] = data_df[size_column].copy()
        
        # Apply log transform if available
        if hasattr(trace_model, 'sizemap_log_transform') and trace_model.sizemap_log_transform:
            data_df[size_column_sorted] = data_df[size_column_sorted].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Normalize the size column to map between min_size and max_size
        if len(data_df) > 0:
            size_range = max_size - min_size
            col_min = data_df[size_column_sorted].min()
            col_max = data_df[size_column_sorted].max()
            
            # Avoid division by zero if all values are the same
            if col_max > col_min:
                size_normalized = ((data_df[size_column_sorted] - col_min) / 
                                (col_max - col_min)) * size_range + min_size
            else:
                size_normalized = pd.Series([min_size + (size_range/2)] * len(data_df), index=data_df.index)
                
            sizeref = 2. * max(size_normalized) / (max_size**2)
            data_df[size_column_sorted] = size_normalized
            data_df[size_column_sorted].fillna(min_size, inplace=True)
        else:
            # Handle empty dataframe
            sizeref = 1.0
        
        # Apply sorting
        if trace_model.sizemap_sort_mode == 'high on top':
            data_df = data_df.sort_values(
                by=size_column_sorted,
                ascending=True
            )
        elif trace_model.sizemap_sort_mode == 'low on top':
            data_df = data_df.sort_values(
                by=size_column_sorted,
                ascending=False
            )
        elif trace_model.sizemap_sort_mode == 'shuffled':
            data_df = data_df.sample(frac=1)
        
        # Update marker properties
        marker['size'] = data_df[size_column_sorted]
        marker['sizemin'] = min_size
        marker['sizeref'] = sizeref
        
        return marker, data_df

    def _integrated_sort(self, marker: dict, data_df: pd.DataFrame, 
                        trace_model, unique_str: str) -> Tuple[dict, pd.DataFrame]:
        """
        Performs integrated sorting considering both heatmap and sizemap.
        
        Args:
            marker: The marker dictionary to update
            data_df: The dataframe to sort
            trace_model: The TraceEditorModel containing sort settings
            unique_str: Unique string for column naming
            
        Returns:
            tuple: (updated marker, sorted dataframe)
        """
        heatmap_column = trace_model.heatmap_column
        sizemap_column = trace_model.sizemap_column
        
        heatmap_sorted_col = self.HEATMAP_PATTERN.format(col=heatmap_column, us=unique_str)
        sizemap_sorted_col = self.SIZEMAP_PATTERN.format(col=sizemap_column, us=unique_str)
        
        # Process heatmap column
        data_df[heatmap_sorted_col] = data_df[heatmap_column].copy()
        if hasattr(trace_model, 'heatmap_log_transform') and trace_model.heatmap_log_transform:
            data_df[heatmap_sorted_col] = data_df[heatmap_column].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Process sizemap column
        data_df[sizemap_sorted_col] = data_df[sizemap_column].copy()
        if hasattr(trace_model, 'sizemap_log_transform') and trace_model.sizemap_log_transform:
            data_df[sizemap_sorted_col] = data_df[sizemap_column].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Normalize sizemap values
        min_size = float(trace_model.sizemap_min)
        max_size = float(trace_model.sizemap_max)
        size_range = max_size - min_size
        
        if len(data_df) > 0:
            col_min = data_df[sizemap_sorted_col].min()
            col_max = data_df[sizemap_sorted_col].max()
            
            # Avoid division by zero if all values are the same
            if col_max > col_min:
                size_normalized = ((data_df[sizemap_sorted_col] - col_min) / 
                                (col_max - col_min)) * size_range + min_size
            else:
                size_normalized = pd.Series([min_size + (size_range/2)] * len(data_df), index=data_df.index)
                
            data_df[sizemap_sorted_col] = size_normalized
            data_df[sizemap_sorted_col].fillna(min_size, inplace=True)
        
        # Handle heatmap sort mode
        if trace_model.heatmap_sort_mode == 'high on top':
            data_df = data_df.sort_values(
                by=heatmap_sorted_col,
                ascending=True
            )
        elif trace_model.heatmap_sort_mode == 'low on top':
            data_df = data_df.sort_values(
                by=heatmap_sorted_col,
                ascending=False
            )
        elif trace_model.heatmap_sort_mode == 'shuffled':
            data_df = data_df.sample(frac=1)
        
        # Handle sizemap sort mode
        if trace_model.sizemap_sort_mode == 'high on top':
            data_df = data_df.sort_values(
                by=sizemap_sorted_col,
                ascending=True
            )
        elif trace_model.sizemap_sort_mode == 'low on top':
            data_df = data_df.sort_values(
                by=sizemap_sorted_col,
                ascending=False
            )
        elif trace_model.sizemap_sort_mode == 'shuffled':
            data_df = data_df.sample(frac=1)
        
        # Update marker properties
        if len(data_df) > 0:
            sizeref = 2. * data_df[sizemap_sorted_col].max() / (max_size**2)
        else:
            sizeref = 1.0
        
        marker['size'] = data_df[sizemap_sorted_col]
        marker['sizemin'] = min_size
        marker['sizeref'] = sizeref
        marker['color'] = data_df[heatmap_sorted_col]
        marker['colorscale'] = trace_model.heatmap_colorscale
        
        if hasattr(trace_model, 'heatmap_reverse_colorscale') and trace_model.heatmap_reverse_colorscale:
            marker['colorscale'] += '_r'
        
        # Configure colorbar
        marker['colorbar'] = dict(
            title=dict(
                text=heatmap_column,
                side=trace_model.heatmap_title_position if hasattr(trace_model, 'heatmap_title_position') else 'right',
                font=dict(
                    size=float(trace_model.heatmap_title_font_size) if hasattr(trace_model, 'heatmap_title_font_size') else 12,
                    family=trace_model.heatmap_font if hasattr(trace_model, 'heatmap_font') else 'Arial'
                )
            ),
            len=float(trace_model.heatmap_colorbar_len),
            thickness=float(trace_model.heatmap_colorbar_thickness),
            x=float(trace_model.heatmap_colorbar_x),
            y=float(trace_model.heatmap_colorbar_y),
            tickfont=dict(
                size=float(trace_model.heatmap_tick_font_size) if hasattr(trace_model, 'heatmap_tick_font_size') else 10,
                family=trace_model.heatmap_font if hasattr(trace_model, 'heatmap_font') else 'Arial'
            ),
            orientation='h' if hasattr(trace_model, 'heatmap_bar_orientation') and trace_model.heatmap_bar_orientation == 'horizontal' else 'v'
        )
        
        marker['cmin'] = float(trace_model.heatmap_min)
        marker['cmax'] = float(trace_model.heatmap_max)
        
        return marker, data_df
    
    def _perform_molar_conversion(self, df: pd.DataFrame, setup_model, 
                             x_columns: List[str], y_columns: List[str], 
                             unique_str: str) -> pd.DataFrame:
        """
        Performs molar conversion on the dataframe using scaled column values.
        
        Args:
            df: The dataframe to convert
            setup_model: The SetupMenuModel
            x_columns: List of columns for the x axis
            y_columns: List of columns for the y axis
            unique_str: Unique string for column naming
            
        Returns:
            The converted dataframe
        """
        # For cartesian plots, we convert scaled columns to molar values 
        # and then sum them to get the axis values
        
        # Get formula mappings from setup model if available
        formula_map = None
        if hasattr(setup_model, 'chemical_formulas') and hasattr(setup_model.chemical_formulas, 'formulas'):
            formula_map = {}
            for axis_name, axis_cols in zip(
                ['x_axis', 'y_axis'],
                [x_columns, y_columns]
            ):
                if axis_name in setup_model.chemical_formulas.formulas:
                    for col, formula in setup_model.chemical_formulas.formulas[axis_name].items():
                        if col in x_columns + y_columns:
                            formula_map[col] = formula
        
        # Process each axis
        for axis_name, axis_cols_list in zip(['x', 'y'], [x_columns, y_columns]):
            # Create a list to store molar columns
            molar_columns = []
            
            # Process each column in this axis
            for col in axis_cols_list:
                if formula_map and col in formula_map:
                    # Get the formula for this column
                    formula = formula_map[col]
                    
                    # Get the scaled column name
                    scaled_col_name = self.SCALED_COLUMN_PATTERN.format(
                        col=col, axis=axis_name, us=unique_str
                    )
                    
                    # Calculate molar mass using the calculator
                    try:
                        molar_mass = self.calculator.get_molar_mass(formula)
                        
                        # Create molar proportion column
                        molar_col_name = f"__{col}_{axis_name}_molar_{unique_str}"
                        df[molar_col_name] = df[scaled_col_name] / molar_mass
                        
                        # Add to list of molar columns
                        molar_columns.append(molar_col_name)
                    except Exception as e:
                        # Skip this column if there's an error calculating molar mass
                        print(f"\t\tWARNING: Error calculating molar mass for {formula}: {e}")
                else:
                    # If no formula mapping, use the scaled column directly
                    scaled_col_name = self.SCALED_COLUMN_PATTERN.format(
                        col=col, axis=axis_name, us=unique_str
                    )
                    molar_columns.append(scaled_col_name)
            
            # Sum columns to get the axis value
            if molar_columns:
                df[f'__{axis_name}_scaled_sum_{unique_str}'] = df[molar_columns].sum(axis=1)
            else:
                # If no molar columns, use 0
                df[f'__{axis_name}_scaled_sum_{unique_str}'] = 0
        
        return df

    def _get_hover_data_and_template(
            self, 
            setup_model: "SetupMenuModel", 
            trace_model: "TraceEditorModel", 
            data_df: pd.DataFrame, 
            x_columns: List[str], 
            y_columns: List[str], 
            scaling_maps: Dict[str, Dict[str, float]]
        ) -> Tuple[np.ndarray, str]:
        """
        Generates custom data for hover tooltips and an HTML template for the hover data.
        
        Args:
            setup_model: The SetupMenuModel
            trace_model: The TraceEditorModel
            data_df: The dataframe containing the data
            x_columns: List of columns for the x axis
            y_columns: List of columns for the y axis
            scaling_maps: Dictionary mapping axis names to column scaling dictionaries
            
        Returns:
            tuple: (customdata array, hovertemplate string)
        """
        # Collect all axis columns
        axis_columns = x_columns + y_columns
        
        # Create a merged scaling map for hover display
        merged_scale_map = {}
        for axis, col_map in scaling_maps.items():
            for col, factor in col_map.items():
                if col not in merged_scale_map or axis == 'all':
                    merged_scale_map[col] = factor
        
        # Determine which columns to display in hover
        if hasattr(setup_model, 'axis_members') and hasattr(setup_model.axis_members, 'hover_data') and setup_model.axis_members.hover_data:
            # Use hover data selected by the user
            hover_cols = setup_model.axis_members.hover_data
        else:
            # Default to apex columns and heatmap/sizemap columns
            hover_cols = axis_columns.copy()
            
            if trace_model.heatmap_on and trace_model.heatmap_column not in hover_cols:
                hover_cols.append(trace_model.heatmap_column)
                
            if trace_model.sizemap_on and trace_model.sizemap_column not in hover_cols:
                hover_cols.append(trace_model.sizemap_column)
                
            if trace_model.filters_on:
                for filter_obj in trace_model.filters:
                    if hasattr(filter_obj, 'filter_column') and filter_obj.filter_column not in hover_cols:
                        hover_cols.append(filter_obj.filter_column)
        
        # Construct the hover template
        hovertemplate = "<b>x</b>: %{x}<br><b>y</b>: %{y}"
        hovertemplate += "".join(
            f"<br><b>{f'{format_scale_factor(merged_scale_map.get(header, 1.0))}×' if header in merged_scale_map and merged_scale_map.get(header, 1.0) != 1 else ''}{header}:</b> %{{customdata[{i}]}}"
            for i, header in enumerate(hover_cols)
        )
        
        # Construct customdata with rounded values
        customdata = []
        for header in hover_cols:
            try:
                # Try to round numeric values
                rounded_values = np.round(data_df[header].values.astype(float), 4)
            except (ValueError, TypeError):
                # Use raw values for non-numeric columns
                rounded_values = data_df[header].values
            customdata.append(rounded_values)
        
        # If no hover columns, create a placeholder column
        if not customdata:
            customdata = [[0] * len(data_df)]
        
        # Transpose to match shape expected by Plotly
        customdata = np.array(customdata).T
        
        # Add row indices to customdata
        indices = data_df.index.to_numpy().reshape(-1, 1)
        customdata = np.hstack((customdata, indices))
        
        # Disable default hover text
        hovertemplate += "<extra></extra>"
        
        return customdata, hovertemplate
