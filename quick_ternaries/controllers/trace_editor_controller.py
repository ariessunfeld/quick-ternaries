from typing import TYPE_CHECKING

# -----------------------------------

import numpy as np
import pandas as pd
from PySide6.QtWidgets import QDoubleSpinBox
from PySide6.QtWidgets import QComboBox
from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QTabWidget

# -----------------------------------

from quick_ternaries.utils.functions import get_numeric_columns_from_dataframe
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.views.filter_editor_view import FilterEditorView

if TYPE_CHECKING:
    from quick_ternaries.models.data_library_model import DataLibraryModel
    from quick_ternaries.models.trace_editor_model import TraceEditorModel
    from quick_ternaries.views.trace_editor_view import TraceEditorView

class TraceEditorController:
    def __init__(
            self,
            model: "TraceEditorModel",
            view: "TraceEditorView",
            data_library: "DataLibraryModel",
        ):
        self.model = model
        self.view = view
        self.data_library = data_library  # Pass the DataLibraryModel for lookup
        self.connect_heatmap_column_change()

    def _update_heatmap_min_max_for_column(self, column_name: str):
        """Update heatmap min/max based on the selected column's median."""
        if not column_name:
            return
            
        # Get the dataframe
        datafile = self.model.datafile
        if not datafile or not datafile.file_path:
            return
            
        df = self.data_library.dataframe_manager.get_dataframe_by_metadata(datafile)
        if df is None or column_name not in df.columns:
            return
            
        # Calculate the median
        # TODO fix this lazy try/except
        try:
            # Filter to only numeric values and drop NaNs for median calculation
            numeric_values = pd.to_numeric(df[column_name], errors='coerce').dropna()
            if len(numeric_values) > 0:
                median_value = np.nanmedian(numeric_values)
                
                # Set min to 0 and max to 2x median
                self.model.heatmap_min = 0.0
                self.model.heatmap_max = float(median_value * 2)
                
                # Update the UI widgets if they exist
                if hasattr(self.view, "widgets"):
                    min_widget = self.view.widgets.get("heatmap_min")
                    max_widget = self.view.widgets.get("heatmap_max")
                    
                    if min_widget and isinstance(min_widget, QDoubleSpinBox):
                        min_widget.blockSignals(True)
                        min_widget.setValue(self.model.heatmap_min)
                        min_widget.blockSignals(False)
                        
                    if max_widget and isinstance(max_widget, QDoubleSpinBox):
                        max_widget.blockSignals(True)
                        max_widget.setValue(self.model.heatmap_max)
                        max_widget.blockSignals(False)
        except Exception as e:
            print(f"Error calculating median for column {column_name}: {e}")


    def connect_heatmap_column_change(self):
        """Connect to heatmap column combobox currentTextChanged signal."""
        if hasattr(self.view, "widgets"):
            heatmap_combo = self.view.widgets.get("heatmap_column")
            if heatmap_combo:
                # Disconnect any existing connections first
                try:
                    heatmap_combo.currentTextChanged.disconnect(self._on_heatmap_column_changed)
                except (TypeError, RuntimeError):
                    pass  # No connections exist
                    
                # Connect our handler
                heatmap_combo.currentTextChanged.connect(self._on_heatmap_column_changed)
            
    def _on_heatmap_column_changed(self, column_name: str):
        """Handle when the heatmap column changes."""
        # Update min/max based on the data
        self._update_heatmap_min_max_for_column(column_name)

    def calculate_datafile_change_impacts(self, new_datafile):
        """
        Calculate the impacts of changing from the current datafile to a new one.
        
        Args:
            new_datafile: The potential new datafile metadata
            
        Returns:
            tuple: (impacts_list, has_critical_impacts)
                - impacts_list: List of string descriptions of impacts
                - has_critical_impacts: True if there are critical impacts that might lose data
        """
        impacts = []
        has_critical = False
        
        # Skip if the datafiles are the same
        if self.model.datafile == new_datafile:
            return impacts, has_critical
        
        # Get current dataframe
        current_df = None
        if self.model.datafile and self.model.datafile.file_path:
            current_df = self.data_library.dataframe_manager.get_dataframe_by_metadata(self.model.datafile)
        
        # Get new dataframe
        new_df = None
        if new_datafile and new_datafile.file_path:
            new_df = self.data_library.dataframe_manager.get_dataframe_by_metadata(new_datafile)
        
        if new_df is None:
            impacts.append("⚠️ Cannot access the new datafile - unable to validate impacts")
            has_critical = True
            return impacts, has_critical
        
        # Compare columns between dataframes
        current_columns = set(current_df.columns) if current_df is not None else set()
        new_columns = set(new_df.columns)
        
        # Get numeric columns from new dataframe
        new_numeric_cols = get_numeric_columns_from_dataframe(new_df)
        new_numeric_cols_set = set(new_numeric_cols)
        
        # Check heatmap column
        if hasattr(self.model, "heatmap_on") and self.model.heatmap_on:
            heatmap_col = self.model.heatmap_column
            if heatmap_col:
                if heatmap_col not in new_columns:
                    impacts.append(f"🔴 Heatmap column '{heatmap_col}' not found in new datafile - will be reset")
                    has_critical = True
                elif heatmap_col not in new_numeric_cols_set:
                    impacts.append(f"🔴 Heatmap column '{heatmap_col}' is not numeric in new datafile - will be reset")
                    has_critical = True
        
        # Check sizemap column
        if hasattr(self.model, "sizemap_on") and self.model.sizemap_on:
            print(f"Checking sizemap column '{self.model.sizemap_column}' impacts")
            sizemap_col = self.model.sizemap_column
            if sizemap_col:
                if sizemap_col not in new_columns:
                    impacts.append(f"🔴 Sizemap column '{sizemap_col}' not found in new datafile - will be reset")
                    has_critical = True
                    print(f"  Sizemap column '{sizemap_col}' not found in new columns: {list(new_columns)[:5]}...")
                elif sizemap_col not in new_numeric_cols_set:
                    impacts.append(f"🔴 Sizemap column '{sizemap_col}' is not numeric in new datafile - will be reset")
                    has_critical = True
                    print(f"  Sizemap column '{sizemap_col}' not numeric in new datafile")
                else:
                    print(f"  Sizemap column '{sizemap_col}' is valid in new datafile")
        else:
            print(f"Sizemap not enabled or no sizemap_on attribute, sizemap_on={getattr(self.model, 'sizemap_on', 'MISSING')}")

        
        # Check filters
        if hasattr(self.model, "filters_on") and self.model.filters_on and hasattr(self.model, "filters"):
            for i, filter_model in enumerate(self.model.filters):
                filter_col = filter_model.filter_column
                if filter_col:
                    if filter_col not in new_columns:
                        impacts.append(f"🔴 Filter '{filter_model.filter_name}' column '{filter_col}' not found in new datafile - will be reset")
                        has_critical = True
                    else:
                        # Check if operation is compatible with new column type
                        old_is_numeric = (current_df is not None and 
                                        filter_col in current_df.columns and 
                                        pd.api.types.is_numeric_dtype(current_df[filter_col]))
                        new_is_numeric = filter_col in new_numeric_cols_set
                        
                        if old_is_numeric != new_is_numeric:
                            # Type of column changed, check if operation is compatible
                            if old_is_numeric and not new_is_numeric:
                                # Switched from numeric to non-numeric
                                if filter_model.filter_operation in [
                                    "<", ">", "<=", ">=", "==", "a < x < b", "a <= x < b", "a < x <= b", "a <= x <= b"
                                ]:
                                    impacts.append(f"🔴 Filter '{filter_model.filter_name}' operation '{filter_model.filter_operation}' not compatible with non-numeric column in new datafile - will be reset")
                                    has_critical = True
                            elif not old_is_numeric and new_is_numeric:
                                # This is actually an improvement, but still note it
                                impacts.append(f"ℹ️ Filter '{filter_model.filter_name}' column changed from non-numeric to numeric - more operations available")
                        
                        # For "is one of" or "is not one of" operations, check if values exist in new datafile
                        if filter_model.filter_operation in ["is one of", "is not one of"]:
                            if isinstance(filter_model.filter_value1, list) and filter_model.filter_value1:
                                # Get unique values from new dataframe column
                                new_unique_values = new_df[filter_col].dropna().unique()
                                new_unique_values_set = set(str(v) for v in new_unique_values)
                                
                                # Check if all selected values exist in new dataframe
                                missing_values = []
                                for val in filter_model.filter_value1:
                                    if str(val) not in new_unique_values_set:
                                        missing_values.append(val)
                                
                                if missing_values:
                                    # Make more robust (see other place where checking on the emojis present in these strings)
                                    # (can search for the emoji characters to find it)
                                    impacts.append(f"🔶 Filter '{filter_model.filter_name}' has selected values {', '.join(str(v) for v in missing_values)} that don't exist in new datafile")
                                    if len(missing_values) == len(filter_model.filter_value1):
                                        impacts.append(f"🔴 Filter '{filter_model.filter_name}' has no valid selected values in new datafile - will be reset")
                                        has_critical = True
        
        return impacts, has_critical

    def on_datafile_changed(self, new_datafile):
        """
        Handle datafile changes, including updating column options and model values.
        
        This completely replaces the previous implementation with a robust approach
        that properly updates everything dependent on the datafile selection.
        
        Args:
            new_datafile: DataFileMetadata object or string representation of the new datafile
        """
        # Skip empty strings
        if isinstance(new_datafile, str) and not new_datafile.strip():
            return
        
        # Convert string to DataFileMetadata if needed
        if isinstance(new_datafile, str):
            # First try getting it by display string
            metadata = self.data_library.get_metadata_by_display_string(new_datafile)
            
            if metadata is None:
                # If not found, try by file path
                metadata = self.data_library.get_metadata_by_path(new_datafile)
                
                if metadata is None:
                    print(f"Warning: No metadata found for '{new_datafile}', creating new")
                    try:
                        metadata = DataFileMetadata.from_display_string(new_datafile)
                    except Exception as e:
                        print(f"Error parsing display string: {e}")
                        # Just use the string as file path with default values
                        metadata = DataFileMetadata(file_path=new_datafile)
        elif isinstance(new_datafile, DataFileMetadata):
            metadata = new_datafile
        else:
            print(f"Unexpected datafile type: {type(new_datafile)}")
            return
        
        # Check if anything is actually changing
        if self.model.datafile == metadata:
            return
        
        # Get the dataframes for validation
        old_df = None
        if self.model.datafile and self.model.datafile.file_path:
            old_df = self.data_library.dataframe_manager.get_dataframe_by_metadata(self.model.datafile)
        
        new_df = self.data_library.dataframe_manager.get_dataframe_by_metadata(metadata)
        if new_df is None:
            print(f"Warning: Could not get dataframe for {str(metadata)}")
            return
        
        # Start collecting changes we'll make to the model
        changes = {}
        
        # Get column information from the new dataframe
        all_columns = list(new_df.columns)
        numeric_columns = get_numeric_columns_from_dataframe(new_df)
        
        # Update the model's datafile
        changes["datafile"] = metadata
        
        # Check and update heatmap column if needed
        if hasattr(self.model, "heatmap_on") and self.model.heatmap_on:
            current_heatmap_col = self.model.heatmap_column
            if current_heatmap_col not in numeric_columns:
                # Current column not available or not numeric, reset to first available or empty
                if numeric_columns:
                    changes["heatmap_column"] = numeric_columns[0]
                else:
                    changes["heatmap_column"] = ""
        
        # Check and update sizemap column if needed
        if hasattr(self.model, "sizemap_on") and self.model.sizemap_on:
            current_sizemap_col = self.model.sizemap_column
            if current_sizemap_col not in numeric_columns:
                # Current column not available or not numeric, reset to first available or empty
                if numeric_columns:
                    changes["sizemap_column"] = numeric_columns[0]
                else:
                    changes["sizemap_column"] = ""
        
        # Check and update filters if needed
        if hasattr(self.model, "filters_on") and self.model.filters_on and hasattr(self.model, "filters"):
            for i, filter_model in enumerate(self.model.filters):
                filter_col = filter_model.filter_column
                
                # Check if filter column exists in new dataframe
                if filter_col not in all_columns:
                    # Column doesn't exist, reset to first available
                    if all_columns:
                        filter_model.filter_column = all_columns[0]
                    else:
                        filter_model.filter_column = ""
                    
                    # Reset operation if needed
                    old_operation = filter_model.filter_operation
                    valid_ops = ["is", "is not", "is one of", "is not one of"]
                    if old_operation not in valid_ops:
                        filter_model.filter_operation = "is"
                    
                    # Reset values
                    filter_model.filter_value1 = ""
                    filter_model.filter_value2 = ""
                else:
                    # Column exists, check if operation is compatible with column type
                    is_numeric = filter_col in numeric_columns
                    
                    if not is_numeric:
                        # For non-numeric columns, only certain operations are valid
                        valid_ops = ["is", "is not", "is one of", "is not one of"]
                        if filter_model.filter_operation not in valid_ops:
                            filter_model.filter_operation = "is"
                    
                    # For "is one of" or "is not one of" operations, check if values exist
                    if filter_model.filter_operation in ["is one of", "is not one of"]:
                        if isinstance(filter_model.filter_value1, list) and filter_model.filter_value1:
                            # Get unique values from new dataframe column
                            new_unique_values = new_df[filter_col].dropna().unique()
                            new_unique_values_set = set(str(v) for v in new_unique_values)
                            
                            # Filter out values that don't exist
                            valid_values = [val for val in filter_model.filter_value1 
                                        if str(val) in new_unique_values_set]
                            
                            # Update if any values were removed
                            if len(valid_values) < len(filter_model.filter_value1):
                                filter_model.filter_value1 = valid_values
        
        # Now apply all the changes to the model
        for attr, value in changes.items():
            setattr(self.model, attr, value)
        
        # Update the view to reflect the changes
        self.view.update_from_model()
        
        # Update view widgets with new column options
        heatmap_combo = self.view.widgets.get("heatmap_column")
        if heatmap_combo:
            heatmap_combo.blockSignals(True)
            heatmap_combo.clear()
            heatmap_combo.addItems(numeric_columns)
            
            # Set to current model value
            current_value = self.model.heatmap_column
            if current_value in numeric_columns:
                heatmap_combo.setCurrentText(current_value)
            elif numeric_columns:
                heatmap_combo.setCurrentText(numeric_columns[0])
            heatmap_combo.blockSignals(False)

        sizemap_combo = self.view.widgets.get("sizemap_column")
        if sizemap_combo:
            sizemap_combo.blockSignals(True)
            sizemap_combo.clear()
            sizemap_combo.addItems(numeric_columns)
            
            # Set to current model value
            current_value = self.model.sizemap_column
            if current_value in numeric_columns:
                sizemap_combo.setCurrentText(current_value)
            elif numeric_columns:
                sizemap_combo.setCurrentText(numeric_columns[0])
            sizemap_combo.blockSignals(False)
        
        # Update filter column options
        self.view.update_filter_columns(all_columns)
        
        # Reconnect any signals that need to be reconnected
        self.connect_heatmap_column_change()
        
        # Update min/max values for heatmap if applicable
        if hasattr(self.model, "heatmap_on") and self.model.heatmap_on:
            # If heatmap column was changed, make sure to update min/max
            if "heatmap_column" in changes:
                print(f"Datafile change triggered heatmap column update to {changes['heatmap_column']}")
                self._update_heatmap_min_max_for_column(changes['heatmap_column'])
            else:
                print(f"Updating heatmap min/max for existing column: {self.model.heatmap_column}")
                self._update_heatmap_min_max_for_column(self.model.heatmap_column)

    def update_filter_columns_for_datafile(self, all_cols):
        """Update all filter columns based on the current datafile.
        
        Args:
            all_cols: List of all column names from the current datafile
        """
        if not hasattr(self.model, "filters") or not self.model.filters:
            return
        
        # Find the currently visible filter editor
        current_filter_editor = None
        if hasattr(self.view, "filterTabWidget"):
            current_index = self.view.filterTabWidget.currentRow()
            
            # Find all filter editors in the view
            for child in self.view.findChildren(FilterEditorView):
                if hasattr(child, "filter_model"):
                    # Check if this editor matches the current filter
                    if current_index >= 0 and current_index < len(self.model.filters):
                        if child.filter_model is self.model.filters[current_index]:
                            current_filter_editor = child
                            break
        
        # Update column options for all filters in the model
        for filter_index, filter_model in enumerate(self.model.filters):
            current_column = filter_model.filter_column
            
            # 1. Update the model value if current column doesn't exist in new datafile
            column_exists = current_column in all_cols
            if current_column and not column_exists and all_cols:
                # Update the model with the first available column
                filter_model.filter_column = all_cols[0]
                print(f"Updated filter column from '{current_column}' to '{all_cols[0]}'")
            
            # 2. If this is the current filter being displayed, update the UI
            if current_filter_editor and current_filter_editor.filter_model is filter_model:
                filter_combo = current_filter_editor.widgets.get("filter_column")
                if filter_combo:
                    filter_combo.blockSignals(True)
                    filter_combo.clear()
                    filter_combo.addItems(all_cols)
                    
                    # Set to valid column value
                    if column_exists:
                        filter_combo.setCurrentText(current_column)
                    elif all_cols:
                        filter_combo.setCurrentText(all_cols[0])
                    filter_combo.blockSignals(False)
                    
                    # Trigger an update of the value widgets based on new column type
                    current_filter_editor.update_filter_value_widgets()

