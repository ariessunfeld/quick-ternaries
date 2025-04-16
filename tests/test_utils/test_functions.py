import pytest
import pandas as pd
from quick_ternaries.utils.functions import (
    is_valid_formula,
    recursive_to_dict,
    find_header_row_excel,
    find_header_row_csv,
    get_sheet_names,
    get_suggested_header,
    get_columns_from_dataframe,
    get_numeric_columns_from_dataframe,
    get_all_columns_from_dataframe,
    get_sorted_unique_values_from_dataframe,
    is_numeric_column_in_dataframe,
    get_preview_data_from_dataframe,
    get_numeric_columns_from_file,
    get_all_columns_from_file,
    get_sorted_unique_values,
    is_numeric_column,
    get_preview_data,
    validate_data_library,
    suggest_formula_from_column_name,
    util_convert_hex_to_rgba
)

class TestUtilFunctions:
    """Tests for utility functions in functions.py"""
    
    def test_is_valid_formula(self):
        """Test chemical formula validation."""
        # Valid formulas
        assert is_valid_formula("SiO2") is True
        assert is_valid_formula("Al2O3") is True
        assert is_valid_formula("FeO") is True
        assert is_valid_formula("H2O") is True
        assert is_valid_formula("CaMgSi2O6") is True
        assert is_valid_formula("Si02") is True  # 0 instead of O, interpreted as Si2
        
        # Invalid formulas
        assert is_valid_formula("") is False
        assert is_valid_formula("NotAFormula") is False
        assert is_valid_formula("!!Invalid!!") is False
    
    def test_get_numeric_columns_from_dataframe(self, sample_dataframe):
        """Test extracting numeric columns from DataFrame."""
        numeric_cols = get_numeric_columns_from_dataframe(sample_dataframe)
        assert numeric_cols == ['A', 'B', 'C']
        assert 'Category' not in numeric_cols
        
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        assert get_numeric_columns_from_dataframe(empty_df) == []
        
        # Test with None
        assert get_numeric_columns_from_dataframe(None) == []

    def test_find_header_row_csv(self, sample_csv_file):
        """Test identifying header row on CSV file"""
        header_row = find_header_row_csv(sample_csv_file, 16)
        assert header_row == 0

    def test_get_sheet_names_excel(self, sample_excel_file):
        """Test that get_sheet_names returns a valid sheet list for an Excel file."""
        sheet_names = get_sheet_names(sample_excel_file)
        # Expect the file to have at least one sheet, "sheet_1"
        assert isinstance(sheet_names, list)
        assert "sheet_1" in sheet_names
        assert len(sheet_names) >= 1

    def test_get_sheet_names_non_excel(self, sample_csv_file):
        """Test that get_sheet_names returns an empty list for a non-Excel file."""
        sheet_names = get_sheet_names(sample_csv_file)
        assert sheet_names == []

    def test_get_sheet_names_nonexistent(self, tmp_path):
        """Test that get_sheet_names returns an empty list when the file does not exist."""
        non_existent_file = tmp_path / "nonexistent.xlsx"
        sheet_names = get_sheet_names(str(non_existent_file))
        assert sheet_names == []

    def test_get_sheet_names_multi_sheet(self, sample_excel_file_multi_sheet):
        """Test that get_sheet_names returns all sheet names for an Excel file with multiple sheets."""
        sheet_names = get_sheet_names(sample_excel_file_multi_sheet)
        # For debugging, print detected sheet names:
        print("Detected sheet names:", sheet_names)
        expected_sheet_names = {"Sheet1", "Sheet2"}
        assert set(sheet_names) == expected_sheet_names
    
    def test_get_columns_from_dataframe(self, sample_dataframe):
        """Test getting all columns from DataFrame."""
        columns = get_columns_from_dataframe(sample_dataframe)
        assert set(columns) == {'A', 'B', 'C', 'Category'}
        
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        assert get_columns_from_dataframe(empty_df) == set()
        
        # Test with None
        assert get_columns_from_dataframe(None) == set()
    
    def test_get_sorted_unique_values_from_dataframe(self, sample_dataframe):
        """Test extracting sorted unique values from a column."""
        # Test with numeric column
        a_values = get_sorted_unique_values_from_dataframe(sample_dataframe, 'A')
        assert a_values == [1, 2, 3, 4, 5]
        
        # Test with categorical column
        cat_values = get_sorted_unique_values_from_dataframe(sample_dataframe, 'Category')
        assert cat_values == ['X', 'Y', 'Z']
        
        # Test with non-existent column
        assert get_sorted_unique_values_from_dataframe(sample_dataframe, 'NonExistent') == []
        
        # Test with None DataFrame
        assert get_sorted_unique_values_from_dataframe(None, 'A') == []
    
    def test_util_convert_hex_to_rgba(self):
        """Test conversion of hex colors to RGBA format."""
        # Test standard hex color
        assert util_convert_hex_to_rgba("#FF0000") == "rgba(255, 0, 0, 1)"
        
        # Test with alpha
        assert util_convert_hex_to_rgba("#80FF0000") == "rgba(255, 0, 0, 0.5019607843137255)"
        
        # Test lowercase
        assert util_convert_hex_to_rgba("#00ff00") == "rgba(0, 255, 0, 1)"
        
        # Test without hash
        assert util_convert_hex_to_rgba("0000FF") == "rgba(0, 0, 255, 1)"

    # --- Tests for is_numeric_column_in_dataframe ---
    def test_is_numeric_column_in_dataframe_valid(self, sample_dataframe):
        """
        Test that numeric columns in a valid dataframe are detected correctly.
        'A', 'B', and 'C' should be numeric, while 'Category' is not.
        """
        assert is_numeric_column_in_dataframe(sample_dataframe, 'A') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'B') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'C') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'Category') is False

    def test_is_numeric_column_in_dataframe_invalid(self):
        """
        Test that the function returns False when either the dataframe or column is None.
        """
        # When the dataframe is None
        assert is_numeric_column_in_dataframe(None, 'A') is False
        # When the column is None
        df = pd.DataFrame({'A': [1, 2, 3]})
        assert is_numeric_column_in_dataframe(df, None) is False

    # --- Tests for get_preview_data_from_dataframe ---
    def test_get_preview_data_from_dataframe(self, sample_dataframe):
        """
        Test that get_preview_data_from_dataframe returns the correct number of rows
        as a list of lists.
        """
        n_rows = 3
        preview = get_preview_data_from_dataframe(sample_dataframe, n_rows=n_rows)
        # Check that we get a list with n_rows items (or less if the df is smaller)
        assert isinstance(preview, list)
        assert len(preview) == min(n_rows, len(sample_dataframe))
        # Compare the first row from the preview to that from df.head()
        expected_first_row = sample_dataframe.head(1).values.tolist()[0]
        assert preview[0] == expected_first_row

    def test_get_preview_data_from_dataframe_none(self):
        """
        Test that passing None as the dataframe returns an empty list.
        """
        preview = get_preview_data_from_dataframe(None, n_rows=5)
        assert preview == []

    # --- Tests for get_numeric_columns_from_file ---
    def test_get_numeric_columns_from_file_csv(self, sample_csv_file):
        """
        Test that numeric columns are correctly detected from a CSV file.
        Expected numeric columns are all columns except 'Sample'.
        """
        numeric_cols = get_numeric_columns_from_file(sample_csv_file)
        expected = ['SiO2', 'Al2O3', 'FeOt', 'CaO', 'MgO', 'Na2O', 'K2O']
        # Order does not matter, so we compare as sets.
        assert set(numeric_cols) == set(expected)

    def test_get_numeric_columns_from_file_excel(self, sample_excel_file):
        """
        Test that numeric columns are correctly detected from an Excel file.
        Because the sample file was written without a header, specify header=0 and the sheet name.
        """
        numeric_cols = get_numeric_columns_from_file(sample_excel_file, header=0, sheet='sheet_1')
        expected = ['SiO2', 'Al2O3', 'FeOt', 'CaO', 'MgO', 'Na2O', 'K2O']
        assert set(numeric_cols) == set(expected)

    def test_get_numeric_columns_from_file_with_dataframe_manager(self, mock_dataframe_manager):
        """
        Test that if a data_source with a file_path attribute is provided along with
        a dataframe_manager, the function returns the numeric columns from the cached DataFrame.
        The mocked DataFrame returns numeric columns: 'SiO2', 'Al2O3', 'FeOt'
        """
        # Create a dummy metadata object with a file_path attribute.
        class DummyMetadata:
            file_path = "dummy.csv"
        metadata = DummyMetadata()
        numeric_cols = get_numeric_columns_from_file(metadata, dataframe_manager=mock_dataframe_manager)
        expected = ['SiO2', 'Al2O3', 'FeOt']
        assert set(numeric_cols) == set(expected)


