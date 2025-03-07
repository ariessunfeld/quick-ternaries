import re
import io
import os
import sys
import copy
import uuid
import json
from typing import (
    Optional,
    List,
    Union,
    Dict
)
from dataclasses import (
    dataclass, 
    field, 
    fields,
    asdict,
    is_dataclass
)

import pandas as pd
import numpy as np

# Import plotly components (add these to your imports)
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import get_colorscale

from dataclasses import dataclass, field, fields
from PySide6.QtWidgets import (QLineEdit, QDoubleSpinBox, QComboBox, QListWidget, QListWidgetItem,
                             QWidget, QFormLayout, QHBoxLayout, QPushButton, QListWidget,
                             QVBoxLayout, QMessageBox, QInputDialog, QCompleter)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, Signal, QTimer

from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QMessageBox,
    QVBoxLayout, 
    QHBoxLayout, 
    QListWidget, 
    QListWidgetItem,
    QGroupBox,
    QStackedWidget, 
    QLabel, 
    QAbstractItemView, 
    QSplitter,
    QPushButton, 
    QLineEdit, 
    QComboBox, 
    QFormLayout,
    QDoubleSpinBox, 
    QCheckBox, 
    QFileDialog, 
    QInputDialog,
    QSpacerItem
)
from PySide6.QtCore import Qt, QRect, QEvent, QPoint
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QSplitterHandle, QSplitter
from PySide6.QtWidgets import QScrollArea
from PySide6.QtGui import QIcon, QPixmap, QPainter, QCursor, QColor
from PySide6.QtWidgets import QPushButton, QColorDialog, QHBoxLayout, QWidget, QLabel
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt, Signal
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, QMenu
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox



# If available, use QWebEngineView; otherwise fall back.

from PySide6.QtWebEngineWidgets import QWebEngineView

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

from src.services.utils.contour_utils import (
    transform_to_cartesian, 
    compute_kde_contours, 
    convert_contour_to_ternary
)

# --------------------------------------------------------------------
# Constants / Pinned Item Labels
# --------------------------------------------------------------------
SETUP_MENU_LABEL = "Setup Menu"
ADD_TRACE_LABEL = "Add Trace (+)"


def recursive_to_dict(obj):
    """Recursively convert dataclass objects (or lists/dicts) to dictionaries."""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, list):
        return [recursive_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: recursive_to_dict(v) for k, v in obj.items()}
    else:
        return obj

def find_header_row_excel(file, max_rows_scan, sheet_name):
    """Returns the 'best' header row for an Excel file."""
    min_score = float('inf')
    best_header_row = None

    try:
        # Read the full sheet to know how many rows there are
        df = pd.read_excel(file, sheet_name=sheet_name)
    except FileNotFoundError as err:
        print(err)
        return None

    n_rows_search = min(len(df), max_rows_scan)

    for i in range(n_rows_search):
        try:
            # Read candidate header with nrows to compute a score
            df_candidate = pd.read_excel(file, sheet_name=sheet_name, header=i, nrows=n_rows_search+1)
        except Exception as e:
            print(f"Error reading excel file with header {i}: {e}")
            continue

        columns = df_candidate.columns.tolist()
        num_unnamed = sum('unnamed' in str(name).lower() for name in columns)
        num_unique = len(set(columns))
        # For each column, check if all values in the column (in the preview) are of the same type.
        type_consistency = sum(df_candidate[col].apply(type).nunique() == 1 for col in df_candidate.columns)

        total_score = num_unnamed - num_unique - type_consistency

        if total_score < min_score:
            min_score = total_score
            best_header_row = i

    return best_header_row

def find_header_row_csv(file, max_rows_scan):
    """Returns the 'best' header row for a CSV file."""
    min_score = float('inf')
    best_header_row = None

    try:
        df = pd.read_csv(file)
    except FileNotFoundError as err:
        print(err)
        return None

    n_rows_search = min(len(df) - 1, max_rows_scan)

    for i in range(n_rows_search):
        try:
            df_candidate = pd.read_csv(file, header=i, nrows=n_rows_search+1)
        except Exception as e:
            print(f"Error reading CSV file with header {i}: {e}")
            continue

        columns = df_candidate.columns.tolist()
        num_unnamed = sum('unnamed' in str(name).lower() for name in columns)
        num_unique = len(set(columns))
        type_consistency = sum(df_candidate[col].apply(type).nunique() == 1 for col in df_candidate.columns)

        total_score = num_unnamed - num_unique - type_consistency

        if total_score < min_score:
            min_score = total_score
            best_header_row = i

    return best_header_row

def get_sheet_names(file_path):
    """
    Returns a list of sheet names for an Excel file.
    If the file is not an Excel file, returns an empty list.
    """
    try:
        if file_path.lower().endswith(('.xls', '.xlsx')):
            xls = pd.ExcelFile(file_path)
            return xls.sheet_names
        else:
            return []
    except Exception as e:
        print(f"Error in get_sheet_names: {str(e)}")
        return []

def get_suggested_header(file_path, sheet=None, max_rows_scan=24):
    """
    Returns the suggested header row index for the file.
    
    For CSV files, calls find_header_row_csv.
    For Excel files, calls find_header_row_excel using the specified sheet (or the first sheet if none is provided).
    """
    if file_path.lower().endswith('.csv'):
        return find_header_row_csv(file_path, max_rows_scan)
    elif file_path.lower().endswith(('.xls', '.xlsx')):
        if sheet is None:
            sheets = get_sheet_names(file_path)
            if sheets:
                sheet = sheets[0]
            else:
                return None
        return find_header_row_excel(file_path, max_rows_scan, sheet)
    else:
        return None  
    

def get_columns_from_dataframe(df):
    """
    Returns a set of column names from a dataframe.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        set: Column names
    """
    if df is None:
        return set()
    return set(df.columns)

def get_numeric_columns_from_dataframe(df):
    """
    Returns a list of numeric column names from a dataframe.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        list: Numeric column names
    """
    if df is None:
        return []
    return df.select_dtypes(include=['number']).columns.tolist()

def get_all_columns_from_dataframe(df):
    """
    Returns all column names from a dataframe as a list.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        list: Column names
    """
    if df is None:
        return []
    return df.columns.tolist()

def get_sorted_unique_values_from_dataframe(df, column=None):
    """
    Returns a sorted list of unique (non-null) values from the specified column.
    
    Args:
        df: pandas DataFrame
        column: Column name to get unique values from
        
    Returns:
        list: Sorted unique values
    """
    if df is None or column is None or column not in df.columns:
        return []
    
    # Drop missing values and get unique values
    unique_values = df[column].dropna().unique().tolist()
    
    # Try numeric sort if possible
    try:
        if unique_values:
            # Attempt to convert first value to float as a proxy
            float(unique_values[0])
            unique_values.sort(key=lambda x: float(x))
        else:
            unique_values.sort()
    except Exception:
        # Otherwise, sort as strings
        unique_values.sort(key=lambda x: str(x))
    
    return unique_values

def is_numeric_column_in_dataframe(df, column=None):
    """
    Determines whether the specified column in the dataframe is numeric.
    
    Args:
        df: pandas DataFrame
        column: Column name to check
        
    Returns:
        bool: True if the column is numeric, False otherwise
    """
    if df is None or column is None:
        return False
    
    numeric_columns = get_numeric_columns_from_dataframe(df)
    return column in numeric_columns

def get_preview_data_from_dataframe(df, n_rows=24):
    """
    Returns a list of lists containing the first n_rows of the dataframe.
    
    Args:
        df: pandas DataFrame
        n_rows: Number of rows to return
        
    Returns:
        list: Preview data as a list of lists
    """
    if df is None:
        return []
    
    # Limit to first n_rows
    preview_df = df.head(n_rows)
    return preview_df.values.tolist()

# Create wrapper functions that work with either DataFileMetadata (preferred) or raw file paths
def get_columns_from_file(data_source, header=None, sheet=None, dataframe_manager=None):
    """
    Returns a set of column names from the file or metadata.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_columns_from_dataframe(df)
    
    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith('.csv'):
            if header is not None:
                df = pd.read_csv(file_path, header=header, nrows=0)
            else:
                df = pd.read_csv(file_path, nrows=0)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            if header is not None:
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, nrows=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=0)
        else:
            return set()
        return set(df.columns)
    return set()

def get_numeric_columns_from_file(data_source, header=None, sheet=None, dataframe_manager=None):
    """
    Returns a list of numeric column names.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_numeric_columns_from_dataframe(df)
    
    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith('.csv'):
            if header is not None:
                df = pd.read_csv(file_path, header=header, nrows=10)
            else:
                df = pd.read_csv(file_path, nrows=10)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            if header is not None:
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, nrows=10)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
        else:
            return []
        return df.select_dtypes(include=['number']).columns.tolist()
    return []

def get_all_columns_from_file(data_source, header=None, sheet=None, dataframe_manager=None):
    """
    Returns all column names as a list.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_all_columns_from_dataframe(df)
    
    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith('.csv'):
            if header is not None:
                df = pd.read_csv(file_path, header=header, nrows=0)
            else:
                df = pd.read_csv(file_path, nrows=0)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            if header is not None:
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, nrows=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=0)
        else:
            return []
        return df.columns.tolist()
    return []

def get_sorted_unique_values(data_source, header=None, sheet=None, column=None, dataframe_manager=None):
    """
    Returns a sorted list of unique values from the specified column.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_sorted_unique_values_from_dataframe(df, column)
    
    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str) and column:
        file_path = data_source
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, header=header, usecols=[column])
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, usecols=[column])
            else:
                return []
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
        
        # Drop missing values and get unique values
        unique_values = df[column].dropna().unique().tolist()
        
        # Try numeric sort if possible
        try:
            if unique_values:
                # Attempt to convert first value to float as a proxy
                float(unique_values[0])
                unique_values.sort(key=lambda x: float(x))
            else:
                unique_values.sort()
        except Exception:
            # Otherwise, sort as strings
            unique_values.sort(key=lambda x: str(x))
        
        return unique_values
    return []

def is_numeric_column(data_source, header=None, sheet=None, column=None, dataframe_manager=None):
    """
    Determines whether the specified column is numeric.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return is_numeric_column_in_dataframe(df, column)
    
    # Fall back to original implementation
    if not column:
        return False
    # get_numeric_columns_from_file is assumed to be available per your utility functions.
    numeric_columns = get_numeric_columns_from_file(data_source, header, sheet)
    return column in numeric_columns

def get_preview_data(data_source, sheet=None, n_rows=24, dataframe_manager=None):
    """
    Returns a list of lists containing the first n_rows of the file.
    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, 'file_path') and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_preview_data_from_dataframe(df, n_rows)
    
    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith('.csv'):
            # Use header=None so all rows are treated as data
            df = pd.read_csv(file_path, header=None, nrows=n_rows)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, header=None, sheet_name=sheet, nrows=n_rows)
        else:
            return []
        return df.values.tolist()
    return []

@dataclass
class DataFileMetadata:
    file_path: str
    header_row: Optional[int] = None
    sheet: Optional[str] = None
    # This will store an identifier to retrieve the dataframe from DataframeManager
    df_id: Optional[str] = None

    def to_dict(self):
        # Exclude df_id from serialization
        result = {
            "file_path": self.file_path,
            "header_row": self.header_row,
            "sheet": self.sheet
        }
        return result

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
    

