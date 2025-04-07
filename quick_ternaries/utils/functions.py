import os
from dataclasses import is_dataclass, asdict
from typing import TYPE_CHECKING

import pandas as pd
import numpy as np
from molmass import Formula
from PySide6.QtWidgets import QMessageBox, QFileDialog

from quick_ternaries.models.data_file_metadata_model import DataFileMetadata

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget
    from quick_ternaries.models.data_library_model import DataLibraryModel

def is_valid_formula(formula: str) -> bool:
    """
    Checks if the provided chemical formula is valid by attempting to compute its molar mass using molmass.
    
    Parameters:
        formula (str): The chemical formula to validate.
    
    Returns:
        bool: True if the formula is valid and a molar mass can be computed, False otherwise.
    """
    try:
        # Create a Formula object which computes properties including molar mass.
        f = Formula(formula)
        # Optionally, check that the computed molar mass is positive.
        return f.mass > 0
    except Exception:
        return False
    
def recursive_to_dict(obj):
    """Recursively convert dataclass objects (or lists/dicts) to
    dictionaries."""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, list):
        return [recursive_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: recursive_to_dict(v) for k, v in obj.items()}
    else:
        return obj
    
# def canonical_category(x):
#     """
#     Convert a cell to a canonical category: either 'numeric', 'string', or 'nan'.
#     This helps standardize type inference between Excel and CSV.
#     """
#     try:
#         if pd.isna(x):
#             return "nan"
#         # Try to convert to float. If it works, consider the value numeric.
#         float(x)
#         return "numeric"
#     except Exception:
#         return "string"


# def find_header_row_excel(file, max_rows_scan, sheet_name):
#     """Returns the 'best' header row for an Excel file."""
#     min_score = float("inf")
#     best_header_row = None

#     try:
#         # Read the full sheet to know how many rows there are
#         df = pd.read_excel(file, sheet_name=sheet_name)
#     except FileNotFoundError as err:
#         print(err)
#         return None

#     n_rows_search = min(len(df), max_rows_scan)

#     for i in range(n_rows_search):
#         try:
#             # Read candidate header with nrows to compute a score
#             df_candidate = pd.read_excel(
#                 file, sheet_name=sheet_name, header=i, nrows=n_rows_search + 1
#             )
#         except Exception as e:
#             print(f"Error reading excel file with header {i}: {e}")
#             continue

#         columns = df_candidate.columns.tolist()
#         num_unnamed = sum("unnamed" in str(name).lower() for name in columns)
#         num_unique = len(set(columns))
#         # For each column, check if all values in the column (in the preview) are of the same type.
#         type_consistency = sum(
#             df_candidate[col].apply(type).nunique() == 1 for col in df_candidate.columns
#         )

#         total_score = num_unnamed - num_unique - type_consistency

#         if total_score < min_score:
#             min_score = total_score
#             best_header_row = i

#     return best_header_row

def find_header_row_excel(file, max_rows_scan=10, sheet_name='Sheet1'):
    """
    Returns the most likely header row for an Excel file.
    
    The function reads the Excel sheet without a header, preserving the original data layout.
    It considers each row (up to max_rows_scan) as a potential header and computes a score based on:
    
      - Duplicate count: Calculated as the total number of entries minus the number of unique entries.
      - Type consistency: For each column, it checks whether all values (in the rows following the candidate header)
        share the same type. A consistent column is scored as 1.
    
    The score for a candidate header is given by:
    
        score = duplicate_count - type_consistency
        
    Lower scores indicate a better candidate header.
    
    Parameters:
        file (str): Path to the Excel file.
        max_rows_scan (int): Maximum number of rows to consider as header candidates.
        sheet_name (str): Name of the sheet to process.
        
    Returns:
        int or None: The index of the best header row, or None if an error occurs.
    """
    try:
        # Read the entire sheet without a header
        df = pd.read_excel(file, sheet_name=sheet_name, header=None)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    best_score = float("inf")
    best_candidate = None
    num_rows = len(df)
    max_candidates = min(max_rows_scan, num_rows)
    
    for i in range(max_candidates):
        # Candidate header row as a list
        candidate_header = df.iloc[i].tolist()
        # Compute the duplicate count (raw count of duplicates)
        duplicate_count = len(candidate_header) - len(set(candidate_header))
        
        # Evaluate type consistency for each column using all rows following the candidate header
        type_consistency = 0
        for col_idx in range(len(candidate_header)):
            col_data = df.iloc[i+1:, col_idx] if i+1 < num_rows else pd.Series()
            if not col_data.empty:
                # Count the column as consistent if all values have the same type
                if col_data.apply(type).nunique() == 1:
                    type_consistency += 1
        
        # Calculate the overall score: lower is better
        score = duplicate_count - type_consistency
        
        print(f"Row {i}: candidate header: {candidate_header}")
        print(f"    Duplicate count: {duplicate_count}, Type consistency: {type_consistency}, Score: {score}")
        
        if score < best_score:
            best_score = score
            best_candidate = i

    return best_candidate


