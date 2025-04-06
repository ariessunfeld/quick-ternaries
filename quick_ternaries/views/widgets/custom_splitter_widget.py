from PySide6.QtWidgets import QSplitter
from quick_ternaries.views.widgets.custom_splitter_handle_widget import CustomSplitterHandle

class CustomSplitter(QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)


