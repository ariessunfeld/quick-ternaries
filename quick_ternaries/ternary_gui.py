import os
import sys
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFontDialog,
    QGridLayout, QPushButton, QLabel, QWidget, QLineEdit, 
    QFileDialog, QComboBox, QCheckBox, QSpinBox, QListWidget, 
    QSpacerItem, QSizePolicy, QCompleter, QMessageBox, QInputDialog)

from PySide6.QtGui import QFont

import pandas as pd
import numpy as np

from .advanced_widgets import AdvancedSettingsDialog, InfoButton
from .filter_widgets import FilterDialog, SelectedValuesList, FilterWidget
from .file_handling_utils import find_header_row_csv, find_header_row_excel
from .ternary_utils import add_molar_columns, make_ternary_trace, plot_ternary, parse_ternary_type

def show_exception(type, value, tb):
    """Exception Hook"""
    QMessageBox.critical(None, "An unhandled exception occurred", str(value)[:min(len(str(value)), 600)])
    sys.__excepthook__(type, value, tb)


class MainWindow(QMainWindow):

    NO_FILE_SELECTED = "No file selected"
    LOAD_DATA_FILE = "Load data file"
    TERNARY_TYPES = [
        "Al2O3 CaO+Na2O+K2O FeOT+MgO", 
        "SiO2+Al2O3 CaO+Na2O+K2O FeOT+MgO", 
        "Al2O3 CaO+Na2O K2O", 
        "Custom"]
    HEATMAP_TIP = "Tip: Set a low 'range max' to bring out the gradient in your data."\
        "\nPoints with higher values than 'range max' will still be plotted;"\
        "\nthey will just have the same color as the highest value on the scale."\
        "\nThe default 'range max' value is twice the median of the selected column."

    def __init__(self):
        super().__init__()

        # Set up img and csv directories if needed
        self.home_dir = os.path.expanduser('~')
        self.img_dir = os.path.join(self.home_dir, 'Documents', 'ternaries', 'img')
        self.csv_dir = os.path.join(self.home_dir, 'Documents', 'ternaries', 'csv')
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        if not os.path.exists(self.csv_dir):
            os.makedirs(self.csv_dir)

        self.setWindowTitle("Ternary Diagram Creator")

        self.df = None
        
        # Create a QVBoxLayout instance
        layout = QVBoxLayout()

        font_layout = QHBoxLayout()
        self.font_button = QPushButton("Change Font Size", self)
        #self.font_button.clicked.connect(self.choose_font)
        self.font_button.clicked.connect(self.choose_font_size)
        font_spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        font_layout.addWidget(self.font_button)
        font_layout.addItem(font_spacer)
        layout.addLayout(font_layout)
        
        # Create a QLabel and QPushButton for data file
        file_loader_layout = QGridLayout()
        self.file_label = QLabel(MainWindow.NO_FILE_SELECTED)
        self.load_button = QPushButton(MainWindow.LOAD_DATA_FILE)
        self.load_button.clicked.connect(self.load_data_file)
        file_loader_layout.addWidget(self.file_label, 0, 0)
        file_loader_layout.addWidget(self.load_button, 0, 1)
        layout.addLayout(file_loader_layout)
        
        # Create a QComboBox for selecting diagram type
        ternary_type_selection_layout = QGridLayout()
        ternary_type_selection_layout.addWidget(QLabel("Ternary Type:"), 0, 0)
        self.diagram_type_combobox = QComboBox()
        self.diagram_type_combobox.addItems(MainWindow.TERNARY_TYPES)
        self.diagram_type_combobox.currentIndexChanged.connect(self.update_visibility)
        ternary_type_selection_layout.addWidget(self.diagram_type_combobox, 0, 1)
        layout.addLayout(ternary_type_selection_layout)

        # Create widgets for custom diagram type selection
        self.available_columns_list = QListWidget()
        self.custom_type_widgets = []
        self.selected_values_lists = {}
        grid_layout = QGridLayout()  # A grid layout for the custom type widgets
        apices = ['Top', 'Left', 'Right']
        for i in range(3):
            inner_grid_layout = QGridLayout()
            vbox_layout = QVBoxLayout()  # A vertical layout for each apex's widgets
            lb = QLabel(f"{apices[i]} apex element(s):")
            vbox_layout.addWidget(lb)
            lw = SelectedValuesList(self)
            self.selected_values_lists[i] = lw
            add_btn = QPushButton("Add >>")
            add_btn.clicked.connect(lambda checked=False, lw=lw: self.add_column(lw))
            vbox_layout.addWidget(add_btn)
            remove_btn = QPushButton("Remove <<")
            remove_btn.clicked.connect(lambda checked=False, lw=lw: self.remove_value(lw))
            vbox_layout.addWidget(remove_btn)
            inner_grid_layout.addLayout(vbox_layout, 0, 0)
            inner_grid_layout.addWidget(lw, 0, 1)
            grid_layout.addLayout(inner_grid_layout, i+1, 0)  # Add the QVBoxLayout to the grid layout in the appropriate column
            self.custom_type_widgets.extend([lb, lw, add_btn, remove_btn])
        
        # Create a QHBoxLayout and add available_columns_list and grid_layout
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.available_columns_list)
        h_layout.addLayout(grid_layout)
        layout.addLayout(h_layout)  # Add the horizontal layout to the main layout
        self.custom_type_widgets.extend([self.available_columns_list])
        
        # Create a QCheckBox for custom apex names
        self.apex_names_checkbox = QCheckBox('Customize apex display names')
        self.apex_names_checkbox.stateChanged.connect(self.update_visibility)
        layout.addWidget(self.apex_names_checkbox)

        # Create QLineEdit for naming apices and setting the title
        self.custom_apex_name_widgets = []

        self.apex1_name = QLineEdit()
        self.apex2_name = QLineEdit()
        self.apex3_name = QLineEdit()

        self.apex1_tag = QLabel("Top apex display name:")
        self.apex2_tag = QLabel("Left apex display name:")
        self.apex3_tag = QLabel("Right apex display name:")

        apex1_hlayout = QHBoxLayout()
        apex1_hlayout.addWidget(self.apex1_tag)
        apex1_hlayout.addWidget(self.apex1_name)

        apex2_hlayout = QHBoxLayout()
        apex2_hlayout.addWidget(self.apex2_tag)
        apex2_hlayout.addWidget(self.apex2_name)

        apex3_hlayout = QHBoxLayout()
        apex3_hlayout.addWidget(self.apex3_tag)
        apex3_hlayout.addWidget(self.apex3_name)

        self.custom_apex_name_widgets.extend(
            [
                self.apex1_name, self.apex1_tag, 
                self.apex2_name, self.apex2_tag,
                self.apex3_name, self.apex3_tag])

        layout.addLayout(apex1_hlayout)
        layout.addLayout(apex2_hlayout)
        layout.addLayout(apex3_hlayout)

        # Create a layout for Title
        title_layout = QGridLayout()
        title_layout.addWidget(QLabel('Title:'), 0, 0)
        self.title_field = QLineEdit()
        title_layout.addWidget(self.title_field, 0, 1)
        layout.addLayout(title_layout)
        
        # Create a QSpinBox for point size options
        point_size_layout = QGridLayout()
        self.point_size = QSpinBox()
        self.point_size.setRange(1, 14)  # Set min and max values
        self.point_size.setValue(6)
        point_size_layout.addWidget(QLabel("Point Size:"), 0, 0)
        point_size_layout.addWidget(self.point_size, 0, 1)
        layout.addLayout(point_size_layout)

        # Create a QCheckBox for heatmap options
        self.heatmap_checkbox = QCheckBox("Use Heatmap")
        self.heatmap_checkbox.stateChanged.connect(self.update_visibility)
        layout.addWidget(self.heatmap_checkbox)

        # Create QComboBox for heatmap column
        self.heatmap_column = QComboBox()
        self.heatmap_column.currentIndexChanged.connect(self.inject_range_min_max)
        self.heatmap_column_label = QLabel("Heatmap Column:")
        self.heatmap_color_min = QLineEdit()
        self.heatmap_color_max = QLineEdit()
        self.heatmap_color_min_label = QLabel("Range min:")
        self.heatmap_color_max_label = QLabel("Range max:")
        self.heatmap_range_info_button = InfoButton(self, MainWindow.HEATMAP_TIP)
        heatmap_layout = QGridLayout()
        heatmap_layout.addWidget(self.heatmap_column_label, 0, 0)
        heatmap_layout.addWidget(self.heatmap_column, 0, 1)
        cmin_layout = QHBoxLayout()
        cmin_layout.addWidget(self.heatmap_color_min_label)
        cmin_layout.addWidget(self.heatmap_color_min)
        cmax_layout = QHBoxLayout()
        cmax_layout.addWidget(self.heatmap_color_max_label)
        cmax_layout.addWidget(self.heatmap_color_max)
        cmax_layout.addWidget(self.heatmap_range_info_button)
        heatmap_layout.addLayout(cmin_layout, 1, 0)
        heatmap_layout.addLayout(cmax_layout, 1, 1)
        layout.addLayout(heatmap_layout)

        # Create a QCheckBox for filter options
        filter_checkbox_layout = QHBoxLayout()
        self.filter_checkbox = QCheckBox("Use Filter(s)")
        self.filter_checkbox.stateChanged.connect(self.update_visibility)
        self.filter_checkbox.stateChanged.connect(self.update_filter_visibility)
        self.show_filters_button = QPushButton("Show Filter(s)")
        #self.show_filters_button.setFixedWidth(4)
        self.show_filters_button.clicked.connect(self.show_filter_dialog)
        filter_checkbox_layout.addWidget(self.filter_checkbox)
        filter_checkbox_layout.addWidget(self.show_filters_button)
        self.show_filters_button.setVisible(False)
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        filter_checkbox_layout.addItem(spacer)
        layout.addLayout(filter_checkbox_layout)

        # Create layout & widgets for advanced settings
        advanced_checkbox_layout = QHBoxLayout()
        self.advanced_settings_dialog = AdvancedSettingsDialog(self)
        self.advanced_checkbox = QCheckBox("Use Advanced Settings")
        self.show_advanced_settings_button = QPushButton("Show Advanced Settings")
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # Add widgets to layout
        advanced_checkbox_layout.addWidget(self.advanced_checkbox)
        advanced_checkbox_layout.addWidget(self.show_advanced_settings_button)
        advanced_checkbox_layout.addItem(spacer)
        layout.addLayout(advanced_checkbox_layout)
        # Connect signals
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_visibility)
        self.show_advanced_settings_button.clicked.connect(self.advanced_settings_dialog.show)


        # Create a Filters Widget dialog area
        self.filter_dialog = FilterDialog(self)
        self.filter_dialog.accepted.connect(self.show_filter_shower_button)
        self.filter_dialog.finished.connect(self.show_filter_shower_button)

        bottom_buttons = QHBoxLayout()

        # Create a "Preview Ternary" button
        self.generate_button = QPushButton("Preview Ternary")
        self.generate_button.clicked.connect(self.generate_diagram)  # Connect to slot
        bottom_buttons.addWidget(self.generate_button)

        # Create a "Preview & Save" button
        self.preview_and_save_button = QPushButton("Preview + Save")
        self.preview_and_save_button.clicked.connect(self.preview_and_save)
        bottom_buttons.addWidget(self.preview_and_save_button)

        # Create a "Save Filtered Data" button
        self.save_filtered_data_button = QPushButton("Save Filtered Data")
        self.save_filtered_data_button.clicked.connect(self.save_filtered_data)
        bottom_buttons.addWidget(self.save_filtered_data_button)

        # Add buttons to layout
        layout.addLayout(bottom_buttons)

        # Create a container QWidget and set the layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.update_visibility()

    def update_advanced_visibility(self):
        pass

    def save_filtered_data(self):
        if self.df is None:
            QMessageBox.critical(None, "Warning", 'You must load data first.')
            return
        all_input = self.get_all_input_values()

        if all_input['use filter']:
            df = self.filter_dialog.apply_all_filters(self.df)
        else:
            df = self.df

        df = add_molar_columns(df, all_input)

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")
        csv_fname = f'filtered_data_{timestamp}.csv'
        df.to_csv(os.path.join(self.csv_dir, csv_fname), index=0)
        QMessageBox.information(
            self, 
            'New Data File', 
            f'New CSV written to disk: {os.path.join(self.csv_dir, csv_fname)}')

    def preview_and_save(self):
        if self.df is None:
            QMessageBox.critical(None, "Warning", 'You must load data first.')
            return
        all_input = self.get_all_input_values()

        if all_input['use filter']:
            df = self.filter_dialog.apply_all_filters(self.df)
        else:
            df = self.df

        df = add_molar_columns(df, all_input)

        plot_data = make_ternary_trace(
            df,
            'top_apex_molar_normed',
            'left_apex_molar_normed',
            'right_apex_molar_normed',
            use_heatmap=all_input['use heatmap'],
            heatmap_col=all_input['heatmap column'],
            cmin=all_input['heatmap color min'],
            cmax=all_input['heatmap color max'],
            size=all_input['point size']
            #color_col=all_input['heatmap column']
        )

        # Break this out into its own function
        if all_input['use custom apex names']:
            top_name = all_input['top apex custom name']
            left_name = all_input['left apex custom name']
            right_name = all_input['right apex custom name']
        else:
            tops, lefts, rights = parse_ternary_type(all_input['ternary type'], all_input)
            top_name = '+'.join(tops)
            left_name = '+'.join(lefts)
            right_name = '+'.join(rights)

        if all_input['title']:
            title = all_input['title']
        else:
            title = 'Untitled'

        fig = plot_ternary([plot_data], title, top_name, left_name, right_name)

        fig.show()

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d-%H-%M-%S")

        html_fname = f"ternary_{title.replace(' ', '_')}_{timestamp}.html"

        fig.write_html(os.path.join(self.img_dir, html_fname))
        QMessageBox.information(
            self, 
            'New Image File', 
            f'New image written to disk: {os.path.join(self.img_dir, html_fname)}')

        png_fname = f"ternary_{title.replace(' ', '_')}_{timestamp}.png"

        fig.write_image(os.path.join(self.img_dir, png_fname), scale=10, engine='kaleido') # TODO don't hardcode scale
        QMessageBox.information(
            self, 
            'New Image File', 
            f'New image written to disk: {os.path.join(self.img_dir, png_fname)}') # TODO don't hardcode PNG; allow JPG (in Advanced Settings)

    def load_data_file(self):
        data_file, _ = QFileDialog.getOpenFileName(None, "Open data file", "", "Data Files (*.csv *.xlsx)")
        if data_file:
            self.file_label.setText(data_file)
            if data_file.endswith('.csv'):
                try:
                    header = find_header_row_csv(data_file, 16)
                    self.df = pd.read_csv(data_file, header=header)  # Load the data and store in self.df
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    return
            elif data_file.endswith('.xlsx'):
                try:
                    excel_file = pd.ExcelFile(data_file)
                    sheets = excel_file.sheet_names
                    if len(sheets) > 1:
                        sheet, ok = QInputDialog.getItem(self, "Select Excel Sheet", f"Choose a sheet from {os.path.basename(data_file)}", sheets, 0, False)
                        if not ok:
                            self.file_label.setText(MainWindow.NO_FILE_SELECTED)
                            return
                    else:
                        sheet = sheets[0]
                    header = find_header_row_excel(data_file, 16, sheet)
                    self.df = excel_file.parse(sheet, header=header)  # Load the data and store in self.df
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    return
            self.available_columns_list.clear()
            self.available_columns_list.addItems(self.df.columns)
            self.heatmap_column.clear()
            self.heatmap_column.addItems(self.df.columns)
            for filter in self.filter_dialog.filters_scroll_area.filters:
                self.filter_dialog.inject_data_to_filter(filter, self.df)
            self.advanced_settings_dialog.load_data(self.df)
            self.update_visibility()

    def inject_data_to_filter(self, filter: FilterWidget):
        if self.df is not None:
            filter.column_combobox.clear()
            filter.column_combobox.addItems(self.df.columns)
            filter.update_visibility()

    def inject_range_min_max(self):
        if self.df is not None:
            col = self.heatmap_column.currentText()
            dtype = self.df[col].dtype
            if np.issubdtype(dtype, np.number):  # If the dtype is numeric
                self.heatmap_color_min.setText(str(min(self.df[col])))
                self.heatmap_color_max.setText(str(2 * np.median(self.df[col])))
    
    def update_visibility(self):
        self.show_filters_button.setVisible(False)
        is_filter = self.filter_checkbox.isChecked()
        if not is_filter:
            self.filter_dialog.hide()
        self.show_filters_button.setVisible(is_filter and self.filter_dialog.isHidden())
        is_custom_type = self.diagram_type_combobox.currentText() == 'Custom'
        use_custom_apex_names = self.apex_names_checkbox.isChecked()
        for widget in self.custom_type_widgets:
            widget.setVisible(is_custom_type)
        is_heatmap = self.heatmap_checkbox.isChecked()
        self.heatmap_column.setVisible(is_heatmap)
        self.heatmap_column_label.setVisible(is_heatmap)
        self.heatmap_color_min.setVisible(is_heatmap)
        self.heatmap_color_min_label.setVisible(is_heatmap)
        self.heatmap_color_max.setVisible(is_heatmap)
        self.heatmap_color_max_label.setVisible(is_heatmap)
        self.heatmap_range_info_button.setVisible(is_heatmap)
        for lt in self.custom_apex_name_widgets:
            lt.setVisible(use_custom_apex_names)

    def update_filter_visibility(self):
        is_filter = self.filter_checkbox.isChecked()
        if is_filter:
            self.filter_dialog.show()
        self.show_filter_shower_button()
        #    if self.filter_dialog.isHidden():
        #        self.show_filters_button.setVisible(True)
        #    else:
        #        self.show_filters_button.setVisible(False)
    
    def show_filter_dialog(self):
        self.filter_dialog.show()

    def show_filter_shower_button(self):
        self.show_filters_button.setVisible(self.filter_checkbox.isChecked() and self.filter_dialog.isHidden())

    def add_column(self, lw: QListWidget):
        selected_item = self.available_columns_list.currentItem()
        if selected_item is not None:
            self.available_columns_list.takeItem(self.available_columns_list.row(selected_item))
            lw.addItem(selected_item)

    def remove_value(self, lw: SelectedValuesList):
        selected_item = lw.currentItem()
        if selected_item is not None:
            lw.takeItem(lw.row(selected_item))
            self.available_columns_list.addItem(selected_item)

    def get_all_input_values(self):
        """Returns a dictionary with all input parameters from gui"""
        # TODO validation / type checking?
        ret = {
            'file': self.file_label.text(),
            'ternary type': self.diagram_type_combobox.currentText(),
            'top apex selected values': [
                self.selected_values_lists[0].item(x).text() \
                    for x in range(self.selected_values_lists[0].count())],
            'left apex selected values': [
                self.selected_values_lists[1].item(x).text() \
                    for x in range(self.selected_values_lists[1].count())],
            'right apex selected values': [
                self.selected_values_lists[2].item(x).text() \
                    for x in range(self.selected_values_lists[2].count())],
            'use custom apex names': self.apex_names_checkbox.isChecked(),
            'top apex custom name': self.apex1_name.text(),
            'left apex custom name': self.apex2_name.text(),
            'right apex custom name': self.apex3_name.text(),
            'title': self.title_field.text(),
            'point size': self.point_size.text(),
            'use heatmap': self.heatmap_checkbox.isChecked(),
            'heatmap column': self.heatmap_column.currentText(),
            'heatmap color min': self.heatmap_color_min.text(),
            'heatmap color max': self.heatmap_color_max.text(),
            'use filter': self.filter_checkbox.isChecked()}
            
        if ret['use filter']:
            ret |= {f'filter {i}': filter.get_parameters() \
                    for i, filter in enumerate(self.filter_dialog.filters_scroll_area.filters)}
        
        return ret

    def generate_diagram(self):
        if self.df is None:
            QMessageBox.critical(None, "Warning", 'You must load data first.')
            return
        all_input = self.get_all_input_values()

        if all_input['use filter']:
            df = self.filter_dialog.apply_all_filters(self.df)
        else:
            df = self.df

        df = add_molar_columns(df, all_input)

        plot_data = make_ternary_trace(
            df,
            'top_apex_molar_normed',
            'left_apex_molar_normed',
            'right_apex_molar_normed',
            use_heatmap=all_input['use heatmap'],
            heatmap_col=all_input['heatmap column'],
            cmin=all_input['heatmap color min'],
            cmax=all_input['heatmap color max'],
            size=all_input['point size']
            #color_col=all_input['heatmap column']
        )

        # Break this out into its own function
        if all_input['use custom apex names']:
            top_name = all_input['top apex custom name']
            left_name = all_input['left apex custom name']
            right_name = all_input['right apex custom name']
        else:
            tops, lefts, rights = parse_ternary_type(all_input['ternary type'], all_input)
            top_name = '+'.join(tops)
            left_name = '+'.join(lefts)
            right_name = '+'.join(rights)

        if all_input['title']:
            title = all_input['title']
        else:
            title = 'Untitled'

        fig = plot_ternary([plot_data], title, top_name, left_name, right_name)

        fig.show()
    
    def update_filter_ops(self):
        column_name = self.filter_column.currentText()
        if column_name:  # If there is a selected column
            dtype = self.df[column_name].dtype
            if dtype == 'object':  # If the dtype is object (likely string)
                self.filter_op.clear()
                self.filter_op.addItems(['Equals', 'One of'])
            elif np.issubdtype(dtype, np.number):  # If the dtype is numeric
                self.filter_op.clear()
                self.filter_op.addItems(
                    ['Equals', 'One of', '<', '>', '<=', '>=', 'a < x < b', 'a <= x <= b', 'a < x <= b', 'a <= x < b'])
            else:
                self.filter_op.clear()
                self.filter_op.addItems(
                    ['Equals', 'One of', '<', '>', '<=', '>=', 'a < x < b', 'a <= x <= b', 'a < x <= b', 'a <= x < b']
                )
        else:  # No selected column, clear the operations dropdown
            self.filter_op.clear()
        self.update_filter_val_completer()

    def update_filter_val_completer(self):
        column_name = self.filter_column.currentText()
        if column_name:
            unique_values = self.df[column_name].dropna().unique()
            str_unique_values = [str(val) for val in unique_values]
            completer = QCompleter(str_unique_values, self)
            self.filter_val.setCompleter(completer)
            self.filter_val2.setCompleter(completer)
            self.filter_values_list.clear()
            self.filter_values_list.addItems(str_unique_values)
        else:
            self.filter_values_list.clear()
            self.filter_val.setCompleter(None)
            self.filter_val2.setCompleter(None)

    def choose_font(self):
        ok, font = QFontDialog.getFont(QApplication.font(), self)
        print(ok, type(ok))
        print(f"font: {font}, type: {type(font)}")  # add this line to debug
        if ok:
            QApplication.setFont(QFont(font))

    def choose_font_size(self):
        font = QApplication.font()
        current_size = font.pointSize()
        new_size, ok = QInputDialog.getInt(self, "Choose font size", "Font size:", current_size, 6, 20)
        if ok:
            font.setPointSize(new_size)
            QApplication.setFont(font)

def main():
    sys.excepthook = show_exception
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()