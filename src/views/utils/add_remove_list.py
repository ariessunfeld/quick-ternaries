
from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QGridLayout,
    QListWidget,
    QComboBox,
    QCheckBox
)

class AddRemoveList(QWidget):
    """A megawidget for add/remove buttons to the left of a ListWidget"""
    def __init__(self, parent:QWidget|None=None, label: str|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.list = QListWidget()
        self.inner_layout = QVBoxLayout()
        self.inner_layout_widget = QWidget()
        self.button_add = QPushButton('Add >>')
        self.button_remove = QPushButton('Remove <<')
        if label:
            self.label = QLabel(label)
            self.inner_layout.addWidget(self.label)
        self.inner_layout.addWidget(self.button_add)
        self.inner_layout.addWidget(self.button_remove)
        self.inner_layout_widget.setLayout(self.inner_layout)
        self.layout.addWidget(self.inner_layout_widget)
        self.layout.addWidget(self.list)

    # Direct access to self.list methods (QListWidget methods) 
    def currentItem(self):
        return self.list.currentItem()
    
    def clear(self):
        self.list.clear()

    def addItem(self, data: str):
        self.list.addItem(data)

    def addItems(self, data: list[str]):
        self.list.addItems(data)

    def get_items(self):
        ret = []
        for row in range(len(self.list.count())):
            ret.append(self.list.itemAt(row).text())
        return ret