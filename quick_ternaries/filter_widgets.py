"""This module contains several classes useful for designing filter widgets
using PySide6

AvailableValuesList: A subclass of QListWidget that handles transferring values to
    a SelectedValuesList by pressing the Enter or Return key

SelectedValuesList: A subclass of QListWidget that handles transferring values back
    to an associated AvailableValuesList by pressing the Delete or Backspace key

FilterDialog: A subclass of QDialog that is a container for filter widgets and 
    supports cumulative filter application to a dataframe

FiltersWidget: A subclass of QWidget that contains a scroll area and handles 
    adding / supports removing FilterWidgets from its scroll area
"""

from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QPushButton, QLabel, QWidget, QLineEdit, QComboBox, 
    QListWidget, QCompleter, QScrollArea, QMessageBox,
    QDialog)
from PySide6.QtCore import Qt, Slot

import numpy as np

from quick_ternaries.filter_strategies import (
    EqualsFilterStrategy, OneOfFilterStrategy, GreaterThanFilterStrategy,
    GreaterEqualFilterStrategy, LessThanFilterStrategy, LessEqualFilterStrategy,
    BetweenFilterStrategy, BetweenEqualFilterStrategy, BetweenLowerEqualFilterStrategy,
    BetweenHigherEqualFilterStrategy
)

