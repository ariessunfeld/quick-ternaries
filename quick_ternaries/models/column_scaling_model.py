from dataclasses import dataclass, field

# --------------------------------------------------------------------
# Column Scaling Model
# --------------------------------------------------------------------
@dataclass
class ColumnScalingModel:
    """Model for storing column scaling factors for each axis.

    The scaling_factors dictionary maps:
    axis_name -> {column_name -> scale_factor}
    """

    scaling_factors: dict = field(
        default_factory=dict,
        metadata={"plot_types": ["cartesian", "ternary"]},
    )

    def __post_init__(self):
        # Initialize with empty dictionaries for each axis
        if not self.scaling_factors:
            self.scaling_factors = {
                "x_axis": {},
                "y_axis": {},
                "left_axis": {},
                "right_axis": {},
                "top_axis": {},
                "hover_data": {},
            }

    def get_scale(self, axis_name, column_name):
        """Get the scale factor for a column on an axis."""
        return self.scaling_factors.get(axis_name, {}).get(column_name, 1.0)

    def set_scale(self, axis_name, column_name, scale_factor):
        """Set the scale factor for a column on an axis."""
        if axis_name not in self.scaling_factors:
            self.scaling_factors[axis_name] = {}
        self.scaling_factors[axis_name][column_name] = scale_factor

    def clean_unused_scales(self, axis_name, valid_columns):
        """Remove scale factors for columns that are no longer selected."""
        if axis_name in self.scaling_factors:
            # Create a copy of keys to avoid modifying during iteration
            column_keys = list(self.scaling_factors[axis_name].keys())
            for column in column_keys:
                if column not in valid_columns:
                    del self.scaling_factors[axis_name][column]