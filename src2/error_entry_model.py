from dataclasses import asdict, dataclass, field, fields, is_dataclass
from typing import Dict, List, Optional, Union, Tuple, Optional
@dataclass
class ErrorEntryModel:
    """
    Model for storing error values for each component in a contour trace.
    Maps component names to error values.
    """
    entries: Dict[str, float] = field(default_factory=dict)
    
    def get_error(self, component: str) -> float:
        """Get the error value for a component."""
        return self.entries.get(component, 0.0)
    
    def set_error(self, component: str, value: float):
        """Set the error value for a component, ensuring it’s a native float."""
        self.entries[component] = float(value)
    
    def get_sorted_repr(self) -> List[Tuple[str, str]]:
        """
        Get a sorted representation of the entries.
        Returns list of (component, error) tuples.
        """
        sorted_items = sorted(self.entries.items(), key=lambda x: x[0])
        return [(k, str(v)) for k, v in sorted_items]
    
    def to_dict(self):
        """Convert to dictionary for serialization, converting all values to float."""
        # Ensure all values are converted to native Python float
        return {"entries": {k: float(v) for k, v in self.entries.items()}}
    
    @classmethod
    def from_dict(cls, d: dict):
        """Create from dictionary after deserialization."""
        entries = d.get("entries", {})
        # Ensure each value is a native float
        entries = {k: float(v) for k, v in entries.items()}
        return cls(entries=entries)