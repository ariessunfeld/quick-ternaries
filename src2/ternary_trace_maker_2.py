import time
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from molar_calculator import MolarMassCalculator
from filters import (
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

class TernaryTraceMaker:
    """
    Creates Plotly Scatterternary traces for ternary diagrams based on the provided
    setup and trace models.
    """
    
    APEX_PATTERN = '__{apex}_{us}'
    HEATMAP_PATTERN = '__{col}_heatmap_{us}'
    SIZEMAP_PATTERN = '__{col}_sizemap_{us}'
    
    def __init__(self):
        """Initialize the trace maker with filter strategies and molar calculator."""
        self.calculator = MolarMassCalculator()
        
        # Filter strategies mapping
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
        }
    
    def make_trace(self, setup_model, trace_model) -> go.Scatterternary:
        """
        Creates a Plotly Scatterternary trace based on the provided setup and trace models.
        
        Args:
            setup_model: The SetupMenuModel containing global plot settings
            trace_model: The TraceEditorModel containing trace-specific settings
            
        Returns:
            A Plotly Scatterternary trace object
        """
        unique_str = self._generate_unique_str()
        
        # Get the column lists for each apex from the setup model
        top_columns = setup_model.axis_members.top_axis
        left_columns = setup_model.axis_members.left_axis
        right_columns = setup_model.axis_members.right_axis
        
        # Basic trace properties
        name = trace_model.trace_name
        marker = self._get_basic_marker_dict(trace_model)
        
        # Get scaling map
        scaling_map = self._get_scaling_map(setup_model)
        
        # Prepare the data for plotting
        marker, trace_data_df = self._prepare_data(
            setup_model, 
            trace_model,
            top_columns, 
            left_columns, 
            right_columns,
            unique_str,
            marker,
            scaling_map
        )
        
        # Get hover data and template
        customdata, hovertemplate = self._get_hover_data_and_template(
            setup_model, 
            trace_model, 
            trace_data_df,
            top_columns, 
            left_columns, 
            right_columns,
            scaling_map
        )
        
        # Get the values for each apex
        a = trace_data_df[self.APEX_PATTERN.format(apex='top', us=unique_str)]
        b = trace_data_df[self.APEX_PATTERN.format(apex='left', us=unique_str)]
        c = trace_data_df[self.APEX_PATTERN.format(apex='right', us=unique_str)]
        
        # Create the Scatterternary trace
        return go.Scatterternary(
            a=a, b=b, c=c,
            name=name,
            mode='markers',
            marker=marker,
            customdata=customdata,
            hovertemplate=hovertemplate,
            showlegend=True
        )
    
    def _get_scaling_map(self, setup_model) -> Dict[str, float]:
        """
        Extracts the scaling map from the setup model.
        
        Args:
            setup_model: The SetupMenuModel
            
        Returns:
            Dictionary mapping column names to scale factors
        """
        scaling_map = {}
        scaling_factors = setup_model.column_scaling.scaling_factors
        
        for axis_name, columns_dict in scaling_factors.items():
            for column, factor in columns_dict.items():
                if factor != 1.0:
                    scaling_map[column] = factor
        
        return scaling_map
    
    def _prepare_data(self, setup_model, trace_model, top_columns, left_columns, 
                     right_columns, unique_str, marker, scaling_map) -> Tuple[dict, pd.DataFrame]:
        """
        Prepares the data for plotting by applying filters, scaling, and configuring markers.
        
        Args:
            setup_model: The SetupMenuModel
            trace_model: The TraceEditorModel
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            unique_str: Unique string for column naming
            marker: Base marker dictionary
            scaling_map: Dictionary mapping column names to scale factors
            
        Returns:
            tuple: (marker, dataframe)
        """
        # Get the dataframe from the selected data file
        trace_data_df = trace_model.datafile.get_data().copy()
        
        # Apply filters if enabled
        if trace_model.filters_on:
            trace_data_df = self._apply_filters(trace_data_df, trace_model)
        
        # Apply scaling if needed
        if scaling_map:
            trace_data_df = self._apply_scale_factors(trace_data_df, scaling_map)
        
        # Apply molar conversion if enabled
        if trace_model.convert_from_wt_to_molar:
            trace_data_df = self._perform_molar_conversion(
                trace_data_df,
                setup_model,
                top_columns,
                left_columns,
                right_columns,
                unique_str
            )
        else:
            # Just sum the columns for each apex
            for apex_name, apex_cols_list in zip(
                ['top', 'left', 'right'], 
                [top_columns, left_columns, right_columns]
            ):
                trace_data_df[self.APEX_PATTERN.format(apex=apex_name, us=unique_str)] = \
                    trace_data_df[apex_cols_list].sum(axis=1)
        
        # Configure markers based on heatmap and sizemap settings
        if trace_model.heatmap_on and trace_model.sizemap_on:
            # Sort considering both heatmap and sizemap columns
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
        # Access filters from the trace model
        for filter_obj in trace_model.filters:
            # Skip if filter is not configured properly
            if not hasattr(filter_obj, 'column') or not hasattr(filter_obj, 'operation'):
                continue
                
            column = filter_obj.column
            operation = filter_obj.operation
            
            # Get values based on operation type
            filter_params = {
                'column': column,
                'operation': operation,
            }
            
            if operation in ['Equals', '<', '>', '≤', '≥', 'Exclude one']:
                filter_params['value 1'] = filter_obj.single_value
            elif operation in ['One of', 'Exclude multiple']:
                filter_params['selected values'] = filter_obj.selected_values
            elif operation in ['a < x < b', 'a ≤ x ≤ b', 'a ≤ x < b', 'a < x ≤ b']:
                filter_params['value a'] = filter_obj.value_a
                filter_params['value b'] = filter_obj.value_b
            
            # Apply the filter using appropriate strategy
            filter_strategy = self.operation_strategies.get(operation)
            if filter_strategy:
                data_df = filter_strategy.filter(data_df, filter_params)
        
        return data_df
    
    def _perform_molar_conversion(self, df: pd.DataFrame, setup_model, 
                                 top_columns: List[str], left_columns: List[str], 
                                 right_columns: List[str], unique_str: str) -> pd.DataFrame:
        """
        Performs molar conversion on the dataframe using scaled column values.
        
        Args:
            df: The dataframe to convert
            setup_model: The SetupMenuModel
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            unique_str: Unique string for column naming
            
        Returns:
            The converted dataframe
        """
        # Create molar converter with the scaled columns
        molar_converter = MolarConverter(
            df,
            top_columns,
            left_columns,
            right_columns,
            self.APEX_PATTERN,
            self.SCALED_COLUMN_PATTERN,
            unique_str,
            self.calculator
        )
        
        # Use formula mappings if available
        if hasattr(setup_model, 'molar_conversion_model'):
            formula_map = dict(setup_model.molar_conversion_model.get_sorted_repr())
            return molar_converter.molar_conversion(formula_map)
        else:
            # Default conversion if no mapping is provided
            return molar_converter.molar_conversion()
    
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
        if trace_model.heatmap_log_transform:
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
        if trace_model.heatmap_reverse_colorscale:
            colorscale += '_r'
        
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
            orientation='h' if trace_model.heatmap_bar_orientation == 'horizontal' else 'v'
        )
        
        # Set min and max values
        marker['cmin'] = float(trace_model.heatmap_min)
        marker['cmax'] = float(trace_model.heatmap_max)
        
        return marker, data_df
    
    def _perform_molar_conversion(self, df: pd.DataFrame, setup_model, 
                                 top_columns: List[str], left_columns: List[str], 
                                 right_columns: List[str], unique_str: str) -> pd.DataFrame:
        """
        Performs molar conversion on the dataframe.
        
        Args:
            df: The dataframe to convert
            setup_model: The SetupMenuModel
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            unique_str: Unique string for column naming
            
        Returns:
            The converted dataframe
        """
        # Create molar converter
        molar_converter = MolarConverter(
            df,
            top_columns,
            left_columns,
            right_columns,
            self.APEX_PATTERN,
            unique_str,
            self.calculator
        )
        
        # Use formula mappings if available
        if hasattr(setup_model, 'molar_conversion_model'):
            formula_map = dict(setup_model.molar_conversion_model.get_sorted_repr())
            return molar_converter.molar_conversion(formula_map)
        else:
            # Default conversion if no mapping is provided
            return molar_converter.molar_conversion()
    
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
        if trace_model.heatmap_log_transform:
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
        if trace_model.heatmap_reverse_colorscale:
            colorscale += '_r'
        
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
            orientation='h' if trace_model.heatmap_bar_orientation == 'horizontal' else 'v'
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
        
        # Normalize the size column
        size_range = max_size - min_size
        size_normalized = ((data_df[size_column_sorted] - data_df[size_column_sorted].min()) /
                         (data_df[size_column_sorted].max() - data_df[size_column_sorted].min())) * size_range + min_size
        sizeref = 2. * max(size_normalized) / (max_size**2)
        data_df[size_column_sorted] = size_normalized
        data_df[size_column_sorted].fillna(0.0, inplace=True)
        
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
        if trace_model.heatmap_log_transform:
            data_df[heatmap_sorted_col] = data_df[heatmap_column].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Process sizemap column
        data_df[sizemap_sorted_col] = data_df[sizemap_column].copy()
        if hasattr(trace_model, 'sizemap_log_transform') and trace_model.sizemap_log_transform:
            data_df[sizemap_sorted_col] = data_df[sizemap_column].apply(lambda x: np.log(x) if x > 0 else 0)
        
        # Normalize sizemap values
        min_size = float(trace_model.sizemap_min)
        max_size = float(trace_model.sizemap_max)
        size_range = max_size - min_size
        
        size_normalized = ((data_df[sizemap_sorted_col] - data_df[sizemap_sorted_col].min()) /
                         (data_df[sizemap_sorted_col].max() - data_df[sizemap_sorted_col].min())) * size_range + min_size
        data_df[sizemap_sorted_col] = size_normalized
        data_df[sizemap_sorted_col].fillna(0.0, inplace=True)
        
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
        sizeref = 2. * max(size_normalized) / (max_size**2)
        
        marker['size'] = data_df[sizemap_sorted_col]
        marker['sizemin'] = min_size
        marker['sizeref'] = sizeref
        marker['color'] = data_df[heatmap_sorted_col]
        marker['colorscale'] = trace_model.heatmap_colorscale
        
        if trace_model.heatmap_reverse_colorscale:
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
            orientation='h' if trace_model.heatmap_bar_orientation == 'horizontal' else 'v'
        )
        
        marker['cmin'] = float(trace_model.heatmap_min)
        marker['cmax'] = float(trace_model.heatmap_max)
        
        return marker, data_df
    
    def _get_hover_data_and_template(self, setup_model, trace_model, data_df: pd.DataFrame, 
                                    top_columns: List[str], left_columns: List[str], 
                                    right_columns: List[str], scaling_maps: Dict[str, Dict[str, float]]) -> Tuple[np.ndarray, str]:
        """
        Generates custom data for hover tooltips and an HTML template for the hover data.
        
        Args:
            setup_model: The SetupMenuModel
            trace_model: The TraceEditorModel
            data_df: The dataframe containing the data
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            scaling_maps: Dictionary mapping apex names to column scaling dictionaries
            
        Returns:
            tuple: (customdata array, hovertemplate string)
        """
        # Collect all apex columns
        apex_columns = top_columns + left_columns + right_columns
        
        # Create a merged scaling map for hover display
        merged_scale_map = {}
        for apex, col_map in scaling_maps.items():
            for col, factor in col_map.items():
                if col not in merged_scale_map or apex == 'all':
                    merged_scale_map[col] = factor
        """
        Generates custom data for hover tooltips and an HTML template for the hover data.
        
        Args:
            setup_model: The SetupMenuModel
            trace_model: The TraceEditorModel
            data_df: The dataframe containing the data
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            scaling_map: Dictionary mapping column names to scale factors
            
        Returns:
            tuple: (customdata array, hovertemplate string)
        """
        # Collect all apex columns
        apex_columns = top_columns + left_columns + right_columns
        
        # Determine which columns to display in hover
        use_custom_hover_data = hasattr(setup_model, 'custom_hover_data_is_checked') and setup_model.custom_hover_data_is_checked
        
        if use_custom_hover_data and hasattr(setup_model, 'axis_members') and hasattr(setup_model.axis_members, 'hover_data'):
            # Use custom hover data selected by the user
            hover_cols = setup_model.axis_members.hover_data
        else:
            # Default to apex columns and heatmap/sizemap columns
            hover_cols = apex_columns.copy()
            
            if trace_model.heatmap_on and trace_model.heatmap_column not in hover_cols:
                hover_cols.append(trace_model.heatmap_column)
                
            if trace_model.sizemap_on and trace_model.sizemap_column not in hover_cols:
                hover_cols.append(trace_model.sizemap_column)
                
            if trace_model.filters_on:
                for filter_obj in trace_model.filters:
                    if hasattr(filter_obj, 'column') and filter_obj.column not in hover_cols:
                        hover_cols.append(filter_obj.column)
        
        # Construct the hover template
        hovertemplate = "".join(
            f"<br><b>{f'{merged_scale_map.get(header, 1.0)}×' if header in merged_scale_map and merged_scale_map.get(header, 1.0) != 1 else ''}{header}:</b> %{{customdata[{i}]}}"
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
        
        # Transpose to match shape expected by Plotly
        customdata = np.array(customdata).T
        
        # Add row indices to customdata
        indices = data_df.index.to_numpy().reshape(-1, 1)
        customdata = np.hstack((customdata, indices))
        
        # Disable default hover text
        hovertemplate += "<extra></extra>"
        
        return customdata, hovertemplate
    
    def _get_basic_marker_dict(self, trace_model) -> dict:
        """
        Returns a dictionary with basic marker properties.
        
        Args:
            trace_model: The TraceEditorModel containing marker settings
            
        Returns:
            Dictionary with marker properties
        """
        marker = dict(
            size=float(trace_model.point_size),
            symbol=trace_model.point_shape,
            color=trace_model.trace_color
        )
        return marker
    
    def _generate_unique_str(self) -> str:
        """
        Generates a unique string to use in column names.
        
        Returns:
            A unique string based on current time
        """
        return str(hash(time.time()))


class MolarConverter:
    """
    Handles conversion from weight percentages to molar proportions for ternary plots.
    """
    
    MOLAR_PATTERN = '__{col}_molar_{us}'
    
    def __init__(self, 
                trace_data_df: pd.DataFrame,
                top_columns: List[str], 
                left_columns: List[str], 
                right_columns: List[str],
                apex_pattern: str,
                scaled_column_pattern: str,
                unique_str: str,
                calculator):
        """
        Initialize the molar converter.
        
        Args:
            trace_data_df: The dataframe to convert
            top_columns: List of columns for the top apex
            left_columns: List of columns for the left apex
            right_columns: List of columns for the right apex
            apex_pattern: Pattern to use for apex column names
            scaled_column_pattern: Pattern for scaled column names
            unique_str: Unique string for column naming
            calculator: MolarMassCalculator instance
        """
        self.trace_data_df = trace_data_df
        self.top_columns = top_columns
        self.left_columns = left_columns
        self.right_columns = right_columns
        self.apex_pattern = apex_pattern
        self.scaled_column_pattern = scaled_column_pattern
        self.unique_str = unique_str
        self.calculator = calculator
    
    def molar_conversion(self, formula_map=None) -> pd.DataFrame:
        """
        Performs molar conversion on the dataframe using scaled columns.
        
        Args:
            formula_map: Optional dictionary mapping column names to chemical formulas
            
        Returns:
            The converted dataframe
        """
        apex_columns = self.top_columns + self.left_columns + self.right_columns
        
        # Use provided formula map or default to using column names as formulas
        molar_mapping = formula_map or {c: c for c in apex_columns}
        
        # Process each apex
        for apex_name, apex_cols_list in zip(
            ['top', 'left', 'right'], 
            [self.top_columns, self.left_columns, self.right_columns]
        ):
            # Create a list to store molar columns
            molar_columns = []
            
            # Process each column in this apex
            for col in apex_cols_list:
                if col in molar_mapping:
                    # Get the formula for this column
                    formula = molar_mapping[col]
                    
                    # Get the scaled column name
                    scaled_col_name = self.scaled_column_pattern.format(
                        col=col, apex=apex_name, us=self.unique_str
                    )
                    
                    # Calculate molar mass using the calculator
                    try:
                        molar_mass = self.calculator.get_molar_mass(formula)
                        
                        # Create molar proportion column
                        molar_col_name = self.MOLAR_PATTERN.format(col=f"{col}_{apex_name}", us=self.unique_str)
                        self.trace_data_df[molar_col_name] = self.trace_data_df[scaled_col_name] / molar_mass
                        
                        # Add to list of molar columns
                        molar_columns.append(molar_col_name)
                    except Exception as e:
                        # Skip this column if there's an error calculating molar mass
                        print(f"Error calculating molar mass for {formula}: {e}")
            
            # Sum molar columns to get the apex value
            if molar_columns:
                self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = \
                    self.trace_data_df[molar_columns].sum(axis=1)
            else:
                # If no molar columns, use 0
                self.trace_data_df[self.apex_pattern.format(apex=apex_name, us=self.unique_str)] = 0
        
        return self.trace_data_df