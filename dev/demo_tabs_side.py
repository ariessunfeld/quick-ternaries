from PySide6.QtWidgets import QApplication, QTabWidget, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

class TabDemo(QTabWidget):
    def __init__(self, parent=None):
        super(TabDemo, self).__init__(parent)

        # Set tab position to the West (left side)
        self.setTabPosition(QTabWidget.West)

        # Create the first tab
        self.tab1 = QWidget()
        self.tab1_layout = QVBoxLayout(self.tab1)
        self.tab1_label = QLabel('Content of tab 1')
        self.tab1_layout.addWidget(self.tab1_label)

        # Create the second tab
        self.tab2 = QWidget()
        self.tab2_layout = QVBoxLayout(self.tab2)
        self.tab2_label = QLabel('Content of tab 2')
        self.tab2_layout.addWidget(self.tab2_label)

        # Add tabs to the QTabWidget
        self.addTab(self.tab1, "Tab 1")
        self.addTab(self.tab2, "Tab 2")

if __name__ == "__main__":
    app = QApplication([])
    tab_demo = TabDemo()
    tab_demo.show()
    app.exec()

