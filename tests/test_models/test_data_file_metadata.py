import pytest
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata

class TestDataFileMetadata:
    """Tests for the DataFileMetadata model."""
    
    def test_initialization(self):
        """Test basic initialization of DataFileMetadata."""
        # Test with minimal parameters
        metadata = DataFileMetadata(file_path="test.csv")
        assert metadata.file_path == "test.csv"
        assert metadata.header_row is None
        assert metadata.sheet is None
        assert metadata.df_id is None
        
        # Test with all parameters
        metadata = DataFileMetadata(
            file_path="test.xlsx",
            header_row=1,
            sheet="Sheet1",
            df_id="test_id"
        )
        assert metadata.file_path == "test.xlsx"
        assert metadata.header_row == 1
        assert metadata.sheet == "Sheet1"
        assert metadata.df_id == "test_id"
    
    def test_string_representation(self):
        """Test string representation of DataFileMetadata."""
        # Test with minimal parameters
        metadata = DataFileMetadata(file_path="test.csv")
        assert str(metadata) == "test.csv"
        
        # Test with header
        metadata = DataFileMetadata(file_path="test.csv", header_row=1)
        assert str(metadata) == "test.csv :: header=1"
        
        # Test with sheet
        metadata = DataFileMetadata(file_path="test.xlsx", sheet="Sheet1")
        assert str(metadata) == "test.xlsx :: sheet=Sheet1"
        
        # Test with all parameters
        metadata = DataFileMetadata(
            file_path="test.xlsx",
            header_row=1,
            sheet="Sheet1"
        )
        assert str(metadata) == "test.xlsx :: sheet=Sheet1 :: header=1"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = DataFileMetadata(
            file_path="test.xlsx",
            header_row=1,
            sheet="Sheet1",
            df_id="test_id"  # This should be excluded from to_dict
        )
        
        result = metadata.to_dict()
        assert result == {
            "file_path": "test.xlsx",
            "header_row": 1,
            "sheet": "Sheet1"
        }
        assert "df_id" not in result
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "file_path": "test.xlsx",
            "header_row": 1,
            "sheet": "Sheet1"
        }
        
        metadata = DataFileMetadata.from_dict(data)
        assert metadata.file_path == "test.xlsx"
        assert metadata.header_row == 1
        assert metadata.sheet == "Sheet1"
        assert metadata.df_id is None
    
    def test_from_display_string(self):
        """Test parsing from display string."""
        # Test with just file path
        metadata = DataFileMetadata.from_display_string("test.csv")
        assert metadata.file_path == "test.csv"
        assert metadata.header_row is None
        assert metadata.sheet is None
        
        # Test with header
        metadata = DataFileMetadata.from_display_string("test.csv :: header=1")
        assert metadata.file_path == "test.csv"
        assert metadata.header_row == 1
        assert metadata.sheet is None
        
        # Test with sheet
        metadata = DataFileMetadata.from_display_string("test.xlsx :: sheet=Sheet1")
        assert metadata.file_path == "test.xlsx"
        assert metadata.header_row is None
        assert metadata.sheet == "Sheet1"
        
        # Test with both
        metadata = DataFileMetadata.from_display_string("test.xlsx :: sheet=Sheet1 :: header=1")
        assert metadata.file_path == "test.xlsx"
        assert metadata.header_row == 1
        assert metadata.sheet == "Sheet1"