# def find_header_row_csv(file, max_rows_scan):
#     """Returns the 'best' header row for a CSV file."""
#     min_score = float("inf")
#     best_header_row = None

#     try:
#         df = pd.read_csv(file)
#     except FileNotFoundError as err:
#         print(err)
#         return None

#     n_rows_search = min(len(df), max_rows_scan)

#     for i in range(n_rows_search):
#         try:
#             df_candidate = pd.read_csv(file, header=i, nrows=n_rows_search + 1)
#         except Exception as e:
#             print(f"Error reading CSV file with header {i}: {e}")
#             continue

#         columns = df_candidate.columns.tolist()
#         num_unnamed = sum("unnamed" in str(name).lower() for name in columns)
#         num_unique = len(set(columns))
#         type_consistency = sum(
#             df_candidate[col].apply(type).nunique() == 1 for col in df_candidate.columns
#         )

#         total_score = num_unnamed - num_unique - type_consistency

#         if total_score < min_score:
#             min_score = total_score
#             best_header_row = i

#     return best_header_row

def find_header_row_csv(file, max_rows_scan=16):
    """
    Returns the most likely header row for a CSV file.
    
    The function reads the CSV file without a header and considers each row (up to max_rows_scan)
    as a potential header row. It calculates a score based on two metrics:
    
      - Duplicate Count: How many duplicate entries exist in the candidate header.
      - Type Consistency: For each column, whether the data in the rows following the candidate header
        have consistent types (i.e., all values in the column share the same type).
    
    A lower score suggests a better candidate.
    
    Parameters:
        file (str): Path to the CSV file.
        max_rows_scan (int): Maximum number of rows to consider as header candidates.
        
    Returns:
        int or None: The index of the best header row, or None if an error occurs.
    """
    try:
        # Read the CSV file with no header to preserve the original data layout.
        df = pd.read_csv(file, header=None)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

    best_score = float("inf")
    best_candidate = None
    num_rows = len(df)
    max_candidates = min(max_rows_scan, num_rows)
    
    for i in range(max_candidates):
        # Use the candidate row as the header
        candidate_header = df.iloc[i].tolist()
        # Calculate the duplicate count (raw duplicates, not the auto-renamed ones)
        duplicate_count = len(candidate_header) - len(set(candidate_header))
        
        # Check type consistency in each column using all rows after the candidate header.
        type_consistency = 0
        for col in range(len(candidate_header)):
            # Get all data for this column after the candidate header row.
            col_data = df.iloc[i+1:, col] if i+1 < num_rows else pd.Series()
            if not col_data.empty:
                # If all values in the column share the same type, count this column as consistent.
                if col_data.apply(type).nunique() == 1:
                    type_consistency += 1
        
        # The scoring formula is a heuristic: lower scores are better.
        score = duplicate_count - type_consistency
        
        print(f"Row {i}: candidate header: {candidate_header}")
        print(f"    Duplicate count: {duplicate_count}, Type consistency: {type_consistency}, Score: {score}")
        
        if score < best_score:
            best_score = score
            best_candidate = i

    return best_candidate


def get_sheet_names(file_path):
    """Returns a list of sheet names for an Excel file.

    If the file is not an Excel file, returns an empty list.
    """
    try:
        if file_path.lower().endswith((".xls", ".xlsx")):
            xls = pd.ExcelFile(file_path)
            return xls.sheet_names
        else:
            return []
    except Exception as e:
        print(f"Error in get_sheet_names: {str(e)}")
        return []


def get_suggested_header(file_path, sheet=None, max_rows_scan=24):
    """Returns the suggested header row index for the file.

    For CSV files, calls find_header_row_csv. For Excel files, calls
    find_header_row_excel using the specified sheet (or the first sheet if none
    is provided).
    """
    if file_path.lower().endswith(".csv"):
        return find_header_row_csv(file_path, max_rows_scan)
    elif file_path.lower().endswith((".xls", ".xlsx")):
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
    """Returns a set of column names from a dataframe.

    Args:
        df: pandas DataFrame

    Returns:
        set: Column names
    """
    if df is None:
        return set()
    return set(df.columns)