class DataframeManager:
    """
    Manages loading and caching of dataframes to avoid repetitive disk reads.
    """
    def __init__(self):
        self._dataframes: Dict[str, pd.DataFrame] = {}
        
    def load_dataframe(self, metadata: DataFileMetadata) -> str:
        """
        Loads a dataframe based on metadata and returns an identifier.
        
        Args:
            metadata: DataFileMetadata containing file path, header row, and sheet name
            
        Returns:
            str: The identifier for the loaded dataframe
        """
        df_id = f"{metadata.file_path}:{metadata.sheet}:{metadata.header_row}"
        
        try:
            if metadata.file_path.lower().endswith('.csv'):
                df = pd.read_csv(metadata.file_path, header=metadata.header_row)
            elif metadata.file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(metadata.file_path, header=metadata.header_row, sheet_name=metadata.sheet)
            else:
                raise ValueError(f"Unsupported file format: {metadata.file_path}")
                
            self._dataframes[df_id] = df
            return df_id
            
        except Exception as e:
            print(f"Error loading dataframe: {e}")
            return None
            
    def get_dataframe(self, df_id: str) -> Optional[pd.DataFrame]:
        """
        Retrieves a dataframe by its identifier.
        
        Args:
            df_id: The dataframe identifier
            
        Returns:
            Optional[pd.DataFrame]: The requested dataframe or None if not found
        """
        return self._dataframes.get(df_id)
        
    def get_dataframe_by_metadata(self, metadata: DataFileMetadata) -> Optional[pd.DataFrame]:
        """
        Gets a dataframe for the given metadata. If not already loaded, loads it.
        
        Args:
            metadata: DataFileMetadata containing file path, header row, and sheet name
            
        Returns:
            Optional[pd.DataFrame]: The requested dataframe or None if loading failed
        """
        # Check if metadata has a df_id and if it's valid
        if metadata.df_id and metadata.df_id in self._dataframes:
            return self._dataframes[metadata.df_id]
            
        # Load the dataframe if needed
        df_id = self.load_dataframe(metadata)
        if df_id:
            # Update the metadata with the df_id
            metadata.df_id = df_id
            return self._dataframes[df_id]
        return None
        
    def remove_dataframe(self, df_id: str) -> bool:
        """
        Removes a dataframe from the cache.
        
        Args:
            df_id: The dataframe identifier
            
        Returns:
            bool: True if successful, False otherwise
        """
        if df_id in self._dataframes:
            del self._dataframes[df_id]
            return True
        return False
        
    def clear_cache(self):
        """Clears all cached dataframes."""
        self._dataframes.clear()
        
    def reload_dataframe(self, metadata: DataFileMetadata) -> bool:
        """
        Forces a reload of the dataframe from disk.
        
        Args:
            metadata: DataFileMetadata containing file path, header row, and sheet name
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Remove existing dataframe if there's a df_id
        if metadata.df_id:
            self.remove_dataframe(metadata.df_id)
            
        # Load fresh dataframe
        df_id = self.load_dataframe(metadata)
        if df_id:
            metadata.df_id = df_id
            return True
        return False

@dataclass
class DataLibraryModel:
    loaded_files: List[DataFileMetadata] = field(default_factory=list)
    # The dataframe_manager is a transient property (not serialized)
    # This special field metadata ensures it's excluded from serialization
    _dataframe_manager: Optional[DataframeManager] = field(default=None, repr=False, compare=False, hash=False, metadata={"exclude_from_dict": True})
    
    def __post_init__(self):
        # Initialize the dataframe manager if needed
        if self._dataframe_manager is None:
            self._dataframe_manager = DataframeManager()
    
    @property
    def dataframe_manager(self):
        # Ensure dataframe_manager is always available
        if self._dataframe_manager is None:
            self._dataframe_manager = DataframeManager()
        return self._dataframe_manager
    
    def to_dict(self):
        """
        Custom to_dict method that explicitly excludes the dataframe_manager
        """
        return {"loaded_files": [file.to_dict() for file in self.loaded_files]}
    
    @classmethod
    def from_dict(cls, d: dict):
        # Create a new instance with loaded files from dict
        files = [DataFileMetadata.from_dict(fd) for fd in d.get("loaded_files", [])]
        return cls(loaded_files=files)
    
    def add_file(self, metadata: DataFileMetadata) -> bool:
        """
        Add a new file to the data library and load its dataframe.
        
        Args:
            metadata: DataFileMetadata object with file path, header, and sheet
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Load the dataframe
        df_id = self.dataframe_manager.load_dataframe(metadata)
        if df_id:
            # Set the df_id on the metadata
            metadata.df_id = df_id
            # Add to loaded files
            self.loaded_files.append(metadata)
            return True
        return False
    
    def remove_file(self, file_path: str) -> bool:
        """
        Remove a file from the data library and its dataframe from the cache.
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        for i, metadata in enumerate(self.loaded_files):
            if metadata.file_path == file_path:
                # Remove the dataframe from the cache if it has a df_id
                if metadata.df_id:
                    self.dataframe_manager.remove_dataframe(metadata.df_id)
                # Remove the metadata from loaded_files
                self.loaded_files.pop(i)
                return True
        return False
    
    def get_dataframe(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Get the dataframe for a file by its path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[pd.DataFrame]: The dataframe or None if not found
        """
        for metadata in self.loaded_files:
            if metadata.file_path == file_path:
                return self.dataframe_manager.get_dataframe_by_metadata(metadata)
        return None
    
    def reload_all_dataframes(self) -> bool:
        """
        Reload all dataframes from disk.
        Useful after loading a workspace.
        
        Returns:
            bool: True if all reloads were successful, False otherwise
        """
        success = True
        for metadata in self.loaded_files:
            # Skip if file doesn't exist - handle this separately
            if not os.path.exists(metadata.file_path):
                success = False
                continue
                
            result = self.dataframe_manager.reload_dataframe(metadata)
            if not result:
                success = False
        return success
    
    def reload_dataframe(self, file_path: str) -> bool:
        """
        Reload a specific dataframe from disk.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        for metadata in self.loaded_files:
            if metadata.file_path == file_path:
                return self.dataframe_manager.reload_dataframe(metadata)
        return False
    
    def get_metadata_by_path(self, file_path: str) -> Optional[DataFileMetadata]:
        """
        Get metadata for a file by its path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[DataFileMetadata]: The metadata or None if not found
        """
        for metadata in self.loaded_files:
            if metadata.file_path == file_path:
                return metadata
        return None
    
    def clear(self):
        """Clear all loaded files and dataframes."""
        self.loaded_files.clear()
        self.dataframe_manager.clear_cache()
    
    def update_file_paths(self, path_mapping: dict) -> bool:
        """
        Update file paths in the data library based on a mapping.
        Useful after loading a workspace when files have moved.
        
        Args:
            path_mapping: Dict mapping old paths to new paths
            
        Returns:
            bool: True if all updates were successful, False otherwise
        """
        success = True
        for metadata in self.loaded_files:
            if metadata.file_path in path_mapping:
                old_path = metadata.file_path
                new_path = path_mapping[old_path]
                metadata.file_path = new_path
                # Clear any existing df_id
                metadata.df_id = None
                # Try to load the dataframe with the new path
                if not self.dataframe_manager.load_dataframe(metadata):
                    success = False
        return success
    
class HeaderSelectionDialog(QDialog):
    def __init__(self, file_path, sheet=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.sheet = sheet
        self.setWindowTitle("Select Header Row")
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Please select the header row:"))
        
        self.combo = QComboBox(self)
        
        # Get preview data using the updated helper; this shows up to 24 rows and 8 columns per row
        preview_data = get_preview_data(file_path, sheet, 24)  # Assumes get_preview_data is implemented
        n_rows = len(preview_data)
        
        for i in range(n_rows):
            row_data = preview_data[i]
            displayed_columns = row_data[:8]  # Limit to first 8 columns
            option_text = f"Row {i}: " + ", ".join(map(str, displayed_columns))
            self.combo.addItem(option_text, userData=i)
        
        # Use the new get_suggested_header with the sheet parameter
        suggested = get_suggested_header(file_path, sheet)
        if suggested is not None and suggested < n_rows:
            self.combo.setCurrentIndex(suggested)
        
        layout.addWidget(self.combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    @staticmethod
    def getHeader(parent, file_path, sheet=None):
        dialog = HeaderSelectionDialog(file_path, sheet, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.combo.currentData(), True
        return None, False
          
class SheetSelectionDialog(QDialog):
    def __init__(self, file_path, sheets, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle("Select Sheet")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Please select the sheet:"))
        
        self.combo = QComboBox(self)
        for sheet in sheets:
            self.combo.addItem(sheet)
        layout.addWidget(self.combo)
        
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    @staticmethod
    def getSheet(parent, file_path, sheets):
        dialog = SheetSelectionDialog(file_path, sheets, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.combo.currentText(), True
        return None, False
    
def validate_data_library(data_library: DataLibraryModel, parent: QWidget):
    """
    Iterates over each DataFileMetadata in the library. If the file does not exist,
    prompts the user to locate the file. Updates the metadata in place.
    
    Returns:
        dict: A mapping from old file paths to new file paths for any files that were updated.
    """
    file_path_mapping = {}  # Map from old paths to new paths
    
    for idx, meta in enumerate(data_library.loaded_files):
        if not os.path.exists(meta.file_path):
            msg = f"File not found: {meta.file_path}\nPlease locate the missing file."
            QMessageBox.warning(parent, "Missing Data File", msg)
            new_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Locate Missing Data File",
                "",
                "Data Files (*.csv *.xlsx)"
            )
            if new_path:
                # Create a new metadata object preserving the header and sheet settings.
                old_path = meta.file_path
                new_meta = DataFileMetadata(
                    file_path=new_path,
                    header_row=meta.header_row,
                    sheet=meta.sheet
                )
                data_library.loaded_files[idx] = new_meta
                file_path_mapping[old_path] = new_path
            else:
                # Optionally, you might want to remove the missing file from the library.
                # For now, we leave it unchanged.
                pass
    
    return file_path_mapping
       

class ColorScaleDropdown(QWidget):
    """
    Alternative implementation using a combobox dropdown for color scale selection
    """
    colorScaleChanged = Signal(str)  # Signal emitted when color scale changes
    
    # List of standard Plotly color scales
    PLOTLY_COLOR_SCALES = [
        "Plotly3", "Viridis", "Cividis", "Inferno", "Magma", "Plasma", 'Turbo',
        'Blackbody', 'Bluered', 'Electric', 'Hot', 'Jet', 'Rainbow', 'Blues',
        'BuGn', 'BuPu', 'GnBu', 'Greens', 'Greys', 'OrRd', 'Oranges', 'PuBu',
        'PuBuGn', 'PuRd', 'Purples', 'RdBu', 'RdPu', 'Reds', 'YlGn', 'YlGnBu',
        'YlOrBr', 'YlOrRd', 'turbid', 'thermal', 'haline', 'solar', 'ice',
        'gray', 'deep', 'dense', 'algae', 'matter', 'speed', 'amp', 'tempo',
        'Burg', 'Burgyl', 'Redor', 'Oryel', 'Peach', 'Pinkyl', 'Mint', 'Blugrn',
        'Darkmint', 'Emrld', 'Aggrnyl', 'Bluyl', 'Teal', 'Tealgrn', 'Purp',
        'Purpor', 'Sunset', 'Magenta', 'Sunsetdark', 'Agsunset', 'Brwnyl'
    ]
    
    def __init__(self, colorscale="Viridis", parent=None):
        super().__init__(parent)
        
        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the combobox for selection
        self.comboBox = QComboBox()
        self.comboBox.setIconSize(QPixmap(60, 15).size())
        
        # Add colorscales to combobox
        for cs_name in self.PLOTLY_COLOR_SCALES:
            icon = self.create_colorscale_icon(cs_name)
            self.comboBox.addItem(icon, cs_name)
        
        # Add widgets to layout
        layout.addWidget(self.comboBox)
        
        # Set the initial color scale
        self.setColorScale(colorscale)
        
        # Connect signals
        self.comboBox.currentTextChanged.connect(self.onColorScaleSelected)
    
    def setColorScale(self, colorscale_name):
        """Set the color scale from its name"""
        try:
            # Find the index of the color scale in the combobox
            index = self.PLOTLY_COLOR_SCALES.index(colorscale_name)
            self.comboBox.setCurrentIndex(index)
            
            # Update the preview
            pixmap = self.create_colorscale_icon(colorscale_name).pixmap(80, 20)
            # self.preview.setPixmap(pixmap)
            
            # Store the current color scale
            self.current_colorscale = colorscale_name
        except (ValueError, IndexError) as e:
            # Default to first color scale if there's an issue
            print(f"Error setting color scale: {e}")
            if len(self.PLOTLY_COLOR_SCALES) > 0:
                self.setColorScale(self.PLOTLY_COLOR_SCALES[0])
            else:
                self.current_colorscale = "Viridis"
    
    def onColorScaleSelected(self, colorscale_name):
        """Handle selection of a color scale from the combobox"""
        self.setColorScale(colorscale_name)
        self.colorScaleChanged.emit(colorscale_name)
    
    def getColorScale(self):
        """Return the current color scale name"""
        return self.current_colorscale
    
    def create_colorscale_icon(self, colorscale_name, width=150, height=20):
        """Create a QIcon for a Plotly color scale"""
        try:
            # Try to get the colorscale
            colorscale = None
            try:
                colorscale = get_colorscale(colorscale_name)
            except:
                print(f'Failed to get colorscale for scale name {colorscale_name}')
                # If get_colorscale fails, create a simple gradient
                colorscale = [(0, "lightblue"), (0.5, "blue"), (1, "darkblue")]
            
            # Create a subplot with a single cell
            fig = make_subplots(rows=1, cols=1)

            # Create a heatmap trace
            heatmap_data = np.array([list(range(width))])
            fig.add_trace(go.Heatmap(z=heatmap_data, colorscale=colorscale, showscale=False))

            # Update the layout
            fig.update_layout(
                width=width, height=height,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False
            )

            # Convert to image
            img_bytes = fig.to_image(format="png")

            # Create QIcon
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            return QIcon(pixmap)
        except Exception as e:
            # Return an empty icon if there's an error
            print(f"Error generating color scale icon: {e}")
            return QIcon()

class ShapeButtonWithMenu(QWidget):
    """
    Alternative implementation that uses a button + popup menu instead of a combobox.
    This matches the style of the ColorButton more closely.
    """
    shapeChanged = Signal(str)  # Signal emitted when shape changes
    
    # List of standard Plotly marker shapes
    PLOTLY_SHAPES = [
        "circle", "square", "diamond", "cross", "x", "triangle-up", "triangle-down", 
        "triangle-left", "triangle-right", "pentagon", "hexagon", "star", "hexagram",
        "star-triangle-up", "star-triangle-down", "star-square", "star-diamond",
        "diamond-tall", "diamond-wide", "hourglass", "bowtie"
    ]
    
    def __init__(self, shape="circle", parent=None):
        super().__init__(parent)
        
        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the shape preview widget
        self.shapePreview = QLabel()
        self.shapePreview.setMinimumSize(24, 24)
        self.shapePreview.setMaximumSize(24, 24)
        self.shapePreview.setAlignment(Qt.AlignCenter)
        
        # Create the button to open the menu
        self.button = QPushButton("Select Shape")
        
        # Add widgets to layout
        layout.addWidget(self.shapePreview)
        layout.addWidget(self.button)
        
        # Create the menu but don't show it yet
        self.createMenu()
        
        # Set the initial shape
        self.setShape(shape)
        
        # Connect button click to show menu
        self.button.clicked.connect(self.showMenu)
    
    def createMenu(self):
        """Create the popup menu with all shape options"""
        self.menu = QMenu(self)
        
        # Create an action for each shape with an icon
        for shape_name in self.PLOTLY_SHAPES:
            icon = self.create_plotly_marker_icon(shape_name)
            action = QAction(icon, shape_name, self)
            action.triggered.connect(lambda checked=False, s=shape_name: self.onShapeSelected(s))
            self.menu.addAction(action)
    
    def showMenu(self):
        """Show the popup menu when the button is clicked"""
        # Position the menu below the button
        pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
        self.menu.popup(pos)
    
    def setShape(self, shape_name):
        """Set the shape from its name"""
        try:
            # Validate the shape name is in our list
            if shape_name not in self.PLOTLY_SHAPES:
                shape_name = "circle"  # Default to circle if invalid
                
            # Update the preview
            icon = self.create_plotly_marker_icon(shape_name)
            self.shapePreview.setPixmap(icon.pixmap(24, 24))
            
            # Store the current shape
            self.current_shape = shape_name
        except Exception as e:
            print(f"Error setting shape: {e}")
            # Default to circle if there's an issue
            self.current_shape = "circle"
            icon = self.create_plotly_marker_icon("circle")
            if not icon.isNull():
                self.shapePreview.setPixmap(icon.pixmap(24, 24))
    
    def onShapeSelected(self, shape_name):
        """Handle selection of a shape from the menu"""
        self.setShape(shape_name)
        self.shapeChanged.emit(shape_name)
    
    def getShape(self):
        """Return the current shape name"""
        return self.current_shape
    
    def create_plotly_marker_icon(self, shape, size=32):
        """Create a QIcon for a Plotly marker shape"""
        try:
            # Create a subplot with a single cell
            fig = make_subplots(rows=1, cols=1)

            # Add a scatter trace with the desired marker
            fig.add_trace(go.Scatter(
                x=[0], y=[0],
                mode='markers',
                marker=dict(symbol=shape, size=size*0.8, color='black')
            ))

            # Update the layout to remove axes and set a fixed range
            fig.update_layout(
                width=size, height=size,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(visible=False, range=[-1, 1]),
                yaxis=dict(visible=False, range=[-1, 1]),
                showlegend=False
            )

            # Convert to image
            img_bytes = fig.to_image(format="png")

            # Create QIcon
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            return QIcon(pixmap)
        except Exception as e:
            # Return an empty icon if there's an error
            print(f"Error generating shape icon: {e}")
            return QIcon()

class ColorButton(QWidget):
    """
    Custom widget displaying the current color and providing a button to open a color picker.
    """
    colorChanged = Signal(str)  # Signal emitted when color changes (color as hex string)
    
    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)
        
        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the color preview widget
        self.colorPreview = QLabel()
        self.colorPreview.setMinimumSize(24, 24)
        self.colorPreview.setMaximumSize(24, 24)
        self.colorPreview.setAutoFillBackground(True)
        
        # Create the button
        self.button = QPushButton("Select Color")
        
        # Add widgets to layout
        layout.addWidget(self.colorPreview)
        layout.addWidget(self.button)
        
        # Set the initial color
        self.setColor(color)
        
        # Connect the button click to open the color dialog
        self.button.clicked.connect(self.openColorDialog)
    
    def setColor(self, color_str):
        """Set the color from string (hex code or color name)"""
        try:
            # Try to convert the string to a QColor
            if color_str.startswith('#'):
                # Hex code
                color = QColor(color_str)
            else:
                # Color name (e.g., 'red', 'blue')
                color = QColor(color_str)
            
            # Update the preview
            palette = self.colorPreview.palette()
            palette.setColor(QPalette.Window, color)
            self.colorPreview.setPalette(palette)
            
            # Store the current color
            self.current_color = color_str
        except:
            # Default to black if there's an issue
            palette = self.colorPreview.palette()
            palette.setColor(QPalette.Window, QColor("#000000"))
            self.colorPreview.setPalette(palette)
            self.current_color = "#000000"
    
    def openColorDialog(self):
        """Open the color picker dialog"""
        # Get the current color for the dialog
        initial_color = QColor(self.current_color)
        
        # Open Qt's color dialog
        color = QColorDialog.getColor(
            initial_color, 
            self,
            "Select Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )
        
        # If a valid color was selected (not cancelled)
        if color.isValid():
            # Get the hex code
            hex_color = color.name()
            
            # Update the button
            self.setColor(hex_color)
            
            # Emit the signal with the new color
            self.colorChanged.emit(hex_color)
    
    def getColor(self):
        """Return the current color as string"""
        return self.current_color
    
# --------------------------------------------------------------------
# Custom Splitter Classes
# --------------------------------------------------------------------
class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.orientation = orientation
        cursor = Qt.CursorShape.SplitHCursor if orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor
        self.setCursor(cursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Transparent background

        grip_color = QColor(128, 128, 128)
        painter.setBrush(grip_color)
        if self.orientation == Qt.Orientation.Horizontal:
            width = self.width()
            center_x = width // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(center_x - dot_radius, self.height() // 2 + i * spacing - dot_radius,
                                    int(dot_radius * 2), int(dot_radius * 2))
        else:
            height = self.height()
            center_y = height // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(self.width() // 2 + i * spacing - dot_radius, center_y - dot_radius,
                                    int(dot_radius * 2), int(dot_radius * 2))

    def enterEvent(self, event):
        cursor = Qt.CursorShape.SplitHCursor if self.orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor
        self.setCursor(cursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

class CustomSplitter(QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)

# --------------------------------------------------------------------
# MultiFieldSelector Widget
# --------------------------------------------------------------------
class MultiFieldSelector(QWidget):
    """
    A composite widget that lets users select one or more fields.
    Displays current selections in a list with Add/Remove buttons.
    """

    selectionChanged = Signal(list)  # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_options = []
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)
        btn_layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        self.addButton = QPushButton("Add", self)
        self.removeButton = QPushButton("Remove", self)
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.removeButton)
        btn_layout.addStretch()
        self.addButton.clicked.connect(self.add_field)
        self.removeButton.clicked.connect(self.remove_field)

    def set_available_options(self, options):
        # Store options as list of strings
        self.available_options = [str(opt) for opt in options]

    def add_field(self):
        """Show a dialog to add a field, with better handling of empty options."""
        current_selected = self.get_selected_fields()
        choices = [opt for opt in self.available_options if opt not in current_selected]
        
        if not choices:
            print("No available choices in MultiFieldSelector.add_field()")
            QMessageBox.information(self, "No Available Fields", 
                                "There are no available fields to add. This may happen if there are no common columns across loaded data files.")
            return
        
        item, ok = QInputDialog.getItem(self, "Select Field", "Available Fields:", choices, 0, False)
        if ok and item:
            self.listWidget.addItem(item)
            self.selectionChanged.emit(self.get_selected_fields())

    def remove_field(self):
        current_item = self.listWidget.currentItem()
        if current_item:
            row = self.listWidget.row(current_item)
            self.listWidget.takeItem(row)
            self.selectionChanged.emit(self.get_selected_fields())

    def get_selected_fields(self):
        """Return all currently selected fields as a list of strings"""
        return [self.listWidget.item(i).text() for i in range(self.listWidget.count())]

    def set_selected_fields(self, fields_list):
        """
        Set the selected fields in the list widget.
        Ensures all fields in fields_list are in available_options first.
        """
        # Clear current selections
        self.listWidget.clear()
        
        # Convert all fields to strings for consistency
        if not fields_list:
            return
            
        if isinstance(fields_list, str):
            print('\n\n\n\n\nLIST CASE')
            # Handle case where a string was passed instead of a list
            fields_list = [f.strip() for f in fields_list.split(",")]
        
        # Make sure all values are strings
        fields_list = [str(field) for field in fields_list]
        
        # Make sure all fields to add are in available_options
        for field in fields_list:
            if field not in self.available_options:
                self.available_options.append(field)
        
        # Now add each field to the list widget
        for field in fields_list:
            self.listWidget.addItem(field)

# --------------------------------------------------------------------
# TabListWidget and TabPanel (for managing tabs)
# --------------------------------------------------------------------
class TabListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Drop and source is self.viewport():
            self.dropEvent(event)
            return True
        return super().eventFilter(source, event)

    def dropEvent(self, event):
        selected_item = self.currentItem()
        super().dropEvent(event)
        if selected_item:
            row = self.row(selected_item)
            if row != -1:
                self.setCurrentRow(row)
                self.itemClicked.emit(selected_item)
        if self.item(0) is None or self.item(0).text() != SETUP_MENU_LABEL:
            self._remove_pinned_items(SETUP_MENU_LABEL)
            setup_item = self._create_setup_item()
            self.insertItem(0, setup_item)
        if self.item(self.count() - 1) is None or self.item(self.count() - 1).text() != ADD_TRACE_LABEL:
            self._remove_pinned_items(ADD_TRACE_LABEL)
            add_item = self._create_add_item()
            self.addItem(add_item)

    def _remove_pinned_items(self, label):
        for i in reversed(range(self.count())):
            it = self.item(i)
            if it and it.text() == label:
                self.takeItem(i)

    def _create_setup_item(self) -> QListWidgetItem:
        item = QListWidgetItem(SETUP_MENU_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _create_add_item(self) -> QListWidgetItem:
        item = QListWidgetItem(ADD_TRACE_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def startDrag(self, supportedActions):
        current_item = self.currentItem()
        if current_item and current_item.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return
        super().startDrag(supportedActions)

    def mimeData(self, items):
        if items:
            for it in items:
                if it.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                    return None
        return super().mimeData(items)

class TabPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = TabListWidget()
        self.listWidget.itemSelectionChanged.connect(self._on_item_selection_changed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.listWidget)

        self.tabSelectedCallback = None      # (unique_id) -> ...
        self.tabRenamedCallback = None       # (unique_id, new_label) -> ...
        self.tabRemovedCallback = None       # (unique_id) -> ...
        self.tabAddRequestedCallback = None  # () -> ...

        # Map unique_id -> associated model (TraceEditorModel or SetupMenuModel)
        self.id_to_widget = {}

        setup_item = self._create_setup_item()
        self.listWidget.addItem(setup_item)
        add_item = self._create_add_item()
        self.listWidget.addItem(add_item)

        # Remove icon for deletion
        self.removeIcon = QIcon()
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawLine(2, 2, 14, 14)
        painter.drawLine(14, 2, 2, 14)
        painter.end()
        self.removeIcon.addPixmap(pm)

        self.listWidget.itemClicked.connect(self._on_item_clicked)
        self.listWidget.itemChanged.connect(self._on_item_changed)

        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self.on_palette_changed)
        self.apply_dynamic_style()

    def _on_item_selection_changed(self):
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            label = item.text()
            if label not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                if uid and self.tabSelectedCallback:
                    self.tabSelectedCallback(uid)

    def _create_setup_item(self) -> QListWidgetItem:
        item = QListWidgetItem(SETUP_MENU_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _create_add_item(self) -> QListWidgetItem:
        item = QListWidgetItem(ADD_TRACE_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def apply_dynamic_style(self):
        if not QApplication.instance():
            return
        palette = QApplication.instance().palette()
        base_color = palette.base().color().name()
        text_color = palette.text().color().name()
        alt_base_color = palette.alternateBase().color().name()
        highlight_color = palette.highlight().color().name()
        highlight_text_color = palette.highlightedText().color().name()

        style = f"""
        QListWidget {{
            background-color: {base_color};
            color: {text_color};
            border: 1px solid #aaa;
            font-size: 14pt;
            margin: 0px;
        }}
        QListWidget::item {{
            background-color: {alt_base_color};
            border: 1px solid #ccc;
            margin: 4px;
            padding: 8px;
        }}
        QListWidget::item:selected {{
            background-color: {highlight_color};
            color: {highlight_text_color};
        }}
        """
        self.listWidget.setStyleSheet(style)

    def on_palette_changed(self):
        self.apply_dynamic_style()

    def add_tab(self, title: str, model) -> str:
        unique_id = str(uuid.uuid4())
        self.id_to_widget[unique_id] = model

        new_item = QListWidgetItem(title)
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        new_item.setIcon(self.removeIcon)
        new_item.setData(Qt.ItemDataRole.UserRole, unique_id)

        insert_index = self.listWidget.count() - 1
        self.listWidget.insertItem(insert_index, new_item)
        self.listWidget.setCurrentItem(new_item)
        return unique_id

    def select_tab_by_id(self, unique_id: str):
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None:
                item_id = it.data(Qt.ItemDataRole.UserRole)
                if item_id == unique_id:
                    self.listWidget.setCurrentItem(it)
                    break

    def remove_tab_by_id(self, unique_id: str):
        old_selected_item = self.listWidget.currentItem()
        old_selected_uid = None
        if old_selected_item:
            old_selected_uid = old_selected_item.data(Qt.ItemDataRole.UserRole)
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                self.listWidget.takeItem(i)
                self.id_to_widget.pop(unique_id, None)
                break
        if old_selected_uid != unique_id:
            if old_selected_item and self.listWidget.row(old_selected_item) != -1:
                self.listWidget.setCurrentItem(old_selected_item)
            else:
                if self.listWidget.count() > 0:
                    self.listWidget.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem):
        label = item.text()
        if label == SETUP_MENU_LABEL:
            if self.tabSelectedCallback:
                self.tabSelectedCallback("setup-menu-id")
            return
        if label == ADD_TRACE_LABEL:
            if self.tabAddRequestedCallback:
                self.tabAddRequestedCallback()
            return
        if self._clicked_on_remove_icon(item):
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabRemovedCallback:
                self.tabRemovedCallback(uid)
        else:
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabSelectedCallback:
                self.tabSelectedCallback(uid)

    def _on_item_changed(self, item: QListWidgetItem):
        label = item.text()
        if label in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        if uid and self.tabRenamedCallback:
            self.tabRenamedCallback(uid, label)
        self.listWidget.itemClicked.emit(item)

    def _clicked_on_remove_icon(self, item: QListWidgetItem) -> bool:
        pos = self.listWidget.viewport().mapFromGlobal(QCursor.pos())
        item_rect = self.listWidget.visualItemRect(item)
        icon_size = 16
        margin_left = 20
        icon_left = item_rect.left() + margin_left
        icon_top = item_rect.top() + (item_rect.height() - icon_size) // 2
        icon_rect = QRect(icon_left, icon_top, icon_size, icon_size)
        return icon_rect.contains(pos)

# --------------------------------------------------------------------
# Filter Model
# --------------------------------------------------------------------
@dataclass
class FilterModel:
    # Allowed operations for numeric filters.
    ALLOWED_NUMERIC_OPERATIONS = ["<", ">", "==", "a < x < b", "a <= x < b", "a < x <= b"]

    filter_name: str = field(
        default="Filter",
        metadata={"label": "Filter Name:", "widget": QLineEdit}
    )
    filter_column: str = field(
        default="",
        metadata={"label": "Filter Column:", "widget": QComboBox}
    )
    # The filter_operation field will be re-populated dynamically.
    filter_operation: str = field(
        default="",
        metadata={
            "label": "Filter Operation:",
            "widget": QComboBox,
            # Note: allowed_values here is not used directly because we repopulate it.
        }
    )
    # For numeric operations that require one or two values.
    # For non-numeric, the value widget will be replaced with a text field (or MultiFieldSelector).
    filter_value1: str = field(
        default="",
        metadata={"label": "Value A:"}
    )
    filter_value2: str = field(
        default="",
        metadata={"label": "Value B:"}
    )

    def to_dict(self):
        """Convert filter model to dictionary, properly handling multi-value cases"""
        result = asdict(self)
        # Handle special case for multi-value filters
        if self.filter_operation in ["is one of", "is not one of"]:
            # If filter_value1 is a list, convert it to a comma-separated string
            if isinstance(self.filter_value1, list):
                result["filter_value1"] = ",".join(str(x) for x in self.filter_value1)
        return result

    @classmethod
    def from_dict(cls, d):
        """Create a filter model from dictionary, properly handling multi-value cases"""
        # Make a copy to avoid modifying the input
        data = d.copy()
        
        # Handle the special case for multi-value filters
        op = data.get("filter_operation", "")
        if op in ["is one of", "is not one of"]:
            val = data.get("filter_value1", "")
            if isinstance(val, str) and val:
                # Store as a proper list
                data["filter_value1"] = [x.strip() for x in val.split(",")]
            elif not isinstance(val, list):
                # Initialize as empty list if not string or list
                data["filter_value1"] = []
                
        return cls(**data)


class FilterTabWidget(QListWidget):
    filterSelectedCallback = Signal(int)
    filterAddRequestedCallback = Signal()
    filterRenamedCallback = Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.NoDragDrop)
        self.setEditTriggers(QListWidget.DoubleClicked)
        self.viewport().installEventFilter(self)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)
        self.filters = []
        self._refresh_tabs()
    
    def _refresh_tabs(self):
        self.clear()
        for name in self.filters:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.addItem(item)
        add_item = QListWidgetItem("Add Filter (+)")
        add_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.addItem(add_item)
    
    def set_filters(self, filter_names: list):
        self.filters = filter_names.copy()
        self._refresh_tabs()
        if self.filters:
            self.setCurrentRow(0)

    def add_filter_tab(self, filter_name: str):
        self.filters.append(filter_name)
        self._refresh_tabs()
        self.setCurrentRow(len(self.filters) - 1)

    def update_filter_tab(self, index: int, new_name: str):
        if 0 <= index < len(self.filters):
            self.filters[index] = new_name
            item = self.item(index)
            if item:
                item.setText(new_name)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        if item.text() == "Add Filter (+)":
            self.filterAddRequestedCallback.emit()
        else:
            index = self.row(item)
            self.filterSelectedCallback.emit(index)
    
    def _on_item_changed(self, item: QListWidgetItem):
        if item.text() == "Add Filter (+)":
            return
        index = self.row(item)
        self.filters[index] = item.text()
        self.filterRenamedCallback.emit(index, item.text())


class FilterEditorView(QWidget):
    def __init__(self, filter_model: FilterModel, parent=None):
        super().__init__(parent)
        self.filter_model = filter_model
        self.widgets = {}
        self.form_layout = QFormLayout(self)
        self.setLayout(self.form_layout)
        self._build_ui()
        self.update_from_model()
        # Immediately update the value widgets based on current column and operation.
        self.update_filter_value_widgets()
    
    def _build_ui(self):
        # Build widgets for all fields except the value widgets,
        # which will be handled dynamically.
        for f in fields(self.filter_model):
            if f.name in ["filter_value1", "filter_value2"]:
                continue  # handled dynamically later
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                widget.textChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
            elif isinstance(widget, QComboBox):
                if f.name == "filter_column":
                    # Get columns from the current dataframe
                    main_window = self.window()
                    datafile = None
                    df = None  # Initialize dataframe variable
                    
                    # Get the current datafile metadata from the trace editor view
                    if hasattr(main_window, 'traceEditorView') and hasattr(main_window.traceEditorView, 'model'):
                        datafile = main_window.traceEditorView.model.datafile
                        
                    # Get the dataframe from the dataframe manager
                    if datafile and hasattr(main_window, 'setupMenuModel') and hasattr(main_window.setupMenuModel, 'data_library'):
                        data_library = main_window.setupMenuModel.data_library
                        df = data_library.dataframe_manager.get_dataframe_by_metadata(datafile)
                    
                    # If we have a dataframe, get its columns
                    if df is not None:
                        all_cols = df.columns.tolist()
                        widget.clear()
                        widget.addItems(all_cols)
                        if value and value.strip():
                            if value in all_cols:
                                widget.setCurrentText(value)
                            else:
                                widget.addItem(value)
                                widget.setCurrentText(value)
                        elif all_cols:
                            widget.setCurrentText(all_cols[0])
                            self.filter_model.filter_column = all_cols[0]
                else:
                    widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
            self.form_layout.addRow(label_text, widget)
        
        # For filter_operation, update its behavior to trigger updating value widgets.
        if "filter_operation" in self.widgets:
            self.widgets["filter_operation"].currentTextChanged.connect(
                lambda text: self._on_field_changed("filter_operation", text)
            )
            self.widgets["filter_operation"].currentTextChanged.connect(lambda _: self.update_filter_value_widgets())
        
        # For filter_column, update value widgets when changed.
        if "filter_column" in self.widgets:
            self.widgets["filter_column"].currentTextChanged.connect(
                lambda text: self._on_field_changed("filter_column", text)
            )
            self.widgets["filter_column"].currentTextChanged.connect(lambda _: self.update_filter_value_widgets())
    
    def _on_field_changed(self, field_name, value):
        setattr(self.filter_model, field_name, value)
        if field_name == "filter_name":
            parent_widget = self.parent()
            while parent_widget is not None:
                ftw = parent_widget.findChild(FilterTabWidget)
                if ftw is not None:
                    idx = ftw.currentRow()
                    if idx >= 0:
                        ftw.update_filter_tab(idx, value)
                    break
                parent_widget = parent_widget.parent()
    
    def update_filter_value_widgets(self):
        """
        Rebuild the input widget(s) for filter_value1 (and filter_value2, if needed)
        based on the selected column's type and the chosen filter operation.
        """
        # Determine column and get the dataframe
        col = self.widgets["filter_column"].currentText()
        main_window = self.window()
        datafile = None
        df = None
        
        # Get the current datafile metadata from the trace editor view
        if hasattr(main_window, 'traceEditorView') and hasattr(main_window.traceEditorView, 'model'):
            datafile = main_window.traceEditorView.model.datafile
            
        # Get the dataframe from the dataframe manager
        if datafile and hasattr(main_window, 'setupMenuModel') and hasattr(main_window.setupMenuModel, 'data_library'):
            data_library = main_window.setupMenuModel.data_library
            df = data_library.dataframe_manager.get_dataframe_by_metadata(datafile)
        
        # Determine if column is numeric and get unique values
        if df is not None and col in df.columns:
            numeric = col in df.select_dtypes(include=['number']).columns
            suggestions = df[col].dropna().unique().tolist()
            
            # Sort suggestions
            try:
                if suggestions and numeric:
                    suggestions.sort(key=lambda x: float(x))
                else:
                    suggestions.sort(key=lambda x: str(x))
            except Exception:
                suggestions.sort(key=lambda x: str(x))
        else:
            numeric = True  # default assumption
            suggestions = []
        
        # Get the current filter_value1 content to preserve it
        current_value1 = self.filter_model.filter_value1
        
        # Ensure suggestions are strings.
        suggestions = [str(s) for s in suggestions]
        
        # If we have a multi-value filter, make sure all values are in suggestions
        if self.filter_model.filter_operation in ["is one of", "is not one of"]:
            if isinstance(current_value1, list):
                for val in current_value1:
                    str_val = str(val)
                    if str_val not in suggestions:
                        suggestions.append(str_val)
        
        # Use the saved model value for filter_operation if present.
        saved_op = self.filter_model.filter_operation

        # Update the filter_operation combo box.
        op_widget = self.widgets["filter_operation"]
        op_widget.blockSignals(True)
        op_widget.clear()
        if numeric:
            new_ops = FilterModel.ALLOWED_NUMERIC_OPERATIONS + ["is", "is not", "is one of", "is not one of"]
        else:
            new_ops = ["is", "is not", "is one of", "is not one of"]
        op_widget.addItems(new_ops)
        if saved_op in new_ops:
            op_widget.setCurrentText(saved_op)
        else:
            op_widget.setCurrentIndex(0)
        op_widget.blockSignals(False)
        op = op_widget.currentText()
        # Save back the op to the model (if it changed).
        self.filter_model.filter_operation = op
        
        # Create new widgets for filter_value1 and filter_value2...
        # (Rest of the method remains the same as in the original code)
        
        # ---- Rebuild filter_value1 ----
        # Remove previous row (both label and widget) if they exist.
        if "filter_value1_label" in self.widgets:
            old_label = self.widgets.pop("filter_value1_label")
            self.form_layout.removeWidget(old_label)
            old_label.deleteLater()
        if "filter_value1" in self.widgets:
            old_widget = self.widgets.pop("filter_value1")
            self.form_layout.removeWidget(old_widget)
            old_widget.deleteLater()
        
        # Create new widget for filter_value1.
        if op in ["is one of", "is not one of"]:
            new_w = MultiFieldSelector(self)
            # Important: Set available options BEFORE setting selected fields
            new_w.set_available_options(suggestions)
            
            # Handle the saved values - ensure they're properly formatted
            saved_value = current_value1
            if isinstance(saved_value, str) and saved_value:
                saved_fields = [v.strip() for v in saved_value.split(",")]
            elif isinstance(saved_value, list):
                saved_fields = saved_value
            else:
                saved_fields = []
                
            # Now set the selected fields
            new_w.set_selected_fields(saved_fields)
            
            # Connect after initializing to avoid triggering during setup
            new_w.selectionChanged.connect(lambda sel: self._on_field_changed("filter_value1", sel))
        else:
            new_w = QLineEdit(self)
            if numeric and op in FilterModel.ALLOWED_NUMERIC_OPERATIONS:
                new_w.setValidator(QDoubleValidator())
            else:
                completer = QCompleter(suggestions, self)
                new_w.setCompleter(completer)
            
            # Set the current value
            if isinstance(current_value1, list) and current_value1:
                # Convert list to comma-separated string
                new_w.setText(", ".join(str(v) for v in current_value1))
            elif current_value1:
                new_w.setText(str(current_value1))
                
            new_w.textChanged.connect(lambda text: self._on_field_changed("filter_value1", text))
        
        # Add new row with a label.
        label1 = QLabel("Value A:", self)
        self.widgets["filter_value1_label"] = label1
        self.widgets["filter_value1"] = new_w
        self.form_layout.addRow(label1, new_w)
        
        # ---- Rebuild filter_value2 (only for range operations on numeric data) ----
        if "filter_value2_label" in self.widgets:
            old_label2 = self.widgets.pop("filter_value2_label")
            self.form_layout.removeWidget(old_label2)
            old_label2.deleteLater()
        if "filter_value2" in self.widgets:
            old_widget2 = self.widgets.pop("filter_value2")
            self.form_layout.removeWidget(old_widget2)
            old_widget2.deleteLater()
        
        if numeric and op in ["a < x < b", "a <= x < b", "a < x <= b"]:
            new_w2 = QLineEdit(self)
            new_w2.setValidator(QDoubleValidator())
            new_w2.textChanged.connect(lambda text: self._on_field_changed("filter_value2", text))
            # Set the current value
            if self.filter_model.filter_value2:
                new_w2.setText(str(self.filter_model.filter_value2))
            label2 = QLabel("Value B:", self)
            self.widgets["filter_value2_label"] = label2
            self.widgets["filter_value2"] = new_w2
            self.form_layout.addRow(label2, new_w2)
    
    def update_from_model(self):
        # Update static widgets.
        for f in fields(self.filter_model):
            if f.name in ["filter_value1", "filter_value2"]:
                continue  # their widgets are handled dynamically
            widget = self.widgets.get(f.name)
            if not widget:
                continue
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
        # Now update the dynamic value widgets.
        self.update_filter_value_widgets()
        
        # For multi-field selectors, update the selected items.
        op = self.filter_model.filter_operation
        if op in ["is one of", "is not one of"]:
            multi_field_widget = self.widgets.get("filter_value1")
            if multi_field_widget and hasattr(multi_field_widget, "set_selected_fields"):
                # Recalculate suggestions (must match the ones used in update_filter_value_widgets)
                col = self.widgets["filter_column"].currentText()
                main_window = self.window()
                datafile = None
                if (hasattr(main_window, 'traceEditorView') and 
                    hasattr(main_window.traceEditorView, 'model')):
                    datafile = main_window.traceEditorView.model.datafile
                if datafile and datafile.file_path:
                    suggestions = get_sorted_unique_values(
                        datafile.file_path,
                        datafile.header_row,
                        datafile.sheet,
                        col
                    )
                else:
                    suggestions = []
                # Normalize suggestions to strings.
                suggestions = [str(s) for s in suggestions]
                
                # Get the saved value.
                value = getattr(self.filter_model, "filter_value1", [])
                if isinstance(value, str) and value:
                    fields_list = [v.strip() for v in value.split(",")]
                elif isinstance(value, list):
                    fields_list = value
                else:
                    fields_list = []
                
                # FIXED: Instead of trying to normalize and match values, ensure all 
                # saved values are included in the available options
                for v in fields_list:
                    if v not in suggestions:
                        suggestions.append(v)
                
                # Update available options to include saved values
                multi_field_widget.set_available_options(suggestions)
                
                # Set selected fields directly
                multi_field_widget.set_selected_fields(fields_list)
    
    def set_filter_model(self, new_filter_model: FilterModel):
        self.filter_model = new_filter_model
        self.update_from_model()

@dataclass
class TraceEditorModel:
    trace_name: str = field(
        default="Default Trace",
        metadata={"label": "Trace Name:", "widget": QLineEdit, "plot_types": ["ternary", "cartesian"]}
    )
    datafile: DataFileMetadata = field(
        default_factory=lambda: DataFileMetadata(file_path=""),
        metadata={"label": "Datafile:", "widget": QComboBox, "plot_types": ["ternary", "cartesian"]}
    )
    is_contour: bool = field(
        default=False,
        metadata={"label": None, "widget": None, "plot_types": ["ternary", "cartesian"]}
    )
    trace_color: str = field(
        default="blue",
        metadata={"label": "Point Color:", "widget": ColorButton, "plot_types": ["ternary", "cartesian"]}
    )
    point_shape: str = field(
        default="circle",
        metadata={"label": "Point Shape:", "widget": ShapeButtonWithMenu, "plot_types": ["ternary", "cartesian"]}
    ) 
    convert_from_wt_to_molar: bool = field(
        default=False,
        metadata={
            "label": "Convert from wt% to molar:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
        }
    )
    point_size: float = field(
        default=5.0,
        metadata={"label": "Point Size:", "widget": QDoubleSpinBox, "plot_types": ["ternary", "cartesian"]}
    )
    line_on: bool = field(
        default=True,
        metadata={"label": "Line On:", "widget": QCheckBox, "plot_types": ["cartesian"]}
    )
    line_style: str = field(
        default="solid",
        metadata={"label": "Line Style:", "widget": QComboBox, "plot_types": ["cartesian"]}
    )
    line_thickness: float = field(
        default=1.0,
        metadata={"label": "Line Thickness:", "widget": QDoubleSpinBox, "plot_types": ["cartesian"]}
    )
    heatmap_on: bool = field(
        default=False,
        metadata={"label": "Heatmap On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    # New field: advanced toggle inside heatmap group.
    heatmap_use_advanced: bool = field(
        default=False,
        metadata={
            "label": "Use advanced settings:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "group": "heatmap",
            "depends_on": "heatmap_on"
        }
    )
    # Basic heatmap settings (always visible when heatmap is on)
    heatmap_column: str = field(
        default="",
        metadata={
            "label": "Heatmap Column:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_min: float = field(
        default=0.0,
        metadata={
            "label": "Heatmap Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_max: float = field(
        default=1.0,
        metadata={
            "label": "Heatmap Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    # Advanced options – marked with "advanced": True and depend on both heatmap_on and heatmap_use_advanced.
    heatmap_colorscale: str = field(
        default="Viridis",
        metadata={
            "label": "Heatmap Colorscale:",
            "widget": ColorScaleDropdown,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True
        }
    )
    heatmap_reverse_colorscale: bool = field(
        default=False,
        metadata={
            "label": "Reverse colorscale:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True
        }
    )
    heatmap_log_transform: bool = field(
        default=False,
        metadata={
            "label": "Log-transform:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True
        }
    )
    heatmap_sort_mode: str = field(
        default="no change",
        metadata={
            "label": "Heatmap Sort Mode:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "advanced": True
        }
    )
    # Advanced heatmap colorbar position & dimensions fields
    heatmap_bar_orientation: str = field(
        default="vertical",
        metadata={
            "label": "Bar orientation:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position && Dimensions",
            "advanced": True
        }
    )
    heatmap_colorbar_x: float = field(
        default=1.1,
        metadata={
            "label": "X Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position && Dimensions",
            "advanced": True
        }
    )
    heatmap_colorbar_y: float = field(
        default=0.5,
        metadata={
            "label": "Y Position:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True
        }
    )
    heatmap_colorbar_len: float = field(
        default=0.6,
        metadata={
            "label": "Length:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True
        }
    )
    heatmap_colorbar_thickness: float = field(
        default=18.0,
        metadata={
            "label": "Thickness:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["heatmap_on", "heatmap_use_advanced"],
            "group": "heatmap",
            "subgroup": "position_dimensions",
            "subgroup_title": "Position & Dimensions",
            "advanced": True
        }
    )
    sizemap_on: bool = field(
        default=False,
        metadata={
            "label": "Sizemap On:", 
            "widget": QCheckBox, 
            "plot_types": ["ternary", "cartesian"]
        }
    )
    sizemap_column: str = field(
        default="",
        metadata={
            "label": "Sizemap Column:", 
            "widget": QComboBox, 
            "plot_types": ["ternary", "cartesian"], 
            "depends_on": "sizemap_on", 
            "group": "sizemap"
        }
    )
    sizemap_sort_mode: str = field(
        default="no change",
        metadata={
            "label": "Sizemap Sort Mode:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap"
        }
    )
    sizemap_min: float = field(
        default=0.0,
        metadata={
            "label": "Sizemap Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap"
        }
    )
    sizemap_max: float = field(
        default=1.0,
        metadata={
            "label": "Sizemap Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "sizemap_on",
            "group": "sizemap"
        }
    )
    filters_on: bool = field(
        default=False,
        metadata={"label": "Filters On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    filters: list = field(
        default_factory=list,
        metadata={"label": "Filters:", "widget": None, "plot_types": ["ternary", "cartesian"]}
    )
    # Contour confidence level - updated to use self-describing options
    contour_level: str = field(
        default="Contour: 1-sigma",
        metadata={
            "label": "", # No separate label needed
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "is_contour",
        }
    )
    # Custom percentile (only visible when contour_level is "Contour: Custom percentile")
    contour_percentile: float = field(
        default=95.0,
        metadata={
            "label": "Percentile:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": ["is_contour", ("contour_level", "Contour: Custom percentile")]
        }
    )

    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict):
        # Create a copy to avoid modifying the input
        d_copy = d.copy()
        
        # Handle filters with proper deserialization
        if "filters" in d_copy and isinstance(d_copy["filters"], list):
            d_copy["filters"] = [
                FilterModel.from_dict(item) if isinstance(item, dict) else item 
                for item in d_copy["filters"]
            ]
            
        # Handle datafile conversion
        datafile_value = d_copy.get("datafile", None)
        if isinstance(datafile_value, dict):
            d_copy["datafile"] = DataFileMetadata.from_dict(datafile_value)
        elif isinstance(datafile_value, str):
            d_copy["datafile"] = DataFileMetadata(file_path=datafile_value)
        else:
            d_copy["datafile"] = DataFileMetadata(file_path="")
            
        return cls(**d_copy)
    
    @classmethod
    def _convert_filter(cls, d: dict):
        # If the operation is multi-field and filter_value1 is a non-empty string,
        # split it into a list.
        op = d.get("filter_operation", "")
        if op in ["is one of", "is not one of"]:
            val = d.get("filter_value1", "")
            if isinstance(val, str) and val:
                d["filter_value1"] = [x.strip() for x in val.split(",")]
        return d

class TraceEditorView(QWidget):
    def __init__(self, model: TraceEditorModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # default
        self.widgets = {}      # Maps field names to widget instances.
        self.group_boxes = {}  # Maps group names to (group_box, layout)

        # Wrap the entire editor in a scroll area.
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.form_layout = QFormLayout(self.content)
        self.content.setLayout(self.form_layout)
        self.scroll.setWidget(self.content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll)
        self.setLayout(main_layout)

        self._build_ui()
        self.set_plot_type(self.current_plot_type)

    def update_filter_columns(self, datafile: str):
        """Update all filter columns based on the current datafile."""
        if not hasattr(self, "filterTabWidget") or not datafile:
            return
            
        # Get all available columns from the current datafile
        all_cols = get_all_columns_from_file(datafile)
        if not all_cols:
            return
            
        # Get the currently selected filter
        current_index = self.filterTabWidget.currentRow()
        if current_index < 0 or current_index >= len(self.model.filters):
            return
            
        # Update any visible filter editor
        for child in self.findChildren(FilterEditorView):
            filter_combo = child.widgets.get('filter_column')
            if filter_combo:
                # Get the current value before updating
                current_value = filter_combo.currentText()
                
                # Update with new items
                filter_combo.blockSignals(True)
                filter_combo.clear()
                filter_combo.addItems(all_cols)
                
                # Try to preserve the previous selection if possible
                if current_value and current_value.strip():
                    if filter_combo.findText(current_value) == -1:
                        filter_combo.addItem(current_value)
                    filter_combo.setCurrentText(current_value)
                else:
                    filter_combo.setCurrentText(all_cols[0])
                filter_combo.blockSignals(False)

    def _build_ui(self):
        # Clear existing state.
        self.widgets = {}
        self.group_boxes = {}
        self.subgroup_boxes = {}  # Track nested group boxes
        group_fields = {}
        subgroup_fields = {}  # Track fields that go in nested group boxes
        
        # Process each field in the model.
        for f in fields(self.model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                if f.name == "trace_name":
                    widget.textChanged.connect(lambda text, fname=f.name: self._on_trace_name_changed(text))
                else:
                    widget.textChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
            elif isinstance(widget, ColorButton):
                widget.setColor(value)
                widget.colorChanged.connect(lambda color_str, fname=f.name: setattr(self.model, fname, color_str))
            elif isinstance(widget, ColorScaleDropdown):
                # Handle our custom ColorScaleDropdown
                widget.setColorScale(value)
                widget.colorScaleChanged.connect(lambda scale_str, fname=f.name: setattr(self.model, fname, scale_str))
            elif isinstance(widget, ShapeButtonWithMenu):
                # Special handling for our custom shape buttons
                widget.setShape(value)
                widget.shapeChanged.connect(lambda shape_str, fname=f.name: setattr(self.model, fname, shape_str))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
                widget.valueChanged.connect(lambda val, fname=f.name: setattr(self.model, fname, val))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
                widget.stateChanged.connect(lambda state, fname=f.name: setattr(self.model, fname, bool(state)))
                if f.name in ("heatmap_on", "sizemap_on"):
                    widget.stateChanged.connect(lambda _: self.set_plot_type(self.current_plot_type))
                if f.name == "filters_on":
                    widget.stateChanged.connect(lambda _: self._update_filters_visibility())
            elif isinstance(widget, QComboBox):
                if f.name == "line_style":
                    widget.addItems(["solid", "dashed", "dotted"])
                elif f.name == "heatmap_sort_mode":
                    widget.addItems(["no change", "high on top", "low on top", "shuffled"])
                elif f.name == "heatmap_colorscale":
                    widget.addItems(["Viridis", "Cividis", "Plasma", "Inferno"])
                elif f.name == "sizemap_sort_mode":
                    widget.addItems(["no change", "high on top", "low on top", "shuffled"])
                elif f.name == "sizemap_scale":
                    widget.addItems(["linear", "log"])
                elif f.name == "heatmap_bar_orientation":
                    widget.addItems(["vertical", "horizontal"])
                elif f.name == "contour_level":
                    widget.addItems(["Contour: 1-sigma", "Contour: 2-sigma"]) # Removing custom percentile option until view handling is working
                    # widget.currentTextChanged.connect(lambda _: QTimer.singleShot(100, self.set_plot_type(self.current_plot_type)))
                else:
                    widget.addItems([])
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
            
            # Enhanced grouping with subgrouping support
            group_name = metadata.get("group", None)
            subgroup_name = metadata.get("subgroup", None)
            
            if group_name and subgroup_name:
                # This field goes in a nested group box
                key = (group_name, subgroup_name)
                if key not in subgroup_fields:
                    subgroup_fields[key] = []
                subgroup_fields[key].append((f.name, label_text, widget, metadata))
            elif group_name:
                # This field goes in a regular group box
                if group_name not in group_fields:
                    group_fields[group_name] = []
                group_fields[group_name].append((f.name, label_text, widget, metadata))
            else:
                # This field goes directly in the form
                self.form_layout.addRow(label_text, widget)

        print(f"Found subgroup fields: {list(subgroup_fields.keys())}")

         # Now handle group boxes and nested group boxes
        for group_name, field_tuples in group_fields.items():
            if group_name == "heatmap":
                print(f"Building heatmap group with {len(field_tuples)} fields")
                # Special handling for heatmap group
                group_box = QGroupBox("Heatmap", self)
                vlayout = QVBoxLayout(group_box)
                
                # Create a form layout for basic fields
                basic_form = QFormLayout()
                
                # Create an advanced container
                advanced_container = QWidget(self)
                advanced_form = QFormLayout(advanced_container)
                advanced_container.setLayout(advanced_form)
                self.advanced_heatmap_container = advanced_container
                
                # Process field tuples to separate basic and advanced
                toggle_tuple = None
                for fname, label_text, widget, meta in field_tuples:
                    if fname == "heatmap_use_advanced":
                        toggle_tuple = (fname, label_text, widget, meta)
                    elif meta.get("advanced", False):
                        # Only add fields without a subgroup directly to advanced form
                        if not meta.get("subgroup"):
                            advanced_form.addRow(label_text, widget)
                    else:
                        basic_form.addRow(label_text, widget)
                
                # Add basic form to the main layout
                vlayout.addLayout(basic_form)
                
                # Add the advanced toggle after basic fields
                if toggle_tuple:
                    t_fname, t_label, t_widget, t_meta = toggle_tuple
                    basic_form.addRow(t_label, t_widget)
                    # Connect the toggle to update visibility of advanced items
                    if isinstance(t_widget, QCheckBox):
                        # Disconnect any existing connections first to avoid duplicates
                        try:
                            t_widget.stateChanged.disconnect()
                        except:
                            pass
                        # Connect to our enhanced handler
                        t_widget.stateChanged.connect(lambda state: self._update_advanced_visibility(bool(state)))
                
                # Now handle any nested group boxes within the heatmap advanced section
                for (group, subgroup), sub_field_tuples in subgroup_fields.items():
                    if group == "heatmap":
                        print(f"Building nested groupbox for {subgroup} with {len(sub_field_tuples)} fields")
                        # Create the nested group box with title from metadata
                        subgroup_title = sub_field_tuples[0][3].get("subgroup_title", subgroup.replace("_", " ").title())
                        nested_group_box = QGroupBox(subgroup_title)
                        nested_layout = QFormLayout(nested_group_box)
                        
                        # Add fields to the nested group box
                        for sub_fname, sub_label, sub_widget, sub_meta in sub_field_tuples:
                            print(f"  Adding field {sub_fname} to nested groupbox")
                            nested_layout.addRow(sub_label, sub_widget)
                        
                        # Store the nested group box for visibility control
                        self.subgroup_boxes[(group, subgroup)] = nested_group_box
                        
                        # Add the nested group box to the advanced container
                        advanced_form.addRow(nested_group_box)
                
                # Add the advanced container to the main layout
                vlayout.addWidget(advanced_container)
                
                # Set initial visibility based on model
                heatmap_use_advanced = getattr(self.model, "heatmap_use_advanced", False)
                print(f"Initial heatmap_use_advanced state: {heatmap_use_advanced}")
                advanced_container.setVisible(heatmap_use_advanced)
                
                # Store the heatmap group box for later visibility control
                self.group_boxes["heatmap"] = (group_box, vlayout)
                self.form_layout.addRow(group_box)
                
                # Force nested groupbox visibility update
                self._update_advanced_visibility(heatmap_use_advanced)
            else:
                group_box = QGroupBox(group_name.capitalize(), self)
                group_layout = QFormLayout(group_box)
                for fname, label_text, widget, meta in field_tuples:
                    group_layout.addRow(label_text, widget)
                self.group_boxes[group_name] = (group_box, group_layout)
                self.form_layout.addRow(group_box)
        self._build_filters_ui()

    def _update_advanced_visibility(self, show_advanced):
        """Update visibility of all advanced components when the toggle changes"""
        print(f"Updating advanced visibility: {show_advanced}")
        
        # First, update the main advanced container
        if hasattr(self, "advanced_heatmap_container"):
            self.advanced_heatmap_container.setVisible(show_advanced)
            print(f"Set advanced_heatmap_container visibility to {show_advanced}")
        
        # Then, update all nested groupboxes
        for (group, subgroup), nested_box in self.subgroup_boxes.items():
            if group == "heatmap":
                print(f"Setting {group}/{subgroup} visibility to {show_advanced}")
                nested_box.setVisible(show_advanced)
                
                # Force visibility of all child widgets too
                for i in range(nested_box.layout().count()):
                    item = nested_box.layout().itemAt(i)
                    if item and item.widget():
                        item.widget().setVisible(show_advanced)
        
        # Update the model value
        if hasattr(self.model, "heatmap_use_advanced"):
            self.model.heatmap_use_advanced = show_advanced

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type.lower()
        # Process ungrouped fields.
        for f in fields(self.model):
            metadata = f.metadata
            if "widget" not in metadata or metadata["widget"] is None or "group" in metadata:
                continue
            widget = self.widgets.get(f.name)
            label = self.form_layout.labelForField(widget)
            visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
            if "depends_on" in metadata:
                dep = metadata["depends_on"]
                if isinstance(dep, list):
                    for d in dep:
                        if isinstance(d, str):
                            visible = visible and bool(getattr(self.model, d))
                        elif isinstance(d, tuple) and len(d) == 2:
                            # If tuple, check that dependent field equals necessary value
                            visible = visible and getattr(self.model, d[0]) == d[1]
                else:
                    visible = visible and bool(getattr(self.model, dep))
            if visible:
                widget.show()
                if label:
                    label.show()
            else:
                widget.hide()
                if label:
                    label.hide()
        # Process grouped fields with nested groupbox support
        for group_name, (group_box, _) in self.group_boxes.items():
            if group_name == "heatmap":
                heatmap_on = getattr(self.model, "heatmap_on", False)
                group_box.setVisible(heatmap_on)
                if heatmap_on:
                    # Use our dedicated method to update all advanced visibility
                    heatmap_use_advanced = getattr(self.model, "heatmap_use_advanced", False)
                    self._update_advanced_visibility(heatmap_use_advanced)
            else:
                group_visible = False
                for f in fields(self.model):
                    metadata = f.metadata
                    if metadata.get("group", None) != group_name:
                        continue
                    field_visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
                    if "depends_on" in metadata:
                        dep = metadata["depends_on"]
                        if isinstance(dep, list):
                            for d in dep:
                                field_visible = field_visible and bool(getattr(self.model, d))
                        else:
                            field_visible = field_visible and bool(getattr(self.model, dep))
                    if field_visible:
                        group_visible = True
                        break
                group_box.setVisible(group_visible)
        self._update_filters_visibility()

    def update_from_model(self):
        for f in fields(self.model):
            metadata = f.metadata
            if "widget" not in metadata or metadata["widget"] is None:
                continue
            widget = self.widgets.get(f.name)
            if not widget:
                continue
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                # For heatmap and sizemap columns, just add the saved value if needed
                if f.name in ["heatmap_column", "sizemap_column"] and value:
                    # Add the saved value to the combobox if it's not already there
                    if widget.findText(value) == -1 and value:
                        widget.addItem(value)
                # Now set the current text
                widget.setCurrentText(str(value))
            elif isinstance(widget, ColorButton):
                # Update the color button
                widget.setColor(value)
            elif isinstance(widget, ShapeButtonWithMenu):
                # Update the shape button
                widget.setShape(value)
            elif isinstance(widget, ColorScaleDropdown):
                # Update the color scale button
                widget.setColorScale(value)

        if "heatmap_colorbar_x" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_x"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(-2.0, 3.0)
                spinbox.setSingleStep(0.1)
        
        if "heatmap_colorbar_y" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_y"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(0.0, 1.0)
                spinbox.setSingleStep(0.05)
        
        if "heatmap_colorbar_len" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_len"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(0.1, 1.0)
                spinbox.setSingleStep(0.05)
        
        if "heatmap_colorbar_thickness" in self.widgets:
            spinbox = self.widgets["heatmap_colorbar_thickness"]
            if isinstance(spinbox, QDoubleSpinBox):
                spinbox.setRange(1.0, 50.0)
                spinbox.setSingleStep(1.0)

    def _on_trace_name_changed(self, text: str):
        self.model.trace_name = text
        if hasattr(self, "traceNameChangedCallback") and self.traceNameChangedCallback:
            self.traceNameChangedCallback(text)

    def set_model(self, new_model: TraceEditorModel):
        self.model = new_model
        self.update_from_model()
        self.set_plot_type(self.current_plot_type)
        self._build_filters_ui()

    # --- Filters UI Methods in TraceEditorView ---
    def _build_filters_ui(self):
        from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout
        if hasattr(self, "filtersGroupBox"):
            self.form_layout.removeWidget(self.filtersGroupBox)
            self.filtersGroupBox.deleteLater()
        self.filtersGroupBox = QGroupBox("Filters", self)
        filters_layout = QHBoxLayout(self.filtersGroupBox)
        self.filtersGroupBox.setLayout(filters_layout)
        self.filterTabWidget = FilterTabWidget(self)
        filters_layout.addWidget(self.filterTabWidget)
        self.filterEditorContainer = QWidget(self)
        self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
        self.filterEditorContainer.setLayout(self.filterEditorLayout)
        filters_layout.addWidget(self.filterEditorContainer)
        filter_names = [f.filter_name for f in self.model.filters] if self.model.filters else []
        self.filterTabWidget.set_filters(filter_names)
        if self.model.filters:
            self.currentFilterIndex = 0
            self.filterTabWidget.setCurrentRow(0)
            self._show_current_filter()
        else:
            self.currentFilterIndex = None
        self.filterTabWidget.filterSelectedCallback.connect(self.on_filter_selected)
        self.filterTabWidget.filterAddRequestedCallback.connect(self.on_filter_add_requested)
        self.filterTabWidget.filterRenamedCallback.connect(self.on_filter_renamed)
        self.form_layout.addRow(self.filtersGroupBox)
        self._update_filters_visibility()

    def _show_current_filter(self):
        if self.currentFilterIndex is None or self.currentFilterIndex >= len(self.model.filters):
            return
        if hasattr(self, "filterEditorLayout"):
            while self.filterEditorLayout.count():
                w = self.filterEditorLayout.takeAt(0).widget()
                if w is not None:
                    w.deleteLater()
        current_filter = self.model.filters[self.currentFilterIndex]
        self.currentFilterEditor = FilterEditorView(current_filter, self)
        self.filterEditorLayout.addWidget(self.currentFilterEditor)

    def on_filter_selected(self, index: int):
        if index < 0 or index >= len(self.model.filters):
            return
        self.currentFilterIndex = index
        self._show_current_filter()

    def on_filter_add_requested(self):
        new_filter = FilterModel()
        self.model.filters.append(new_filter)
        self.filterTabWidget.add_filter_tab(new_filter.filter_name)
        self.currentFilterIndex = len(self.model.filters) - 1
        self._show_current_filter()

    def on_filter_renamed(self, index: int, new_name: str):
        if index < 0 or index >= len(self.model.filters):
            return
        self.model.filters[index].filter_name = new_name
        if self.currentFilterIndex == index and hasattr(self, "currentFilterEditor"):
            self.currentFilterEditor.update_from_model()

    def _update_filters_visibility(self):
        if hasattr(self, "filtersGroupBox"):
            if getattr(self.model, "filters_on", False):
                self.filtersGroupBox.show()
            else:
                self.filtersGroupBox.hide()

class TraceEditorController:
    def __init__(self, model: TraceEditorModel, view: TraceEditorView, data_library: DataLibraryModel):
        self.model = model
        self.view = view
        self.data_library = data_library  # Pass the DataLibraryModel for lookup
        datafile_combo = view.widgets.get("datafile")
        if datafile_combo:
            datafile_combo.currentTextChanged.connect(self.on_datafile_changed)

    def on_datafile_changed(self, new_file: Union[str, DataFileMetadata]):
        """Handle datafile changes with smarter column handling for heatmap and sizemap."""
        print(f"Datafile changed to: {new_file}")
        
        # Get the appropriate metadata
        if isinstance(new_file, str):
            metadata = self.data_library.get_metadata_by_path(new_file)
            if not metadata:
                # If the path isn't in our library, create a basic metadata object
                metadata = DataFileMetadata(file_path=new_file)
        elif isinstance(new_file, DataFileMetadata):
            metadata = new_file
        else:
            print(f"Unexpected datafile type: {type(new_file)}")
            return
            
        # Update the model's datafile
        self.model.datafile = metadata
        print(f"Datafile changed to: {self.model.datafile}")
        
        # Get the dataframe
        df = self.data_library.dataframe_manager.get_dataframe_by_metadata(metadata)
        if df is None:
            print(f"Warning: Could not get dataframe for {metadata.file_path}")
            return
            
        # Get numeric columns from the dataframe
        numeric_cols = get_numeric_columns_from_dataframe(df)
        print(f"Numeric columns in new file: {numeric_cols}")
        
        # Get ALL columns from the dataframe (for filters)
        all_cols = get_all_columns_from_dataframe(df)
        
        # --- Update heatmap column options ---
        heatmap_combo = self.view.widgets.get("heatmap_column")
        if heatmap_combo:
            heatmap_combo.blockSignals(True)
            current_value = self.model.heatmap_column
            print(f"Current heatmap column: {current_value}")
            
            # Clear and add new columns
            heatmap_combo.clear()
            heatmap_combo.addItems(numeric_cols)
            
            # Check if current value exists in the new file's columns
            value_exists_in_new_file = current_value in numeric_cols
            
            # If this is an interactive datafile change (not a workspace load)
            # and the current value is not in the new file, we must change it
            if not value_exists_in_new_file:
                if numeric_cols:
                    print(f"Heatmap column '{current_value}' not in new file, switching to '{numeric_cols[0]}'")
                    self.model.heatmap_column = numeric_cols[0]
                    heatmap_combo.setCurrentText(numeric_cols[0])
                else:
                    print("No numeric columns in new file, clearing heatmap column")
                    self.model.heatmap_column = ""
            else:
                print(f"Keeping existing heatmap column '{current_value}' as it exists in new file")
                heatmap_combo.setCurrentText(current_value)
            
            heatmap_combo.blockSignals(False)

        # --- Update sizemap column options similarly ---
        sizemap_combo = self.view.widgets.get("sizemap_column")
        if sizemap_combo:
            sizemap_combo.blockSignals(True)
            current_value = self.model.sizemap_column
            
            # Clear and add new columns
            sizemap_combo.clear()
            sizemap_combo.addItems(numeric_cols)
            
            # Check if current value exists in the new file's columns
            value_exists_in_new_file = current_value in numeric_cols
            
            # If the value doesn't exist in the new file, change it
            if not value_exists_in_new_file:
                if numeric_cols:
                    self.model.sizemap_column = numeric_cols[0]
                    sizemap_combo.setCurrentText(numeric_cols[0])
                else:
                    self.model.sizemap_column = ""
            else:
                sizemap_combo.setCurrentText(current_value)
                
            sizemap_combo.blockSignals(False)
        
        # --- Update filter column options in existing filters ---
        if hasattr(self.model, 'filters') and self.model.filters:
            for filter_model in self.model.filters:
                # Find the filter editor if it exists
                filter_editor = None
                for child in self.view.findChildren(FilterEditorView):
                    if hasattr(child, 'filter_model') and child.filter_model == filter_model:
                        filter_editor = child
                        break
                
                if filter_editor and hasattr(filter_editor, 'widgets'):
                    filter_combo = filter_editor.widgets.get('filter_column')
                    if filter_combo:
                        filter_combo.blockSignals(True)
                        current_value = filter_model.filter_column
                        filter_combo.clear()
                        filter_combo.addItems(all_cols)
                        
                        # Check if current value exists in the new file's columns
                        value_exists_in_new_file = current_value in all_cols
                        
                        # If the value doesn't exist in the new file, change it
                        if not value_exists_in_new_file:
                            if all_cols:
                                filter_model.filter_column = all_cols[0]
                                filter_combo.setCurrentText(all_cols[0])
                            else:
                                filter_model.filter_column = ""
                        else:
                            filter_combo.setCurrentText(current_value)
                        
                        filter_combo.blockSignals(False)

# --------------------------------------------------------------------
# Setup Menu Models
# --------------------------------------------------------------------
    
# --------------------------------------------------------------------
# Column Scaling Widget
# --------------------------------------------------------------------
class ColumnScalingWidget(QWidget):
    """
    Widget that displays selected columns for each axis/apex and allows setting
    scale factors for each column.
    """
    scaleChanged = Signal(str, str, float)  # axis_name, column_name, scale_factor
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.axis_sections = {}  # axis_name -> QGroupBox
        self.scale_inputs = {}   # (axis_name, column_name) -> QDoubleSpinBox
        
        # Add heading label
        heading = QLabel("<b>Column Scaling:</b>")
        heading.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(heading)
        
        # Add help text
        help_text = QLabel("Set scale factors for each column. Values will be multiplied by these factors before plotting.")
        help_text.setWordWrap(True)
        self.layout().addWidget(help_text)
        
        # Add a spacer
        self.layout().addSpacing(10)

    def update_columns(self, axis_name, columns, current_scales=None):
        """
        Update the widget to show the current columns for an axis
        
        Args:
            axis_name: Name of the axis (x_axis, y_axis, etc.)
            columns: List of column names selected for this axis
            current_scales: Dictionary of current scale values (column_name -> scale_factor)
        """
        # Default scales dictionary if none provided
        if current_scales is None:
            current_scales = {}
            
        # Format the axis name for display
        display_name = axis_name.replace("_", " ").title()
        
        # Remove the old section if it exists
        if axis_name in self.axis_sections:
            section = self.axis_sections[axis_name]
            self.layout().removeWidget(section)
            section.deleteLater()
            # Clean up scale_inputs references for this axis
            keys_to_remove = [k for k in self.scale_inputs if k[0] == axis_name]
            for key in keys_to_remove:
                del self.scale_inputs[key]
        
        # Create a new section if there are columns
        if columns:
            section = QGroupBox(display_name)
            section_layout = QFormLayout(section)
            
            for column in columns:
                spin_box = QDoubleSpinBox()
                spin_box.setRange(0.01, 1000.0)  # Wide range for flexibility
                spin_box.setSingleStep(0.1)
                spin_box.setDecimals(3)  # More precision
                
                # Set current value from the model or default to 1.0
                scale_value = current_scales.get(column, 1.0)
                spin_box.setValue(scale_value)
                
                # Use a lambda that captures the current values
                def make_callback(a=axis_name, c=column):
                    return lambda value: self.scaleChanged.emit(a, c, value)
                
                spin_box.valueChanged.connect(make_callback())
                
                # Store reference to the spin box
                self.scale_inputs[(axis_name, column)] = spin_box
                
                # Add to layout
                section_layout.addRow(QLabel(column), spin_box)
            
            self.axis_sections[axis_name] = section
            self.layout().addWidget(section)
        
        # Add a spacer at the end to push everything up
        # if not self.layout().count() or not isinstance(self.layout().itemAt(self.layout().count()-1), QSpacerItem):
        #     self.layout().addStretch(1)

    def set_scale_value(self, axis_name, column_name, value):
        """Set the scale value for a specific column in an axis"""
        key = (axis_name, column_name)
        if key in self.scale_inputs:
            # Block signals to prevent triggering the valueChanged signal
            self.scale_inputs[key].blockSignals(True)
            self.scale_inputs[key].setValue(value)
            self.scale_inputs[key].blockSignals(False)

    def clear(self):
        """Clear all scaling sections"""
        for section in self.axis_sections.values():
            self.layout().removeWidget(section)
            section.deleteLater()
        self.axis_sections.clear()
        self.scale_inputs.clear()

# --------------------------------------------------------------------
# Column Scaling Model
# --------------------------------------------------------------------
@dataclass
class ColumnScalingModel:
    """
    Model for storing column scaling factors for each axis.
    The scaling_factors dictionary maps:
    axis_name -> {column_name -> scale_factor}
    """
    scaling_factors: dict = field(
        default_factory=dict,
        metadata={"plot_types": ["cartesian", "histogram", "ternary"]}
    )
    
    def __post_init__(self):
        # Initialize with empty dictionaries for each axis
        if not self.scaling_factors:
            self.scaling_factors = {
                "x_axis": {}, "y_axis": {}, 
                "left_axis": {}, "right_axis": {}, "top_axis": {},
                "hover_data": {}
            }
    
    def get_scale(self, axis_name, column_name):
        """Get the scale factor for a column on an axis"""
        return self.scaling_factors.get(axis_name, {}).get(column_name, 1.0)
    
    def set_scale(self, axis_name, column_name, scale_factor):
        """Set the scale factor for a column on an axis"""
        if axis_name not in self.scaling_factors:
            self.scaling_factors[axis_name] = {}
        self.scaling_factors[axis_name][column_name] = scale_factor
    
    def clean_unused_scales(self, axis_name, valid_columns):
        """Remove scale factors for columns that are no longer selected"""
        if axis_name in self.scaling_factors:
            # Create a copy of keys to avoid modifying during iteration
            column_keys = list(self.scaling_factors[axis_name].keys())
            for column in column_keys:
                if column not in valid_columns:
                    del self.scaling_factors[axis_name][column]

@dataclass
class PlotLabelsModel:
    title: str = field(
        default="My Plot",
        metadata={"label": "Title:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    x_axis_label: str = field(
        default="X Axis",
        metadata={"label": "X Axis Label:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram"]}
    )
    y_axis_label: str = field(
        default="Y Axis",
        metadata={"label": "Y Axis Label:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram"]}
    )
    left_vertex_label: str = field(
        default="Left Vertex",
        metadata={"label": "Left Apex Display Name:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )
    right_vertex_label: str = field(
        default="Right Vertex",
        metadata={"label": "Right Apex Display Name:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )
    top_vertex_label: str = field(
        default="Top Vertex",
        metadata={"label": "Top Apex Display Name:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )

@dataclass
class AxisMembersModel:
    # Now each axis is a list (to allow multiple selections) and uses MultiFieldSelector.
    x_axis: list = field(default_factory=list, metadata={"label": "X Axis:", "widget": MultiFieldSelector, "plot_types": ["cartesian"]})
    y_axis: list = field(default_factory=list, metadata={"label": "Y Axis:", "widget": MultiFieldSelector, "plot_types": ["cartesian"]})
    left_axis: list = field(default_factory=list, metadata={"label": "Left Apex:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})
    right_axis: list = field(default_factory=list, metadata={"label": "Right Apex:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})
    top_axis: list = field(default_factory=list, metadata={"label": "Top Apex:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})
    hover_data: list = field(default_factory=list, metadata={"label": "Hover Data:", "widget": MultiFieldSelector, "plot_types": ["ternary", "cartesian"]})

@dataclass
class AdvancedPlotSettingsModel:
    background_color: str = field(
        default="#FFFFFF",
        metadata={"label": "Background Color:", "widget": ColorButton, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    paper_color: str = field(
        default="#FFFFFF",
        metadata={"label": "Paper Color:", "widget": ColorButton, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    line_width: float = field(
        default=1.0,
        metadata={"label": "Line Width:", "widget": QDoubleSpinBox, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    legend_position: str = field(
        default="top-right",
        metadata={"label": "Legend Position:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font_size: int = field(
        default=12,
        metadata={"label": "Font Size:", "widget": QDoubleSpinBox, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font: str = field(
        default="Arial",
        metadata={"label": "Font:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font_color: str = field(
        default="#000000",
        metadata={"label": "Font Color:", "widget": ColorButton, "plot_types": ["cartesian", "histogram", "ternary"]}
    )

@dataclass
class SetupMenuModel:
    data_library: DataLibraryModel = field(default_factory=DataLibraryModel)
    plot_labels: PlotLabelsModel = field(default_factory=PlotLabelsModel)
    axis_members: AxisMembersModel = field(default_factory=AxisMembersModel)
    column_scaling: ColumnScalingModel = field(default_factory=ColumnScalingModel)
    advanced_settings: AdvancedPlotSettingsModel = field(default_factory=AdvancedPlotSettingsModel)

    def to_dict(self):
        """Convert the model to a dictionary for serialization"""
        result = asdict(self)
        return result
    
    @classmethod
    def from_dict(cls, d: dict):
        """Create a model from a dictionary"""
        return cls(
            data_library=DataLibraryModel.from_dict(d.get("data_library", {})),
            plot_labels=PlotLabelsModel(**d.get("plot_labels", {})),
            axis_members=AxisMembersModel(**d.get("axis_members", {})),
            column_scaling=ColumnScalingModel(**d.get("column_scaling", {})),
            advanced_settings=AdvancedPlotSettingsModel(**d.get("advanced_settings", {}))
        )

# --------------------------------------------------------------------
# Setup Menu Controller
# --------------------------------------------------------------------
class SetupMenuController:
    """
    Controller for the Setup Menu. Recomputes the intersection of column names
    from loaded data files and updates the available options for axis member selectors.
    Uses DataframeManager to avoid repeated disk reads.
    """
    def __init__(self, model: SetupMenuModel, view: 'SetupMenuView'):
        self.model = model
        self.view = view

    def update_axis_options(self):
        """Recompute the intersection of column names from loaded data files and update selectors."""
        # Handle missing files
        file_path_mapping = validate_data_library(self.model.data_library, self.view)
        
        # If any file paths were updated, update the dataframes
        if file_path_mapping:
            self.model.data_library.update_file_paths(file_path_mapping)

        loaded_files = self.model.data_library.loaded_files
        print(f"Loaded files: {loaded_files}")
        
        common_columns = None
        for file_meta in loaded_files:
            # Get the dataframe using the dataframe manager
            df = self.model.data_library.dataframe_manager.get_dataframe_by_metadata(file_meta)
            if df is None:
                print(f"Warning: Could not get dataframe for {file_meta.file_path}")
                continue
                
            # Get columns from the dataframe
            cols = set(df.columns)
            print(f"Columns in {file_meta.file_path}: {cols}")
            
            if common_columns is None:
                common_columns = set(cols)
            else:
                common_columns = common_columns.intersection(cols)
        
        if common_columns is None:
            common_columns = set()
        
        common_list = sorted(common_columns)
        print(f"Common columns across all files: {common_list}")
        
        # Dictionary to track changes in each axis for later updating scaling widget
        axis_changes = {}
        
        axis_widgets = self.view.section_widgets.get("axis_members", {})
        for field_name, widget in axis_widgets.items():
            if isinstance(widget, MultiFieldSelector):
                print(f"Updating MultiFieldSelector for {field_name} with options: {common_list}")
                widget.set_available_options(common_list)
                selected = widget.get_selected_fields()
                print(f"Current selected fields: {selected}")
                valid = [s for s in selected if s in common_list]
                print(f"Valid selections: {valid}")
                
                # Track if selections changed
                axis_changes[field_name] = {
                    'previous': selected,
                    'current': valid
                }
                
                # Update the widget with valid selections
                widget.set_selected_fields(valid)
                
                # Update the model too (since this bypasses the widget's signals)
                setattr(self.model.axis_members, field_name, valid)
                
                # Clean up scaling factors for columns that are no longer valid
                self.model.column_scaling.clean_unused_scales(field_name, valid)
        
        # Update the column scaling widget to reflect the changes
        self.view.update_scaling_widget()

# --------------------------------------------------------------------
# Setup Menu View Updates
# --------------------------------------------------------------------
class SetupMenuView(QWidget):
    def __init__(self, model: SetupMenuModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # Default plot type; will be updated by the controller.
        self.controller = None  # Will be set later by the main window.
        self.section_widgets = {}  # To hold per‑section widget mappings keyed by model attribute name.
        
        # Wrap all contents in a scroll area for vertical scrolling.
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.scroll.setWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content.setLayout(self.content_layout)
        
        # Data Library Section
        self.dataLibraryWidget = QWidget(self)
        data_library_layout = QVBoxLayout(self.dataLibraryWidget)
        self.dataLibraryWidget.setLayout(data_library_layout)
        data_library_label = QLabel("Loaded Data:")
        data_library_layout.addWidget(data_library_label)
        self.dataLibraryList = QListWidget(self)
        data_library_layout.addWidget(self.dataLibraryList)
        btn_layout = QHBoxLayout()
        self.addDataButton = QPushButton("Add Data", self)
        self.removeDataButton = QPushButton("Remove Data", self)
        btn_layout.addWidget(self.addDataButton)
        btn_layout.addWidget(self.removeDataButton)
        data_library_layout.addLayout(btn_layout)
        self.addDataButton.clicked.connect(self.add_data_file)
        self.removeDataButton.clicked.connect(self.remove_data_file)
        self.content_layout.addWidget(self.dataLibraryWidget)
        
        # Plot Labels Section
        self.plotLabelsWidget = self.build_form_section(self.model.plot_labels, "plot_labels")
        self.content_layout.addWidget(self.plotLabelsWidget)
        
        # Axis Members Section
        self.axisMembersWidget = self.build_form_section(self.model.axis_members, "axis_members")
        self.content_layout.addWidget(self.axisMembersWidget)
        
        # Column Scaling Section - NEW
        self.columnScalingWidget = QWidget(self)
        column_scaling_layout = QVBoxLayout(self.columnScalingWidget)
        self.columnScalingWidget.setLayout(column_scaling_layout)
        self.scalingWidget = ColumnScalingWidget(self)
        column_scaling_layout.addWidget(self.scalingWidget)
        self.content_layout.addWidget(self.columnScalingWidget)
        
        # Connect scaling widget signals
        self.scalingWidget.scaleChanged.connect(self.on_scale_changed)
        
        # Advanced Settings Section
        self.advancedSettingsWidget = self.build_form_section(self.model.advanced_settings, "advanced_settings")
        self.content_layout.addWidget(self.advancedSettingsWidget)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.scroll)
        self.setLayout(outer_layout)

        # Initialize to default plot type
        self.set_plot_type(self.current_plot_type)
        
        # Update the column scaling widget with initial values
        self.update_scaling_widget()

    def set_controller(self, controller: SetupMenuController):
        self.controller = controller

    def build_form_section(self, section_model, model_attr_name):
        widget = QWidget(self)
        form_layout = QFormLayout(widget)
        widget.setLayout(form_layout)
        # Store the form layout so we can later access labels.
        if not hasattr(self, "section_form_layouts"):
            self.section_form_layouts = {}
        self.section_form_layouts[model_attr_name] = form_layout
        self.section_widgets[model_attr_name] = {}
        for f in fields(section_model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata or metadata["widget"] is None:
                continue
            widget_cls = metadata["widget"]
            label_text = metadata["label"]
            field_widget = widget_cls(self)
            value = getattr(section_model, f.name)
            if isinstance(field_widget, QLineEdit):
                field_widget.setText(str(value))
                field_widget.textChanged.connect(lambda text, fname=f.name, m=section_model: setattr(m, fname, text))
            elif isinstance(field_widget, ColorButton):
                field_widget.setColor(value)
                field_widget.colorChanged.connect(lambda color_str, fname=f.name, m=section_model: setattr(m, fname, color_str))
            elif isinstance(field_widget, QDoubleSpinBox):
                field_widget.setValue(float(value))
                field_widget.valueChanged.connect(lambda val, fname=f.name, m=section_model: setattr(m, fname, val))
            elif isinstance(field_widget, QCheckBox):
                field_widget.setChecked(bool(value))
                field_widget.stateChanged.connect(lambda state, fname=f.name, m=section_model: setattr(m, fname, bool(state)))
            elif isinstance(field_widget, QComboBox):
                field_widget.addItems([])
                field_widget.setCurrentText(str(value))
                field_widget.currentTextChanged.connect(lambda text, fname=f.name, m=section_model: setattr(m, fname, text))
            elif isinstance(field_widget, MultiFieldSelector):
                field_widget.set_selected_fields(value)
                # Connect selectionChanged to update the model and scaling widget
                field_widget.selectionChanged.connect(
                    lambda sel, fname=f.name, m=section_model: self.on_field_selection_changed(fname, sel, m)
                )
            form_layout.addRow(label_text, field_widget)
            self.section_widgets[model_attr_name][f.name] = field_widget
        return widget

    def on_field_selection_changed(self, field_name, selection, model):
        """Handle when a field selection changes in axis members"""
        # Update the model
        setattr(model, field_name, selection)
        
        # Clean up any scaling factors for columns no longer selected
        self.model.column_scaling.clean_unused_scales(field_name, selection)
        
        # Update the scaling widget for this axis
        self.update_scaling_widget_for_axis(field_name)
    
    def on_scale_changed(self, axis_name, column_name, scale_factor):
        """Handle when a scale factor is changed in the scaling widget"""
        self.model.column_scaling.set_scale(axis_name, column_name, scale_factor)
    
    def update_scaling_widget(self):
        """Update all axes in the scaling widget"""
        # Get all axis field names
        axis_fields = ["x_axis", "y_axis", "left_axis", "right_axis", "top_axis", "hover_data"]
        
        # Update each axis
        for field_name in axis_fields:
            self.update_scaling_widget_for_axis(field_name)
    
    def update_scaling_widget_for_axis(self, axis_name):
        """Update a single axis in the scaling widget"""
        # Get the selected columns for this axis
        axis_widget = self.section_widgets.get("axis_members", {}).get(axis_name)
        if isinstance(axis_widget, MultiFieldSelector):
            columns = axis_widget.get_selected_fields()
            
            # Get the current scale factors for this axis
            current_scales = self.model.column_scaling.scaling_factors.get(axis_name, {})
            
            # Update the scaling widget
            self.scalingWidget.update_columns(axis_name, columns, current_scales)

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            form_layout = self.section_form_layouts.get(section)
            for fname, field_widget in widgets.items():
                # Retrieve metadata for this field.
                metadata = None
                for f in fields(section_model):
                    if f.name == fname:
                        metadata = f.metadata
                        break
                if metadata is None:
                    continue
                show_field = "plot_types" in metadata and self.current_plot_type in metadata["plot_types"]
                if show_field:
                    field_widget.show()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.show()
                else:
                    field_widget.hide()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.hide()
        
        # Show/hide the column scaling widget based on plot type
        scaling_plot_types = ["cartesian", "histogram", "ternary"]
        if self.current_plot_type in scaling_plot_types:
            self.columnScalingWidget.show()
            # Update with the correct axes for this plot type
            self.update_scaling_widget()
        else:
            self.columnScalingWidget.hide()

    def add_data_file(self):
        """Modified add_data_file method to use DataframeManager"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", "Data Files (*.csv *.xlsx)")
        if file_path:
            metadata = None
            if file_path.endswith(".csv"):
                header, ok = HeaderSelectionDialog.getHeader(self, file_path)
                if not ok:
                    return  # User cancelled header selection
                metadata = DataFileMetadata(file_path=file_path, header_row=header)
            elif file_path.endswith(".xlsx"):
                # Assume get_sheet_names returns a list of sheet names
                sheets = get_sheet_names(file_path)
                if len(sheets) > 1:
                    sheet, ok = SheetSelectionDialog.getSheet(self, file_path, sheets)
                    if not ok:
                        return  # User cancelled sheet selection
                else:
                    sheet = sheets[0] if sheets else None
                header, ok = HeaderSelectionDialog.getHeader(self, file_path, sheet=sheet)
                if not ok:
                    return  # User cancelled header selection
                metadata = DataFileMetadata(file_path=file_path, header_row=header, sheet=sheet)
            else:
                # If not CSV or XLSX, simply create a metadata object with file_path
                metadata = DataFileMetadata(file_path=file_path)
            
            # Add the file to the data library using the new method
            if self.model.data_library.add_file(metadata):
                self.dataLibraryList.addItem(file_path)
                if self.controller:
                    self.controller.update_axis_options()
            else:
                QMessageBox.warning(self, "Error", f"Failed to load data from {file_path}")

    def remove_data_file(self):
        """Modified remove_data_file method to use DataframeManager"""
        current_item = self.dataLibraryList.currentItem()
        if current_item:
            file_path = current_item.text()
            
            # Check for dependent traces
            main_window = self.window()  # Retrieve the main window
            dependent_traces = []
            if hasattr(main_window, 'tabPanel'):
                # Iterate over all trace models stored in the tab panel
                for uid, model in main_window.tabPanel.id_to_widget.items():
                    if model is not None and isinstance(model, TraceEditorModel) and model.datafile.file_path == file_path:
                        dependent_traces.append((uid, model.trace_name))
            
            # If there are dependent traces, warn the user
            if dependent_traces:
                trace_names = ", ".join(name for uid, name in dependent_traces)
                msg = (f"The following traces depend on this datafile: {trace_names}.\n"
                    "Deleting the datafile will also remove these traces.\n"
                    "Do you want to continue?")
                reply = QMessageBox.question(self, "Confirm Removal", msg,
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return
                else:
                    # Remove each dependent trace silently
                    for uid, _ in dependent_traces:
                        main_window.tabPanel.remove_tab_by_id(uid)
            
            # Now remove the data file using the new method
            row = self.dataLibraryList.row(current_item)
            self.dataLibraryList.takeItem(row)
            self.model.remove_file(file_path)
            
            if self.controller:
                self.controller.update_axis_options()

    def update_from_model(self):
        # Update custom Data Library list.
        self.dataLibraryList.clear()
        for meta in self.model.data_library.loaded_files:
            self.dataLibraryList.addItem(meta.file_path)
        # Update each section built by build_form_section.
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            for fname, field_widget in widgets.items():
                for f in fields(section_model):
                    if f.name == fname:
                        value = getattr(section_model, fname)
                        if isinstance(field_widget, QLineEdit):
                            field_widget.setText(str(value))
                        elif isinstance(field_widget, QDoubleSpinBox):
                            field_widget.setValue(float(value))
                        elif isinstance(field_widget, QCheckBox):
                            field_widget.setChecked(bool(value))
                        elif isinstance(field_widget, QComboBox):
                            field_widget.setCurrentText(str(value))
                        elif isinstance(field_widget, MultiFieldSelector):
                            field_widget.set_selected_fields(value)
                        elif isinstance(field_widget, ColorButton):
                            field_widget.setColor(value)
                        break
        
        # Update the column scaling widget
        self.update_scaling_widget()


class WorkspaceManager:
    VERSION = "1.0"
    
    def __init__(self, traces: list, setup_model: SetupMenuModel, order=None):
        self.traces = traces
        self.setup_model = setup_model
        self.order = order if order is not None else [str(i) for i in range(len(traces))]
    
    def to_dict(self) -> dict:
        """
        Convert workspace to a dictionary, ensuring DataframeManager is not included.
        """
        # Make a clean copy of the setup model
        setup_dict = self.setup_model.to_dict()
        
        # Process traces: convert each trace model to dict and ensure datafiles are clean
        traces_dicts = []
        for trace in self.traces:
            trace_dict = trace.to_dict()
            # Ensure datafile in trace doesn't contain df_id
            if "datafile" in trace_dict and isinstance(trace_dict["datafile"], dict):
                if "df_id" in trace_dict["datafile"]:
                    trace_dict["datafile"].pop("df_id")
            traces_dicts.append(trace_dict)
        
        return {
            "version": self.VERSION,
            "order": self.order,
            "traces": traces_dicts,
            "setup": setup_dict
        }
    
    def save_to_file(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, d: dict):
        traces = [TraceEditorModel.from_dict(item) for item in d.get("traces", [])]
        setup = SetupMenuModel.from_dict(d.get("setup", {}))
        order = d.get("order", None)
        return cls(traces, setup, order=order)
    
    @classmethod
    def load_from_file(cls, filename: str):
        with open(filename, "r") as f:
            d = json.load(f)
        return cls.from_dict(d)
    
# --------------------------------------------------------------------
# MainWindow: Integrates TabPanel, CenterStack (for TraceEditor and SetupMenu), and Plot Window
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Ternaries")
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vlayout = QVBoxLayout(central_widget)
        main_vlayout.setContentsMargins(0, 0, 0, 0)

        top_banner = self._create_top_banner()
        main_vlayout.addWidget(top_banner)

        self.h_splitter = CustomSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(8)
        self.h_splitter.setStyleSheet("""
        QSplitter::handle {
            width: 5px;
            margin-left: 3px;
            margin-right: 3px;
        }
        """)
        main_vlayout.addWidget(self.h_splitter, 1)

        bottom_banner = self._create_bottom_banner()
        main_vlayout.addWidget(bottom_banner)

        # Left: TabPanel
        self.tabPanel = TabPanel()
        self.h_splitter.addWidget(self.tabPanel)

        # Center: QStackedWidget to hold both TraceEditorView and SetupMenuView.
        self.centerStack = QStackedWidget()
        
        # Instantiate the setup menu view.
        self.setupMenuModel = SetupMenuModel()
        self.setupMenuModel.data_library._dataframe_manager = DataframeManager()
        self.setupMenuView = SetupMenuView(self.setupMenuModel)
        self.centerStack.addWidget(self.setupMenuView)
        self.h_splitter.addWidget(self.centerStack)

        # Instantiate the trace editor view with an initial dummy model.
        self.current_trace_model = TraceEditorModel()
        self.traceEditorView = TraceEditorView(self.current_trace_model)
        self.traceEditorController = TraceEditorController(
            self.current_trace_model, 
            self.traceEditorView, 
            self.setupMenuModel.data_library)
        self.traceEditorView.traceNameChangedCallback = self.on_trace_name_changed
        self.centerStack.addWidget(self.traceEditorView)

        # Right: Plot Window (placeholder)
        self.plotView = QWebEngineView()
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")
        self.h_splitter.addWidget(self.plotView)

        # Connect TabPanel callbacks
        self.tabPanel.tabSelectedCallback = self.on_tab_selected
        self.tabPanel.tabRenamedCallback = self.on_tab_renamed
        self.tabPanel.tabRemovedCallback = self.on_tab_removed
        self.tabPanel.tabAddRequestedCallback = self.create_new_tab

        # Setup Menu special case
        self.setup_id = "setup-menu-id"
        self.tabPanel.id_to_widget[self.setup_id] = None
        
        self.current_tab_id = None

        # Start with Setup Menu selected.
        self.tabPanel.listWidget.setCurrentRow(0)
        self.current_tab_id = "setup-menu-id"
        self._show_setup_content()

        self.plotTypeSelector.currentTextChanged.connect(self.on_plot_type_changed)

        # Create and set up the Setup Menu Controller.
        self.setupController = SetupMenuController(self.setupMenuModel, self.setupMenuView)
        self.setupMenuView.set_controller(self.setupController)

    def _create_top_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        logo_label = QLabel("Quick Ternaries")
        logo_label.setStyleSheet("font-weight: bold; font-size: 16pt;")
        layout.addWidget(logo_label)
        layout.addStretch()
        self.plotTypeSelector = QComboBox()
        self.plotTypeSelector.addItems(["Ternary", "Cartesian", "Histogram"])
        layout.addWidget(self.plotTypeSelector)
        self.settingsButton = QPushButton("Settings")
        layout.addWidget(self.settingsButton)
        return container

    def _create_bottom_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        self.previewButton = QPushButton("Preview")
        self.saveButton = QPushButton("Save")
        self.loadButton = QPushButton("Load")  # New Load button added
        self.exportButton = QPushButton("Export")
        self.bootstrapButton = QPushButton("Bootstrap")
        layout.addWidget(self.previewButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.loadButton)
        layout.addWidget(self.exportButton)
        layout.addWidget(self.bootstrapButton)
        layout.addStretch()
        # Connect button signals
        self.saveButton.clicked.connect(self.save_workspace)
        self.loadButton.clicked.connect(self.load_workspace)
        self.bootstrapButton.clicked.connect(self.on_bootstrap_clicked)
        return container
    
    def on_bootstrap_clicked(self):

        new_label = 'Contour Test'
        model = TraceEditorModel(trace_name=new_label, is_contour=True)

        # Assign the first datafile from the library to the new trace
        if self.setupMenuModel.data_library.loaded_files:
            model.datafile = self.setupMenuModel.data_library.loaded_files[0]
        
        uid = self.tabPanel.add_tab(new_label, model)
        self._save_current_tab_data()
        self.current_tab_id = uid
        
        # Set the model
        self.traceEditorView.set_model(model)
        self.traceEditorController.model = model
        self._show_trace_editor()
        
        # Make sure datafile change handler is triggered to populate columns
        datafile = model.datafile
        if datafile:
            self.traceEditorController.on_datafile_changed(datafile)

    def on_tab_selected(self, unique_id: str):
        self._save_current_tab_data()
        self.current_tab_id = unique_id
        if unique_id == "setup-menu-id":
            self._show_setup_content()
        else:
            model = self.tabPanel.id_to_widget.get(unique_id)
            if isinstance(model, TraceEditorModel):
                self.traceEditorView.set_model(model)
                self._show_trace_editor()
            else:
                self.traceEditorView.set_model(TraceEditorModel())
                self._show_trace_editor()

    def on_tab_renamed(self, unique_id: str, new_label: str):
        if unique_id == "setup-menu-id":
            return
        model = self.tabPanel.id_to_widget.get(unique_id)
        if isinstance(model, TraceEditorModel):
            model.trace_name = new_label
        # Update the display text of the corresponding QListWidgetItem.
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if it and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                it.setText(new_label)
                break

    def on_tab_removed(self, unique_id: str):
        if unique_id == "setup-menu-id":
            return
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
        if unique_id == self.current_tab_id:
            self._save_current_tab_data()
            self.current_tab_id = "setup-menu-id"
            self.tabPanel.listWidget.setCurrentRow(0)
            self._show_setup_content()
        self.tabPanel.remove_tab_by_id(unique_id)

    def create_new_tab(self):
        # Check if any data files have been loaded.
        if not self.setupMenuModel.data_library.loaded_files:
            QMessageBox.warning(self, "Warning", "Please add data first")
            return

        new_trace_number = self._find_next_trace_number()
        new_label = f"Trace {new_trace_number}"
        model = TraceEditorModel(trace_name=new_label)
        
        # Assign the first datafile from the library to the new trace
        if self.setupMenuModel.data_library.loaded_files:
            model.datafile = self.setupMenuModel.data_library.loaded_files[0]
        
        uid = self.tabPanel.add_tab(new_label, model)
        self._save_current_tab_data()
        self.current_tab_id = uid
        
        # Set the model
        self.traceEditorView.set_model(model)
        self.traceEditorController.model = model
        self._show_trace_editor()
        
        # Make sure datafile change handler is triggered to populate columns
        datafile = model.datafile
        if datafile:
            self.traceEditorController.on_datafile_changed(datafile)

    def update_trace_datafile_options(self):
        # Get the list of loaded data files (DataFileMetadata objects)
        data_files = self.setupMenuModel.data_library.loaded_files
        combobox = self.traceEditorView.widgets.get("datafile")
        if combobox:
            # Save the current model value (if any)
            model_value = self.traceEditorView.model.datafile.file_path if self.traceEditorView.model.datafile else ""
            combobox.clear()
            # Add each file’s path as an option
            for meta in data_files:
                combobox.addItem(meta.file_path)
            # Set the combobox to the model’s file path if it exists among the loaded files
            if model_value and any(meta.file_path == model_value for meta in data_files):
                combobox.setCurrentText(model_value)
            elif data_files:
                # If no match, default to the first file in the list.
                combobox.setCurrentText(data_files[0].file_path)
                # Also update the trace model with the corresponding metadata.
                self.traceEditorView.model.datafile = data_files[0]


    def _find_next_trace_number(self) -> int:
        pattern = re.compile(r"^Trace\s+(\d+)$")
        largest_number = 0
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if not it:
                continue
            text = it.text()
            match = pattern.match(text)
            if match:
                num = int(match.group(1))
                if num > largest_number:
                    largest_number = num
        return largest_number + 1

    def _save_current_tab_data(self):
        pass

    def _show_setup_content(self):
        self.centerStack.setCurrentWidget(self.setupMenuView)
        self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")

    def _show_trace_editor(self):
        self.centerStack.setCurrentWidget(self.traceEditorView)
        
        # Save the original model values before any updates
        model = self.traceEditorView.model
        original_heatmap_column = model.heatmap_column
        original_sizemap_column = model.sizemap_column
        
        # Block ALL signals during UI update
        for widget_name, widget in self.traceEditorView.widgets.items():
            if hasattr(widget, 'blockSignals'):
                widget.blockSignals(True)
        
        # Update the datafile combobox options
        self.update_trace_datafile_options()
        
        # Process numeric columns for the current datafile
        datafile = model.datafile
        if datafile and datafile.file_path:
            numeric_cols = get_numeric_columns_from_file(
                datafile.file_path,
                header=datafile.header_row,
                sheet=datafile.sheet
            )
            
            # Directly update the comboboxes without triggering signals
            heatmap_combo = self.traceEditorView.widgets.get("heatmap_column")
            if heatmap_combo:
                heatmap_combo.clear()
                heatmap_combo.addItems(numeric_cols)
                # Add the original value if it's not in the list
                if original_heatmap_column and original_heatmap_column not in numeric_cols:
                    heatmap_combo.addItem(original_heatmap_column)
                # Now set the combobox value to match the model
                heatmap_combo.setCurrentText(original_heatmap_column)
                
            sizemap_combo = self.traceEditorView.widgets.get("sizemap_column")
            if sizemap_combo:
                sizemap_combo.clear()
                sizemap_combo.addItems(numeric_cols)
                # Add the original value if it's not in the list
                if original_sizemap_column and original_sizemap_column not in numeric_cols:
                    sizemap_combo.addItem(original_sizemap_column)
                # Now set the combobox value to match the model
                sizemap_combo.setCurrentText(original_sizemap_column)
        
        # Unblock signals after all updates are done
        for widget_name, widget in self.traceEditorView.widgets.items():
            if hasattr(widget, 'blockSignals'):
                widget.blockSignals(False)
        
        # Make sure the model still has the original values
        # This is a safeguard in case any signals still fired
        model.heatmap_column = original_heatmap_column
        model.sizemap_column = original_sizemap_column
        
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")

    def on_plot_type_changed(self, plot_type: str):
        plot_type_lower = plot_type.lower()
        self.traceEditorView.set_plot_type(plot_type_lower)
        self.setupMenuView.set_plot_type(plot_type_lower)

    def save_workspace(self):
        """
        Create a serializable representation of the workspace without using deep copying,
        which can preserve references to DataframeManager.
        """
        # Create new, clean dictionaries instead of copying objects
        traces_data = []
        order = []
        
        # Gather trace information
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                order.append(uid)
                model = self.tabPanel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel):
                    # Manually create a clean representation of the trace
                    trace_data = {}
                    for f in fields(model):
                        if f.name == 'datafile':
                            # Manually extract datafile metadata without df_id
                            datafile = getattr(model, f.name)
                            trace_data['datafile'] = {
                                'file_path': datafile.file_path,
                                'header_row': datafile.header_row,
                                'sheet': datafile.sheet
                            }
                        elif f.name == 'filters':
                            # Handle filters list
                            filters = getattr(model, f.name)
                            filters_data = []
                            for filter_model in filters:
                                filter_data = {}
                                for filter_field in fields(filter_model):
                                    filter_data[filter_field.name] = getattr(filter_model, filter_field.name)
                                filters_data.append(filter_data)
                            trace_data[f.name] = filters_data
                        else:
                            # Copy other fields directly
                            trace_data[f.name] = getattr(model, f.name)
                    traces_data.append(trace_data)
        
        # Create the setup model data manually
        setup_data = {'data_library': {}, 'plot_labels': {}, 'axis_members': {}, 'advanced_settings': {}}
        
        # Process data_library
        setup_data['data_library']['loaded_files'] = []
        for metadata in self.setupMenuModel.data_library.loaded_files:
            # Only include essentials, no df_id
            setup_data['data_library']['loaded_files'].append({
                'file_path': metadata.file_path,
                'header_row': metadata.header_row,
                'sheet': metadata.sheet
            })
        
        # Process other setup sections
        for section_name in ['plot_labels', 'axis_members', 'advanced_settings']:
            section = getattr(self.setupMenuModel, section_name)
            for f in fields(section):
                setup_data[section_name][f.name] = getattr(section, f.name)
        
        # Build the complete workspace data
        workspace_data = {
            'version': WorkspaceManager.VERSION,
            'order': order,
            'traces': traces_data,
            'setup': setup_data
        }
        
        # Save to file
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workspace", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, "w") as f:
                    json.dump(workspace_data, f, indent=2)
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Failed to save workspace: {str(e)}")

    def load_workspace(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Workspace", "", "JSON Files (*.json)")
        if filename:
            try:
                print(f"Loading workspace from {filename}")
                
                workspace = WorkspaceManager.load_from_file(filename)

                # Validate data files and get mapping for any relocated files
                file_path_mapping = validate_data_library(workspace.setup_model.data_library, self)
                
                # Update all trace models with the new file paths
                for trace_model in workspace.traces:
                    if hasattr(trace_model, "datafile") and isinstance(trace_model.datafile, DataFileMetadata):
                        old_path = trace_model.datafile.file_path
                        if old_path in file_path_mapping:
                            # Update the datafile with the new path
                            new_path = file_path_mapping[old_path]
                            trace_model.datafile = DataFileMetadata(
                                file_path=new_path,
                                header_row=trace_model.datafile.header_row,
                                sheet=trace_model.datafile.sheet
                            )
                
                # Update the SetupMenu model and ensure it has a DataframeManager
                self.setupMenuModel = workspace.setup_model
                if not hasattr(self.setupMenuModel.data_library, '_dataframe_manager') or self.setupMenuModel.data_library._dataframe_manager is None:
                    self.setupMenuModel.data_library._dataframe_manager = DataframeManager()
                    
                # Load all dataframes into memory
                for metadata in self.setupMenuModel.data_library.loaded_files:
                    # Load the dataframe
                    df_id = self.setupMenuModel.data_library.dataframe_manager.load_dataframe(metadata)
                    if df_id:
                        metadata.df_id = df_id
                    else:
                        print(f"Warning: Failed to load dataframe for {metadata.file_path}")
                
                # Refresh the setup menu view
                self.setupMenuView.model = self.setupMenuModel
                self.setupMenuView.update_from_model()
                self.setupMenuView.set_plot_type(self.setupMenuView.current_plot_type)
                
                # Reinitialize the controller with the new model
                self.setupController = SetupMenuController(self.setupMenuModel, self.setupMenuView)
                self.setupMenuView.set_controller(self.setupController)
                
                # IMPORTANT: Force update of the axis options after loading
                self.setupController.update_axis_options()
                
                # Clear existing trace tabs (except the setup-menu)
                keys_to_remove = [uid for uid in self.tabPanel.id_to_widget if uid != "setup-menu-id"]
                for uid in keys_to_remove:
                    self.tabPanel.remove_tab_by_id(uid)
                    
                # Add each loaded trace to the TabPanel
                trace_ids = []
                for trace_model in workspace.traces:
                    uid = self.tabPanel.add_tab(trace_model.trace_name, trace_model)
                    trace_ids.append((uid, trace_model))
                
                # IMPORTANT: Force content update before changing tab selection
                self.centerStack.setCurrentWidget(self.setupMenuView)
                self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")
                
                # Now safe to update current tab state
                self.current_tab_id = "setup-menu-id"
                
                # Select the Setup Menu tab
                self.tabPanel.listWidget.setCurrentRow(0)
                
                # Process events to ensure UI is fully updated
                QApplication.processEvents()
                
                # Little bit redundant...
                self.tabPanel.listWidget.setCurrentRow(0)
                self.tabPanel.select_tab_by_id('setup-menu-id')
                self.tabPanel.tabSelectedCallback('setup-menu-id')
                QApplication.processEvents()
                print("Workspace loading complete.")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"Failed to load workspace: {str(e)}")

    def _fix_combobox_model_sync(self, combo_name, model_field_name):
        """Make sure the combobox and model value stay in sync."""
        combo = self.traceEditorView.widgets.get(combo_name)
        if combo and hasattr(self.traceEditorView.model, model_field_name):
            model_value = getattr(self.traceEditorView.model, model_field_name)
            
            # Force the model value into the combobox options
            if model_value and combo.findText(model_value) == -1:
                combo.addItem(model_value)
                
            # Set the combobox to the model value
            combo.setCurrentText(model_value)



    def on_trace_name_changed(self, new_name: str):
        # Update the display text of the currently selected tab in the sidebar.
        uid = self.current_tab_id
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == uid:
                item.setText(new_name)
                break


# --------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
