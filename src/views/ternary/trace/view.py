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
    QApplication,
    QScrollArea
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
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Scroll area to hold the content layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # Widget to hold all the content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.scroll_area.setWidget(self.content_widget)

        # Select Data
        self.select_data = LeftLabeledComboBox('Select Data:')
        #self.select_data.combobox.addItem('DATA.csv')  # Example item
        self.content_layout.addWidget(self.select_data)

        # Convert from wt% to molar
        self.convert_wtp_molar_checkbox = LeftLabeledCheckbox('Convert from wt% to molar:')
        self.convert_wtp_molar_checkbox.checkbox.setChecked(True)
        self.content_layout.addWidget(self.convert_wtp_molar_checkbox)

        # Name
        self.name_line_edit = LeftLabeledLineEdit('Name:')
        self.content_layout.addWidget(self.name_line_edit)

        # Point Size
        self.point_size_spinbox = LeftLabeledSpinBox('Point Size:')
        self.point_size_spinbox.setValue(6)
        self.content_layout.addWidget(self.point_size_spinbox)

        # Select Point Shape
        self.select_point_shape = LeftLabeledComboBox('Select Point Shape:')
        self.select_point_shape.addItems([
            'circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 
            'triangle-down', 'triangle-left', 'triangle-right', 'pentagon', 
            'hexagon', 'star', 'hexagram', 'star-square', 'star-diamond', 
            'star-triangle-up', 'star-triangle-down'
        ])
        self.content_layout.addWidget(self.select_point_shape)

        # Color
        self.color_picker = LeftLabeledColorPicker('Color:')
        self.content_layout.addWidget(self.color_picker)

        # Use Heatmap
        self.use_heatmap_checkbox = LeftLabeledCheckbox('Use Heatmap')
        self.content_layout.addWidget(self.use_heatmap_checkbox)

        # Use Filter(s)
        self.use_filter_checkbox = LeftLabeledCheckbox('Use Filter(s)')
        self.content_layout.addWidget(self.use_filter_checkbox)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = TernaryTraceEditorView()
    window.show()

    sys.exit(app.exec())