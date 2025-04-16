import sys
import os
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Add the project root to the Python path so we can import the project modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Mock QApplication for tests that require GUI components
@pytest.fixture
def qt_app_mock():
    """Mock for QApplication to avoid needing actual GUI for tests."""
    with patch('PySide6.QtWidgets.QApplication') as mock:
        mock.instance.return_value = mock
        yield mock

# Create a sample DataFrame for testing
@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50],
        'C': [100, 200, 300, 400, 500],
        'Category': ['X', 'Y', 'X', 'Z', 'Y']
    })

# Create a sample Excel file for testing
@pytest.fixture(scope="session")
def sample_excel_file(tmp_path_factory):
    """Create a temporary Excel file for testing file loading.
    
    Sheet name is set to "sheet_1"
    """
    tmp_dir = tmp_path_factory.mktemp("data")
    file_path = os.path.join(tmp_dir, "test_data.xlsx")
    
    # Create a DataFrame and save it to Excel
    df = pd.DataFrame({
        'SiO2': [72.0, 68.5, 76.2],
        'Al2O3': [14.2, 15.8, 12.5],
        'FeOt': [3.5, 4.2, 2.8],
        'CaO': [1.8, 2.2, 1.2],
        'MgO': [0.8, 1.5, 0.5],
        'Na2O': [3.2, 3.8, 3.6],
        'K2O': [4.5, 3.9, 5.2],
        'Sample': ['Sample1', 'Sample2', 'Sample3']
    })
    
    df.to_excel(file_path, index=False, header=True, sheet_name='sheet_1')
    
    return file_path


# Create a sample Excel file with intended header=1 for testing
@pytest.fixture(scope="session")
def sample_excel_file_header_1(tmp_path_factory):
    """Create a temporary Excel file for testing file loading.
    
    Sheet name is set to "sheet_1"
    """
    tmp_dir = tmp_path_factory.mktemp("data")
    file_path = os.path.join(tmp_dir, "test_data.xlsx")
    
    # Each inner list is a row. Row 0 has duplicate values.
    rows = [
        ["meta", "comp", "comp", "comp", "comp"],
        ["Sample", "SiO2", "FeOT", "Na2O", "MgO"],
        ["name1", 1.5, 2.5, 3.5, 12.1],
        ["name2", 1.3, 1.4, 1.6, 11.1],
        ["name3", 1.2, 2.1, 1.7, 10.1]
    ]
    
    # Create a DataFrame from the list of rows.
    df = pd.DataFrame(rows)
    
    df.to_excel(file_path, index=False, header=True, sheet_name='sheet_1')
    
    return file_path

@pytest.fixture
def sample_excel_file_multi_sheet(tmp_path):
    """
    Create a temporary Excel file with multiple sheets.
    
    This file will have two sheets: "Sheet1" and "Sheet2".
    Returns the file path as a string.
    """
    file_path = tmp_path / "test_data_multi.xlsx"
    
    # Create sample data for each sheet.
    df1 = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [4, 5, 6]
    })
    df2 = pd.DataFrame({
        'X': ['a', 'b', 'c'],
        'Y': ['d', 'e', 'f']
    })
    
    # Write to Excel with multiple sheets using openpyxl.
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="Sheet1", index=False)
        df2.to_excel(writer, sheet_name="Sheet2", index=False)
    
    # Return the file path as a string.
    return str(file_path)



# Fixture for the standard Excel file (with normal header row)
@pytest.fixture
def hardcopy_excel_standard():
    """Return the file path for the standard Excel file with header in the first row."""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "data", "test_data_standard.xlsx")
    return file_path

# Fixture for the Excel file where the intended header is on row 1 (i.e. second row)
@pytest.fixture
def hardcopy_excel_header1():
    """Return the file path for the Excel file with intended header row at index 1."""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "data", "test_data_header1.xlsx")
    return file_path

# Fixture for the standard CSV file (with normal header row)
@pytest.fixture
def hardcopy_csv_standard():
    """Return the file path for the standard CSV file with header in the first row."""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "data", "test_data_standard.csv")
    return file_path

# Fixture for the CSV file where the intended header is on row 1
@pytest.fixture
def hardcopy_csv_header1():
    """Return the file path for the CSV file with intended header row at index 1."""
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, "data", "test_data_header1.csv")
    return file_path




# Create a sample CSV file for testing
@pytest.fixture(scope="session")
def sample_csv_file(tmp_path_factory):
    """Create a temporary CSV file for testing file loading."""
    tmp_dir = tmp_path_factory.mktemp("data")
    file_path = os.path.join(tmp_dir, "test_data.csv")
    
    # Create a DataFrame and save it to CSV
    df = pd.DataFrame({
        'SiO2': [72.0, 68.5, 76.2],
        'Al2O3': [14.2, 15.8, 12.5],
        'FeOt': [3.5, 4.2, 2.8],
        'CaO': [1.8, 2.2, 1.2],
        'MgO': [0.8, 1.5, 0.5],
        'Na2O': [3.2, 3.8, 3.6],
        'K2O': [4.5, 3.9, 5.2],
        'Sample': ['Sample1', 'Sample2', 'Sample3']
    })
    
    df.to_csv(file_path, index=False)

    return file_path

# Create a sample CSV file for testing with header=1
@pytest.fixture(scope="session")
def sample_csv_file_header_1(tmp_path_factory):
    """Create a temporary CSV file with duplicate header values."""
    tmp_dir = tmp_path_factory.mktemp("data")
    file_path = os.path.join(tmp_dir, "test_data_complex.csv")
    
    # Each inner list is a row. Row 0 has duplicate values.
    rows = [
        ["meta", "comp", "comp", "comp", "comp"],
        ["Sample", "SiO2", "FeOT", "Na2O", "MgO"],
        ["name1", 1.5, 2.5, 3.5, 12.1],
        ["name2", 1.3, 1.4, 1.6, 11.1],
        ["name3", 1.2, 2.1, 1.7, 10.1]
    ]
    
    # Create a DataFrame from the list of rows.
    df = pd.DataFrame(rows)
    # Write the file without an extra header or index.
    df.to_csv(file_path, index=False, header=True)
    
    return file_path

# Mock for DataframeManager
@pytest.fixture
def mock_dataframe_manager():
    """Create a mock for the DataframeManager."""
    mock = MagicMock()
    
    # Configure the mock to return a DataFrame when get_dataframe_by_metadata is called
    def get_dataframe_side_effect(metadata):
        if metadata and hasattr(metadata, 'file_path'):
            return pd.DataFrame({
                'SiO2': [72.0, 68.5, 76.2],
                'Al2O3': [14.2, 15.8, 12.5],
                'FeOt': [3.5, 4.2, 2.8],
                'Sample': ['Sample1', 'Sample2', 'Sample3']
            })
        return None
    
    mock.get_dataframe_by_metadata.side_effect = get_dataframe_side_effect
    return mock