class TestDataFrameFunctions:
    def test_is_numeric_column_in_dataframe(self, sample_dataframe):
        """
        Test that numeric columns in a valid DataFrame are detected correctly.
        For the sample_dataframe:
          - 'A', 'B', and 'C' are numeric.
          - 'Category' is not numeric.
        """
        assert is_numeric_column_in_dataframe(sample_dataframe, 'A') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'B') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'C') is True
        assert is_numeric_column_in_dataframe(sample_dataframe, 'Category') is False

    def test_get_preview_data_from_dataframe(self, sample_dataframe):
        """
        Test that get_preview_data_from_dataframe returns the expected number of rows
        as a list of lists and that the data match.
        """
        n_rows = 3
        preview = get_preview_data_from_dataframe(sample_dataframe, n_rows=n_rows)
        # The preview should be a list and have at most n_rows items.
        assert isinstance(preview, list)
        assert len(preview) == min(n_rows, len(sample_dataframe))
        # Verify the first row matches the DataFrame's head.
        expected_first_row = sample_dataframe.head(1).values.tolist()[0]
        assert preview[0] == expected_first_row

class TestGetNumericColumnsFromFile:
    def test_get_numeric_columns_from_file_excel_standard(self, hardcopy_excel_standard):
        """
        For the standard Excel file (with header row in the first row),
        we expect the numeric columns to be all except the 'Sample' column.
        """
        # Read with header=0 and sheet name "sheet_1"
        numeric_cols = get_numeric_columns_from_file(
            hardcopy_excel_standard, header=0, sheet="sheet_1"
        )
        expected = ['SiO2', 'Al2O3', 'FeOt', 'CaO', 'MgO', 'Na2O', 'K2O']
        assert set(numeric_cols) == set(expected)

    def test_get_numeric_columns_from_file_excel_header1(self, hardcopy_excel_header1):
        """
        For the Excel file where the intended header is on row 1,
        we pass header=1. The intended header row is:
            ["Sample", "SiO2", "FeOt", "Na2O", "MgO"]
        so the numeric columns should be all except 'Sample'.
        """
        numeric_cols = get_numeric_columns_from_file(
            hardcopy_excel_header1, header=1, sheet="sheet_1"
        )
        expected = ['SiO2', 'FeOt', 'Na2O', 'MgO']
        assert set(numeric_cols) == set(expected)

    def test_get_numeric_columns_from_file_csv_standard(self, hardcopy_csv_standard):
        """
        For the standard CSV file (with header in the first row),
        the expected numeric columns are all columns except 'Sample'.
        """
        numeric_cols = get_numeric_columns_from_file(hardcopy_csv_standard)
        expected = ['SiO2', 'Al2O3', 'FeOt', 'CaO', 'MgO', 'Na2O', 'K2O']
        assert set(numeric_cols) == set(expected)

    def test_get_numeric_columns_from_file_csv_header1(self, hardcopy_csv_header1):
        """
        For the CSV file where the intended header is on row 1,
        pass header=1 so that the header row is correctly interpreted.
        """
        numeric_cols = get_numeric_columns_from_file(hardcopy_csv_header1, header=1)
        expected = ['SiO2', 'FeOt', 'Na2O', 'MgO']
        assert set(numeric_cols) == set(expected)

