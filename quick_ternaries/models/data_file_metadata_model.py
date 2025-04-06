from dataclasses import dataclass
from typing import Optional


@dataclass
class DataFileMetadata:
    file_path: str
    header_row: Optional[int] = None
    sheet: Optional[str] = None
    df_id: Optional[str] = None

    def __str__(self):
        """Return a human-readable string representation."""
        parts = [self.file_path]
        if self.sheet:
            parts.append(f"sheet={self.sheet}")
        if self.header_row is not None:
            parts.append(f"header={self.header_row}")
        return " :: ".join(parts)
    
    def to_dict(self):
        # Exclude df_id from serialization
        result = {
            "file_path": self.file_path,
            "header_row": self.header_row,
            "sheet": self.sheet,
        }
        return result

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)
    
    @classmethod
    def from_display_string(cls, display_str: str):
        """Parse a display string back into a DataFileMetadata object."""
        parts = display_str.split(" :: ")
        file_path = parts[0]
        header_row = None
        sheet = None
        
        for part in parts[1:]:
            if part.startswith("sheet="):
                sheet = part[6:]
            elif part.startswith("header="):
                try:
                    header_row = int(part[7:])
                except ValueError:
                    pass
        
        return cls(file_path=file_path, header_row=header_row, sheet=sheet)