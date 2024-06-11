"""
Contains the TraceView(QWidget) class, 
which contains the widgets needed for configuring individual traces, 
and is used in the dynamic content area of the MainWindow
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QSpinBox,
    QColorDialog,
    QPushButton,
    QCheckBox,
    QApplication
)
from PySide6.QtCore import Qt
from src.views.utils import (
    LeftLabeledLineEdit, 
    LeftLabeledCheckbox, 
    LeftLabeledComboBox, 
    LeftLabeledSpinBox, 
    LeftLabeledColorPicker
)


class TernaryTraceEditorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Select Data
        self.select_data = LeftLabeledComboBox('Select Data:')
        #self.select_data.combobox.addItem('DATA.csv')  # Example item
        self.layout.addWidget(self.select_data)

        # Convert from wt% to molar
        self.convert_wtp_molar_checkbox = LeftLabeledCheckbox('Convert from wt% to molar:')
        self.convert_wtp_molar_checkbox.checkbox.setChecked(True)
        self.layout.addWidget(self.convert_wtp_molar_checkbox)

        # Name
        self.name_line_edit = LeftLabeledLineEdit('Name:')
        self.layout.addWidget(self.name_line_edit)

        # Point Size
        self.point_size_spinbox = LeftLabeledSpinBox('Point Size:')
        self.point_size_spinbox.setValue(6)
        self.layout.addWidget(self.point_size_spinbox)

        # Select Point Shape
        self.select_point_shape = LeftLabeledComboBox('Select Point Shape:')
        self.select_point_shape.addItems([
            'circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 
            'triangle-down', 'triangle-left', 'triangle-right', 'pentagon', 
            'hexagon', 'star', 'hexagram', 'star-square', 'star-diamond', 
            'star-triangle-up', 'star-triangle-down'
        ])
        self.layout.addWidget(self.select_point_shape)

        # Color
        self.color_picker = LeftLabeledColorPicker('Color:')
        self.layout.addWidget(self.color_picker)

        # Use Heatmap
        self.use_heatmap_checkbox = LeftLabeledCheckbox('Use Heatmap')
        self.layout.addWidget(self.use_heatmap_checkbox)

        # Use Filter(s)
        self.use_filter_checkbox = LeftLabeledCheckbox('Use Filter(s)')
        self.layout.addWidget(self.use_filter_checkbox)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = TernaryTraceEditorView()
    window.show()

    sys.exit(app.exec())