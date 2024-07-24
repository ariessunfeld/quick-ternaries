"""Custom PushButton class, wraps QPushButton"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt

class PushButton(QPushButton):
    """Custom Pushbutton
    
    Can implement styling, etc here
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
