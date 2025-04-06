from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox

class SheetSelectionDialog(QDialog):
    """
    A dialog for selecting a sheet from an Excel file.
    """
    def __init__(self, file_path, sheets, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle("Select Sheet")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Please select the sheet:"))

        self.combo = QComboBox(self)
        for sheet in sheets:
            self.combo.addItem(sheet)
        layout.addWidget(self.combo)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)

    @staticmethod
    def getSheet(parent, file_path, sheets):
        """
        Static method to show the dialog and return the selected sheet.
        Args:
            parent: The parent widget.
            file_path: The path to the Excel file.
            sheets: A list of available sheets.
        Returns:
            A tuple containing the selected sheet name and a boolean indicating success.
        """
        dialog = SheetSelectionDialog(file_path, sheets, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.combo.currentText(), True
        return None, False
