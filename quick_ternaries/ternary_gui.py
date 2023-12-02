import os
import sys

import numpy as np
import pandas as pd

from PySide6.QtWidgets import (
    QApplication, QCheckBox, QColorDialog, QComboBox, QDialog, QFileDialog, QFontDialog, QGridLayout,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox,
    QPushButton, QScrollArea, QSpinBox, QStackedWidget, QVBoxLayout, QWidget)

from PySide6.QtCore import Slot, Qt, QObject, QSize, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QFontDatabase, QIcon, QPalette
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView

from quick_ternaries.advanced_widgets import InfoButton
from quick_ternaries.filter_widgets import FilterDialog, SelectedValuesList, FilterWidget
from quick_ternaries.file_handling_utils import find_header_row_csv, find_header_row_excel
from ternary_utils import TernaryGraph, Trace, get_apex_names, create_title

#GITHUB_LINK = "https://github.com/ariessunfeld/quick-ternaries"
GITHUB_LINK = "https://gitlab.lanl.gov"

class CustomTabButton(QWidget):
    def __init__(self,
                 name: str,
                 identifier: str,
                 index: int,
                 change_tab_callback,
                 remove_tab_callback,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tab_button = QHBoxLayout(self)

        self.label = QLabel(name)
        self.tab_button.addWidget(self.label)

        # If the tab is removable, render with '✕' button
        if remove_tab_callback:
            self.close_button = QPushButton("✕")
            self.close_button.setFixedSize(QSize(20, 20))
            self.close_button.clicked.connect(lambda: remove_tab_callback(self))
            self.tab_button.addWidget(self.close_button)

        self.tab_button.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.tab_button)

        # Store the callbacks and index for later use
        self.change_tab_callback = change_tab_callback
        self.identifier = str(identifier)
        self.index = index
        
        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)  # Set the cursor to a pointer

        self.applyStyles()

    def applyStyles(self):
        # Set the styles for the whole widget (outline here)
        self.setStyleSheet("""
            CustomTabButton {
                border: 1px solid gray;
                border-radius: 4px;
                background-color: lightgray;
            }
        """)
        if hasattr(self, 'close_button'):
            self.close_button.setStyleSheet("border: none; background-color: transparent; ")

    def mousePressEvent(self, event):
        """
        Display the contents of the last clicked tab.

        Args:
            event:
        """
        self.change_tab_callback(self.index)


