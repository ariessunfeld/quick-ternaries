from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QInputDialog,
    QMessageBox,
)
from PySide6.QtCore import Signal

# --------------------------------------------------------------------
# MultiFieldSelector Widget
# --------------------------------------------------------------------
class MultiFieldSelector(QWidget):
    """A composite widget that lets users select one or more fields.

    Displays current selections in a list with Add/Remove buttons.
    """

    selectionChanged = Signal(list)  # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_options = []
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.listWidget = QListWidget(self)
        self.listWidget.setMaximumHeight(100)
        layout.addWidget(self.listWidget)
        btn_layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        self.addButton = QPushButton("Add", self)
        self.removeButton = QPushButton("Remove", self)
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.removeButton)
        btn_layout.addStretch()
        self.addButton.clicked.connect(self.add_field)
        self.removeButton.clicked.connect(self.remove_field)

    def set_available_options(self, options):
        # Store options as list of strings
        self.available_options = [str(opt) for opt in options]

    def add_field(self):
        """Show a dialog to add a field, with better handling of empty
        options."""
        current_selected = self.get_selected_fields()
        choices = [opt for opt in self.available_options if opt not in current_selected]

        if not choices:
            print("No available choices in MultiFieldSelector.add_field()")
            QMessageBox.information(
                self,
                "No Available Fields",
                "There are no available fields to add. This may happen if there are no common columns across loaded data files.",
            )
            return

        item, ok = QInputDialog.getItem(
            self, "Select Field", "Available Fields:", choices, 0, False
        )
        if ok and item:
            self.listWidget.addItem(item)
            self.selectionChanged.emit(self.get_selected_fields())

    def remove_field(self):
        current_item = self.listWidget.currentItem()
        if current_item:
            row = self.listWidget.row(current_item)
            self.listWidget.takeItem(row)
            self.selectionChanged.emit(self.get_selected_fields())

    def get_selected_fields(self):
        """Return all currently selected fields as a list of strings."""
        return [self.listWidget.item(i).text() for i in range(self.listWidget.count())]

    def set_selected_fields(self, fields_list):
        """Set the selected fields in the list widget.

        Ensures all fields in fields_list are in available_options first.
        """
        # Clear current selections
        self.listWidget.clear()

        # Convert all fields to strings for consistency
        if not fields_list:
            return

        if isinstance(fields_list, str):
            # Handle case where a string was passed instead of a list
            fields_list = [f.strip() for f in fields_list.split(",")]

        # Make sure all values are strings
        fields_list = [str(field) for field in fields_list]

        # Make sure all fields to add are in available_options
        for field in fields_list:
            if field not in self.available_options:
                self.available_options.append(field)

        # Now add each field to the list widget
        for field in fields_list:
            self.listWidget.addItem(field)