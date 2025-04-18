from PySide6.QtWidgets import QFrame, QWidget

class HLineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget = QFrame(self)
        self.widget.setFrameShape(QFrame.HLine)
        self.widget.setFrameShadow(QFrame.Sunken)