class TabManager(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tab_counter = 0
        self.trace_editors = {}
        self.setup_scroll_area()

    def setup_scroll_area(self):
        self.content_stack = QStackedWidget()
        self.controls_layout = QHBoxLayout(self)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for tabs
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("border: none; ")

        # Set a maximum width for the scroll area
        self.scroll_area.setMaximumWidth(150)  # Adjust this value as needed
        self.scroll_area.setMinimumWidth(100)  # Adjust this value as needed

        # Container widget for scroll area
        self.scroll_widget = QWidget()
        self.scroll_area.setWidget(self.scroll_widget)

        # Layout for the container widget
        self.tab_layout = QVBoxLayout(self.scroll_widget)
        self.tab_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_layout.setSpacing(5)
        self.tab_layout.setAlignment(Qt.AlignTop)

        # Add the start setup tab
        self.start_setup = StartSetup()
        self.add_start_setup_tab()

        # New tab button
        self.new_tab_button = QPushButton("+ Add Trace")
        self.new_tab_button.setCursor(Qt.PointingHandCursor)
        self.new_tab_button.clicked.connect(self.add_trace)

        # Add new tab button to the tab layout
        self.tab_layout.addWidget(self.new_tab_button)

        self.controls_layout.addWidget(self.scroll_area)
        self.controls_layout.addWidget(self.content_stack)

    def add_start_setup_tab(self):
        start_setup_widget = QWidget()
        start_setup_widget.setLayout(self.start_setup.start_setup_layout)
        self.content_stack.addWidget(start_setup_widget)
        start_setup_tab = CustomTabButton(name = "Start Setup",
                                            identifier = "StartSetup",
                                            index = 0,
                                            change_tab_callback = lambda index: self.change_tab(index),
                                            remove_tab_callback = None)
        self.tab_layout.addWidget(start_setup_tab)
        self.change_tab(0)

    def add_trace(self):
        start_setup_data = self.start_setup.get_data()

        if start_setup_data["file"] == "No file selected":
            QMessageBox.critical(self, "Error", "Please select data file")
        else:
            self.tab_counter += 1

            new_trace_editor = TraceEditor(self.start_setup)

            tab_id = str(self.tab_counter)  # Unique identifier for the tab
            self.trace_editors[tab_id] = new_trace_editor
            self.add_tab(f"Trace {tab_id}", new_trace_editor.trace_config_layout)

    def add_tab(self, name, custom_layout):
        tab_index = self.tab_layout.count() - 1
        tab_id    = self.tab_counter

        tab_button = CustomTabButton(name,
                                     identifier = tab_id,
                                     index = tab_index,
                                     change_tab_callback = lambda index: self.change_tab(index),
                                     remove_tab_callback = self.remove_tab)
        self.tab_layout.insertWidget(tab_index, tab_button)

        content_widget = QWidget()
        content_widget.setLayout(custom_layout)
        self.content_stack.addWidget(content_widget)
        self.change_tab(tab_index) # Change tabs to the newly created one

    def remove_tab(self, tab):
        # Confirm before removing the tab
        if QMessageBox.question(self, 'Confirm Delete', "Do you really want to delete this trace?") == QMessageBox.Yes:
            all_ids = list(self.trace_editors.keys())
            all_ids.sort()
            tab_index = all_ids.index(tab.identifier) + 1

            # Remove the tab button
            tab_button_to_remove = self.tab_layout.takeAt(tab_index).widget()
            if tab_button_to_remove:
                tab_button_to_remove.deleteLater()

            # Remove the corresponding widget from the content stack
            widget_to_remove = self.content_stack.widget(tab_index)
            if widget_to_remove:
                self.content_stack.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()

            # Update the indices of subsequent tabs
            for i in range(tab_index, self.tab_layout.count() - 1):  # Exclude the new tab button
                tab_button = self.tab_layout.itemAt(i).widget()
                if isinstance(tab_button, CustomTabButton):
                    tab_button.index -= 1  # Decrement the index

            # Update trace editors
            del self.trace_editors[tab.identifier] # Delete the TraceEditor instance

            # TODO: Only change tabs if the deleted tab index is <= the current tab index
            self.change_tab(tab_index - 1)

    def change_tab(self, index):
        self.content_stack.setCurrentIndex(index)
        # Update the visual style of all tabs
        for i in range(self.tab_layout.count()):
            tab_button = self.tab_layout.itemAt(i).widget()
            if isinstance(tab_button, CustomTabButton):
                if i == index:
                    # Style for selected tab
                    tab_button.setStyleSheet("font-weight: bold; \
                                              background-color: lightgray; \
                                              border: 1px solid gray;\
                                              border-radius: 4px")
                else:
                    # Style for unselected tabs
                    tab_button.setStyleSheet("font-weight: normal; \
                                              background-color: transparent; \
                                              border: 1px solid gray;\
                                              border-radius: 4px;")

    def get_all_data(self):
        # Collect data from all TraceEditors
        data = {'StartSetup': self.start_setup.get_data()}  # Include StartSetup data
        for tab_id, editor in self.trace_editors.items():
            editor_data = editor.get_data()
            data[tab_id] = editor_data
        return data


class TraceEditor(QWidget):
    HEATMAP_TIP = "Tip: Set a low 'range max' to bring out the gradient in your data."\
        "\nPoints with higher values than 'range max' will still be plotted;"\
        "\nthey will just have the same color as the highest value on the scale."\
        "\nThe default 'range max' value is twice the median of the selected column."

    def __init__(self, start_setup):
        super().__init__()
        self.df = start_setup.df.copy()
        self.trace_config_layout = QVBoxLayout()
        self._setup_trace_name()
        self._setup_point_size_layout()
        self._setup_trace_shape()
        self._setup_trace_color()
        self._setup_heatmap_options()
        self._setup_filter_options()
        self._update_visibility()
        self.current_color = '#636EFA' # Default color

    def get_data(self):
        if self.filter_checkbox.isChecked():
            dataframe = self.filter_dialog.apply_all_filters(self.df)
        else:
            dataframe = self.df

        use_heatmap = self.heatmap_checkbox.isChecked()
        if use_heatmap:
            heatmap_column = self.heatmap_column.currentText()
            cmin = str(self.heatmap_color_min.text())
            cmax = str(self.heatmap_color_max.text())
            if cmin.replace(".","").isnumeric():
                cmin = float(cmin)
            else:
                QMessageBox.critical(self, "Error", "Please choose numeric value for cmin")
                return
            if cmax.replace(".","").isnumeric():
                cmax = float(cmax)
            else:
                QMessageBox.critical(self, "Error", "Please choose numeric value for cmax")
                return
            dataframe['color'] = dataframe[heatmap_column]
        else:
            color = self.trace_color.text()
            if color:
                dataframe['color'] = self.replace_colors(dataframe,color)
            else:
                dataframe['color'] = self.replace_colors(dataframe,'#636EFA')
            cmin = None
            cmax = None

        trace_name = self.trace_name.text()
        if trace_name == "":
            trace_name = None

        symbol = self.trace_shape.currentText()

        size = str(self.point_size.text())
        if size.replace(".","").isnumeric():
            size = float(size)

        data = {
            'dataframe': dataframe,
            'name': trace_name,
            'size': size,
            'symbol': symbol,
            'cmin': cmin,
            'cmax': cmax
            }
        
        return data
    
    def replace_colors(self, dataframe, new_color):
        try:
            if dataframe['color'].dtype.kind in 'biufc':
                dataframe['color'] = new_color
            else:
                dataframe['color'] = dataframe['color'].replace(to_replace=self.current_color, value=new_color)
        except:
            dataframe['color'] = new_color
        self.current_color = new_color
        return dataframe['color']

    def _setup_trace_name(self):
        self.trace_name = QLineEdit()

        trace_name_label = QLabel("Name:")

        trace_name_layout = QHBoxLayout()
        trace_name_layout.addWidget(trace_name_label)
        trace_name_layout.addWidget(self.trace_name)

        self.trace_config_layout.addLayout(trace_name_layout)

    def _setup_trace_shape(self):
        self.trace_shape = QComboBox()

        trace_shape_label = QLabel("Select Point Shape:")

        plotly_shapes = ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up',
                         'triangle-down', 'triangle-left', 'triangle-right', 'pentagon', 'hexagon',
                         'star', 'hexagram', 'star-square', 'star-diamond', 'star-triangle-up',
                         'star-triangle-down']
        self.trace_shape.addItems(plotly_shapes)

        trace_shape_layout = QHBoxLayout()
        trace_shape_layout.addWidget(trace_shape_label)
        trace_shape_layout.addWidget(self.trace_shape)

        self.trace_config_layout.addLayout(trace_shape_layout)

    def _setup_point_size_layout(self):
        """
        Set up layout for adjusting ternary point size using a spinbox.
        """
        self.point_size = QSpinBox()
        self.point_size.setRange(1, 14)
        self.point_size.setValue(6)

        point_size_layout = QGridLayout()
        point_size_layout.addWidget(QLabel("Point Size:"), 0, 0)
        point_size_layout.addWidget(self.point_size, 0, 1)
        self.trace_config_layout.addLayout(point_size_layout)

    def _setup_trace_color(self):
        self.trace_color = QLineEdit()

        trace_color_label = QLabel("Color:")

        trace_color_layout = QHBoxLayout()
        trace_color_layout.addWidget(trace_color_label)
        trace_color_layout.addWidget(self.trace_color)

        self.trace_config_layout.addLayout(trace_color_layout)

    def _setup_heatmap_options(self):
        """
        Configure heatmap options for the plotted points.
        """
        self.heatmap_checkbox = QCheckBox("Use Heatmap")
        self.heatmap_checkbox.stateChanged.connect(self._update_visibility)
        self.trace_config_layout.addWidget(self.heatmap_checkbox)

        # Dropdown for selecting which column to use for heatmap and related controls
        self.heatmap_column = QComboBox()
        self.heatmap_column.currentIndexChanged.connect(self._inject_range_min_max)
        self.heatmap_column_label = QLabel("Heatmap Column:")
        self.heatmap_color_min = QLineEdit()
        self.heatmap_color_max = QLineEdit()
        self.heatmap_color_min_label = QLabel("Range min:")
        self.heatmap_color_max_label = QLabel("Range max:")

        # Info button with a tooltip for explaining heatmap range
        self.heatmap_range_info_button = InfoButton(self, self.HEATMAP_TIP)

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

        self.trace_config_layout.addLayout(heatmap_layout)

    def inject_data_to_filter(self, filter: FilterWidget):
        if self.df is not None:
            filter.column_combobox.clear()
            filter.column_combobox.addItems(self.df.columns)
            filter.update_visibility()

    def _inject_range_min_max(self):
        if self.df is not None:
            col = self.heatmap_column.currentText()
            dtype = self.df[col].dtype
            if np.issubdtype(dtype, np.number):  # If the dtype is numeric
                self.heatmap_color_min.setText(str(min(self.df[col])))
                self.heatmap_color_max.setText(str(2 * np.median(self.df[col])))

    def _setup_filter_options(self):
        """
        Set up conditional filtering options for the plotted data.
        """
        # Initialize the filter dialog
        self.filter_dialog = FilterDialog(self)

        # Layout for filter checkbox and show filters button
        filter_checkbox_layout = QHBoxLayout()

        # Checkbox for enabling/disabling filters
        self.filter_checkbox = QCheckBox("Use Filter(s)")
        self.filter_checkbox.stateChanged.connect(self.update_filter_visibility)

        # Button to show the filter dialog
        self.show_filters_button = QPushButton("Show Filter(s)")
        self.show_filters_button.clicked.connect(self.filter_dialog.show)
        self.show_filters_button.setVisible(False)  # Hidden by default

        # Add checkbox and button to the layout
        filter_checkbox_layout.addWidget(self.filter_checkbox)
        filter_checkbox_layout.addWidget(self.show_filters_button)
        filter_checkbox_layout.addStretch()  # Add stretch to align items to the left

        # Add the filter options layout to the main controls layout
        self.trace_config_layout.addLayout(filter_checkbox_layout)

        # Configure the filter dialog
        self.filter_dialog.accepted.connect(self.update_filter_visibility)
        self.filter_dialog.finished.connect(self.update_filter_visibility)

    def update_filter_visibility(self):
        """
        Update the visibility of filter-related widgets based on the current state.
        """
        is_filter_enabled = self.filter_checkbox.isChecked()
        self.show_filters_button.setVisible(is_filter_enabled and self.filter_dialog.isHidden())

        if is_filter_enabled and self.filter_dialog.isHidden():
            self.filter_dialog.show()
        else:
            self.filter_dialog.hide()

    def _update_visibility(self):
        is_heatmap = self.heatmap_checkbox.isChecked()
        if is_heatmap:
            self.heatmap_column.addItems(self.df.columns)
        self.heatmap_column.setVisible(is_heatmap)
        self.heatmap_column_label.setVisible(is_heatmap)
        self.heatmap_color_min.setVisible(is_heatmap)
        self.heatmap_color_min_label.setVisible(is_heatmap)
        self.heatmap_color_max.setVisible(is_heatmap)
        self.heatmap_color_max_label.setVisible(is_heatmap)
        self.heatmap_range_info_button.setVisible(is_heatmap)


