from src.models.start_setup.custom_apex_selection_model import CustomApexSelectionModel
from src.views.start_setup.custom_apex_selection_view import CustomApexSelectionView

class CustomApexSelectionController:
    def __init__(self, model: CustomApexSelectionModel, view: CustomApexSelectionView):
        
        # models and views are instantiated outside this class
        # hence, they get passed to the initialization method
        self.model = model
        self.view = view

        self.setup_connections()
        
    def setup_connections(self):
        # Add/remove button connections
        self.view.add_remove_list_top_apex_columns.button_add.clicked.connect(self.clicked_top_apex_button_add)
        self.view.add_remove_list_top_apex_columns.button_remove.clicked.connect(self.clicked_top_apex_button_remove)
        self.view.add_remove_list_right_apex_columns.button_add.clicked.connect(self.clicked_right_apex_button_add)
        self.view.add_remove_list_right_apex_columns.button_remove.clicked.connect(self.clicked_right_apex_button_remove)
        self.view.add_remove_list_left_apex_columns.button_add.clicked.connect(self.clicked_left_apex_button_add)
        self.view.add_remove_list_left_apex_columns.button_remove.clicked.connect(self.clicked_left_apex_button_remove)

    def clicked_top_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's top_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_top_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_top_apex_button_remove(self):
        """Gets selected column from view's top_apex columns,
        adds to model's available columns and removes from model's top_apex columns"""
        selected_column = self.view.add_remove_list_top_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_top_apex_column(col)
            self.model.add_available_column(col)

    def clicked_right_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's right_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_right_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_right_apex_button_remove(self):
        """Gets selected column from view's right_apex columns,
        adds to model's available columns and removes from model's right_apex columns"""
        selected_column = self.view.add_remove_list_right_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_right_apex_column(col)
            self.model.add_available_column(col)

    def clicked_left_apex_button_add(self):
        """Gets selected column from view's available_columns,
        adds to model's left_apex_columns and removes from model's available columns"""
        selected_column = self.view.list_widget_available_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.add_left_apex_column(col)
            self.model.remove_available_column(col)

    def clicked_left_apex_button_remove(self):
        """Gets selected column from view's left_apex columns,
        adds to model's available columns and removes from model's left_apex columns"""
        selected_column = self.view.add_remove_list_left_apex_columns.currentItem()
        if selected_column is not None:
            col = selected_column.text()
            self.model.remove_left_apex_column(col)
            self.model.add_available_column(col)
