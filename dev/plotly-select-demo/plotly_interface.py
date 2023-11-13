from PySide6.QtCore import QObject, Slot

class PlotlyInterface(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selectedIndices = []
        self.selectedColor = 'blue'  # Default color

    @Slot(list)
    def receiveSelectedIndices(self, indices):
        self.selectedIndices = indices

    def applyColorChange(self):
        for index in self.selectedIndices:
            if 0 <= index < len(self.main_window.data):
                self.main_window.data.at[index, 'color'] = self.selectedColor
        self.main_window.plotTernary()  # Re-plot with updated colors

