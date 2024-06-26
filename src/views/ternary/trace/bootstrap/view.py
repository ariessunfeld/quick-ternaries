from typing import Any, Optional
from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QTableView, 
    QHeaderView,
    QGroupBox
)
import pandas as pd

from src.views.utils import (
    LeftLabeledLineEdit, 
    LeftLabeledColorPicker,
    LeftLabeledComboBox
)

from src.models.utils.pandas_series_model import PandasSeriesModel

class TernaryBootstrapTraceEditorView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        # GroupBox to hold the QTableView
        self.group_box = QGroupBox("Selected Point", self)
        self.group_box.setMaximumHeight(110)
        self.group_box_layout = QVBoxLayout(self.group_box)

        # QTableView to display pd.Series
        self.table_view = QTableView(self)
        self.table_view.setMaximumHeight(100)  # Set a fixed maximum height
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.group_box_layout.addWidget(self.table_view)

        self.layout.addWidget(self.group_box)

        # LeftLabeledLineEdit for Name
        self.name_edit = LeftLabeledLineEdit("Contour name:")
        
        # LeftLabeledColorPicker for Color
        self.color_picker = LeftLabeledColorPicker("Contour color:")
        
        # Dropdown for sigma selection
        self.sigma_dropdown = LeftLabeledComboBox("Contour:")
        self.sigma_dropdown.addItems(["1 sigma", "2 sigma", "custom"])

        # LeftLabeledLineEdit for custom percentile
        self.percentile_edit = LeftLabeledLineEdit("Percentile:")

        self.layout.addWidget(self.sigma_dropdown)
        self.layout.addWidget(self.percentile_edit)
        self.layout.addWidget(self.name_edit)
        self.layout.addWidget(self.color_picker)

        # Connect the dropdown to visibility update method
        self.sigma_dropdown.valueChanged.connect(self.update_percentile_visibility)

        # Initial state: hide the custom percentile input
        self.update_percentile_visibility('1 sigma')

    def update_percentile_visibility(self, value: str) -> None:
        """Update the visibility of the custom percentile input based on the dropdown selection."""
        if value == 'custom':
            self.percentile_edit.clear()
            self.percentile_edit.setEnabled(True)
        elif value == '1 sigma':
            self.percentile_edit.setText('68.0')
            self.percentile_edit.setEnabled(False)
        elif value == '2 sigma':
            self.percentile_edit.setText('95.0')
            self.percentile_edit.setEnabled(False)

    def refresh(self, model: Any) -> None:
        """Refresh the view with data from the model."""
        # Update the table view with the pd.Series data
        series: pd.Series = model.get_series()
        self.table_view.setModel(PandasSeriesModel(series))
        self.table_view.setMaximumHeight(100)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Update the name and color fields
        self.name_edit.setText(model.get_name())
        self.color_picker.setColor(model.get_color())

        # Update the sigma dropdown
        sigma_value = model.get_sigma()
        if sigma_value in ["1 sigma", "2 sigma"]:
            self.sigma_dropdown.setCurrentText(sigma_value)
        else:
            self.sigma_dropdown.setCurrentText("custom")
            self.percentile_edit.setText(str(sigma_value))
        
        # Update visibility
        self.update_percentile_visibility(sigma_value)

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create a dummy model for demonstration
    class DummyModel:
        def get_series(self):
            return pd.Series({'Col1': 1, 'Col2': 2, 'Col3': 3, 'Col4': 4})

        def get_name(self):
            return "Dummy Name"

        def get_color(self):
            return "#ff0000"

        def get_sigma(self):
            return "1 sigma"

    window = TernaryBootstrapTraceEditorView()
    window.refresh(DummyModel())
    window.show()

    sys.exit(app.exec_())