class TestHeaderRowDetection:
    def test_find_header_row_csv_standard(self, hardcopy_csv_standard):
        """
        For the standard CSV file (with the header in row 0),
        the header-detection algorithm should return 0.
        """
        header_row = find_header_row_csv(hardcopy_csv_standard, max_rows_scan=10)
        print("Detected CSV standard header row:", header_row)
        assert header_row == 0

    def test_find_header_row_csv_header1(self, hardcopy_csv_header1):
        """
        For the CSV file where the intended header is on row 1,
        the header-detection algorithm should return 1.
        """
        header_row = find_header_row_csv(hardcopy_csv_header1, max_rows_scan=10)
        print("Detected CSV header1 header row:", header_row)
        assert header_row == 1

    def test_find_header_row_excel_standard(self, hardcopy_excel_standard):
        """
        For the standard Excel file (with the header in row 0),
        the header-detection algorithm should return 0.
        """
        header_row = find_header_row_excel(hardcopy_excel_standard, max_rows_scan=10, sheet_name='sheet_1')
        print("Detected Excel standard header row:", header_row)
        assert header_row == 0

    def test_find_header_row_excel_header1(self, hardcopy_excel_header1):
        """
        For the Excel file where the intended header is on row 1,
        the header-detection algorithm should return 1.
        """
        header_row = find_header_row_excel(hardcopy_excel_header1, max_rows_scan=10, sheet_name='sheet_1')
        print("Detected Excel header1 header row:", header_row)
        assert header_row == 1