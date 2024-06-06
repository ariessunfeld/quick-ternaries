from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QListWidget,
    QComboBox,
    QCheckBox
)

class LoadedDataScrollView(QWidget):
    # This is where loaded data will be shown
    # Like the tabs for traces, loaded data should
    # have little Xs that allow for removal
    pass

    def add_item(self, *args):
        pass

    def remove_item(self, identifier, *args):
        pass