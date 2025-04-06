from typing import TYPE_CHECKING

from PySide6.QtWidgets import QComboBox

from quick_ternaries.utils.functions import validate_data_library
from quick_ternaries.views.widgets import MultiFieldSelector

if TYPE_CHECKING:
    from quick_ternaries.models.setup_menu_model import SetupMenuModel
    from quick_ternaries.views.setup_menu_view import SetupMenuView

class SetupMenuController:
    """Controller for the Setup Menu.

    Recomputes the intersection of column names from loaded data files and
    updates the available options for axis member selectors. Uses
    DataframeManager to avoid repeated disk reads.
    """

    def __init__(self, model: "SetupMenuModel", view: "SetupMenuView"):
        self.model = model
        self.view = view

    def update_axis_options(self):
        """Recompute the intersection of column names from loaded data files
        and update selectors."""
        # Handle missing files
        file_path_mapping = validate_data_library(self.model.data_library, self.view)

        # If any file paths were updated, update the dataframes
        if file_path_mapping:
            self.model.data_library.update_file_paths(file_path_mapping)

        loaded_files = self.model.data_library.loaded_files

        common_columns = None
        for file_meta in loaded_files:
            # Get the dataframe using the dataframe manager
            df = self.model.data_library.dataframe_manager.get_dataframe_by_metadata(
                file_meta
            )
            if df is None:
                print(f"Warning: Could not get dataframe for {file_meta.file_path}")
                continue

            # Get columns from the dataframe
            cols = set(df.columns)

            if common_columns is None:
                common_columns = set(cols)
            else:
                common_columns = common_columns.intersection(cols)

        if common_columns is None:
            common_columns = set()

        common_list = sorted(common_columns)

        # Dictionary to track changes in each axis for later updating widgets
        axis_changes = {}

        axis_widgets = self.view.section_widgets.get("axis_members", {})
        for field_name, widget in axis_widgets.items():
            if isinstance(widget, MultiFieldSelector):
                widget.set_available_options(common_list)
                selected = widget.get_selected_fields()
                valid = [s for s in selected if s in common_list]

                # Track if selections changed
                axis_changes[field_name] = {"previous": selected, "current": valid}

                # Update the widget with valid selections
                widget.set_selected_fields(valid)

                # Update the model too (since this bypasses the widget's signals)
                setattr(self.model.axis_members, field_name, valid)

                # Clean up scaling factors for columns that are no longer valid
                self.model.column_scaling.clean_unused_scales(field_name, valid)
                
                # Clean up formulas for columns that are no longer valid
                self.model.chemical_formulas.clean_unused_formulas(field_name, valid)
            
            # Handle the categorical_column ComboBox for Zmap
            elif field_name == "categorical_column" and isinstance(widget, QComboBox):
                # Save current value
                current_value = widget.currentText()
                
                # Update options
                widget.clear()
                widget.addItems(common_list)
                
                # Restore current value if valid
                if current_value in common_list:
                    widget.setCurrentText(current_value)
                elif common_list:
                    widget.setCurrentText(common_list[0])
                    # Update the model with the new value
                    self.model.axis_members.categorical_column = common_list[0]

        # Update the column scaling widget to reflect the changes
        self.view.update_scaling_widget()
        
        # Update the formula widget to reflect the changes
        self.view.update_formula_widget()
