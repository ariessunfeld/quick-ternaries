"""GUI for Ternary App"""

import os
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QFontDialog,
    QGridLayout, QPushButton, QLabel, QWidget, QLineEdit, 
    QFileDialog, QComboBox, QCheckBox, QSpinBox, QListWidget, 
    QSpacerItem, QSizePolicy, QCompleter, QMessageBox, QInputDialog, QDialog)

from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QFont, QFontDatabase, QDesktopServices
from PySide6.QtWebEngineWidgets import QWebEngineView

import pandas as pd
from pandas import ExcelWriter

import numpy as np
import plotly.io as pio

from quick_ternaries.advanced_widgets import AdvancedSettingsDialog, InfoButton
from quick_ternaries.filter_widgets import FilterDialog, SelectedValuesList, FilterWidget
from quick_ternaries.file_handling_utils import find_header_row_csv, find_header_row_excel
from quick_ternaries.ternary_utils import add_molar_columns, make_ternary_trace, plot_ternary, parse_ternary_type

def show_exception(type, value, tb):
    """Exception Hook"""
    QMessageBox.critical(None, "An unhandled exception occurred", str(value)[:min(len(str(value)), 600)])
    sys.__excepthook__(type, value, tb)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")

        # The main layout for the dialog
        layout = QVBoxLayout(self)

        # Create the label and the spinbox for changing font size directly
        self.fontsize_label = QLabel("Fontsize:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setMinimum(6)  # Min font size
        self.font_size_spinbox.setMaximum(20) # Max font size
        self.font_size_spinbox.setValue(self.font().pointSize())  # Set the current font size
        self.font_size_spinbox.valueChanged.connect(self.change_font_size)

        # Add the label and spinbox to the horizontal layout
        fontsize_layout = QHBoxLayout()
        fontsize_layout.addWidget(self.fontsize_label)
        fontsize_layout.addWidget(self.font_size_spinbox)
        layout.addLayout(fontsize_layout)  # Adding the horizontal layout to the main vertical layout

        # Button for advanced font settings
        self.font_advanced_button = QPushButton("Advanced Font Settings")
        self.font_advanced_button.clicked.connect(self.font_advanced)

        # Add the advanced settings button to the main layout
        layout.addWidget(self.font_advanced_button)

    def change_font_size(self, value:int):
        """
        Change font size.

        Args:
            value: The current fontsize.
        """
        font = QApplication.font()
        font.setPointSize(value)
        QApplication.setFont(font)

    def font_advanced(self):
        """
        Change font family/size.
        """
        ok, font = QFontDialog.getFont(QApplication.font(), self)
        if ok:
            QApplication.setFont(font)


class MainWindow(QMainWindow):
    """
    Main application window.
    """

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
        """
        Initialize the main window, set up necessary directories, fonts, and layouts, and
        set the window title.
        """
        super().__init__()
        self.current_figure = None 
        self.df = None
        self.setup_fonts()
        self.setup_layouts()
        self.setWindowTitle("Ternary Diagram Creator")

    def setup_fonts(self):
        """
        Load the 'Motter Tektura' font and use it to set up the application's title label.
        The title label is configured to display the 'quick ternaries' logo which includes a
        hyperlink to the project repository.
        """
        current_directory = Path(__file__).resolve().parent
        font_path = current_directory / 'assets' / 'fonts' / 'Motter Tektura Normal.ttf'
        font_path_str = str(font_path)
        font_id = QFontDatabase.addApplicationFont(font_path_str)
        if font_id != -1:
            # If the font was successfully loaded, proceed to set up the title label
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.custom_font = QFont(font_families[0], pointSize=20)
                self.title_label = QLabel()
                self.title_label.setFont(self.custom_font)
                self.title_label.setTextFormat(Qt.RichText) # Enable rich text for hyperlink styling
                self.title_label.setText(
                    '<a href="https://github.com/ariessunfeld/quick-ternaries" ' +
                    'style="color: black; text-decoration:none;">' +
                    'quick ternaries' +
                    '</a>'
                )
                self.title_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
                self.title_label.setOpenExternalLinks(True) # Allow the label to open links

    def setup_layouts(self):
        """
        Configure the main layout of the application, organizing control elements and the
        ternary plot display area.
        """
        main_layout = QHBoxLayout() # Horizontal layout to separate controls from the plot area
        self.controls_layout = QVBoxLayout() # Layout for control elements
        self.ternary_plot_layout = QVBoxLayout() # Layout for the ternary plot

        # Initialize various sections of the UI
        self.setup_title_layout()
        self.setup_file_loader_layout()
        self.setup_ternary_type_selection_layout()
        self.setup_custom_type_selection_widgets()
        self.setup_apex_name_widgets()
        self.setup_title_field()
        self.setup_point_size_layout()
        self.setup_heatmap_options()
        self.setup_filter_options()
        self.setup_advanced_settings()
        self.setup_bottom_buttons()
        self.setup_ternary_plot()
        self.finalize_layout(main_layout)

    def setup_title_layout(self):
        """
        Layout for control panel title. Includes the 'quick ternaries' title logo and a settings
        button that is displayed as a gear icon.
        """
        current_directory = Path(__file__).resolve().parent
        settings_icon_path = current_directory / 'assets' / 'icons' / 'settings_icon.png'
        settings_icon_path_str = str(settings_icon_path)
        
        self.settings_button = QPushButton(self)
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setIcon(QIcon(settings_icon_path_str))
        self.settings_button.setStyleSheet('border: none;') # Remove the button outline
        self.settings_button.setIconSize(QSize(20, 20))
        self.settings_button.setFixedSize(20, 20)
        self.settings_button.setCursor(Qt.PointingHandCursor) # Change cursor to pointing hand on hover

        title_settings_layout = QHBoxLayout()
        title_settings_layout.addWidget(self.title_label)
        title_settings_layout.addStretch(1) # Push title to the left and settings to the right
        title_settings_layout.addWidget(self.settings_button)
        self.controls_layout.insertLayout(0, title_settings_layout) # Insert at the top of the controls layout

    def setup_file_loader_layout(self):
        """
        Layout for file loading. Includes a label to display the file path and
        a button to trigger the file loading dialog.
        """
        file_loader_layout = QGridLayout()
        self.file_label = QLabel(MainWindow.NO_FILE_SELECTED)
        self.load_button = QPushButton(MainWindow.LOAD_DATA_FILE)
        self.load_button.clicked.connect(self.load_data_file)

        file_loader_layout.addWidget(self.file_label, 0, 0)
        file_loader_layout.addWidget(self.load_button, 0, 1)

        self.controls_layout.addLayout(file_loader_layout)

    def setup_ternary_type_selection_layout(self):
        """
        Layout for choosing the type of ternary diagram.
        """
        ternary_type_selection_layout = QGridLayout()
        ternary_type_selection_layout.addWidget(QLabel("Ternary Type:"), 0, 0)
        self.diagram_type_combobox = QComboBox()
        self.diagram_type_combobox.addItems(MainWindow.TERNARY_TYPES)
        self.diagram_type_combobox.currentIndexChanged.connect(self.update_visibility)

        ternary_type_selection_layout.addWidget(self.diagram_type_combobox, 0, 1)

        self.controls_layout.addLayout(ternary_type_selection_layout)

    def setup_custom_type_selection_widgets(self):
        """
        Selecting custom apices for the ternary.
        """
        self.available_columns_list = QListWidget()
        self.custom_type_widgets = []
        self.selected_values_lists = {}
        grid_layout = QGridLayout() 

        apices = ['Top', 'Left', 'Right']
        for i, apex in enumerate(apices):
            inner_grid_layout = QGridLayout()
            vbox_layout = QVBoxLayout()

            label = QLabel(f"{apex} apex element(s):")
            vbox_layout.addWidget(label)
            list_widget = SelectedValuesList(self)
            self.selected_values_lists[i] = list_widget

            add_btn = QPushButton("Add >>")
            add_btn.clicked.connect(lambda _, lw=list_widget: self.add_column(lw))
            vbox_layout.addWidget(add_btn)

            remove_btn = QPushButton("Remove <<")
            remove_btn.clicked.connect(lambda _, lw=list_widget: self.remove_value(lw))
            vbox_layout.addWidget(remove_btn)

            inner_grid_layout.addLayout(vbox_layout, 0, 0)
            inner_grid_layout.addWidget(list_widget, 0, 1)
            grid_layout.addLayout(inner_grid_layout, i, 0)
            self.custom_type_widgets.extend([label, list_widget, add_btn, remove_btn])

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.available_columns_list)
        h_layout.addLayout(grid_layout)

        self.controls_layout.addLayout(h_layout)
        self.custom_type_widgets.append(self.available_columns_list)

    def setup_apex_name_widgets(self):
        """
        Customize the display names of the apices. These widgets are only visible when the user 
        checks the 'Customize apex display names' option.
        """
        self.apex_names_checkbox = QCheckBox('Customize apex display names')
        self.apex_names_checkbox.stateChanged.connect(self.update_visibility)
        self.controls_layout.addWidget(self.apex_names_checkbox)

        # Line edits and labels for custom apex names, added to QHBoxLayouts for organization
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

        # Aggregate the widgets for easy access and manipulation
        self.custom_apex_name_widgets.extend(
            [self.apex1_name, self.apex1_tag,
             self.apex2_name, self.apex2_tag,
             self.apex3_name, self.apex3_tag])

        self.controls_layout.addLayout(apex1_hlayout)
        self.controls_layout.addLayout(apex2_hlayout)
        self.controls_layout.addLayout(apex3_hlayout)

    def setup_title_field(self):
        """
        Setting a title for the ternary figure.
        """
        title_layout = QGridLayout()
        title_layout.addWidget(QLabel('Title:'), 0, 0)
        self.title_field = QLineEdit()
        title_layout.addWidget(self.title_field, 0, 1)

        self.controls_layout.addLayout(title_layout)

    def setup_point_size_layout(self):
        """
        Adjust ternary point size using a spinbox.
        """
        point_size_layout = QGridLayout()
        self.point_size = QSpinBox()
        self.point_size.setRange(1, 14)  # Define the range for point size
        self.point_size.setValue(6)      # Set the default value
        point_size_layout.addWidget(QLabel("Point Size:"), 0, 0)
        point_size_layout.addWidget(self.point_size, 0, 1)

        self.controls_layout.addLayout(point_size_layout)

    def setup_heatmap_options(self):
        """
        Configure heatmap options for the plotted points.
        """
        self.heatmap_checkbox = QCheckBox("Use Heatmap")
        self.heatmap_checkbox.stateChanged.connect(self.update_visibility)
        self.controls_layout.addWidget(self.heatmap_checkbox)

        # Dropdown for selecting which column to use for heatmap and related controls
        self.heatmap_column = QComboBox()
        self.heatmap_column.currentIndexChanged.connect(self.inject_range_min_max)
        self.heatmap_column_label = QLabel("Heatmap Column:")
        self.heatmap_color_min = QLineEdit()
        self.heatmap_color_max = QLineEdit()
        self.heatmap_color_min_label = QLabel("Range min:")
        self.heatmap_color_max_label = QLabel("Range max:")
        
        # Info button with a tooltip for explaining heatmap range
        self.heatmap_range_info_button = InfoButton(self, MainWindow.HEATMAP_TIP)
        
        # Layout for heatmap configuration controls
        heatmap_layout = QGridLayout()
        heatmap_layout.addWidget(self.heatmap_column_label, 0, 0)
        heatmap_layout.addWidget(self.heatmap_column, 0, 1)
        
        # Layouts for minimum and maximum color range fields
        cmin_layout = QHBoxLayout()
        cmin_layout.addWidget(self.heatmap_color_min_label)
        cmin_layout.addWidget(self.heatmap_color_min)
        
        cmax_layout = QHBoxLayout()
        cmax_layout.addWidget(self.heatmap_color_max_label)
        cmax_layout.addWidget(self.heatmap_color_max)
        cmax_layout.addWidget(self.heatmap_range_info_button)

        heatmap_layout.addLayout(cmin_layout, 1, 0)
        heatmap_layout.addLayout(cmax_layout, 1, 1)

        self.controls_layout.addLayout(heatmap_layout)

    def setup_filter_options(self):
        """
        Conditional filtering for the plotted data (optional)
        """
        filter_checkbox_layout = QHBoxLayout()

        # Enable/disable filtering
        self.filter_checkbox = QCheckBox("Use Filter(s)")
        self.filter_checkbox.stateChanged.connect(self.update_visibility)
        self.filter_checkbox.stateChanged.connect(self.update_filter_visibility)

        # Filter settings dialog
        self.show_filters_button = QPushButton("Show Filter(s)")
        # self.show_filters_button.setFixedWidth(4)  # Uncomment to fix the width if needed
        self.show_filters_button.clicked.connect(self.show_filter_dialog)

        filter_checkbox_layout.addWidget(self.filter_checkbox)
        filter_checkbox_layout.addWidget(self.show_filters_button)

        # Hide the 'Show Filter(s)' button by default
        self.show_filters_button.setVisible(False)

        # Align the checkbox and button to the left
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        filter_checkbox_layout.addItem(spacer)

        # Add the filter options layout to the main controls layout
        self.controls_layout.addLayout(filter_checkbox_layout)

        # Initialize the filter dialog but do not show it yet
        self.filter_dialog = FilterDialog(self)
        # Connect dialog signals to update UI appropriately
        self.filter_dialog.accepted.connect(self.show_filter_shower_button)
        self.filter_dialog.finished.connect(self.show_filter_shower_button)


    def setup_advanced_settings(self):
        """
        Advanced settings button.
        """
        advanced_checkbox_layout = QHBoxLayout()

        self.advanced_settings_dialog = AdvancedSettingsDialog(self)

        # Enable/disable advanced settings
        self.advanced_checkbox = QCheckBox("Use Advanced Settings")

        # Display the advanced settings dialog
        self.show_advanced_settings_button = QPushButton("Show Advanced Settings")

        # Align to the left
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)

        advanced_checkbox_layout.addWidget(self.advanced_checkbox)
        advanced_checkbox_layout.addWidget(self.show_advanced_settings_button)
        advanced_checkbox_layout.addItem(spacer)

        self.controls_layout.addLayout(advanced_checkbox_layout)

        self.advanced_checkbox.stateChanged.connect(self.update_advanced_visibility)
        self.show_advanced_settings_button.clicked.connect(self.advanced_settings_dialog.show)

    def setup_bottom_buttons(self):
        """
        The bottom buttons in the UI for previewing and saving the ternary diagram, and saving 
        filtered data.
        """
        # Horizontal layout for bottom buttons
        bottom_buttons = QHBoxLayout()

        # Button to generate the ternary diagram preview
        self.generate_button = QPushButton("Preview Ternary")
        self.generate_button.clicked.connect(self.generate_diagram)  # Connect the button to its action

        # Button to save the generated ternary diagram
        self.save_ternary_button = QPushButton("Save Ternary")
        self.save_ternary_button.clicked.connect(self.save_ternary_figure)

        # Button to save the filtered data if any filters are applied
        self.save_filtered_data_button = QPushButton("Save Filtered Data")
        self.save_filtered_data_button.clicked.connect(self.save_filtered_data)

        # Add buttons to the layout
        bottom_buttons.addWidget(self.generate_button)
        bottom_buttons.addWidget(self.save_ternary_button)
        bottom_buttons.addWidget(self.save_filtered_data_button)

        # Add the bottom buttons layout to the main controls layout
        self.controls_layout.addLayout(bottom_buttons)

    def setup_ternary_plot(self):
        """
        Initialize the QWebEngineView widget that will display the ternary plot.
        """
        self.ternary_view = QWebEngineView()
        self.ternary_plot_layout.addWidget(self.ternary_view)

    def finalize_layout(self, main_layout: QHBoxLayout):
        """
        Finalizes the main layout by adding the control and plot layouts with appropriate stretch factors.
        Sets the central widget of the main window with the finalized layout.

        Args:
            main_layout: The main window that contains the entire UI.
        """
        main_layout.addLayout(self.controls_layout, 1)
        main_layout.addLayout(self.ternary_plot_layout, 3)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        self.update_visibility()

    def open_settings(self):
        """
        Creates and opens the settings dialog for the application.
        """
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec()

    def update_advanced_visibility(self):
        pass

    def save_filtered_data(self):
        """
        Saves the filtered data to a user-specified location and format after applying filters.
        """
        if self.df is None:
            QMessageBox.critical(self, "Warning", 'You must load data first.')
            return

        all_input = self.get_all_input_values()

        if all_input['use filter']:
            df = self.filter_dialog.apply_all_filters(self.df)
        else:
            df = self.df

        df = add_molar_columns(df, all_input)

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_types = "CSV Files (*.csv);;JSON Files (*.json);;Excel Files (*.xlsx);;All Files (*)"
        file_name, selected_filter = QFileDialog.getSaveFileName(self, "Save Filtered Data", "",
                                                file_types, options=options)

        if file_name:
            # Ensure the file_name has the proper extension if it was not provided.
            if '.' not in os.path.splitext(file_name)[1]:
                extension = selected_filter.split("(*")[1].split(")")[0]  # Extract the extension
                file_name += extension

            # Save the DataFrame to the selected file path
            try:
                if file_name.endswith('.csv'):
                    df.to_csv(file_name, index=False)
                elif file_name.endswith('.json'):
                    df.to_json(file_name, orient='records', lines=True)
                elif file_name.endswith('.xlsx'):
                    with ExcelWriter(file_name) as writer:
                        df.to_excel(writer, index=False)
                QMessageBox.information(
                    self,
                    'Data Saved',
                    f'Filtered data has been saved as: {file_name}')
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    'Save Error', 
                    f'An error occurred while saving the file: {e}')
        
    def save_ternary_figure(self):
        """
        Save the ternary to a specified location with a specified file type
        """
        if self.current_figure is not None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_types = "PNG Files (*.png);;JPEG Files (*.jpg);;SVG Files (*.svg);;PDF Files (*.pdf);;HTML Files (*.html);;All Files (*)"
            file_name, selected_filter = QFileDialog.getSaveFileName(self, "Save Ternary Diagram", "",
                                                    file_types, options=options)
            if file_name:
                # Get the extension from the selected filter if the file_name has no extension
                if '.' not in os.path.splitext(file_name)[1]:
                    extension = selected_filter.split("(*")[1].split(")")[0]  # Extract the extension
                    file_name += extension
                if file_name.endswith('.html'):
                    # Save interactive plot as HTML
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(self.current_figure.to_html(include_plotlyjs='cdn'))
                else:
                    # Save static image. The format is inferred from the extension of the file_name.
                    pio.write_image(self.current_figure, file_name)
        else:
            QMessageBox.critical(self, "Error", "There is no ternary diagram to save. Please generate one first.")

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
    
    def _default_ternary_title(self, ternary_type:str):
        """
        Create a default title based off the type of ternary.

        Ex: "A CNK FM Ternary Diagram"

        Args:
            ternary_type: The type of ternary being plotted. 
                          Ex: Al2O3 CaO+Na2O+K2O FeOT+MgO
        """
        ternary_title = ternary_type.split(" ")
        ternary_title = [apex.split("+") for apex in ternary_title]
        ternary_title = [[ox[0] if ox!="MnO" else "Mn" for ox in apex] for apex in ternary_title]
        ternary_title = " ".join(["".join(apex) for apex in ternary_title])
        return ternary_title + " Ternary Diagram"

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
            top_name   = all_input['top apex custom name']
            left_name  = all_input['left apex custom name']
            right_name = all_input['right apex custom name']
        else:
            tops, lefts, rights = parse_ternary_type(all_input['ternary type'], all_input)
            top_name   = '+'.join(tops)
            left_name  = '+'.join(lefts)
            right_name = '+'.join(rights)

        if all_input['title']:
            title = all_input['title']
        else:
            title = self._default_ternary_title(all_input['ternary type'])

        fig = plot_ternary([plot_data], title, top_name, left_name, right_name)
        self.current_figure = fig

        # Convert the figure to HTML
        html_string = fig.to_html(include_plotlyjs='cdn')

        # Set the HTML content to the QWebEngineView
        self.ternary_view.setHtml(html_string)
    
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

def main():
    sys.excepthook = show_exception
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
