import pytest
from quick_ternaries.services.molar_mass_calculator import MolarMassCalculator, MolarMassCalculatorException

class TestMolarMassCalculator:
    """Tests for the MolarMassCalculator service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = MolarMassCalculator()
    
    def test_valid_formulas(self):
        """Test calculation of molar mass for valid formulas."""
        # Test simple formulas with known molar masses
        # SiO2 = 28.0855 + 2*15.999 = 60.0835
        assert abs(self.calculator.get_molar_mass("SiO2") - 60.0835) < 0.001
        
        # Al2O3 = 2*26.9815 + 3*15.999 = 101.9615
        assert abs(self.calculator.get_molar_mass("Al2O3") - 101.9615) < 0.001
        
        # Test handling of FeOt (special case)
        # FeO = 55.845 + 15.999 = 71.844
        assert abs(self.calculator.get_molar_mass("FeOt") - 71.844) < 0.001
        
    def test_invalid_formulas(self):
        """Test error handling for invalid formulas."""
        # Empty string
        with pytest.raises(MolarMassCalculatorException):
            self.calculator.get_molar_mass("")
        
        # Invalid formula
        with pytest.raises(MolarMassCalculatorException):
            self.calculator.get_molar_mass("NotAValidFormula")
        
        # Invalid element
        with pytest.raises(MolarMassCalculatorException):
            self.calculator.get_molar_mass("Xx2O3")  # Xx is not an element