def get_numeric_columns_from_dataframe(df):
    """Returns a list of numeric column names from a dataframe.

    Args:
        df: pandas DataFrame

    Returns:
        list: Numeric column names
    """
    if df is None:
        return []
    return df.select_dtypes(include=["number"]).columns.tolist()


def get_all_columns_from_dataframe(df):
    """Returns all column names from a dataframe as a list.

    Args:
        df: pandas DataFrame

    Returns:
        list: Column names
    """
    if df is None:
        return []
    return df.columns.tolist()


def get_sorted_unique_values_from_dataframe(df, column=None):
    """Returns a sorted list of unique (non-null) values from the specified
    column.

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
    """Determines whether the specified column in the dataframe is numeric.

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
    """Returns a list of lists containing the first n_rows of the dataframe.

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


def get_numeric_columns_from_file(
    data_source, header=None, sheet=None, dataframe_manager=None
):
    """Returns a list of numeric column names.

    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, "file_path") and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_numeric_columns_from_dataframe(df)

    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith(".csv"):
            if header is not None:
                df = pd.read_csv(file_path, header=header, nrows=10)
            else:
                df = pd.read_csv(file_path, nrows=10)
        elif file_path.lower().endswith((".xls", ".xlsx")):
            if header is not None:
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, nrows=10)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=10)
        else:
            return []
        return df.select_dtypes(include=["number"]).columns.tolist()
    return []


def get_all_columns_from_file(
    data_source, header=None, sheet=None, dataframe_manager=None
):
    """Returns all column names as a list.

    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, "file_path") and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_all_columns_from_dataframe(df)

    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith(".csv"):
            if header is not None:
                df = pd.read_csv(file_path, header=header, nrows=0)
            else:
                df = pd.read_csv(file_path, nrows=0)
        elif file_path.lower().endswith((".xls", ".xlsx")):
            if header is not None:
                df = pd.read_excel(file_path, header=header, sheet_name=sheet, nrows=0)
            else:
                df = pd.read_excel(file_path, sheet_name=sheet, nrows=0)
        else:
            return []
        return df.columns.tolist()
    return []


def get_sorted_unique_values(
    data_source, header=None, sheet=None, column=None, dataframe_manager=None
):
    """Returns a sorted list of unique values from the specified column.

    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, "file_path") and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_sorted_unique_values_from_dataframe(df, column)

    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str) and column:
        file_path = data_source
        try:
            if file_path.lower().endswith(".csv"):
                df = pd.read_csv(file_path, header=header, usecols=[column])
            elif file_path.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(
                    file_path, header=header, sheet_name=sheet, usecols=[column]
                )
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


