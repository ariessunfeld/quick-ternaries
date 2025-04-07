import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QComboBox

from quick_ternaries.controllers.setup_menu_controller import SetupMenuController
from quick_ternaries.views.widgets import MultiFieldSelector


@pytest.mark.unit
class TestSetupMenuController:
    """Tests for the SetupMenuController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a more complete mock structure
        self.model = MagicMock()
        # Create data_library as a separate mock with necessary attributes
        self.model.data_library = MagicMock()
        self.model.data_library.loaded_files = []
        self.model.data_library.dataframe_manager = MagicMock()
        
        # Create other required parts of the model
        self.model.axis_members = MagicMock()
        self.model.column_scaling = MagicMock()
        self.model.chemical_formulas = MagicMock()
        
        self.view = MagicMock()
        
        # Create a real controller with mocked components
        self.controller = SetupMenuController(self.model, self.view)
    
    @patch('quick_ternaries.controllers.setup_menu_controller.validate_data_library')
    def test_update_axis_options(self, mock_validate):
        """Test updating axis options in the controller."""
        # Setup mocks
        mock_validate.return_value = {}  # No file path mapping needed
        
        # Create mock data
        mock_metadata = MagicMock()
        mock_metadata.file_path = "test.csv"
        
        # Setup model with mock data
        self.model.data_library.loaded_files = [mock_metadata]
        
        # Mock the dataframe return value
        mock_df = MagicMock()
        mock_df.columns = ['A', 'B', 'C']
        self.model.data_library.dataframe_manager.get_dataframe_by_metadata.return_value = mock_df
        
        # Setup mock section widgets
        mock_widget = MagicMock(spec=MultiFieldSelector)
        self.view.section_widgets = {
            "axis_members": {
                "top_axis": mock_widget,
                "left_axis": mock_widget,
                "right_axis": mock_widget,
                "hover_data": mock_widget
            }
        }
        
        # Call the method
        self.controller.update_axis_options()
        
        # Verify the validate_data_library was called
        mock_validate.assert_called_once()
        
        # Verify the widgets were updated
        assert mock_widget.set_available_options.call_count >= 1
        mock_widget.set_available_options.assert_called_with(['A', 'B', 'C'])
    
    @patch('quick_ternaries.controllers.setup_menu_controller.validate_data_library')
    def test_update_axis_options_with_categorical(self, mock_validate):
        """Test updating axis options with categorical column."""
        # Setup mocks
        mock_validate.return_value = {}  # No file path mapping needed
        
        # Create mock data
        mock_metadata = MagicMock()
        mock_metadata.file_path = "test.csv"
        
        # Setup model with mock data
        self.model.data_library.loaded_files = [mock_metadata]
        
        # Mock the dataframe return value
        mock_df = MagicMock()
        mock_df.columns = ['A', 'B', 'C']
        self.model.data_library.dataframe_manager.get_dataframe_by_metadata.return_value = mock_df
        
        # Setup mock section widgets including categorical_column
        mock_multi_field = MagicMock(spec=MultiFieldSelector)
        mock_combo = MagicMock(spec=QComboBox)
        self.view.section_widgets = {
            "axis_members": {
                "top_axis": mock_multi_field,
                "left_axis": mock_multi_field,
                "right_axis": mock_multi_field,
                "hover_data": mock_multi_field,
                "categorical_column": mock_combo
            }
        }
        
        # Call the method
        self.controller.update_axis_options()
        
        # Verify the widgets were updated
        assert mock_multi_field.set_available_options.call_count >= 1
        mock_multi_field.set_available_options.assert_called_with(['A', 'B', 'C'])
        mock_combo.clear.assert_called_once()
        mock_combo.addItems.assert_called_once_with(['A', 'B', 'C'])