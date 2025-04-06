from PySide6.QtWidgets import QSplitter
from src3.views.widgets.custom_splitter_handle_widget import CustomSplitterHandle

class CustomSplitter(QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)