class StartSetup:
    NO_FILE_SELECTED = "No file selected"
    LOAD_DATA_FILE = "Load data file"
    TERNARY_TYPES = [
        "Al2O3 CaO+Na2O+K2O FeOT+MgO", 
        "SiO2+Al2O3 CaO+Na2O+K2O FeOT+MgO", 
        "Al2O3 CaO+Na2O K2O", 
        "Custom"]

    def __init__(self):
        self.start_setup_layout  = QVBoxLayout()  # Start menu layout
        self.data_library = []
        self.setup_file_loader_layout()
        self._setup_molar_conversion()
        self.setup_ternary_type_selection_layout()
        self.setup_custom_type_selection_widgets()
        self.setup_apex_name_widgets()
        self.setup_title_field()
        self.update_visibility()

    def setup_file_loader_layout(self):
        """
        Layout for file loading. Includes a label to display the file path and
        a button to trigger the file loading dialog.
        """
        file_loader_layout = QGridLayout()
        self.file_label = QLineEdit(self.NO_FILE_SELECTED)
        self.file_label.setReadOnly(True)
        self.file_label.setFrame(False)
        self.file_label.setCursor(Qt.IBeamCursor)
        self.file_label.setStyleSheet("""
            QLineEdit {
                border: none;
                background-color: transparent;
            }
        """)
        self.load_button = QPushButton(self.LOAD_DATA_FILE)
        self.load_button.clicked.connect(self.load_data_file)
        
        file_loader_layout.addWidget(self.file_label,  0, 0)
        file_loader_layout.addWidget(self.load_button, 0, 1)
        
        self.start_setup_layout.addLayout(file_loader_layout)

    def _setup_molar_conversion(self):
        """
        Set up conditional filtering options for the plotted data.
        """
        # Layout for filter checkbox and show filters button
        molar_conversion_checkbox_layout = QHBoxLayout()

        # Checkbox for enabling/disabling filters
        self.molar_conversion = QCheckBox("Convert from wt% to molar: ")
        self.molar_conversion.setChecked(True)

        # Add checkbox and button to the layout
        molar_conversion_checkbox_layout.addWidget(self.molar_conversion)

        # Add the filter options layout to the main controls layout
        self.start_setup_layout.addLayout(molar_conversion_checkbox_layout)

    def load_data_file(self):

        os.makedirs("../data", exist_ok=True)
        dev_data = os.listdir("../data")
        if dev_data:

            filepath = "../data/" + dev_data[0]
            self.df = pd.read_csv(filepath)
            self.file_label.setText(dev_data[0])

        else:

            data_file, _ = QFileDialog.getOpenFileName(None, "Open data file", "", "Data Files (*.csv *.xlsx)")
        
            if data_file:

                self.file_label.setText(data_file)
                self.file_label.setToolTip(data_file)
                if data_file.endswith('.csv'):
                    try:
                        header = find_header_row_csv(data_file, 16)
                        self.df = pd.read_csv(data_file, header=header)
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
        self.update_visibility()

    def setup_ternary_type_selection_layout(self):
        """
        Layout for choosing the type of ternary diagram.
        """
        ternary_type_selection_layout = QGridLayout()
        ternary_type_selection_layout.addWidget(QLabel("Ternary Type:"), 0, 0)
        self.diagram_type_combobox = QComboBox()
        self.diagram_type_combobox.addItems(self.TERNARY_TYPES)
        self.diagram_type_combobox.currentIndexChanged.connect(self.update_visibility)

        ternary_type_selection_layout.addWidget(self.diagram_type_combobox, 0, 1)

        self.start_setup_layout.addLayout(ternary_type_selection_layout)

    def setup_custom_type_selection_widgets(self):
        """
        Selecting custom apices for the ternary.
        """
        self.available_columns_list = QListWidget()
        self.custom_type_widgets = []
        self.selected_values_lists = {}
        grid_layout = QGridLayout()

        for i, apex in enumerate(['Top', 'Left', 'Right']):
            inner_grid_layout = QGridLayout()
            vbox_layout = QVBoxLayout()

            label = QLabel(f"{apex} apex element(s):")
            vbox_layout.addWidget(label)
            list_widget = SelectedValuesList(self)
            self.selected_values_lists[i] = list_widget

            add_btn = QPushButton("Add >>")
            add_btn.clicked.connect(lambda *args, lw=list_widget: self._add_column(lw))
            vbox_layout.addWidget(add_btn)

            remove_btn = QPushButton("Remove <<")
            remove_btn.clicked.connect(lambda *args, lw=list_widget: self._remove_value(lw))
            vbox_layout.addWidget(remove_btn)

            inner_grid_layout.addLayout(vbox_layout, 0, 0)
            inner_grid_layout.addWidget(list_widget, 0, 1)
            grid_layout.addLayout(inner_grid_layout, i, 0)
            self.custom_type_widgets.extend([label, list_widget, add_btn, remove_btn])

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.available_columns_list)
        h_layout.addLayout(grid_layout)

        self.start_setup_layout.addLayout(h_layout)
        self.custom_type_widgets.append(self.available_columns_list)

    def _add_column(self, lw: QListWidget):
        selected_item = self.available_columns_list.currentItem()
        if selected_item is not None:
            self.available_columns_list.takeItem(self.available_columns_list.row(selected_item))
            lw.addItem(selected_item)

    def _remove_value(self, lw: SelectedValuesList):
        selected_item = lw.currentItem()
        if selected_item is not None:
            lw.takeItem(lw.row(selected_item))
            self.available_columns_list.addItem(selected_item)

    def setup_apex_name_widgets(self):
        """
        Customize the display names of the apices. These widgets are only visible when the user 
        checks the 'Customize apex display names' option.
        """

        # Line edits and labels for custom apex names, added to QHBoxLayouts for organization
        self.custom_apex_name_widgets = []

        self.top_apex_name   = QLineEdit()
        self.left_apex_name  = QLineEdit()
        self.right_apex_name = QLineEdit()

        self.top_apex_tag   = QLabel("Top apex display name:")
        self.left_apex_tag  = QLabel("Left apex display name:")
        self.right_apex_tag = QLabel("Right apex display name:")

        top_apex_hlayout = QHBoxLayout()
        top_apex_hlayout.addWidget(self.top_apex_tag)
        top_apex_hlayout.addWidget(self.top_apex_name)

        left_apex_hlayout = QHBoxLayout()
        left_apex_hlayout.addWidget(self.left_apex_tag)
        left_apex_hlayout.addWidget(self.left_apex_name)

        right_apex_hlayout = QHBoxLayout()
        right_apex_hlayout.addWidget(self.right_apex_tag)
        right_apex_hlayout.addWidget(self.right_apex_name)

        # Aggregate the widgets for easy access and manipulation
        self.custom_apex_name_widgets.extend(
            [self.top_apex_name,   self.top_apex_tag,
             self.left_apex_name,  self.left_apex_tag,
             self.right_apex_name, self.right_apex_tag])

        self.start_setup_layout.addLayout(top_apex_hlayout)
        self.start_setup_layout.addLayout(left_apex_hlayout)
        self.start_setup_layout.addLayout(right_apex_hlayout)

    def setup_title_field(self):
        """
        Setting a title for the ternary figure.
        """
        title_layout = QGridLayout()
        title_layout.addWidget(QLabel('Title:'), 0, 0)
        self.title_field = QLineEdit()
        title_layout.addWidget(self.title_field, 0, 1)

        self.start_setup_layout.addLayout(title_layout)

    def update_visibility(self):
        is_custom_type = self.diagram_type_combobox.currentText() == 'Custom'
        for widget in self.custom_type_widgets:
            widget.setVisible(is_custom_type)

    def get_ternary_type(self):
        all_custom_apex_values = []
        for apex_index in range(3):
            apex_oxides = self.selected_values_lists[apex_index]
            custom_apex_values = []
            for oxide in range(apex_oxides.count()):
                custom_apex_values.append(apex_oxides.item(oxide).text())
            all_custom_apex_values.append(custom_apex_values)

        ternary_type = self.diagram_type_combobox.currentText()
        if ternary_type == "Custom":
            ternary_type = all_custom_apex_values
        else:
            ternary_type = [apex.split("+") for apex in ternary_type.split(" ")]

        return ternary_type

    def get_data(self):

        data = {
            'file': self.file_label.text(),
            'ternary type': self.get_ternary_type(),
            'apex custom names': [self.top_apex_name.text(),    # Top apex
                                  self.left_apex_name.text(),   # Left apex
                                  self.right_apex_name.text()], # Right apex
            'title': self.title_field.text(),
            'convert_wtp_to_molar': self.molar_conversion.isChecked(),
            }

        return data


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setup_settings_window()

    def setup_settings_window(self):
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


