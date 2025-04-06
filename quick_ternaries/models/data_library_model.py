import os
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from quick_ternaries.utils.df_manager import DataframeManager
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata



@dataclass
class DataLibraryModel:
    loaded_files: List[DataFileMetadata] = field(default_factory=list)
    # The dataframe_manager is a transient property (not serialized)
    # This special field metadata ensures it's excluded from serialization
    _dataframe_manager: Optional[DataframeManager] = field(
        default=None,
        repr=False,
        compare=False,
        hash=False,
        metadata={"exclude_from_dict": True},
    )

    def __post_init__(self):
        # Initialize the dataframe manager if needed
        if self._dataframe_manager is None:
            self._dataframe_manager = DataframeManager()

    @property
    def dataframe_manager(self):
        # Ensure dataframe_manager is always available
        if self._dataframe_manager is None:
            self._dataframe_manager = DataframeManager()
        return self._dataframe_manager

    def to_dict(self):
        """Custom to_dict method that explicitly excludes the
        dataframe_manager."""
        return {"loaded_files": [file.to_dict() for file in self.loaded_files]}

    @classmethod
    def from_dict(cls, d: dict):
        # Create a new instance with loaded files from dict
        files = [DataFileMetadata.from_dict(fd) for fd in d.get("loaded_files", [])]
        return cls(loaded_files=files)

    def add_file(self, metadata: DataFileMetadata) -> bool:
        """Add a new file to the data library and load its dataframe.

        Args:
            metadata: DataFileMetadata object with file path, header, and sheet

        Returns:
            bool: True if successful, False otherwise
        """
        # Load the dataframe
        df_id = self.dataframe_manager.load_dataframe(metadata)
        if df_id:
            # Set the df_id on the metadata
            metadata.df_id = df_id
            # Add to loaded files
            self.loaded_files.append(metadata)
            return True
        return False

    def get_metadata_by_display_string(self, display_str: str) -> Optional[DataFileMetadata]:
        """Get metadata for a file by its display string."""
        return self.dataframe_manager.get_metadata_by_display_string(display_str)

    
    def remove_file(self, display_str: str) -> bool:
        """Remove a file from the data library using its display string."""
        # Get the metadata from the display string
        metadata = self.dataframe_manager.get_metadata_by_display_string(display_str)
        if not metadata:
            # Try to find by file path (if display_str happens to be just a file path)
            for i, file_meta in enumerate(self.loaded_files):
                if file_meta.file_path == display_str:
                    # Remove the dataframe from the cache if it has a df_id
                    if file_meta.df_id:
                        self.dataframe_manager.remove_dataframe(file_meta.df_id)
                    # Remove the metadata from loaded_files
                    self.loaded_files.pop(i)
                    return True
            return False
            
        for i, file_meta in enumerate(self.loaded_files):
            if file_meta is metadata or (
               file_meta.file_path == metadata.file_path and
               file_meta.header_row == metadata.header_row and
               file_meta.sheet == metadata.sheet):
                # Remove the dataframe from the cache if it has a df_id
                if file_meta.df_id:
                    self.dataframe_manager.remove_dataframe(file_meta.df_id)
                # Remove the metadata from loaded_files
                self.loaded_files.pop(i)
                return True
        return False
    
    def get_dataframe(self, display_str: str) -> Optional[pd.DataFrame]:
        """Get the dataframe for a file by its display string."""
        metadata = self.dataframe_manager.get_metadata_by_display_string(display_str)
        if metadata:
            return self.dataframe_manager.get_dataframe_by_metadata(metadata)
        return None

    def reload_all_dataframes(self) -> bool:
        """Reload all dataframes from disk. Useful after loading a workspace.

        Returns:
            bool: True if all reloads were successful, False otherwise
        """
        success = True
        for metadata in self.loaded_files:
            # Skip if file doesn't exist - handle this separately
            if not os.path.exists(metadata.file_path):
                success = False
                continue

            result = self.dataframe_manager.reload_dataframe(metadata)
            if not result:
                success = False
        return success

    def reload_dataframe(self, file_path: str) -> bool:
        """Reload a specific dataframe from disk.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        for metadata in self.loaded_files:
            if metadata.file_path == file_path:
                return self.dataframe_manager.reload_dataframe(metadata)
        return False

    def get_metadata_by_path(self, file_path: str) -> Optional[DataFileMetadata]:
        """Get metadata for a file by its path."""
        for metadata in self.loaded_files:
            if metadata.file_path == file_path:
                return metadata
        return None

    def clear(self):
        """Clear all loaded files and dataframes."""
        self.loaded_files.clear()
        self.dataframe_manager.clear_cache()

    def update_file_paths(self, path_mapping: dict) -> bool:
        """Update file paths in the data library based on a mapping. Useful
        after loading a workspace when files have moved.

        Args:
            path_mapping: Dict mapping old paths to new paths

        Returns:
            bool: True if all updates were successful, False otherwise
        """
        success = True
        for metadata in self.loaded_files:
            if metadata.file_path in path_mapping:
                old_path = metadata.file_path
                new_path = path_mapping[old_path]
                metadata.file_path = new_path
                # Clear any existing df_id
                metadata.df_id = None
                # Try to load the dataframe with the new path
                if not self.dataframe_manager.load_dataframe(metadata):
                    success = False
        return success