from dataclasses import dataclass, field

@dataclass
class ChemicalFormulaModel:
    """Model for storing chemical formulas for each column in each axis."""
    formulas: dict = field(
        default_factory=dict,
        metadata={"plot_types": ["ternary", "cartesian"]},
    )

    def __post_init__(self):
        # Initialize with empty dictionaries for each axis
        if not self.formulas:
            self.formulas = {
                "x_axis": {},
                "y_axis": {},
                "left_axis": {},
                "right_axis": {},
                "top_axis": {},
                "hover_data": {},
            }

    def get_formula(self, axis_name, column_name):
        """Get the formula for a column on an axis."""
        return self.formulas.get(axis_name, {}).get(column_name, "")

    def set_formula(self, axis_name, column_name, formula):
        """Set the formula for a column on an axis."""
        if axis_name not in self.formulas:
            self.formulas[axis_name] = {}
        self.formulas[axis_name][column_name] = formula

    def clean_unused_formulas(self, axis_name, valid_columns):
        """Remove formulas for columns that are no longer selected."""
        if axis_name in self.formulas:
            # Create a copy of keys to avoid modifying during iteration
            column_keys = list(self.formulas[axis_name].keys())
            for column in column_keys:
                if column not in valid_columns:
                    del self.formulas[axis_name][column]