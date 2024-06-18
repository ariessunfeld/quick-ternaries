
from src.models.ternary.setup.custom_hover_data_selection_model import CustomHoverDataSelectionModel
from src.views.ternary.setup import  CustomHoverDataSelectionView

class CustomHoverDataSelectionController:
    def __init__(
            self,
            model: CustomHoverDataSelectionModel,
            view: CustomHoverDataSelectionView):
        """Initialize the Custom Hover Data Selection controller"""
        self.model = model
        self.view = view

        self.setup_connections()

    def setup_connections(self):
        """Connects view events to model"""
        self.view.add_remove_list.button_add.clicked.connect(self.clicked_add)
        self.view.add_remove_list.button_remove.clicked.connect(self.clicked_remove)
        self.model.set_view(self.view)

    def clicked_add(self):
        """Gets selected entry from view's available columns, 
        adds it to model's selected columns,
        and removes it from model's available columns. Model updates view."""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_selected_attr(col)
            self.model.rem_available_attr(col)

    def clicked_remove(self):
        """Gets selected entry from view's selected columns,
        adds it to model's available columns,
        and remove it from model's selected columns. Model updates view."""
        selected_column = self.view.add_remove_list.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_available_attr(col)
            self.model.rem_selected_attr(col)

    def update_columns(self, new_columns: list[str]):
        # Set model's available columns to new_columns
        self.model.available_attrs = []
        for col in new_columns:
            self.model.add_available_attr(col)
        for col in self.model.get_selected_attrs():
            self.model.rem_available_attr(col)
            if col not in new_columns:
                self.model.rem_selected_attr(col)