class LeftSide(QWidget):
    def __init__(self):
        super().__init__()  # Initialize the QWidget part of this class
        self.left_side_layout = QVBoxLayout()
        self.setLayout(self.left_side_layout)  # Set the layout for this widget
        self.setMaximumWidth(500)

        self.setup_top_buttons()
        self.setup_tabs()
        self.setup_bottom_buttons()

    def setup_top_buttons(self):
        top_buttons_layout = QHBoxLayout()
        self.setup_fonts()
        top_buttons_layout.addWidget(self.title_label)
        top_buttons_layout.addStretch(1)
        top_buttons_layout.addWidget(self.create_settings_button())
        self.left_side_layout.insertLayout(0, top_buttons_layout)

    def setup_tabs(self):
        self.tab_manager = TabManager()
        self.left_side_layout.addWidget(self.tab_manager)

    def setup_bottom_buttons(self):
        """
        The bottom buttons in the UI for previewing and saving the ternary diagram as well as 
        saving filtered data.
        """
        # Horizontal layout for bottom buttons
        bottom_buttons = QHBoxLayout()

        # Button to generate the ternary diagram preview
        self.generate_button = QPushButton("Preview Ternary")
        self.generate_button.setCursor(Qt.PointingHandCursor)

        # Button to save the generated ternary diagram
        self.save_ternary_button = QPushButton("Save Ternary")
        self.save_ternary_button.setCursor(Qt.PointingHandCursor)

        # Button to change the color of selected data
        self.change_color_button = QPushButton("Change Color")
        self.change_color_button.setCursor(Qt.PointingHandCursor)

        # Add buttons to the layout
        bottom_buttons.addWidget(self.generate_button)
        bottom_buttons.addWidget(self.save_ternary_button)
        bottom_buttons.addWidget(self.change_color_button)

        # Add the bottom buttons layout to the main controls layout
        self.left_side_layout.addLayout(bottom_buttons)

    def create_settings_button(self):
        button = QPushButton(self)
        button.clicked.connect(self.open_settings_dialog)
        button.setStyleSheet('border: none;')
        button.setIconSize(QSize(20, 20))
        button.setFixedSize(20, 20)
        button.setCursor(Qt.PointingHandCursor)
        self.updateSettingsIcon(button)
        return button
    
    def updateSettingsIcon(self, button):
        """
        Update the settings icon based on the current theme.
        """
        icon_path = './assets/icons/settings_icon.png'
        icon = QIcon(icon_path)
        button.setIcon(icon)

    def open_settings_dialog(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def setup_fonts(self):
        """
        Load the 'Motter Tektura' font and use it to set up the application's title label.
        The title label is configured to display the 'quick ternaries' logo which includes a
        hyperlink to the project repository.
        """
        current_directory = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(current_directory, 'assets', 'fonts', 'Motter Tektura Normal.ttf')
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.title_label = QLabel()
        if font_id != -1:
            # If the font was successfully loaded, proceed to set up the title label
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.custom_font = QFont(font_families[0], pointSize=20)
                self.title_label.setFont(self.custom_font)
        self.updateTitleLabelColor()  # Call a method to set the text color based on the current theme
        self.title_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        self.title_label.setOpenExternalLinks(True) # Allow the label to open links

    def updateTitleLabelColor(self):
        """
        Update the title label hyperlink color based on the current theme.
        """
        # Check the palette to determine if it's dark mode
        palette = self.palette()
        is_dark_mode = palette.color(QPalette.Base).lightness() < palette.color(QPalette.Text).lightness()
        color = 'white' if is_dark_mode else 'black'  # Choose color based on the theme
        self.title_label.setText(
            f'<a href={GITHUB_LINK} ' +
            f'style="color: {color}; text-decoration:none;">' +
            'quick ternaries' +
            '</a>'
        )


class RenderTernary:
    def parse_start_setup_data(self, start_setup_data):
        formula_list = start_setup_data['ternary type']
        apex_names = get_apex_names(formula_list,
                                    start_setup_data['apex custom names'])
        
        title = create_title(formula_list, start_setup_data['title'])

        data = {"formula list": formula_list,
                "apex names": apex_names,
                "title": title,
                "convert_wtp_to_molar": start_setup_data["convert_wtp_to_molar"]}

        return data

    def make_graph(self, all_data):

        start_setup_data = self.parse_start_setup_data(all_data['StartSetup'])
        formula_list = start_setup_data["formula list"]
        apex_names   = start_setup_data["apex names"]
        title        = start_setup_data["title"]

        graph = TernaryGraph(title, apex_names, enable_darkmode=False)
        data = Trace(formula_list, apex_names)

        all_trace_ids = list(all_data.keys())
        all_trace_ids = [i for i in all_trace_ids if i!="StartSetup"]
        all_trace_ids.sort()
        # TODO: Create better method of sorting tab IDs to allow for point plot order customizability
        for trace_id in all_trace_ids:
            trace_data = all_data[trace_id]
            if trace_data is not None:
                trace = data.make_trace(trace_data["dataframe"],
                                        name       = trace_data["name"],
                                        symbol     = trace_data["symbol"],
                                        size       = trace_data["size"],
                                        cmin       = trace_data["cmin"],
                                        cmax       = trace_data["cmax"],
                                        hover_cols = None,
                                        convert_wtp_to_molar = start_setup_data["convert_wtp_to_molar"])
                graph.add_trace(trace)

        return graph

    def write_html(self, graph):

        # Convert the figure to HTML
        html_str = graph.to_html()

        js_code = """
            <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                document.addEventListener("DOMContentLoaded", function() {
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.plotlyInterface = channel.objects.plotlyInterface;
                        var plotElement = document.getElementsByClassName('plotly-graph-div')[0];
                        plotElement.on('plotly_selected', function(eventData) {
                            if (eventData) {
                                var indices = eventData.points.map(function(pt) { return pt.pointIndex; });
                                window.plotlyInterface.receiveSelectedIndices(indices);
                            }
                        });
                    });
                });
            </script>
        """

        complete_html = html_str + js_code

        current_directory = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(current_directory, 'resources', 'ternary.html')
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save the HTML content to the file
        with open(save_path, 'w', encoding='utf-8') as file:
            file.write(complete_html)

        html_object = QUrl.fromLocalFile(os.path.abspath(save_path))

        return html_object

class PlotlyInterface(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.selectedIndices = []
        self.selectedColor = None

    @Slot(list)
    def receiveSelectedIndices(self, indices):
        self.selectedIndices = indices

    def applyColorChange(self):
        all_data = self.main_window.left_side.tab_manager.get_all_data()
        all_traces = [all_data[dict_key] for dict_key in all_data.keys() if dict_key!="StartSetup"]
        for trace in all_traces:
            trace_data = trace['dataframe']
            for index in self.selectedIndices:
                if 0 <= index < len(trace_data):
                    trace_data.at[index, 'color'] = self.selectedColor
        self.main_window.generate_diagram()  # Re-plot with updated colors


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout()
        self.ternary_view = QWebEngineView()
        self.setupWebChannel()
        self.ternary_view.page().setBackgroundColor(Qt.transparent)

        self.left_side = LeftSide()  # Create an instance of LeftSide
        self.main_layout.addWidget(self.left_side)  # Add it to the layout

        self.current_ternary_view = None  # Reference to the current ternary view
        self.connect_ternary_controls()

        # Set the main layout for the central widget
        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.resize(300, 600)

    def generate_diagram(self):
        all_data = self.left_side.tab_manager.get_all_data()
        # Only generate the diagram if there is trace data
        if len(all_data)!=1:
            ternary = RenderTernary()
            graph = ternary.make_graph(all_data)
            ternary_html = ternary.write_html(graph)

            self.ternary_view.load(ternary_html)
            self.ternary_view.setMinimumWidth(500)
            self.main_layout.addWidget(self.ternary_view)
        else:
            if all_data["StartSetup"]["file"] != "No file selected":
                QMessageBox.critical(self, "Error", "Please add a trace before rendering")

    def connect_ternary_controls(self):
        self.left_side.tab_manager.new_tab_button.clicked.connect(self.generate_diagram)
        self.left_side.generate_button.clicked.connect(self.generate_diagram)  # Connect the button to its action

        self.left_side.change_color_button.clicked.connect(self.changeColor)

    def setupWebChannel(self):
        self.plotlyInterface = PlotlyInterface(self)
        channel = QWebChannel(self.ternary_view.page())
        channel.registerObject("plotlyInterface", self.plotlyInterface)
        self.ternary_view.page().setWebChannel(channel)

    @Slot()
    def changeColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.plotlyInterface.selectedColor = color.name()
            # Apply color change to currently selected indices
            self.plotlyInterface.applyColorChange()
            self.generate_diagram()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