def is_numeric_column(
    data_source, header=None, sheet=None, column=None, dataframe_manager=None
):
    """Determines whether the specified column is numeric.

    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, "file_path") and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return is_numeric_column_in_dataframe(df, column)

    # Fall back to original implementation
    if not column:
        return False
    # get_numeric_columns_from_file is assumed to be available per your utility functions.
    numeric_columns = get_numeric_columns_from_file(data_source, header, sheet)
    return column in numeric_columns


def get_preview_data(data_source, sheet=None, n_rows=24, dataframe_manager=None):
    """Returns a list of lists containing the first n_rows of the file.

    Compatible with old API but prefers using dataframe_manager if available.
    """
    # If data_source is DataFileMetadata and dataframe_manager is provided, use cached DataFrame
    if hasattr(data_source, "file_path") and dataframe_manager is not None:
        df = dataframe_manager.get_dataframe_by_metadata(data_source)
        return get_preview_data_from_dataframe(df, n_rows)

    # Fall back to original implementation for backwards compatibility
    if isinstance(data_source, str):
        file_path = data_source
        if file_path.lower().endswith(".csv"):
            # Use header=None so all rows are treated as data
            df = pd.read_csv(file_path, header=None, nrows=n_rows)
        elif file_path.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(file_path, header=None, sheet_name=sheet, nrows=n_rows)
        else:
            return []
        return df.values.tolist()
    return []


def validate_data_library(data_library: "DataLibraryModel", parent: "QWidget"):
    """Iterates over each DataFileMetadata in the library. If the file does not
    exist, prompts the user to locate the file. Updates the metadata in place.

    Returns:
        dict: A mapping from old file paths to new file paths for any files that were updated.
    """
    file_path_mapping = {}  # Map from old paths to new paths

    total_files = len(data_library.loaded_files)
    for idx, meta in enumerate(data_library.loaded_files):
        if not os.path.exists(meta.file_path):
            msg = f"[Loading file {idx+1}/{total_files}]\n\nFile not found: {meta.file_path}\n\nPlease locate the missing file."
            QMessageBox.warning(parent, "Missing Data File", msg)
            new_path, _ = QFileDialog.getOpenFileName(
                parent, "Locate Missing Data File", "", "Data Files (*.csv *.xlsx)"
            )
            if new_path:
                # Create a new metadata object preserving the header and sheet settings.
                old_path = meta.file_path
                new_meta = DataFileMetadata(
                    file_path=new_path, header_row=meta.header_row, sheet=meta.sheet
                )
                data_library.loaded_files[idx] = new_meta
                file_path_mapping[old_path] = new_path
            else:
                # Might want to remove the missing file from the library?
                pass

    return file_path_mapping


def suggest_formula_from_column_name(column_name):
    """Suggest a chemical formula based on a column name.
    
    This function tries to extract a chemical formula from a column name
    using heuristics. Returns an empty string if no formula can be suggested.
    """
    # Strip common suffixes that might be in column names
    suffixes = ["_wt", "_fixed", "_value", "_percent", "_pct", "_normalized", "_norm"]
    cleaned_name = column_name
    for suffix in suffixes:
        if cleaned_name.lower().endswith(suffix.lower()):
            cleaned_name = cleaned_name[:-len(suffix)]
    
    # Check if the cleaned name is already a valid formula
    if is_valid_formula(cleaned_name):
        return cleaned_name
    
    # Try to extract common oxide patterns
    common_oxides = {
        "al2o3": "Al2O3",
        "sio2": "SiO2", 
        "cao": "CaO",
        "mgo": "MgO",
        "na2o": "Na2O",
        "k2o": "K2O",
        "fe2o3": "Fe2O3",
        "feo": "FeO",
        "tio2": "TiO2",
        "p2o5": "P2O5",
        "mno": "MnO",
        "cr2o3": "Cr2O3"
    }
    
    # Check if cleaned_name matches any common oxide pattern (case insensitive)
    for pattern, formula in common_oxides.items():
        if pattern.lower() in cleaned_name.lower():
            return formula
    
    # If no match found, return empty string
    return ""


def util_convert_hex_to_rgba(hex_color: str) -> str:
    """
    Convert a hex color string to rgba format.
    Handles hex formats: #RGB, #RGBA, #RRGGBB, #AARRGGBB
    
    Args:
        hex_color: Hex color string
        
    Returns:
        rgba color string
    """
    # Remove # if present
    has_hash = hex_color.startswith('#')
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
    
    # elif len(hex_color) == 4:  # #RGBA format
    #     r = int(hex_color[0] + hex_color[0], 16)
    #     g = int(hex_color[1] + hex_color[1], 16)
    #     b = int(hex_color[2] + hex_color[2], 16)
    #     a = int(hex_color[3] + hex_color[3], 16) / 255
    #     return f"rgba({r}, {g}, {b}, {a})"
    
    # elif len(hex_color) == 3:  # #RGB format
    #     r = int(hex_color[0] + hex_color[0], 16)
    #     g = int(hex_color[1] + hex_color[1], 16)
    #     b = int(hex_color[2] + hex_color[2], 16)
    #     return f"rgba({r}, {g}, {b}, 1)"
    
    else:
        # If the format is not recognized, return the original color
        ret = f"{hex_color}"
        if has_hash:
            return '#' + ret
        else:
            return ret
        
def format_scale_factor(scale_factor: float) -> str:
    """
    Format a scale factor for display in hover text, handling precision appropriately.
    
    Args:
        scale_factor: The scale factor value
        
    Returns:
        Formatted scale factor as a string
    """
    # Handle precision issues by rounding first
    rounded = round(scale_factor, 4)
    
    # For whole numbers (1, 2, 3, etc.), don't show decimal places
    if rounded == int(rounded):
        return f"{int(rounded)}"
    
    # For numbers with decimal portion, show appropriate precision
    # If it only needs 1 decimal place (e.g., 2.5)
    if rounded == round(rounded, 1):
        return f"{rounded:.1f}"
    
    # If it needs 2 decimal places (e.g., 2.25)
    if rounded == round(rounded, 2):
        return f"{rounded:.2f}"
    
    # Default to 3 decimal places for more precise values
    return f"{rounded:.3f}"
