from dataclasses import dataclass, field, asdict
from PySide6.QtWidgets import QLineEdit, QComboBox

# --------------------------------------------------------------------
# Filter Model
# --------------------------------------------------------------------
@dataclass
class FilterModel:
    # Allowed operations for numeric filters.
    # TODO factor into Enum / into constants.py
    ALLOWED_NUMERIC_OPERATIONS = [
        "<",
        ">",
        "<=",
        ">=",
        "==",
        'is',
        'is not',
        "a < x < b",
        "a <= x < b",
        "a < x <= b",
        "a <= x <= b",
    ]

    filter_name: str = field(
        default="Filter", metadata={"label": "Filter Name:", "widget": QLineEdit}
    )
    filter_column: str = field(
        default="", metadata={"label": "Filter Column:", "widget": QComboBox}
    )
    # The filter_operation field will be re-populated dynamically.
    filter_operation: str = field(
        default="",
        metadata={
            "label": "Filter Operation:",
            "widget": QComboBox,
            # Note: allowed_values here is not used directly because we repopulate it.
        },
    )
    # For numeric operations that require one or two values.
    # For non-numeric, the value widget will be replaced with a text field (or MultiFieldSelector).
    filter_value1: str = field(default="", metadata={"label": "Value A:"})
    filter_value2: str = field(default="", metadata={"label": "Value B:"})

    def to_dict(self):
        """Convert filter model to dictionary, properly handling multi-value
        cases."""
        result = asdict(self)
        # Handle special case for multi-value filters
        if self.filter_operation in ["is one of", "is not one of"]:
            # If filter_value1 is a list, convert it to a comma-separated string
            if isinstance(self.filter_value1, list):
                result["filter_value1"] = ",".join(str(x) for x in self.filter_value1)
        return result

    @classmethod
    def from_dict(cls, d):
        """Create a filter model from dictionary, properly handling multi-value
        cases."""
        # Make a copy to avoid modifying the input
        data = d.copy()

        # Handle the special case for multi-value filters
        op = data.get("filter_operation", "")
        if op in ["is one of", "is not one of"]:
            val = data.get("filter_value1", "")
            if isinstance(val, str) and val:
                # Store as a proper list
                data["filter_value1"] = [x.strip() for x in val.split(",")]
            elif not isinstance(val, list):
                # Initialize as empty list if not string or list
                data["filter_value1"] = []

        return cls(**data)
