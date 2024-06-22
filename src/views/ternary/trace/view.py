"""
Contains the TraceView(QWidget) class, 
which contains the widgets needed for configuring individual traces, 
and is used in the dynamic content area of the MainWindow
"""

from src.views.ternary.trace.heatmap_editor_view import TernaryHeatmapEditorView
from src.views.ternary.trace.molar_conversion_view import TernaryTraceMolarConversionView
from src.views.ternary.trace.filter.view import FilterPanelView

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QApplication,
    QScrollArea
)
from src.views.utils import (
<<<<<<< HEAD
    LeftLabeledLineEdit,
    LeftLabeledCheckbox,
    LeftLabeledComboBox,
    LeftLabeledSpinBox,
    LeftLabeledColorPicker
=======
    LeftLabeledLineEdit, 
    LeftLabeledCheckbox, 
    LeftLabeledComboBox, 
    LeftLabeledSpinBox, 
    LeftLabeledColorPicker,
    InfoButton
>>>>>>> origin/ari
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
        self.convert_molar_checkbox_layout = QHBoxLayout()
        self.convert_wtp_molar_checkbox = LeftLabeledCheckbox('Convert from wt% to molar:')
        self.convert_wtp_molar_checkbox.checkbox.setChecked(False)
        self.convert_molar_checkbox_layout.addWidget(self.convert_wtp_molar_checkbox)
        text = (
            "Tip: When this box is checked, data from this trace that is from the\n"
            "columns specified in the Ternary Type section in the Start Setup view\n"
            "will be converted from weight percent (wt%) to molar proportion.\n"
            "For this to work, valid chemical formulae need to be provided for each column.\n"
            "By default, the column name is used if it is already a valid chemical formula.\n"
            "But if a column is named `Al2O3_corrected`, e.g., you must use the panel that\n"
            "will appear below this checkbox to edit the valid formula to `Al2O3`.\n\n"
            "Note: scaling apices (e.g., `2xAl2O3`) should be done in Start Setup view.")
        self.convert_wtp_molar_infobutton = InfoButton(self, text)
        self.convert_molar_checkbox_layout.addWidget(self.convert_wtp_molar_infobutton, alignment=Qt.AlignRight)
        self.content_layout.addLayout(self.convert_molar_checkbox_layout)

        # Molar conversion specification
        self.molar_conversion_view = TernaryTraceMolarConversionView()
        self.molar_conversion_view.setVisible(False)
        self.content_layout.addWidget(self.molar_conversion_view)

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

        # Heatmap view (hide at first)
        self.heatmap_view = TernaryHeatmapEditorView()
        self.content_layout.addWidget(self.heatmap_view)
        self.heatmap_view.setVisible(False)

        # Use Filter(s)
        self.use_filter_checkbox = LeftLabeledCheckbox('Use Filter(s)')
        self.content_layout.addWidget(self.use_filter_checkbox)

        # Filter view (hide at first)
        self.filter_view = FilterPanelView()
        self.content_layout.addWidget(self.filter_view)
        self.filter_view.setVisible(False)

        # Add the scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area)

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = TernaryTraceEditorView()
    window.show()

    sys.exit(app.exec())