class AvailableValuesList(QListWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.main_window.add_value(self.main_window.selected_values)

class SelectedValuesList(QListWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.main_window.remove_value(self)

class FilterDialog(QDialog):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.setWindowTitle("Filter Settings")

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFocusPolicy(Qt.NoFocus)

        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setFocusPolicy(Qt.NoFocus)

        self.main_window = main_window
        # Set up the FiltersWidget
        self.filters_scroll_area = FiltersWidget(self.main_window)
        self.filters_scroll_area.setMinimumSize(500, 400)

        # Set up the layout
        layout         = QVBoxLayout(self)
        buttons_layout = QHBoxLayout()

        layout.addWidget(self.filters_scroll_area)
        buttons_layout.addWidget(self.ok_button)
        buttons_layout.addWidget(self.cancel_button)
        layout.addLayout(buttons_layout)

    def inject_data_to_filter(self, filter, df):
        if df is not None:
            filter.column_combobox.clear()
            filter.column_combobox.addItems(df.columns)
            filter.update_visibility()

    def apply_all_filters(self, df):
        for filter_widget in self.filters_scroll_area.filters:
            df = filter_widget.apply_filter(df)
        return df

class FilterWidget(QWidget):

    OBJECT_OPERATION_COMBOBOX_CHOICES = [
        'Equals', 'One of']
    NUMERIC_OPERATION_COMBOBOX_CHOICES = [
        'Equals', 'One of', 
        '<', '>', '<=', '>=', 
        'a < x < b', 'a <= x <= b', 'a < x <= b', 'a <= x < b']
    A_B_OPERATION_COMBOBOX_CHOICES = [
        'a < x < b', 'a <= x <= b', 'a < x <= b', 'a <= x < b']

    def __init__(self, main_window):
        super().__init__()

        self.operation_strategies = {
            'Equals': EqualsFilterStrategy(),
            'One of': OneOfFilterStrategy(),
            '<': LessThanFilterStrategy(),
            '>': GreaterThanFilterStrategy(),
            '<=': LessEqualFilterStrategy(),
            '>=': GreaterEqualFilterStrategy(),
            'a < x < b': BetweenFilterStrategy(),
            'a <= x <= b': BetweenEqualFilterStrategy(),
            'a <= x < b': BetweenLowerEqualFilterStrategy(),
            'a < x <= b': BetweenHigherEqualFilterStrategy()
            # Add other strategies here
        }

        self.main_window = main_window

        # Initialize widgets
        self.column_combobox = QComboBox()
        self.column_combobox_label = QLabel("Filter Column:")
        self.operation_combobox = QComboBox()
        self.operation_combobox_label = QLabel("Filter Operation:")
        self.value_entry_1 = QLineEdit()
        self.value_entry_1_label = QLabel('Filter Value(s):')
        self.value_entry_2 = QLineEdit()
        self.value_entry_2_label = QLabel('Value b:')
        self.available_values = AvailableValuesList(self)
        self.available_values_label = QLabel('Available Values')
        self.available_values_label.setAlignment(Qt.AlignCenter)
        self.add_button = QPushButton('Add >>')
        self.add_button.setFocusPolicy(Qt.NoFocus)
        self.rem_button = QPushButton('Remove <<')
        self.rem_button.setFocusPolicy(Qt.NoFocus)
        self.selected_values = SelectedValuesList(self)
        self.selected_values_label = QLabel('Selected Values')
        self.selected_values_label.setAlignment(Qt.AlignCenter)
        self.remove_button = QPushButton('Remove This Filter')
        self.remove_button.setFocusPolicy(Qt.NoFocus)

        # Initialize layout and add widgets
        self.layout = QGridLayout(self)
        self.layout.addWidget(self.column_combobox_label, 0, 0) # Column
        self.layout.addWidget(self.column_combobox, 0, 1)
        self.layout.addWidget(self.operation_combobox_label, 1, 0) # Operation
        self.layout.addWidget(self.operation_combobox, 1, 1)
        self.layout.addWidget(self.value_entry_1_label, 2, 0) # Value a
        self.layout.addWidget(self.value_entry_1, 2, 1)
        self.layout.addWidget(self.value_entry_2_label, 3, 0) # Value b
        self.layout.addWidget(self.value_entry_2, 3, 1)

        # Initialize layout for "One of" selection
        self.pick_values_layout = QHBoxLayout()
        # Add available values area
        self.available_values_layout = QVBoxLayout()
        self.available_values_layout.addWidget(self.available_values_label)
        self.available_values_layout.addWidget(self.available_values)
        self.pick_values_layout.addLayout(self.available_values_layout)
        # Add add/rem buttons
        self.add_remove_layout = QVBoxLayout()
        self.add_remove_layout.addWidget(self.add_button)
        self.add_remove_layout.addWidget(self.rem_button)
        self.pick_values_layout.addLayout(self.add_remove_layout)
        # Add selected values area
        self.selected_values_layout = QVBoxLayout()
        self.selected_values_layout.addWidget(self.selected_values_label)
        self.selected_values_layout.addWidget(self.selected_values)
        self.pick_values_layout.addLayout(self.selected_values_layout)
        # Add everything to self.layout
        self.layout.addLayout(self.pick_values_layout, 4, 1)

        # Add a removal button for the entire filter
        self.layout.addWidget(self.remove_button, 0, 2)

        # Connect signals
        self.column_combobox.currentIndexChanged.connect(self.update_operation_combobox)
        self.column_combobox.currentIndexChanged.connect(self.update_value_entry_completer)
        self.operation_combobox.currentIndexChanged.connect(self.update_value_entry_completer)
        self.operation_combobox.currentIndexChanged.connect(self.update_visibility)
        self.add_button.clicked.connect(
            lambda checked=False, lw=self.selected_values: self.add_value(lw))
        self.rem_button.clicked.connect(
            lambda checked=False, lw=self.selected_values: self.remove_value(lw))

        self.update_visibility()

    def update_operation_combobox(self):
        column_name = self.column_combobox.currentText()
        if column_name:  # If there is a selected column
            dtype = self.main_window.df[column_name].dtype
            if dtype == 'object':  # If the dtype is object (likely string)
                self.operation_combobox.clear()
                self.operation_combobox.addItems(
                    FilterWidget.OBJECT_OPERATION_COMBOBOX_CHOICES)
            elif np.issubdtype(dtype, np.number):  # If the dtype is numeric
                self.operation_combobox.clear()
                self.operation_combobox.addItems(
                    FilterWidget.NUMERIC_OPERATION_COMBOBOX_CHOICES)
            else:
                # TODO handle this case differently from numeric "elif" case
                self.operation_combobox.clear()
                self.operation_combobox.addItems(
                    FilterWidget.NUMERIC_OPERATION_COMBOBOX_CHOICES)
        else:  # No selected column, clear the operations dropdown
            self.operation_combobox.clear()

    def update_value_entry_completer(self):
        column_name = self.column_combobox.currentText()
        if column_name:
            unique_values = self.main_window.df[column_name].dropna().unique()
            sorted_unique_values = sorted([v for v in unique_values])
            str_unique_values = [str(val) for val in sorted_unique_values]
            completer = QCompleter(str_unique_values, self)
            self.value_entry_1.setCompleter(completer)
            self.value_entry_2.setCompleter(completer)
            self.available_values.clear()
            self.selected_values.clear()
            self.available_values.addItems(str_unique_values)
        else:
            self.available_values.clear()
            self.selected_values.clear()
            self.value_entry_1.setCompleter(None)
            self.value_entry_2.setCompleter(None)

    def update_visibility(self):
        # Update Value 1 label based on a/b selection 
        is_a_b = self.operation_combobox.currentText() in FilterWidget.A_B_OPERATION_COMBOBOX_CHOICES
        if is_a_b:
            self.value_entry_1_label.setText('Value a:')
        else:
            self.value_entry_1_label.setText('Filter Value(s):')
        # Update Value 2 visibility based on a/b selection
        self.value_entry_2_label.setVisible(is_a_b)
        self.value_entry_2.setVisible(is_a_b)

        # Update add/remove pick_values_layout visibility based on One of selection
        is_one_of = self.operation_combobox.currentText() == 'One of'
        self.available_values.setVisible(is_one_of)
        self.available_values_label.setVisible(is_one_of)
        self.add_button.setVisible(is_one_of)
        self.rem_button.setVisible(is_one_of)
        self.selected_values.setVisible(is_one_of)
        self.selected_values_label.setVisible(is_one_of)

        # Also hide value 1 entry when One of is selected
        self.value_entry_1_label.setVisible(not is_one_of)
        self.value_entry_1.setVisible(not is_one_of)

    def add_value(self, lw):
        selected_item = self.available_values.currentItem()
        if selected_item is not None:
            self.available_values.takeItem(self.available_values.row(selected_item))
            lw.addItem(selected_item)

    def remove_value(self, lw):
        selected_item = lw.currentItem()
        if selected_item is not None:
            lw.takeItem(lw.row(selected_item))
            self.available_values.addItem(selected_item)

    def get_parameters(self):
        """ Get the current parameters of the filter. """
        sv = self.selected_values
        column = self.column_combobox.currentText()
        dtype = self.main_window.df[column].dtype

        selected_values = [sv.item(x).text() for x in range(sv.count())]

        if np.issubdtype(dtype, np.number):
            try:
                value1 = float(self.value_entry_1.text()) if self.value_entry_1.text() else None
                value2 = float(self.value_entry_2.text()) if self.value_entry_2.text() else None
                selected_values = [float(x) for x in selected_values] if selected_values else []
            except ValueError:
                QMessageBox.warning(self, "Input Error", "Please enter a numeric value.")
                return None
        else:
            value1 = self.value_entry_1.text()
            value2 = self.value_entry_2.text() if self.value_entry_2.text() else None



        return {
            'column': column,
            'operation': self.operation_combobox.currentText(),
            'value 1': value1,
            'value 2': value2,
            'selected values': selected_values,
        }

    def apply_filter(self, df):
        params = self.get_parameters()
        strategy = self.operation_strategies[params['operation']]
        return strategy.filter(df, params)


class FiltersWidget(QWidget):
    def __init__(self, main_window):
        """
        filters: [FilterWidget]
        """
        super().__init__()

        self.main_window = main_window
        self.layout = QVBoxLayout(self)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self.scroll_content = QWidget(self.scroll)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)

        self.add_filter_button = QPushButton('Add Another Filter', self)
        self.add_filter_button.clicked.connect(self.add_filter)
        self.add_filter_button.setFocusPolicy(Qt.NoFocus)

        self.layout.addWidget(self.scroll)
        self.layout.addWidget(self.add_filter_button)

        self.filters = []
        self.add_filter()

    @Slot()
    def add_filter(self):
        filter_widget = FilterWidget(self.main_window)
        filter_widget.remove_button.clicked.connect(lambda: self.remove_filter(filter_widget))
        self.filters.append(filter_widget)
        self.scroll_layout.addWidget(filter_widget)
        self.main_window.inject_data_to_filter(filter_widget)

    @Slot(QWidget)
    def remove_filter(self, filter_widget):
        filter_widget.setParent(None)
        self.filters.remove(filter_widget)

    def get_filters(self):
        """ Get a list of all currently set filters. """
        return [filter_widget.get_parameters() for filter_widget in self.filters]

if __name__ == '__main__':
    app = QApplication([])
    main = FiltersWidget([])
    main.show()
    app.exec()
