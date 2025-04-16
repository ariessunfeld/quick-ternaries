from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QLabel, 
    QComboBox, 
    QDialogButtonBox
)
from quick_ternaries.utils.functions import (
    get_preview_data, 
    get_suggested_header
)

class HeaderSelectionDialog(QDialog):
    def __init__(self, file_path, sheet=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.sheet = sheet
        self.setWindowTitle("Select Header Row")
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Please select the header row:"))

        self.combo = QComboBox(self)

        # Get preview data using the updated helper; this shows up to 24 rows and 8 columns per row
        preview_data = get_preview_data(
            file_path, sheet, 24
        )  # Assumes get_preview_data is implemented
        n_rows = len(preview_data)

        for i in range(n_rows):
            row_data = preview_data[i]
            displayed_columns = row_data[:8]  # Limit to first 8 columns
            option_text = f"Row {i}: " + ", ".join(map(str, displayed_columns)) + " ..."
            self.combo.addItem(option_text, userData=i)

        # Use the new get_suggested_header with the sheet parameter
        suggested = get_suggested_header(file_path, sheet)
        if suggested is not None and suggested < n_rows:
            self.combo.setCurrentIndex(suggested)

        layout.addWidget(self.combo)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    @staticmethod
    def getHeader(parent, file_path, sheet=None):
        dialog = HeaderSelectionDialog(file_path, sheet, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.combo.currentData(), True
        return None, False