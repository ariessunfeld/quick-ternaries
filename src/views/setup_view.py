"""Contains the BaseSetupView(QWidget) class, which encompasses the widgets involved in setup, and is used in the dynamic content area of the MainWindow"""

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout, 
    QLabel, 
    QLineEdit, 
    QPushButton, 
    QGridLayout,
    QListWidget,
    QComboBox,
    QCheckBox,
    QScrollArea,
    QListWidgetItem
)

from PySide6.QtCore import Qt

class ListItemWidget(QWidget):
    def __init__(self, title, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QHBoxLayout(self)

        self.set_title(title)
        self.layout.addStretch()
        self.create_close_button()

        self.setLayout(self.layout)

    def set_title(self, title):
        label = QLabel(title)
        self.layout.addWidget(label)

    def create_close_button(self):
        self.close_button = QPushButton("X")
        self.close_button.setMaximumWidth(20)
        self.layout.addWidget(self.close_button)



class LoadedDataScrollView(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.file_list = QListWidget(self)
        self.set_style()
        
        self.layout.addWidget(self.file_list)
        self.setLayout(self.layout)

    def set_style(self):
        self.file_list.setStyleSheet("""
            QListWidget {
                border: 1px solid gray;
                background-color: transparent;
            }
            QListWidget::item {
                margin: 2px;
                padding: 2px;
            }
            QListWidget::item:selected {
                background: transparent;
                color: black;
            }
        """)

    def add_item(self, title):
        list_item = QListWidgetItem(self.file_list)
        item_widget = ListItemWidget(title)
        list_item.setSizeHint(item_widget.sizeHint())
        self.file_list.addItem(list_item)
        self.file_list.setItemWidget(list_item, item_widget)
        return list_item, item_widget.close_button

    def remove_item(self, item):
        self.file_list.takeItem(self.file_list.row(item))


class AddRemoveList(QWidget):
    """A megawidget for add/remove buttons to the left of a ListWidget"""
    def __init__(self, parent:QWidget|None=None, label: str|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.list = QListWidget()
        self.inner_layout = QVBoxLayout()
        self.inner_layout_widget = QWidget()
        self.button_add = QPushButton('Add >>')
        self.button_remove = QPushButton('Remove <<')
        if label:
            self.label = QLabel(label)
            self.inner_layout.addWidget(self.label)
        self.inner_layout.addWidget(self.button_add)
        self.inner_layout.addWidget(self.button_remove)
        self.inner_layout_widget.setLayout(self.inner_layout)
        self.layout.addWidget(self.inner_layout_widget)
        self.layout.addWidget(self.list)

    # Direct access to self.list methods (QListWidget methods)
    def currentItem(self):
        return self.list.currentItem()
    
    def clear(self):
        self.list.clear()

    def addItem(self, data: str):
        self.list.addItem(data)

    def addItems(self, data: list[str]):
        self.list.addItems(data)

    def get_items(self):
        ret = []
        for row in range(len(self.list.count())):
            ret.append(self.list.itemAt(row).text())
        return ret


class CustomApexSelectionView(QWidget):
    """A megawidget containing the ListWidgets and buttons for custom apex selection"""

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)
        
        self.list_widget_available_columns = QListWidget()
        self.add_remove_list_top_apex_columns = AddRemoveList(self, 'Top Apex')
        self.add_remove_list_right_apex_columns = AddRemoveList(self, 'Right Apex')
        self.add_remove_list_left_apex_columns = AddRemoveList(self, 'Left Apex')

        self.layout.addWidget(self.list_widget_available_columns)
        self.right_layout.addWidget(self.add_remove_list_top_apex_columns)
        self.right_layout.addWidget(self.add_remove_list_right_apex_columns)
        self.right_layout.addWidget(self.add_remove_list_left_apex_columns)
        self.layout.addWidget(self.right_layout_widget)


class CustomHoverDataSelectionView(QWidget):
    """A megawidget containing the ListWidgets and buttons for custom hover data selection"""

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()
        self.right_layout_widget = QWidget()
        self.right_layout_widget.setLayout(self.right_layout)

        self.list_widget_available_columns = QListWidget()
        self.add_remove_list = AddRemoveList(self, 'Hover Data')

        self.layout.addWidget(self.list_widget_available_columns)
        self.right_layout.addWidget(self.add_remove_list)
        self.layout.addWidget(self.right_layout_widget)

        self.setLayout(self.layout)

    def add_to_available_column(self, *args):
        # Should be called by model
        pass

    def add_to_selected_column(self, *args):
        pass

    def remove_from_available_column(self, *args):
        pass

    def remove_from_selected_column(self, *args):
        pass


class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    def __init__(self, label:str = '', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.line_edit = QLineEdit()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)
        self.setLayout(self.layout)

    def text(self):
        return self.line_edit.text()


class LeftLabeledCheckbox(QWidget):
    """A labeled CheckBox megawidget, for check boxes with QLabels to their left"""

    def __init__(self, label:str='', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.label = QLabel(label)
        self.checkbox = QCheckBox()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.checkbox)
        self.setLayout(self.layout)

    def isChecked(self):
        return self.checkbox.isChecked()


class BaseSetupView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setMaximumWidth(500)

        self.loaded_data_scroll_view = LoadedDataScrollView()
        self.button_add_data = QPushButton('Add Data')

        self.combobox_ternary_type = QComboBox()
        self.custom_apex_selection_view = CustomApexSelectionView()
        self.custom_apex_selection_view.setVisible(False)  # Hide the CustomApexSelectionView at first

        self.labeled_line_edit_ternary_title = LeftLabeledLineEdit('Title:')
        self.labeled_line_edit_top_apex_display_name   = LeftLabeledLineEdit('Top Apex (display name):')
        self.labeled_line_edit_right_apex_display_name = LeftLabeledLineEdit('Right Apex (display name):')
        self.labeled_line_edit_left_apex_display_name  = LeftLabeledLineEdit('Left Apex (display name):')

        self.labeled_checkbox_customize_hover_data = LeftLabeledCheckbox('Customize Cursor-Hover Data:')
        self.custom_hover_data_selection_view = CustomHoverDataSelectionView()
        self.custom_hover_data_selection_view.setVisible(False) # Hide the CustomApexSelectionView at first

        self.layout.addWidget(self.loaded_data_scroll_view)
        self.layout.addWidget(self.button_add_data)

        self.layout.addWidget(self.combobox_ternary_type)
        self.layout.addWidget(self.custom_apex_selection_view)

        self.layout.addWidget(self.labeled_line_edit_ternary_title)
        self.layout.addWidget(self.labeled_line_edit_top_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_right_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_left_apex_display_name)

        self.layout.addWidget(self.labeled_checkbox_customize_hover_data)
        self.layout.addWidget(self.custom_hover_data_selection_view)


    def update_loaded_data_scroll_view(self, update):
        pass

    def update_custom_apex_selection_view_visibility(self, is_visible: bool):
        self.custom_apex_selection_view.setVisible(is_visible)

    def update_custom_hover_data_selection_view_visible(self, is_visible: bool):
        self.custom_hover_data_selection_view.setVisible(is_visible)
