"""Class responsible for calculating molar masses"""

from molmass import Formula, FormulaError

class MolarMassCalculatorException(Exception):
    """Exception raised for errors in the MolarMassCalculator."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MolarMassCalculator:

    def get_molar_mass(self, formula: str):
        try:
            if formula.lower() == 'feot':
                formula = 'FeO'
            return Formula(formula).mass
        except FormulaError as e:
            raise MolarMassCalculatorException(f"Invalid chemical formula '{formula}': {e}")

