import pytest
import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch
from quick_ternaries.services.ternary_trace_maker import TernaryTraceMaker
from quick_ternaries.utils.functions import format_scale_factor

class TestTernaryTraceMaker:
    """Tests for the TernaryTraceMaker service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.trace_maker = TernaryTraceMaker()
    
    def test_format_scale_factor(self):
        """Test formatting of scale factors for hover display."""
        # Test integer values
        assert format_scale_factor(1.0) == "1"
        assert format_scale_factor(2.0) == "2"
        assert format_scale_factor(10.0) == "10"
        
        # Test floating point values with one decimal place
        assert format_scale_factor(1.5) == "1.5"
        assert format_scale_factor(2.5) == "2.5"
        
        # Test floating point values with two decimal places
        assert format_scale_factor(1.25) == "1.25"
        assert format_scale_factor(2.75) == "2.75"
        
        # Test floating point values with three decimal places
        assert format_scale_factor(1.125) == "1.125"
        assert format_scale_factor(2.375) == "2.375"
        
        # Test rounding of excess precision
        assert format_scale_factor(1.0000000001) == "1"
        assert format_scale_factor(2.2499999999) == "2.25"
        assert format_scale_factor(3.12345678) == "3.123"
    
    @patch('quick_ternaries.services.ternary_trace_maker.np')
    def test_get_hover_data_and_template_basic(self, mock_np):
        """Test basic functionality of hover data and template generation."""
        # Mock setup
        setup_model = MagicMock()
        setup_model.axis_members.hover_data = []
        
        trace_model = MagicMock()
        trace_model.heatmap_on = False
        trace_model.sizemap_on = False
        trace_model.filters_on = False
        
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4], 'C': [5, 6]})
        
        top_columns = ['A']
        left_columns = ['B']
        right_columns = ['C']
        scaling_maps = {'top': {}, 'left': {}, 'right': {}, 'all': {}}
        
        # Mock numpy arrays
        mock_np.round.return_value = np.array([1, 2])
        mock_np.array().T = np.array([[1, 3, 5], [2, 4, 6]])
        mock_np.hstack.return_value = np.array([[1, 3, 5, 0], [2, 4, 6, 1]])
        
        # Call the method
        customdata, hovertemplate = self.trace_maker._get_hover_data_and_template(
            setup_model, trace_model, df, top_columns, left_columns, right_columns, scaling_maps
        )
        
        # Verify hover template 
        assert "<b>A:</b>" in hovertemplate
        assert "<b>B:</b>" in hovertemplate
        assert "<b>C:</b>" in hovertemplate
        assert "<extra></extra>" in hovertemplate
    
    @patch('quick_ternaries.services.ternary_trace_maker.np')
    def test_get_hover_data_with_scaling(self, mock_np):
        """Test hover data generation with scaling factors."""
        # Mock setup
        setup_model = MagicMock()
        setup_model.axis_members.hover_data = []
        
        trace_model = MagicMock()
        trace_model.heatmap_on = False
        trace_model.sizemap_on = False
        trace_model.filters_on = False
        
        df = pd.DataFrame({'A': [1, 2], 'B': [3, 4], 'C': [5, 6]})
        
        top_columns = ['A']
        left_columns = ['B']
        right_columns = ['C']
        
        # Add scaling factors
        scaling_maps = {
            'top': {'A': 2.0},
            'left': {'B': 1.5},
            'right': {'C': 3.0},
            'all': {'A': 2.0, 'B': 1.5, 'C': 3.0}
        }
        
        # Mock numpy arrays as before
        mock_np.round.return_value = np.array([1, 2])
        mock_np.array().T = np.array([[1, 3, 5], [2, 4, 6]])
        mock_np.hstack.return_value = np.array([[1, 3, 5, 0], [2, 4, 6, 1]])
        
        # Call the method
        customdata, hovertemplate = self.trace_maker._get_hover_data_and_template(
            setup_model, trace_model, df, top_columns, left_columns, right_columns, scaling_maps
        )
        
        # Verify hover template includes scaled values
        assert "<b>2×A:</b>" in hovertemplate
        assert "<b>1.5×B:</b>" in hovertemplate
        assert "<b>3×C:</b>" in hovertemplate
        assert "<extra></extra>" in hovertemplate