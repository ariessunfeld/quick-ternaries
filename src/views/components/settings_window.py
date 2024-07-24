from PySide6.QtWidgets import (
    QVBoxLayout,
    QPushButton,
    QDialog,
    QApplication,
    QFontDialog
)
from PySide6.QtCore import Qt, Signal
from src.views.utils import LeftLabeledSlider

class SettingsDialog(QDialog):
    font_changed = Signal(object)

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setup_settings_window()
        self.setup_connections()

    def setup_settings_window(self):
        self.setWindowTitle("Settings")

        # The main layout for the dialog
        layout = QVBoxLayout(self)

        self.font_size_spinbox = LeftLabeledSlider("Fontsize:")
        self.font_size_spinbox.setRange(6,17)
        self.font_size_spinbox.setValue(self.font().pointSize())

        # Button for advanced font settings
        self.font_advanced_button = QPushButton("Advanced Font Settings")
        self.font_advanced_button.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.font_size_spinbox)
        layout.addWidget(self.font_advanced_button)

    def setup_connections(self):
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)
        self.font_advanced_button.clicked.connect(self.font_advanced)

    def change_font_size(self, value: int):
        """
        Change font size.

        Args:
            value: The current fontsize.
        """
        font = QApplication.font()
        font.setPointSize(value)
        QApplication.setFont(font)
        self.font_changed.emit(font)

    def font_advanced(self):
        """
        Change font family/size.
        """
        ok, font = QFontDialog.getFont(QApplication.font(), self)
        if ok:
            QApplication.setFont(font)
            self.font_changed.emit(font)
