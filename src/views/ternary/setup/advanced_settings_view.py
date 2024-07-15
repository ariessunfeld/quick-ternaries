from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QGridLayout

from src.views.utils import (
    LeftLabeledSpinBox, LeftLabeledColorPicker, LeftLabeledComboBox,
    LeftLabeledFontComboBox, LeftLabeledCheckbox
)

class AdvancedSettingsView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.setup_ui()

    def setup_ui(self):
        self.setup_plot_structure()
        self.setup_colors()
        self.setup_fonts()
        self.main_layout.addStretch(1)

    def setup_plot_structure(self):
        group = QGroupBox("Plot Structure")
        layout = QGridLayout()

        self.ternary_sum_combo = LeftLabeledComboBox("Ternary Sum:")
        self.ternary_sum_combo.addItems(["1", "100"])
        layout.addWidget(self.ternary_sum_combo, 0, 0)

        self.show_grid = LeftLabeledCheckbox("Show Grid")
        self.show_grid.setChecked(True)
        layout.addWidget(self.show_grid, 1, 0)

        self.gridline_step_size = LeftLabeledSpinBox("Gridline Step Size:")
        self.gridline_step_size.setRange(1, 100)
        layout.addWidget(self.gridline_step_size, 1, 1)

        self.show_tick_marks = LeftLabeledCheckbox("Show Tick Marks")
        self.show_tick_marks.setChecked(True)
        layout.addWidget(self.show_tick_marks, 2, 0)

        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def setup_colors(self):
        group = QGroupBox("Colors")
        layout = QGridLayout()

        self.background_color = LeftLabeledColorPicker("Background Color:")
        layout.addWidget(self.background_color, 0, 0)

        self.paper_color = LeftLabeledColorPicker("Paper Color:")
        layout.addWidget(self.paper_color, 1, 0)

        self.gridline_color = LeftLabeledColorPicker("Gridline Color:")
        layout.addWidget(self.gridline_color, 2, 0)

        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def setup_fonts(self):
        group = QGroupBox("Fonts")
        layout = QGridLayout()

        self.title_font_combo = LeftLabeledFontComboBox("Title Font:")
        layout.addWidget(self.title_font_combo, 0, 0)
        self.title_font_size_spinbox = LeftLabeledSpinBox("Title Font Size:")
        self.title_font_size_spinbox.setMinimum(1)
        layout.addWidget(self.title_font_size_spinbox, 0, 1)

        self.axis_font_combo = LeftLabeledFontComboBox("Axis Label Font:")
        layout.addWidget(self.axis_font_combo, 1, 0)
        self.axis_font_size_spinbox = LeftLabeledSpinBox("Axis Label Font Size:")
        self.axis_font_size_spinbox.setMinimum(1)
        layout.addWidget(self.axis_font_size_spinbox, 1, 1)

        self.tick_font_combo = LeftLabeledFontComboBox("Tick Font:")
        layout.addWidget(self.tick_font_combo, 2, 0)
        self.tick_font_size_spinbox = LeftLabeledSpinBox("Tick Font Size:")
        self.tick_font_size_spinbox.setMinimum(1)
        layout.addWidget(self.tick_font_size_spinbox, 2, 1)

        group.setLayout(layout)
        self.main_layout.addWidget(group)
