
from typing import Dict, Optional

import pandas as pd

from quick_ternaries.models.data_file_metadata_model import DataFileMetadata



class DataframeManager:
    """Manages loading and caching of dataframes to avoid repetitive disk reads."""

    def __init__(self):
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._display_to_metadata: Dict[str, DataFileMetadata] = {}

    def load_dataframe(self, metadata: DataFileMetadata) -> str:
        """Loads a dataframe based on metadata and returns an identifier."""
        df_id = f"{metadata.file_path}:{metadata.sheet}:{metadata.header_row}"

        try:
            if metadata.file_path.lower().endswith(".csv"):
                df = pd.read_csv(metadata.file_path, header=metadata.header_row)
            elif metadata.file_path.lower().endswith((".xls", ".xlsx")):
                df = pd.read_excel(
                    metadata.file_path,
                    header=metadata.header_row,
                    sheet_name=metadata.sheet,
                )
            else:
                raise ValueError(f"Unsupported file format: {metadata.file_path}")

            self._dataframes[df_id] = df
            
            # Store the string representation for lookup
            display_str = str(metadata)
            self._display_to_metadata[display_str] = metadata
            
            return df_id

        except Exception as e:
            print(f"Error loading dataframe: {e}")
            return None

    def get_metadata_by_display_string(self, display_str: str) -> Optional[DataFileMetadata]:
        """Get the metadata object from a display string."""
        # Direct lookup from our mapping
        metadata = self._display_to_metadata.get(display_str)
        
        if metadata is None:
            # Try to parse it as a display string
            try:
                parsed_metadata = DataFileMetadata.from_display_string(display_str)
                
                # Check if we have this file in our mapping with different formatting
                for key, value in self._display_to_metadata.items():
                    if value.file_path == parsed_metadata.file_path:
                        if (value.sheet == parsed_metadata.sheet and 
                            value.header_row == parsed_metadata.header_row):
                            return value
                
                # If not found, return the parsed metadata
                return parsed_metadata
            except Exception as e:
                print(f"Error parsing display string: {e}")
                return None
                
        return metadata
    
    def get_dataframe(self, df_id: str) -> Optional[pd.DataFrame]:
        """Retrieves a dataframe by its identifier."""
        return self._dataframes.get(df_id)

    def get_dataframe_by_metadata(self, metadata_or_str) -> Optional[pd.DataFrame]:
        """Gets a dataframe for the given metadata or display string."""
        metadata = None
        
        # Handle string input
        if isinstance(metadata_or_str, str):
            metadata = self.get_metadata_by_display_string(metadata_or_str)
        else:
            metadata = metadata_or_str
            
        if metadata is None:
            return None
            
        # Check if it's a valid DataFileMetadata object
        if not isinstance(metadata, DataFileMetadata):
            print(f"Warning: Expected DataFileMetadata object but got {type(metadata)}")
            return None
        
        # Check if metadata has a df_id and if it's valid
        if metadata.df_id and metadata.df_id in self._dataframes:
            return self._dataframes[metadata.df_id]

        # Load the dataframe if needed
        df_id = self.load_dataframe(metadata)
        if df_id:
            # Update the metadata with the df_id
            metadata.df_id = df_id
            # Add to display mapping
            self._display_to_metadata[str(metadata)] = metadata
            return self._dataframes[df_id]
        return None

    def remove_dataframe(self, df_id: str) -> bool:
        """Removes a dataframe from the cache."""
        if df_id in self._dataframes:
            # Find and remove display strings that map to this df_id
            for display_str, metadata in list(self._display_to_metadata.items()):
                if metadata.df_id == df_id:
                    del self._display_to_metadata[display_str]
            
            del self._dataframes[df_id]
            return True
        return False

    def clear_cache(self):
        """Clears all cached dataframes."""
        self._dataframes.clear()
        self._display_to_metadata.clear()