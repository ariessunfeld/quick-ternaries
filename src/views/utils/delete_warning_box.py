"""Message box with Delete and Cancel buttons"""

from PySide6.QtWidgets import QMessageBox

class DeleteWarningBox(QMessageBox):
    def __init__(self, title: str, text: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(QMessageBox.Question)
        self.addButton('Delete', QMessageBox.YesRole)
        self.addButton('Cancel', QMessageBox.NoRole)
