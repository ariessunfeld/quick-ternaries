"""Megawidget for heatmap configuration within a trace"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout
)
from PySide6.QtCore import Qt
from src.views.utils import LeftLabeledLineEdit, LeftLabeledComboBox, InfoButton

class TernaryHeatmapEditorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Heatmap Column ComboBox
        self.heatmap_column_combobox = LeftLabeledComboBox('Heatmap Column:')
        #self.heatmap_column_combobox.combobox.addItem('File')  # Example item
        self.main_layout.addWidget(self.heatmap_column_combobox)

        # Range Min and Max LineEdits with an InfoButton
        self.range_layout = QHBoxLayout()
        
        self.range_min_line_edit = LeftLabeledLineEdit('Range min:')
        self.range_layout.addWidget(self.range_min_line_edit)
        
        self.range_max_line_edit = LeftLabeledLineEdit('Range max:')
        self.range_layout.addWidget(self.range_max_line_edit)

        # Tooltip InfoButton
        tooltip_text = (
            "Tip: Set a low 'range max' to bring out the gradient in your data.\n"
            "Points with higher values than 'range max' will still be plotted; \n"
            "they will just have the same color as the highest value on the scale.\n"
            "The default 'range max' value is twice the median of the selected column."
        )
        self.info_button = InfoButton(self, tooltip_text)
        self.range_layout.addWidget(self.info_button, alignment=Qt.AlignRight)
        
        self.main_layout.addLayout(self.range_layout)
