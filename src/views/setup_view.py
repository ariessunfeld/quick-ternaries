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
    QComboBox
)

class LoadedDataScrollView(QWidget):
    # This is where loaded data will be shown
    # Like the tabs for traces, loaded data should
    # have little Xs that allow for removal
    pass

class AddRemoveList(QWidget):
    """A megawidget for add/remove buttons to the left of a ListWidget"""
    def __init__(self, parent:QWidget|None=None, label: str|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
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


class LeftLabeledLineEdit(QWidget):
    """A labeled LineEdit megawidget, for line edits with QLabels to their left"""
    
    def __init__(self, text:str = '', parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.label = QLabel(text)
        self.line_edit = QLineEdit()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.line_edit)


class BaseSetupView(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        self.loaded_data_scroll_view = LoadedDataScrollView()
        self.button_add_data = QPushButton('Add Data')
        self.combobox_ternary_type = QComboBox()
        self.custom_apex_selection_view = CustomApexSelectionView()
        self.custom_apex_selection_view.setVisible(False)

        self.labeled_line_edit_ternary_title = LeftLabeledLineEdit('Title:')
        self.labeled_line_edit_top_apex_display_name = LeftLabeledLineEdit('Top Apex (display name):')
        self.labeled_line_edit_right_apex_display_name = LeftLabeledLineEdit('Right Apex (display name):')
        self.labeled_line_edit_left_apex_display_name = LeftLabeledLineEdit('Left Apex (display name):')

        self.layout.addWidget(self.loaded_data_scroll_view)
        self.layout.addWidget(self.button_add_data)
        self.layout.addWidget(self.combobox_ternary_type)
        self.layout.addWidget(self.custom_apex_selection_view)
        self.layout.addWidget(self.labeled_line_edit_ternary_title)
        self.layout.addWidget(self.labeled_line_edit_top_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_right_apex_display_name)
        self.layout.addWidget(self.labeled_line_edit_left_apex_display_name)

    def update_loaded_data_scroll_view(self, update):
        pass

    def update_custom_apex_selection_view_visibility(self, is_visible: bool):
        self.custom_apex_selection_view.setVisible(is_visible)
