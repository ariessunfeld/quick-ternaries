from PySide6.QtWidgets import (
    QApplication, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QCheckBox, QComboBox, QToolButton, QToolTip, QStyle,
    QPushButton, QLabel, QWidget, QLineEdit, QComboBox, 
    QListWidget, QCompleter, QScrollArea, QMessageBox,
    QDialog, QSpacerItem, QSizePolicy, QFrame, QDoubleSpinBox)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCursor


class InfoButton(QWidget):
    def __init__(self, main_window, msg, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

        layout = QVBoxLayout(self)
        self.info_button = QToolButton()
        self.info_button.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.info_button.clicked.connect(lambda _ : self.show_info(msg))
        layout.addWidget(self.info_button)

    def show_info(self, msg):
        QToolTip.showText(QCursor.pos(), msg)

class ScaleFactorsSelection(QWidget):
    def __init__(self, main_window, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_window = main_window

        layout = QVBoxLayout(self)

        self.top_apex_list = QListWidget()
        self.left_apex_list = QListWidget()
        self.right_apex_list = QListWidget()

        self.top_apex_factors = [QDoubleSpinBox() for _ in range(self.main_window.selected_values_lists[0].count())]
        self.left_apex_factors = [QDoubleSpinBox() for _ in range(self.main_window.selected_values_lists[1].count())]
        self.right_apex_factors = [QDoubleSpinBox() for _ in range(self.main_window.selected_values_lists[2].count())]

        self.populate_list(self.top_apex_list, self.main_window.selected_values_lists[0])
        self.populate_list(self.left_apex_list, self.main_window.selected_values_lists[1])
        self.populate_list(self.right_apex_list, self.main_window.selected_values_lists[2])

        grid_layout = QGridLayout()

        grid_layout.addWidget(QLabel("Top"), 0, 0)
        grid_layout.addWidget(QLabel("Scale Factors"), 0, 1)
        self.add_items_to_layout(grid_layout, self.top_apex_list, self.top_apex_factors)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        grid_layout.addWidget(line1, self.top_apex_list.count() + 1, 0, 1, 2)

        grid_layout.addWidget(QLabel("Left"), self.top_apex_list.count() + 2, 0)
        grid_layout.addWidget(QLabel("Scale Factors"), self.top_apex_list.count() + 2, 1)
        self.add_items_to_layout(grid_layout, self.left_apex_list, self.left_apex_factors, start_index=self.top_apex_list.count() + 3)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        grid_layout.addWidget(line2, self.top_apex_list.count() + self.left_apex_list.count() + 3, 0, 1, 2)

        grid_layout.addWidget(QLabel("Right"), self.top_apex_list.count() + self.left_apex_list.count() + 4, 0)
        grid_layout.addWidget(QLabel("Scale Factors"), self.top_apex_list.count() + self.left_apex_list.count() + 4, 1)
        self.add_items_to_layout(grid_layout, self.right_apex_list, self.right_apex_factors, start_index=self.top_apex_list.count() + self.left_apex_list.count() + 5)

        layout.addLayout(grid_layout)

        # Connect signals from the main window to slots in this widget
        self.main_window.diagram_type_combobox.currentIndexChanged.connect(self.update_all_lists)
        self.main_window.selected_values_lists[0].itemChanged.connect(self.update_top_list)
        self.main_window.selected_values_lists[1].itemChanged.connect(self.update_left_list)
        self.main_window.selected_values_lists[2].itemChanged.connect(self.update_right_list)

    def populate_list(self, list_widget, source_list):
        for i in range(source_list.count()):
            list_widget.addItem(source_list.item(i).text())

    def add_items_to_layout(self, layout, list_widget, factors, start_index=1):
        for i in range(list_widget.count()):
            layout.addWidget(list_widget.itemWidget(list_widget.item(i)), start_index + i, 0)
            layout.addWidget(factors[i], start_index + i, 1)

    def update_all_lists(self):
        self.update_top_list()
        self.update_left_list()
        self.update_right_list()

    def update_top_list(self):
        self.top_apex_list.clear()
        print(self.main_window.selected_values_lists[0])
        self.populate_list(self.top_apex_list, self.main_window.selected_values_lists[0])
        self.update_scale_factors(self.top_apex_factors, self.main_window.selected_values_lists[0])

    def update_left_list(self):
        self.left_apex_list.clear()
        self.populate_list(self.left_apex_list, self.main_window.selected_values_lists[1])
        self.update_scale_factors(self.left_apex_factors, self.main_window.selected_values_lists[1])

    def update_right_list(self):
        self.right_apex_list.clear()
        self.populate_list(self.right_apex_list, self.main_window.selected_values_lists[2])
        self.update_scale_factors(self.right_apex_factors, self.main_window.selected_values_lists[2])

    def update_scale_factors(self, factors_list, source_list):
        while len(factors_list) > source_list.count():
            factors_list.pop().deleteLater()
        while len(factors_list) < source_list.count():
            factors_list.append(QDoubleSpinBox())
    

        



class AdvancedCheckboxComboWidget(QWidget):
    def __init__(self, chkbx_name, label, tip_msg, main_window=None):
        super().__init__(main_window)

        layout = QVBoxLayout(self)
        upper_level = QHBoxLayout()
        lower_level = QHBoxLayout()

        self.checkbox = QCheckBox(chkbx_name)
        self.label = QLabel(label)
        self.choice = QComboBox()
        self.info_button = InfoButton(self, tip_msg)
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        upper_level.addWidget(self.checkbox)
        upper_level.addItem(self.spacer)
        upper_level.addWidget(self.info_button)

        layout.addLayout(upper_level)

        lower_level.addWidget(self.label)
        lower_level.addWidget(self.choice)

        layout.addLayout(lower_level)

        # Appearance
        self.choice.setVisible(False)
        self.label.setVisible(False)

        # Signals
        self.checkbox.stateChanged.connect(self.update_visibility)

    def update_visibility(self):
        is_checked = self.checkbox.isChecked()
        self.choice.setVisible(is_checked)
        self.label.setVisible(is_checked)
    
    def add_choices(self, choices: list):
        self.choice.addItems(choices)
    
class AdvancedSettingsDialog(QDialog):

    SYMBOL_TOOL_TIP = "A different symbol will be used for each unique value present in the column you choose."\
        "\nIf your column contains symbol names, these will be used."
    COLOR_TOOL_TIP = "A different color will be used for each unique value present in the column you choose."\
        "\nIf your column contains valid color names, these will be used."\
        "\nUsing this setting will override the heatmap setting in the main window."
    SIZE_TOOL_TIP = "This setting will override the point size setting in the main window"\
        "\nand let you specify point sizes directly. Make sure the column you choose has numeric values."

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window

        layout = QGridLayout(self)

        self.setWindowTitle("Advanced Settings")

        self.adv_color_chkbx = AdvancedCheckboxComboWidget("Use a column for point colors", "Color column:", AdvancedSettingsDialog.COLOR_TOOL_TIP, self)
        self.adv_symbol_chkbx = AdvancedCheckboxComboWidget("Use a column for point symbols", "Symbol column:", AdvancedSettingsDialog.SYMBOL_TOOL_TIP, self)
        self.adv_ptsize_chkbx = AdvancedCheckboxComboWidget("Use a column for point sizes", "Size column:", AdvancedSettingsDialog.SIZE_TOOL_TIP, self)
        
        self.scale_factors = ScaleFactorsSelection(self.main_window)

        layout.addWidget(self.adv_color_chkbx, 0, 0)
        layout.addWidget(self.adv_symbol_chkbx, 1, 0)
        layout.addWidget(self.adv_ptsize_chkbx, 2, 0)
        layout.addWidget(self.scale_factors, 3, 0)

        # Border color / thickness checkbox (starts checked, shows color (starts defaulted to white, QComboBox, plotly-compatible colors), numeric entry for width (starts at 0.2))
        # Highlight points (Will use same filter dialog logic, and then when connecting to ternary, probably need to add a trace and update it or combine this step into pre-processing so that all the non-highlighted data gets plotted as one trace, and then the highlighted data gets plotted as a second trace with the label 'highlight' or something so that we can update it separately...)
        # Scale apices checkbox / choice (checkbox to scale apices, if clicked reveals three label/lineedit pairs, lineedits only accept float values, default to 1, scaling needs to get implemented before molar conversion on data-processing side)
        # Don't convert to molar (checkbox, with a little Info symbol next to it that says "By default, QuickTernaries assumes your data is in wt% or ppm and converts it to molar. If you have already done this step or are not wanting to convert, select this button")

        self.ok_button = QPushButton('OK')
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFocusPolicy(Qt.NoFocus)

        layout.addWidget(self.ok_button, 4, 0)

        self.setLayout(layout)
    
    def update_visibility(self):
        #use_color_column = self.color_column_checkbox.isChecked()
        #self.color_column_choice.setVisible(use_color_column)
        #self.color_column_choice_label.setVisible(use_color_column)

        #use_symbol_column = self.symbol_column_checkbox.isChecked()
        #self.symbol_column_choice.setVisible(use_symbol_column)
        #self.symbol_column_choice_label.setVisible(use_symbol_column)
        pass
    #def show_info(self, text):
    #    QToolTip.showText(QCursor.pos(), text)

    def load_data(self, df):
        """Takes a dataframe and injects data into widgets"""
        columns = df.columns
        self.adv_color_chkbx.add_choices(columns)
        self.adv_symbol_chkbx.add_choices(columns)
        #self.color_column_choice.addItems(columns)
        #self.symbol_column_choice.addItems(columns)

    def dump_parameters(self):
        pass
