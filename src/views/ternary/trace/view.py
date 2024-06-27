"""
Contains the TraceView(QWidget) class, 
which contains the widgets needed for configuring individual traces, 
and is used in the dynamic content area of the MainWindow
"""

from src.views.ternary.trace.heatmap_editor_view import TernaryHeatmapEditorView
from src.views.ternary.trace.molar_conversion_view import TernaryTraceMolarConversionView
from src.views.ternary.trace.filter.view import FilterPanelView
from src.views.ternary.trace.bootstrap.error_entry_view import TernaryBootstrapErrorEntryView

from src.models.utils.pandas_series_model import PandasSeriesModel

import pandas as pd

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
    QScrollArea,
    QGroupBox,
    QTableView,
    QHeaderView
)
from PySide6.QtCore import Qt
from src.views.utils import (
    LeftLabeledLineEdit, 
    LeftLabeledCheckbox, 
    LeftLabeledComboBox, 
    LeftLabeledSpinBox, 
    LeftLabeledColorPicker,
    InfoButton
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

        self.error_entry_view = TernaryBootstrapErrorEntryView()
        self.error_entry_view.setVisible(False)
        self.content_layout.addWidget(self.error_entry_view)

        # GroupBox to hold the QTableView
        self.group_box = QGroupBox("Selected Point", self)
        self.group_box.setMaximumHeight(110)
        self.group_box_layout = QVBoxLayout(self.group_box)
        # QTableView to display pd.Series
        self.table_view = QTableView(self)
        self.table_view.setMaximumHeight(100)  # Set a fixed maximum height
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.group_box_layout.addWidget(self.table_view)
        self.group_box.setVisible(False) # False by default
        self.content_layout.addWidget(self.group_box)

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

        # Dropdown for sigma selection
        self.sigma_dropdown = LeftLabeledComboBox("Contour:")
        self.sigma_dropdown.addItems(["1 sigma", "2 sigma", "custom"])

        # LeftLabeledLineEdit for custom percentile
        self.percentile_edit = LeftLabeledLineEdit("Percentile:", 1)
        self.percentile_edit.setEnabled(False)

        self.sigma_dropdown.setVisible(False)
        self.percentile_edit.setVisible(False)
        self.content_layout.addWidget(self.sigma_dropdown)
        self.content_layout.addWidget(self.percentile_edit)

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

    def switch_to_bootstrap_view(self):

        # Freeze the selected data combobox
        self.select_data.setEnabled(False)

        # Hide the irrelevant widgets
        self.point_size_spinbox.setVisible(False)
        self.select_point_shape.setVisible(False)
        self.use_heatmap_checkbox.setVisible(False)
        self.use_filter_checkbox.setVisible(False)

        # Show the bootstrap widgets
        self.group_box.setVisible(True)
        self.sigma_dropdown.setVisible(True)
        self.percentile_edit.setVisible(True)
        self.error_entry_view.setVisible(True)

    def switch_to_standard_view(self):
        
        # Unfreeze the selected data combobox
        self.select_data.setEnabled(True)

        # Unhide the now-relevant widgets
        self.point_size_spinbox.setVisible(True)
        self.select_point_shape.setVisible(True)
        self.use_heatmap_checkbox.setVisible(True)
        self.use_filter_checkbox.setVisible(True)

        # Hide the bootstrap widgets
        self.group_box.setVisible(False)
        self.sigma_dropdown.setVisible(False)
        self.percentile_edit.setVisible(False)
        self.error_entry_view.setVisible(False)

    def refresh_table_from_series(self, series: pd.Series):
        self.table_view.setModel(PandasSeriesModel(series))
        self.table_view.setMaximumHeight(100)
        
        # Adjust the header to resize to contents initially
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(False)  # Optional: to ensure all columns resize to their contents
        
        # Enable interactive resizing
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Resize the rows to fit the content
        self.table_view.resizeRowsToContents()
        self.table_view.resizeColumnsToContents()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)

    window = TernaryTraceEditorView()
    window.show()

    sys.exit(app.exec())