"""Contains the FilterEditorView(QWidget) class, 
which contains the widgets needed for configuring individual filters, 
and is used in the dynamic content area of the FilterMainWidget
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QSpacerItem,
    QSizePolicy
)
from src.views.utils import (
    LeftLabeledLineEdit,
    LeftLabeledComboBox,
    AddRemoveList
)

class FilterEditorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Filter Column ComboBox
        self.filter_column_combobox = LeftLabeledComboBox('Filter Column:')
        self.main_layout.addWidget(self.filter_column_combobox)

        # Filter Operation ComboBox
        self.filter_operation_combobox = LeftLabeledComboBox('Filter Operation:')
        self.main_layout.addWidget(self.filter_operation_combobox)

        # Filter Value(s) LineEdit
        self.filter_value_line_edit = LeftLabeledLineEdit('Filter Value:')
        self.main_layout.addWidget(self.filter_value_line_edit)

        # Value a and Value b LineEdits for range operations
        self.filter_value_a_line_edit = LeftLabeledLineEdit('Value a:')
        self.filter_value_b_line_edit = LeftLabeledLineEdit('Value b:')
        self.filter_value_a_line_edit.setVisible(False)
        self.filter_value_b_line_edit.setVisible(False)
        self.main_layout.addWidget(self.filter_value_a_line_edit)
        self.main_layout.addWidget(self.filter_value_b_line_edit)

        # Add/Remove layout
        self.add_remove_layout = QVBoxLayout()
        self.add_remove_layout_widget = QWidget()
        self.add_remove_layout_widget.setLayout(self.add_remove_layout)
        self.add_remove_layout_widget.setVisible(False)

        # Row for labels
        self.labels_layout = QHBoxLayout()
        self.available_values_label = QLabel("Available values")
        self.selected_values_label = QLabel("Selected values")
        self.labels_layout.addWidget(self.available_values_label)
        self.labels_layout.addStretch()
        self.labels_layout.addWidget(self.selected_values_label)

        # Row for list widgets
        self.lists_layout = QHBoxLayout()
        self.available_values_list = QListWidget()
        self.add_remove_list = AddRemoveList()
        self.lists_layout.addWidget(self.available_values_list)
        self.lists_layout.addWidget(self.add_remove_list)

        # Add rows to the main add/remove layout
        self.add_remove_layout.addLayout(self.labels_layout)
        self.add_remove_layout.addLayout(self.lists_layout)

        # Add the add/remove layout widget to the main layout
        self.main_layout.addWidget(self.add_remove_layout_widget)

    def clear(self):
        self.filter_column_combobox.clear()
        self.filter_operation_combobox.clear()
        self.filter_value_line_edit.clear()
        self.filter_value_a_line_edit.clear()
        self.filter_value_b_line_edit.clear()
        self.available_values_list.clear()
        self.add_remove_list.clear()
