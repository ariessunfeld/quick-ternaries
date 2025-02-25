import re
import sys
import uuid
import json
from dataclasses import (
    dataclass, 
    field, 
    fields,
    asdict,
    is_dataclass
)

try:
    import pandas as pd
except ImportError:
    pd = None

from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QMessageBox,
    QVBoxLayout, 
    QHBoxLayout, 
    QListWidget, 
    QListWidgetItem,
    QGroupBox,
    QStackedWidget, 
    QLabel, 
    QAbstractItemView, 
    QSplitter,
    QPushButton, 
    QLineEdit, 
    QComboBox, 
    QFormLayout,
    QDoubleSpinBox, 
    QCheckBox, 
    QFileDialog, 
    QInputDialog
)
from PySide6.QtCore import Qt, QRect, QEvent, QPoint
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QSplitterHandle, QSplitter
from PySide6.QtWidgets import QScrollArea
from PySide6.QtGui import QIcon, QPixmap, QPainter, QCursor, QColor

# If available, use QWebEngineView; otherwise fall back.
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = QLabel

# --------------------------------------------------------------------
# Constants / Pinned Item Labels
# --------------------------------------------------------------------
SETUP_MENU_LABEL = "Setup Menu"
ADD_TRACE_LABEL = "Add Trace (+)"


def recursive_to_dict(obj):
    """Recursively convert dataclass objects (or lists/dicts) to dictionaries."""
    if is_dataclass(obj):
        return asdict(obj)
    elif isinstance(obj, list):
        return [recursive_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: recursive_to_dict(v) for k, v in obj.items()}
    else:
        return obj
    

# --------------------------------------------------------------------
# Custom Splitter Classes
# --------------------------------------------------------------------
class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.orientation = orientation
        cursor = Qt.CursorShape.SplitHCursor if orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor
        self.setCursor(cursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Transparent background

        grip_color = QColor(128, 128, 128)
        painter.setBrush(grip_color)
        if self.orientation == Qt.Orientation.Horizontal:
            width = self.width()
            center_x = width // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(center_x - dot_radius, self.height() // 2 + i * spacing - dot_radius,
                                    int(dot_radius * 2), int(dot_radius * 2))
        else:
            height = self.height()
            center_y = height // 2
            dot_radius = 3.5
            spacing = 10
            for i in range(-1, 2):
                painter.drawEllipse(self.width() // 2 + i * spacing - dot_radius, center_y - dot_radius,
                                    int(dot_radius * 2), int(dot_radius * 2))

    def enterEvent(self, event):
        cursor = Qt.CursorShape.SplitHCursor if self.orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor
        self.setCursor(cursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

class CustomSplitter(QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)

# --------------------------------------------------------------------
# MultiFieldSelector Widget
# --------------------------------------------------------------------
class MultiFieldSelector(QWidget):
    """
    A composite widget that lets users select one or more fields.
    Displays current selections in a list with Add/Remove buttons.
    """

    selectionChanged = Signal(list)  # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_options = []
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.listWidget = QListWidget(self)
        layout.addWidget(self.listWidget)
        btn_layout = QVBoxLayout()
        layout.addLayout(btn_layout)
        self.addButton = QPushButton("Add", self)
        self.removeButton = QPushButton("Remove", self)
        btn_layout.addWidget(self.addButton)
        btn_layout.addWidget(self.removeButton)
        btn_layout.addStretch()
        self.addButton.clicked.connect(self.add_field)
        self.removeButton.clicked.connect(self.remove_field)

    def set_available_options(self, options):
        self.available_options = options

    def add_field(self):
        choices = [opt for opt in self.available_options if opt not in self.get_selected_fields()]
        if not choices:
            return
        item, ok = QInputDialog.getItem(self, "Select Field", "Available Fields:", choices, 0, False)
        if ok and item:
            self.listWidget.addItem(item)
            self.selectionChanged.emit(self.get_selected_fields())

    def remove_field(self):
        current_item = self.listWidget.currentItem()
        if current_item:
            row = self.listWidget.row(current_item)
            self.listWidget.takeItem(row)
            self.selectionChanged.emit(self.get_selected_fields())

    def get_selected_fields(self):
        return [self.listWidget.item(i).text() for i in range(self.listWidget.count())]

    def set_selected_fields(self, fields_list):
        self.listWidget.clear()
        for f in fields_list:
            self.listWidget.addItem(f)

# --------------------------------------------------------------------
# TabListWidget and TabPanel (for managing tabs)
# --------------------------------------------------------------------
class TabListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.Drop and source is self.viewport():
            self.dropEvent(event)
            return True
        return super().eventFilter(source, event)

    def dropEvent(self, event):
        selected_item = self.currentItem()
        super().dropEvent(event)
        if selected_item:
            row = self.row(selected_item)
            if row != -1:
                self.setCurrentRow(row)
                self.itemClicked.emit(selected_item)
        if self.item(0) is None or self.item(0).text() != SETUP_MENU_LABEL:
            self._remove_pinned_items(SETUP_MENU_LABEL)
            setup_item = self._create_setup_item()
            self.insertItem(0, setup_item)
        if self.item(self.count() - 1) is None or self.item(self.count() - 1).text() != ADD_TRACE_LABEL:
            self._remove_pinned_items(ADD_TRACE_LABEL)
            add_item = self._create_add_item()
            self.addItem(add_item)

    def _remove_pinned_items(self, label):
        for i in reversed(range(self.count())):
            it = self.item(i)
            if it and it.text() == label:
                self.takeItem(i)

    def _create_setup_item(self) -> QListWidgetItem:
        item = QListWidgetItem(SETUP_MENU_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _create_add_item(self) -> QListWidgetItem:
        item = QListWidgetItem(ADD_TRACE_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def startDrag(self, supportedActions):
        current_item = self.currentItem()
        if current_item and current_item.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return
        super().startDrag(supportedActions)

    def mimeData(self, items):
        if items:
            for it in items:
                if it.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                    return None
        return super().mimeData(items)

class TabPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = TabListWidget()
        self.listWidget.itemSelectionChanged.connect(self._on_item_selection_changed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.listWidget)

        self.tabSelectedCallback = None      # (unique_id) -> ...
        self.tabRenamedCallback = None       # (unique_id, new_label) -> ...
        self.tabRemovedCallback = None       # (unique_id) -> ...
        self.tabAddRequestedCallback = None  # () -> ...

        # Map unique_id -> associated model (TraceEditorModel or SetupMenuModel)
        self.id_to_widget = {}

        setup_item = self._create_setup_item()
        self.listWidget.addItem(setup_item)
        add_item = self._create_add_item()
        self.listWidget.addItem(add_item)

        # Remove icon for deletion
        self.removeIcon = QIcon()
        pm = QPixmap(16, 16)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawLine(2, 2, 14, 14)
        painter.drawLine(14, 2, 2, 14)
        painter.end()
        self.removeIcon.addPixmap(pm)

        self.listWidget.itemClicked.connect(self._on_item_clicked)
        self.listWidget.itemChanged.connect(self._on_item_changed)

        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self.on_palette_changed)
        self.apply_dynamic_style()

    def _on_item_selection_changed(self):
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            label = item.text()
            if label not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                if uid and self.tabSelectedCallback:
                    self.tabSelectedCallback(uid)

    def _create_setup_item(self) -> QListWidgetItem:
        item = QListWidgetItem(SETUP_MENU_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def _create_add_item(self) -> QListWidgetItem:
        item = QListWidgetItem(ADD_TRACE_LABEL)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        return item

    def apply_dynamic_style(self):
        if not QApplication.instance():
            return
        palette = QApplication.instance().palette()
        base_color = palette.base().color().name()
        text_color = palette.text().color().name()
        alt_base_color = palette.alternateBase().color().name()
        highlight_color = palette.highlight().color().name()
        highlight_text_color = palette.highlightedText().color().name()

        style = f"""
        QListWidget {{
            background-color: {base_color};
            color: {text_color};
            border: 1px solid #aaa;
            font-size: 14pt;
            margin: 0px;
        }}
        QListWidget::item {{
            background-color: {alt_base_color};
            border: 1px solid #ccc;
            margin: 4px;
            padding: 8px;
        }}
        QListWidget::item:selected {{
            background-color: {highlight_color};
            color: {highlight_text_color};
        }}
        """
        self.listWidget.setStyleSheet(style)

    def on_palette_changed(self):
        self.apply_dynamic_style()

    def add_tab(self, title: str, model) -> str:
        unique_id = str(uuid.uuid4())
        self.id_to_widget[unique_id] = model

        new_item = QListWidgetItem(title)
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        new_item.setIcon(self.removeIcon)
        new_item.setData(Qt.ItemDataRole.UserRole, unique_id)

        insert_index = self.listWidget.count() - 1
        self.listWidget.insertItem(insert_index, new_item)
        self.listWidget.setCurrentItem(new_item)
        return unique_id

    def select_tab_by_id(self, unique_id: str):
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None:
                item_id = it.data(Qt.ItemDataRole.UserRole)
                if item_id == unique_id:
                    self.listWidget.setCurrentItem(it)
                    break

    def remove_tab_by_id(self, unique_id: str):
        old_selected_item = self.listWidget.currentItem()
        old_selected_uid = None
        if old_selected_item:
            old_selected_uid = old_selected_item.data(Qt.ItemDataRole.UserRole)
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                self.listWidget.takeItem(i)
                self.id_to_widget.pop(unique_id, None)
                break
        if old_selected_uid != unique_id:
            if old_selected_item and self.listWidget.row(old_selected_item) != -1:
                self.listWidget.setCurrentItem(old_selected_item)
            else:
                if self.listWidget.count() > 0:
                    self.listWidget.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem):
        label = item.text()
        if label == SETUP_MENU_LABEL:
            if self.tabSelectedCallback:
                self.tabSelectedCallback("setup-menu-id")
            return
        if label == ADD_TRACE_LABEL:
            if self.tabAddRequestedCallback:
                self.tabAddRequestedCallback()
            return
        if self._clicked_on_remove_icon(item):
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabRemovedCallback:
                self.tabRemovedCallback(uid)
        else:
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabSelectedCallback:
                self.tabSelectedCallback(uid)

    def _on_item_changed(self, item: QListWidgetItem):
        label = item.text()
        if label in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return
        uid = item.data(Qt.ItemDataRole.UserRole)
        if uid and self.tabRenamedCallback:
            self.tabRenamedCallback(uid, label)
        self.listWidget.itemClicked.emit(item)

    def _clicked_on_remove_icon(self, item: QListWidgetItem) -> bool:
        pos = self.listWidget.viewport().mapFromGlobal(QCursor.pos())
        item_rect = self.listWidget.visualItemRect(item)
        icon_size = 16
        margin_left = 20
        icon_left = item_rect.left() + margin_left
        icon_top = item_rect.top() + (item_rect.height() - icon_size) // 2
        icon_rect = QRect(icon_left, icon_top, icon_size, icon_size)
        return icon_rect.contains(pos)

# --------------------------------------------------------------------
# Filter Model
# --------------------------------------------------------------------
@dataclass
class FilterModel:
    filter_name: str = field(
        default="Filter",
        metadata={"label": "Filter Name:", "widget": QLineEdit}
    )
    filter_column: str = field(
        default="",
        metadata={"label": "Filter Column:", "widget": QComboBox}
    )
    filter_operation: str = field(
        default="<",
        metadata={"label": "Filter Operation:", "widget": QComboBox}
    )
    filter_value1: float = field(
        default=0.0,
        metadata={"label": "Value A:", "widget": QDoubleSpinBox}
    )
    filter_value2: float = field(
        default=0.0,
        metadata={
            "label": "Value B:",
            "widget": QDoubleSpinBox,
            "depends_on": "filter_operation",
            "visible_if": "a < x < b"  # custom marker used by the view
        }
    )


# class FilterPanel(QWidget):
#     filterSelectedCallback = Signal(int)  # emits the selected filter index
#     filterAddRequestedCallback = Signal()
#     filterRemovedCallback = Signal(int)
#     filterRenamedCallback = Signal(int, str)
    
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.listWidget = QListWidget(self)
#         layout = QVBoxLayout(self)
#         layout.addWidget(self.listWidget)
#         self.addFilterButton = QPushButton("Add Filter", self)
#         layout.addWidget(self.addFilterButton)
#         self.addFilterButton.clicked.connect(lambda: self.filterAddRequestedCallback.emit())
#         self.listWidget.itemClicked.connect(self._on_item_clicked)
#         self.listWidget.itemChanged.connect(self._on_item_changed)
#         self.filter_models = []  # holds FilterModel instances

#     def _on_item_clicked(self, item: QListWidgetItem):
#         idx = self.listWidget.row(item)
#         self.filterSelectedCallback.emit(idx)

#     def _on_item_changed(self, item: QListWidgetItem):
#         idx = self.listWidget.row(item)
#         new_name = item.text()
#         self.filterRenamedCallback.emit(idx, new_name)

#     def add_filter(self, filter_model: FilterModel):
#         self.filter_models.append(filter_model)
#         item = QListWidgetItem(filter_model.filter_name)
#         item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
#         self.listWidget.addItem(item)

#     def remove_filter(self, index: int):
#         if 0 <= index < len(self.filter_models):
#             self.filter_models.pop(index)
#             self.listWidget.takeItem(index)
#             self.filterRemovedCallback.emit(index)

#     def update_filter_name(self, index: int, new_name: str):
#         item = self.listWidget.item(index)
#         if item:
#             item.setText(new_name)

#     def select_filter(self, index: int):
#         self.listWidget.setCurrentRow(index)
    
#     def get_selected_index(self) -> int:
#         return self.listWidget.currentRow()

# class FilterTabWidget(QListWidget):
#     filterSelectedCallback = Signal(int)
#     filterAddRequestedCallback = Signal()
#     filterRenamedCallback = Signal(int, str)
    
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setDragDropMode(QAbstractItemView.NoDragDrop)
#         self.setEditTriggers(QAbstractItemView.DoubleClicked)
#         self.viewport().installEventFilter(self)
#         self.itemClicked.connect(self._on_item_clicked)
#         self.itemChanged.connect(self._on_item_changed)
#         self._init_tabs()
    
#     def _init_tabs(self):
#         self.clear()
#         self.addFilterTab()
    
#     def addFilterTab(self):
#         add_item = QListWidgetItem("Add Filter (+)")
#         add_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
#         self.addItem(add_item)
    
#     def add_filter_tab(self, filter_name: str):
#         new_item = QListWidgetItem(filter_name)
#         new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
#         self.insertItem(self.count() - 1, new_item)
    
#     def update_filter_tab(self, index: int, new_name: str):
#         item = self.item(index)
#         if item:
#             item.setText(new_name)
    
#     def _on_item_clicked(self, item: QListWidgetItem):
#         if item.text() == "Add Filter (+)":
#             self.filterAddRequestedCallback.emit()
#         else:
#             index = self.row(item)
#             self.filterSelectedCallback.emit(index)
    
#     def _on_item_changed(self, item: QListWidgetItem):
#         if item.text() == "Add Filter (+)":
#             return
#         index = self.row(item)
#         self.filterRenamedCallback.emit(index, item.text())

class FilterTabWidget(QListWidget):
    filterSelectedCallback = Signal(int)
    filterAddRequestedCallback = Signal()
    filterRenamedCallback = Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.NoDragDrop)
        self.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.viewport().installEventFilter(self)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)
        # Maintain an internal list of filter names (not including the add button)
        self.filters = []
        self._refresh_tabs()
    
    def _refresh_tabs(self):
        self.clear()
        # Add each filter tab from our internal list.
        for name in self.filters:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.addItem(item)
        # Always append the "Add Filter (+)" item as the last entry.
        add_item = QListWidgetItem("Add Filter (+)")
        add_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
        self.addItem(add_item)
    
    # def set_filters(self, filter_names: list):
    #     self.filters = filter_names.copy()
    #     self._refresh_tabs()
    
    # def add_filter_tab(self, filter_name: str):
    #     self.filters.append(filter_name)
    #     self._refresh_tabs()
    def set_filters(self, filter_names: list):
        self.filters = filter_names.copy()
        self._refresh_tabs()
        if self.filters:
            self.setCurrentRow(0)

    def add_filter_tab(self, filter_name: str):
        self.filters.append(filter_name)
        self._refresh_tabs()
        # Automatically select the newly added filter (last filter in the list)
        self.setCurrentRow(len(self.filters) - 1)

    
    def update_filter_tab(self, index: int, new_name: str):
        if 0 <= index < len(self.filters):
            self.filters[index] = new_name
            item = self.item(index)
            if item:
                item.setText(new_name)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        # If the "Add Filter (+)" item is clicked (always the last item), emit the add-request signal.
        if item.text() == "Add Filter (+)":
            self.filterAddRequestedCallback.emit()
        else:
            index = self.row(item)
            self.filterSelectedCallback.emit(index)
    
    def _on_item_changed(self, item: QListWidgetItem):
        # Do not allow changes to the "Add Filter (+)" item.
        if item.text() == "Add Filter (+)":
            return
        index = self.row(item)
        self.filters[index] = item.text()
        self.filterRenamedCallback.emit(index, item.text())



# class FilterEditorView(QWidget):
#     def __init__(self, filter_model: FilterModel, parent=None):
#         super().__init__(parent)
#         self.filter_model = filter_model
#         self.widgets = {}
#         self.form_layout = QFormLayout(self)
#         self.setLayout(self.form_layout)
#         self._build_ui()
#         self.update_from_model()
    
#     def _build_ui(self):
#         for f in fields(self.filter_model):
#             metadata = f.metadata
#             if "label" not in metadata or "widget" not in metadata:
#                 continue
#             widget_cls = metadata["widget"]
#             if widget_cls is None:
#                 continue
#             label_text = metadata["label"]
#             widget = widget_cls(self)
#             self.widgets[f.name] = widget
#             value = getattr(self.filter_model, f.name)
#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#                 widget.textChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#                 widget.valueChanged.connect(lambda val, fname=f.name: self._on_field_changed(fname, val))
#             elif isinstance(widget, QComboBox):
#                 if f.name == "filter_operation":
#                     widget.addItems(["<", ">", "==", "a < x < b"])
#                 # For filter_column, options will be set externally.
#                 widget.setCurrentText(str(value))
#                 widget.currentTextChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
#             self.form_layout.addRow(label_text, widget)
#         if "filter_operation" in self.widgets:
#             self.widgets["filter_operation"].currentTextChanged.connect(self.update_visibility)
    
#     def _on_field_changed(self, field_name, value):
#         setattr(self.filter_model, field_name, value)
#         if field_name == "filter_operation":
#             self.update_visibility()
    
#     def update_visibility(self):
#         op = self.widgets["filter_operation"].currentText()
#         # Show filter_value2 only if the operation is "a < x < b"
#         if "filter_value2" in self.widgets:
#             if op == "a < x < b":
#                 self.widgets["filter_value2"].show()
#                 label = self.form_layout.labelForField(self.widgets["filter_value2"])
#                 if label: label.show()
#             else:
#                 self.widgets["filter_value2"].hide()
#                 label = self.form_layout.labelForField(self.widgets["filter_value2"])
#                 if label: label.hide()
    
#     def update_from_model(self):
#         for f in fields(self.filter_model):
#             widget = self.widgets.get(f.name)
#             if not widget: continue
#             value = getattr(self.filter_model, f.name)
#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#             elif isinstance(widget, QComboBox):
#                 widget.setCurrentText(str(value))
#         self.update_visibility()
    
#     def set_filter_model(self, new_filter_model: FilterModel):
#         self.filter_model = new_filter_model
#         self.update_from_model()

class FilterEditorView(QWidget):
    def __init__(self, filter_model: FilterModel, parent=None):
        super().__init__(parent)
        self.filter_model = filter_model
        self.widgets = {}
        self.form_layout = QFormLayout(self)
        self.setLayout(self.form_layout)
        self._build_ui()
        self.update_from_model()
    
    def _build_ui(self):
        for f in fields(self.filter_model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                # When the filter name changes, update both the model and the corresponding tab.
                widget.textChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
                widget.valueChanged.connect(lambda val, fname=f.name: self._on_field_changed(fname, val))
            elif isinstance(widget, QComboBox):
                if f.name == "filter_operation":
                    widget.addItems(["<", ">", "==", "a < x < b"])
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(lambda text, fname=f.name: self._on_field_changed(fname, text))
            self.form_layout.addRow(label_text, widget)
        if "filter_operation" in self.widgets:
            self.widgets["filter_operation"].currentTextChanged.connect(self.update_visibility)
    
    def _on_field_changed(self, field_name, value):
        setattr(self.filter_model, field_name, value)
        if field_name == "filter_name":
            # Propagate this change to the FilterTabWidget.
            parent_widget = self.parent()
            while parent_widget is not None:
                ftw = parent_widget.findChild(FilterTabWidget)
                if ftw is not None:
                    idx = ftw.currentRow()
                    if idx >= 0:
                        ftw.update_filter_tab(idx, value)
                    break
                parent_widget = parent_widget.parent()
        if field_name == "filter_operation":
            self.update_visibility()
    
    def update_visibility(self):
        op = self.widgets["filter_operation"].currentText()
        if "filter_value2" in self.widgets:
            if op == "a < x < b":
                self.widgets["filter_value2"].show()
                label = self.form_layout.labelForField(self.widgets["filter_value2"])
                if label: label.show()
            else:
                self.widgets["filter_value2"].hide()
                label = self.form_layout.labelForField(self.widgets["filter_value2"])
                if label: label.hide()
    
    def update_from_model(self):
        for f in fields(self.filter_model):
            widget = self.widgets.get(f.name)
            if not widget:
                continue
            value = getattr(self.filter_model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
        self.update_visibility()
    
    def set_filter_model(self, new_filter_model: FilterModel):
        self.filter_model = new_filter_model
        self.update_from_model()




# --------------------------------------------------------------------
# Trace Editor Model & View (per earlier design)
# --------------------------------------------------------------------
@dataclass
class TraceEditorModel:
    trace_name: str = field(
        default="Default Trace",
        metadata={"label": "Trace Name:", "widget": QLineEdit, "plot_types": ["ternary", "cartesian"]}
    )
    datafile: str = field(
        default="",
        metadata={"label": "Datafile:", "widget": QLineEdit, "plot_types": ["ternary", "cartesian"]}
    )
    trace_color: str = field(
        default="blue",
        metadata={"label": "Trace Color:", "widget": QLineEdit, "plot_types": ["ternary", "cartesian"]}
    )
    point_size: float = field(
        default=5.0,
        metadata={"label": "Point Size:", "widget": QDoubleSpinBox, "plot_types": ["ternary", "cartesian"]}
    )
    point_opacity: float = field(
        default=1.0,
        metadata={"label": "Point Opacity:", "widget": QDoubleSpinBox, "plot_types": ["ternary", "cartesian"]}
    )
    line_on: bool = field(
        default=True,
        metadata={"label": "Line On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    line_style: str = field(
        default="solid",
        metadata={"label": "Line Style:", "widget": QComboBox, "plot_types": ["ternary", "cartesian"]}
    )
    line_thickness: float = field(
        default=1.0,
        metadata={"label": "Line Thickness:", "widget": QDoubleSpinBox, "plot_types": ["ternary", "cartesian"]}
    )
    heatmap_on: bool = field(
        default=False,
        metadata={"label": "Heatmap On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    # New heatmap configuration fields. They depend on heatmap_on.
    heatmap_column: str = field(
        default="",
        metadata={
            "label": "Heatmap Column:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_sort_mode: str = field(
        default="no change",
        metadata={
            "label": "Heatmap Sort Mode:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_min: float = field(
        default=0.0,
        metadata={
            "label": "Heatmap Min:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_max: float = field(
        default=1.0,
        metadata={
            "label": "Heatmap Max:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    heatmap_colorscale: str = field(
        default="Viridis",
        metadata={
            "label": "Heatmap Colorscale:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"],
            "depends_on": "heatmap_on",
            "group": "heatmap"
        }
    )
    sizemap_on: bool = field(
        default=False,
        metadata={"label": "Sizemap On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    filters_on: bool = field(
        default=False,
        metadata={"label": "Filters On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    filters: list = field(
        default_factory=list,
        metadata={"label": "Filters:", "widget": None, "plot_types": ["ternary", "cartesian"]}
    )

    def to_dict(self):
        # asdict will recursively convert nested dataclasses
        return asdict(self)

    # @classmethod
    # def from_dict(cls, d: dict):
    #     # This assumes that d keys match the dataclass constructor parameters.
    #     return cls(**d)
    
    @classmethod
    def from_dict(cls, d: dict):
        # Convert the filters list to FilterModel instances if needed.
        if "filters" in d and isinstance(d["filters"], list):
            d["filters"] = [
                FilterModel(**item) if isinstance(item, dict) else item 
                for item in d["filters"]
            ]
        return cls(**d)

# class TraceEditorView(QWidget):
#     # def __init__(self, model: TraceEditorModel, parent=None):
#     #     super().__init__(parent)
#     #     self.model = model
#     #     self.current_plot_type = "ternary"  # default
#     #     self.widgets = {}
#     #     self.form_layout = QFormLayout()
#     #     self.setLayout(self.form_layout)
#     #     self._build_ui()
#     #     self.set_plot_type(self.current_plot_type)
#     def __init__(self, model: TraceEditorModel, parent=None):
#         super().__init__(parent)
#         self.model = model
#         self.current_plot_type = "ternary"  # default
#         self.widgets = {}
#         self.group_boxes = {}
#         # Instead of setting a direct layout on self, embed content in a scroll area.
#         self.scroll = QScrollArea(self)
#         self.scroll.setWidgetResizable(True)
#         self.content = QWidget()
#         self.form_layout = QFormLayout(self.content)
#         self.content.setLayout(self.form_layout)
#         self.scroll.setWidget(self.content)
#         # Build the UI (including existing fields and grouped ones, e.g. heatmap).
#         self._build_ui()
#         self.set_plot_type(self.current_plot_type)
#         # Create a main layout that contains the scroll area.
#         layout = QVBoxLayout(self)
#         layout.addWidget(self.scroll)
#         self.setLayout(layout)
    
#     def _build_ui(self):
#         # Clear any previous widgets/groupings.
#         self.widgets = {}
#         self.group_boxes = {}  # Maps group name to (QGroupBox, QFormLayout)
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "label" not in metadata or "widget" not in metadata:
#                 continue
#             widget_cls = metadata["widget"]
#             if widget_cls is None:
#                 continue
#             label_text = metadata["label"]
#             widget = widget_cls(self)
#             self.widgets[f.name] = widget
#             value = getattr(self.model, f.name)
#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#                 if f.name == "trace_name":
#                     # For the trace name field, route changes through a helper method.
#                     widget.textChanged.connect(lambda text, fname=f.name: self._on_trace_name_changed(text))
#                 else:
#                     widget.textChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#                 widget.valueChanged.connect(
#                     lambda val, fname=f.name: setattr(self.model, fname, val)
#                 )
#             elif isinstance(widget, QCheckBox):
#                 widget.setChecked(bool(value))
#                 widget.stateChanged.connect(
#                     lambda state, fname=f.name: setattr(self.model, fname, bool(state))
#                 )
#                 # For heatmap_on, trigger a UI update when toggled.
#                 if f.name == "heatmap_on":
#                     widget.stateChanged.connect(lambda _: self.set_plot_type(self.current_plot_type))
#                 elif f.name == "filters_on":
#                     widget.stateChanged.connect(lambda _: self._update_filters_visibility())
#             elif isinstance(widget, QComboBox):
#                 # Provide specific options based on the field name.
#                 if f.name == "line_style":
#                     widget.addItems(["solid", "dashed", "dotted"])
#                 elif f.name == "heatmap_sort_mode":
#                     widget.addItems(["no change", "high on top", "low on top", "shuffled"])
#                 elif f.name == "heatmap_colorscale":
#                     widget.addItems(["Viridis", "Cividis", "Plasma", "Inferno"])
#                 else:
#                     widget.addItems([])  # Leave empty; can be updated dynamically.
#                 widget.setCurrentText(str(value))
#                 widget.currentTextChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
            
#             # self.form_layout.addRow(label_text, widget)

#             # Check if this field belongs to a group.
#             group_name = metadata.get("group", None)
#             if group_name:
#                 # Create the group box and layout if not already created.
#                 if group_name not in self.group_boxes:
#                     group_box = QGroupBox(group_name.capitalize(), self)
#                     group_layout = QFormLayout()
#                     group_box.setLayout(group_layout)
#                     self.group_boxes[group_name] = (group_box, group_layout)
#                 else:
#                     group_box, group_layout = self.group_boxes[group_name]
#                 group_layout.addRow(label_text, widget)
#             else:
#                 # Add directly to the main form layout.
#                 self.form_layout.addRow(label_text, widget)
        
#         # Finally, add all group boxes to the main form layout (in the order they were created).
#         for group_box, _ in self.group_boxes.values():
#             self.form_layout.addRow(group_box)

#         self._build_filters_ui()

#         # Set initial visibility.
#         self.set_plot_type(self.current_plot_type)
#         self._update_filters_visibility()
    
#     def set_plot_type(self, plot_type: str):
#         self.current_plot_type = plot_type
#         # Process ungrouped fields.
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "widget" not in metadata or metadata["widget"] is None:
#                 continue
#             if "group" in metadata:
#                 continue  # Grouped fields are handled below.
#             widget = self.widgets.get(f.name)
#             label = self.form_layout.labelForField(widget)
#             visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
#             if "depends_on" in metadata:
#                 dep_field = metadata["depends_on"]
#                 visible = visible and bool(getattr(self.model, dep_field))
#             if visible:
#                 widget.show()
#                 if label:
#                     label.show()
#             else:
#                 widget.hide()
#                 if label:
#                     label.hide()
        
#         # Process grouped fields.
#         for group_name, (group_box, group_layout) in self.group_boxes.items():
#             # Assume that all fields in a group share the same dependency; check the first field.
#             group_visible = False
#             # Iterate over fields belonging to this group.
#             for f in fields(self.model):
#                 metadata = f.metadata
#                 if metadata.get("group", None) != group_name:
#                     continue
#                 field_visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
#                 if "depends_on" in metadata:
#                     dep_field = metadata["depends_on"]
#                     field_visible = field_visible and bool(getattr(self.model, dep_field))
#                 if field_visible:
#                     group_visible = True
#                     break
#             if group_visible:
#                 group_box.show()
#             else:
#                 group_box.hide()

#         self._update_filters_visibility()


#     def _build_filters_ui(self):
#         from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout
#         # Create a group box for Filters if not already created.
#         if not hasattr(self, "filtersGroupBox"):
#             self.filtersGroupBox = QGroupBox("Filters", self)
#             filters_layout = QHBoxLayout(self.filtersGroupBox)
#             self.filtersGroupBox.setLayout(filters_layout)
#             # Left: FilterPanel (the filter tabs).
#             self.filterPanel = FilterPanel(self)
#             filters_layout.addWidget(self.filterPanel)
#             # Right: A container for the FilterEditorView.
#             self.filterEditorContainer = QWidget(self)
#             self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
#             self.filterEditorContainer.setLayout(self.filterEditorLayout)
#             filters_layout.addWidget(self.filterEditorContainer)
#             # If no filters exist, add one.
#             if not self.model.filters:
#                 new_filter = FilterModel()
#                 self.model.filters.append(new_filter)
#                 self.filterPanel.add_filter(new_filter)
#             self.currentFilterIndex = 0
#             self._show_current_filter()
#             # Connect filter panel signals.
#             self.filterPanel.filterSelectedCallback.connect(self.on_filter_selected)
#             self.filterPanel.filterAddRequestedCallback.connect(self.on_filter_add_requested)
#             self.filterPanel.filterRenamedCallback.connect(self.on_filter_renamed)

#     def _update_filters_visibility(self):
#         # Show the filters group box if filters_on is True.
#         if hasattr(self, "filtersGroupBox"):
#             if getattr(self.model, "filters_on", False):
#                 self.filtersGroupBox.show()
#             else:
#                 self.filtersGroupBox.hide()

#     # New helper methods to manage filters.
#     def _show_current_filter(self):
#         # Clear any existing FilterEditorView.
#         if hasattr(self, "filterEditorLayout"):
#             while self.filterEditorLayout.count():
#                 w = self.filterEditorLayout.takeAt(0).widget()
#                 if w:
#                     w.deleteLater()
#         # Create and add a new FilterEditorView for the selected filter.
#         current_filter = self.model.filters[self.currentFilterIndex]
#         self.currentFilterEditor = FilterEditorView(current_filter, self)
#         self.filterEditorLayout.addWidget(self.currentFilterEditor)

#     def on_filter_selected(self, index: int):
#         self.currentFilterIndex = index
#         self._show_current_filter()

#     def on_filter_add_requested(self):
#         new_filter = FilterModel()
#         self.model.filters.append(new_filter)
#         self.filterPanel.add_filter(new_filter)
#         self.currentFilterIndex = len(self.model.filters) - 1
#         self._show_current_filter()

#     def on_filter_renamed(self, index: int, new_name: str):
#         self.model.filters[index].filter_name = new_name

#     def _update_filters_visibility(self):
#         # Show or hide the Filters group box based on filters_on.
#         filters_on = bool(getattr(self.model, "filters_on", False))
#         if hasattr(self, "filtersGroupBox"):
#             if filters_on:
#                 self.filtersGroupBox.show()
#             else:
#                 self.filtersGroupBox.hide()


#     def update_from_model(self):
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "widget" not in metadata or metadata["widget"] is None:
#                 continue
#             widget = self.widgets.get(f.name)
#             value = getattr(self.model, f.name)
#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#             elif isinstance(widget, QCheckBox):
#                 widget.setChecked(bool(value))
#             elif isinstance(widget, QComboBox):
#                 widget.setCurrentText(str(value))

#     def _on_trace_name_changed(self, text: str):
#         self.model.trace_name = text
#         # If a callback has been set, notify it of the name change.
#         if hasattr(self, "traceNameChangedCallback") and self.traceNameChangedCallback:
#             self.traceNameChangedCallback(text)
    
#     def set_model(self, new_model: TraceEditorModel):
#         self.model = new_model
#         self.update_from_model()

# class TraceEditorView(QWidget):
#     def __init__(self, model: TraceEditorModel, parent=None):
#         super().__init__(parent)
#         self.model = model
#         self.current_plot_type = "ternary"  # default
#         self.widgets = {}  # Maps field names to widget instances.
#         self.group_boxes = {}  # Maps group names to (QGroupBox, QFormLayout).

#         # Wrap the entire editor in a scroll area.
#         self.scroll = QScrollArea(self)
#         self.scroll.setWidgetResizable(True)
#         self.content = QWidget()
#         self.form_layout = QFormLayout(self.content)
#         self.content.setLayout(self.form_layout)
#         self.scroll.setWidget(self.content)
#         main_layout = QVBoxLayout(self)
#         main_layout.addWidget(self.scroll)
#         self.setLayout(main_layout)

#         # Build the UI.
#         self._build_ui()
#         self.set_plot_type(self.current_plot_type)

#     def _build_ui(self):
#         # Clear existing state.
#         self.widgets = {}
#         self.group_boxes = {}

#         # Iterate over each field in the model.
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "label" not in metadata or "widget" not in metadata:
#                 continue
#             widget_cls = metadata["widget"]
#             if widget_cls is None:
#                 continue
#             label_text = metadata["label"]
#             widget = widget_cls(self)
#             self.widgets[f.name] = widget
#             value = getattr(self.model, f.name)

#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#                 if f.name == "trace_name":
#                     widget.textChanged.connect(lambda text, fname=f.name: self._on_trace_name_changed(text))
#                 else:
#                     widget.textChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#                 widget.valueChanged.connect(lambda val, fname=f.name: setattr(self.model, fname, val))
#             elif isinstance(widget, QCheckBox):
#                 widget.setChecked(bool(value))
#                 widget.stateChanged.connect(lambda state, fname=f.name: setattr(self.model, fname, bool(state)))
#                 if f.name == "heatmap_on":
#                     widget.stateChanged.connect(lambda _: self.set_plot_type(self.current_plot_type))
#                 if f.name == "filters_on":
#                     widget.stateChanged.connect(lambda _: self._update_filters_visibility())
#             elif isinstance(widget, QComboBox):
#                 if f.name == "line_style":
#                     widget.addItems(["solid", "dashed", "dotted"])
#                 elif f.name == "heatmap_sort_mode":
#                     widget.addItems(["no change", "high on top", "low on top", "shuffled"])
#                 elif f.name == "heatmap_colorscale":
#                     widget.addItems(["Viridis", "Cividis", "Plasma", "Inferno"])
#                 else:
#                     widget.addItems([])
#                 widget.setCurrentText(str(value))
#                 widget.currentTextChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))

#             # Place the widget in a group if specified.
#             group_name = metadata.get("group", None)
#             if group_name:
#                 if group_name not in self.group_boxes:
#                     from PySide6.QtWidgets import QGroupBox
#                     group_box = QGroupBox(group_name.capitalize(), self)
#                     group_layout = QFormLayout()
#                     group_box.setLayout(group_layout)
#                     self.group_boxes[group_name] = (group_box, group_layout)
#                 else:
#                     group_box, group_layout = self.group_boxes[group_name]
#                 group_layout.addRow(label_text, widget)
#             else:
#                 self.form_layout.addRow(label_text, widget)

#         # Add each group box to the main form layout.
#         for group_box, _ in self.group_boxes.values():
#             self.form_layout.addRow(group_box)

#         # Build the filters UI.
#         self._build_filters_ui()

#     def set_plot_type(self, plot_type: str):
#         self.current_plot_type = plot_type
#         # Process ungrouped fields.
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "widget" not in metadata or metadata["widget"] is None:
#                 continue
#             if "group" in metadata:
#                 continue  # Grouped fields are handled below.
#             widget = self.widgets.get(f.name)
#             label = self.form_layout.labelForField(widget)
#             visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
#             if "depends_on" in metadata:
#                 dep_field = metadata["depends_on"]
#                 visible = visible and bool(getattr(self.model, dep_field))
#             if visible:
#                 widget.show()
#                 if label:
#                     label.show()
#             else:
#                 widget.hide()
#                 if label:
#                     label.hide()

#         # Process grouped fields.
#         for group_name, (group_box, group_layout) in self.group_boxes.items():
#             group_visible = False
#             for f in fields(self.model):
#                 metadata = f.metadata
#                 if metadata.get("group", None) != group_name:
#                     continue
#                 field_visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
#                 if "depends_on" in metadata:
#                     dep_field = metadata["depends_on"]
#                     field_visible = field_visible and bool(getattr(self.model, dep_field))
#                 if field_visible:
#                     group_visible = True
#                     break
#             if group_visible:
#                 group_box.show()
#             else:
#                 group_box.hide()

#         self._update_filters_visibility()

#     def update_from_model(self):
#         for f in fields(self.model):
#             metadata = f.metadata
#             if "widget" not in metadata or metadata["widget"] is None:
#                 continue
#             widget = self.widgets.get(f.name)
#             value = getattr(self.model, f.name)
#             if isinstance(widget, QLineEdit):
#                 widget.setText(str(value))
#             elif isinstance(widget, QDoubleSpinBox):
#                 widget.setValue(float(value))
#             elif isinstance(widget, QCheckBox):
#                 widget.setChecked(bool(value))
#             elif isinstance(widget, QComboBox):
#                 widget.setCurrentText(str(value))

#     def _on_trace_name_changed(self, text: str):
#         self.model.trace_name = text
#         if hasattr(self, "traceNameChangedCallback") and self.traceNameChangedCallback:
#             self.traceNameChangedCallback(text)

#     def set_model(self, new_model: TraceEditorModel):
#         self.model = new_model
#         self.update_from_model()
#         self.set_plot_type(self.current_plot_type)
#         self._build_filters_ui()

#     # --- Filters UI Methods ---
#     def _build_filters_ui(self):
#         from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout
#         # Remove existing filters group box if it exists.
#         if hasattr(self, "filtersGroupBox"):
#             self.form_layout.removeWidget(self.filtersGroupBox)
#             self.filtersGroupBox.deleteLater()
#         # Create a new group box for Filters.
#         self.filtersGroupBox = QGroupBox("Filters", self)
#         filters_layout = QHBoxLayout(self.filtersGroupBox)
#         self.filtersGroupBox.setLayout(filters_layout)
#         # Left: FilterPanel.
#         self.filterPanel = FilterPanel(self)
#         filters_layout.addWidget(self.filterPanel)
#         # Right: Container for the FilterEditorView.
#         self.filterEditorContainer = QWidget(self)
#         self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
#         self.filterEditorContainer.setLayout(self.filterEditorLayout)
#         filters_layout.addWidget(self.filterEditorContainer)
#         # If no filters exist, add one.
#         if not self.model.filters:
#             new_filter = FilterModel()
#             self.model.filters.append(new_filter)
#             self.filterPanel.add_filter(new_filter)
#         self.currentFilterIndex = 0
#         self._show_current_filter()
#         # Connect filter panel signals.
#         self.filterPanel.filterSelectedCallback.connect(self.on_filter_selected)
#         self.filterPanel.filterAddRequestedCallback.connect(self.on_filter_add_requested)
#         self.filterPanel.filterRenamedCallback.connect(self.on_filter_renamed)
#         # Add the filters group box to the main form layout.
#         self.form_layout.addRow(self.filtersGroupBox)

#     def _show_current_filter(self):
#         # Clear previous editor.
#         if hasattr(self, "filterEditorLayout"):
#             while self.filterEditorLayout.count():
#                 w = self.filterEditorLayout.takeAt(0).widget()
#                 if w is not None:
#                     w.deleteLater()
#         current_filter = self.model.filters[self.currentFilterIndex]
#         self.currentFilterEditor = FilterEditorView(current_filter, self)
#         self.filterEditorLayout.addWidget(self.currentFilterEditor)

#     def on_filter_selected(self, index: int):
#         self.currentFilterIndex = index
#         self._show_current_filter()

#     def on_filter_add_requested(self):
#         new_filter = FilterModel()
#         self.model.filters.append(new_filter)
#         self.filterPanel.add_filter(new_filter)
#         self.currentFilterIndex = len(self.model.filters) - 1
#         self._show_current_filter()

#     def on_filter_renamed(self, index: int, new_name: str):
#         self.model.filters[index].filter_name = new_name

#     def _update_filters_visibility(self):
#         # Toggle the visibility of the Filters group box based on filters_on.
#         if hasattr(self, "filtersGroupBox"):
#             if getattr(self.model, "filters_on", False):
#                 self.filtersGroupBox.show()
#             else:
#                 self.filtersGroupBox.hide()

class TraceEditorView(QWidget):
    def __init__(self, model: TraceEditorModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # default
        self.widgets = {}      # Maps field names to widget instances.
        self.group_boxes = {}  # Maps group names to (QGroupBox, QFormLayout).

        # Wrap the entire editor in a scroll area.
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.form_layout = QFormLayout(self.content)
        self.content.setLayout(self.form_layout)
        self.scroll.setWidget(self.content)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll)
        self.setLayout(main_layout)

        self._build_ui()
        self.set_plot_type(self.current_plot_type)

    def _build_ui(self):
        # Clear existing state.
        self.widgets = {}
        self.group_boxes = {}
        # Process each field in the model.
        for f in fields(self.model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata:
                continue
            widget_cls = metadata["widget"]
            if widget_cls is None:
                continue
            label_text = metadata["label"]
            widget = widget_cls(self)
            self.widgets[f.name] = widget
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
                if f.name == "trace_name":
                    widget.textChanged.connect(lambda text, fname=f.name: self._on_trace_name_changed(text))
                else:
                    widget.textChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
                widget.valueChanged.connect(lambda val, fname=f.name: setattr(self.model, fname, val))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
                widget.stateChanged.connect(lambda state, fname=f.name: setattr(self.model, fname, bool(state)))
                if f.name == "heatmap_on":
                    widget.stateChanged.connect(lambda _: self.set_plot_type(self.current_plot_type))
                if f.name == "filters_on":
                    widget.stateChanged.connect(lambda _: self._update_filters_visibility())
            elif isinstance(widget, QComboBox):
                if f.name == "line_style":
                    widget.addItems(["solid", "dashed", "dotted"])
                elif f.name == "heatmap_sort_mode":
                    widget.addItems(["no change", "high on top", "low on top", "shuffled"])
                elif f.name == "heatmap_colorscale":
                    widget.addItems(["Viridis", "Cividis", "Plasma", "Inferno"])
                else:
                    widget.addItems([])
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(lambda text, fname=f.name: setattr(self.model, fname, text))
            # Place widget in group if specified.
            group_name = metadata.get("group", None)
            if group_name:
                if group_name not in self.group_boxes:
                    from PySide6.QtWidgets import QGroupBox
                    group_box = QGroupBox(group_name.capitalize(), self)
                    group_layout = QFormLayout()
                    group_box.setLayout(group_layout)
                    self.group_boxes[group_name] = (group_box, group_layout)
                else:
                    group_box, group_layout = self.group_boxes[group_name]
                group_layout.addRow(label_text, widget)
            else:
                self.form_layout.addRow(label_text, widget)
        # Add each group box to the main layout.
        for group_box, _ in self.group_boxes.values():
            self.form_layout.addRow(group_box)

        # Build the Filters UI.
        self._build_filters_ui()

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type
        # Process ungrouped fields.
        for f in fields(self.model):
            metadata = f.metadata
            if "widget" not in metadata or metadata["widget"] is None:
                continue
            if "group" in metadata:
                continue  # Skip grouped; handled below.
            widget = self.widgets.get(f.name)
            label = self.form_layout.labelForField(widget)
            visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
            if "depends_on" in metadata:
                dep_field = metadata["depends_on"]
                visible = visible and bool(getattr(self.model, dep_field))
            if visible:
                widget.show()
                if label:
                    label.show()
            else:
                widget.hide()
                if label:
                    label.hide()
        # Process grouped fields.
        for group_name, (group_box, group_layout) in self.group_boxes.items():
            group_visible = False
            for f in fields(self.model):
                metadata = f.metadata
                if metadata.get("group", None) != group_name:
                    continue
                field_visible = ("plot_types" not in metadata) or (self.current_plot_type in metadata["plot_types"])
                if "depends_on" in metadata:
                    dep_field = metadata["depends_on"]
                    field_visible = field_visible and bool(getattr(self.model, dep_field))
                if field_visible:
                    group_visible = True
                    break
            if group_visible:
                group_box.show()
            else:
                group_box.hide()
        self._update_filters_visibility()

    def update_from_model(self):
        for f in fields(self.model):
            metadata = f.metadata
            if "widget" not in metadata or metadata["widget"] is None:
                continue
            widget = self.widgets.get(f.name)
            value = getattr(self.model, f.name)
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))

    def _on_trace_name_changed(self, text: str):
        self.model.trace_name = text
        if hasattr(self, "traceNameChangedCallback") and self.traceNameChangedCallback:
            self.traceNameChangedCallback(text)

    def set_model(self, new_model: TraceEditorModel):
        self.model = new_model
        self.update_from_model()
        self.set_plot_type(self.current_plot_type)
        self._build_filters_ui()

    # # --- Filters UI methods ---
    # def _build_filters_ui(self):
    #     from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout
    #     # Remove existing Filters group if present.
    #     if hasattr(self, "filtersGroupBox"):
    #         self.form_layout.removeWidget(self.filtersGroupBox)
    #         self.filtersGroupBox.deleteLater()
    #     # Create a new Filters group box.
    #     self.filtersGroupBox = QGroupBox("Filters", self)
    #     filters_layout = QHBoxLayout(self.filtersGroupBox)
    #     self.filtersGroupBox.setLayout(filters_layout)
    #     # Left: Use a custom FilterTabWidget.
    #     self.filterTabWidget = FilterTabWidget(self)
    #     filters_layout.addWidget(self.filterTabWidget)
    #     # Right: Container for the FilterEditorView.
    #     self.filterEditorContainer = QWidget(self)
    #     self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
    #     self.filterEditorContainer.setLayout(self.filterEditorLayout)
    #     filters_layout.addWidget(self.filterEditorContainer)
    #     # Populate filter tabs from self.model.filters.
    #     self.filterTabWidget._init_tabs()
    #     for filt in self.model.filters:
    #         self.filterTabWidget.add_filter_tab(filt.filter_name)
    #     # Select the first filter if available.
    #     if self.model.filters and self.model.filters[0]:
    #         self.currentFilterIndex = 0
    #         self._show_current_filter()
    #     # Connect filter tab signals.
    #     self.filterTabWidget.filterSelectedCallback.connect(self.on_filter_selected)
    #     self.filterTabWidget.filterAddRequestedCallback.connect(self.on_filter_add_requested)
    #     self.filterTabWidget.filterRenamedCallback.connect(self.on_filter_renamed)
    #     # Add the Filters group box to the main form layout.
    #     self.form_layout.addRow(self.filtersGroupBox)
    #     self._update_filters_visibility()

    # def _show_current_filter(self):
    #     if hasattr(self, "filterEditorLayout"):
    #         while self.filterEditorLayout.count():
    #             w = self.filterEditorLayout.takeAt(0).widget()
    #             if w is not None:
    #                 w.deleteLater()
    #     current_filter = self.model.filters[self.currentFilterIndex]
    #     self.currentFilterEditor = FilterEditorView(current_filter, self)
    #     self.filterEditorLayout.addWidget(self.currentFilterEditor)

    # def on_filter_selected(self, index: int):
    #     self.currentFilterIndex = index
    #     self._show_current_filter()

    # def on_filter_add_requested(self):
    #     new_filter = FilterModel()
    #     self.model.filters.append(new_filter)
    #     self.filterTabWidget.add_filter_tab(new_filter.filter_name)
    #     self.currentFilterIndex = len(self.model.filters) - 1
    #     self._show_current_filter()

    # # def on_filter_renamed(self, index: int, new_name: str):
    # #     self.model.filters[index].filter_name = new_name
    # def on_filter_renamed(self, index: int, new_name: str):
    #     self.model.filters[index].filter_name = new_name
    #     if hasattr(self, "currentFilterEditor") and self.currentFilterIndex == index:
    #         self.currentFilterEditor.update_from_model()


    # def _update_filters_visibility(self):
    #     # Ensure the Filters UI is visible only if filters_on is True.
    #     if hasattr(self, "filtersGroupBox"):
    #         if getattr(self.model, "filters_on", False):
    #             self.filtersGroupBox.show()
    #         else:
    #             self.filtersGroupBox.hide()

    # --- Filters UI Methods in TraceEditorView ---
    def _build_filters_ui(self):
        from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QVBoxLayout
        # Remove existing Filters group box if present.
        if hasattr(self, "filtersGroupBox"):
            self.form_layout.removeWidget(self.filtersGroupBox)
            self.filtersGroupBox.deleteLater()
        # Create a new Filters group box.
        self.filtersGroupBox = QGroupBox("Filters", self)
        filters_layout = QHBoxLayout(self.filtersGroupBox)
        self.filtersGroupBox.setLayout(filters_layout)
        # Left: Instantiate our new FilterTabWidget.
        self.filterTabWidget = FilterTabWidget(self)
        filters_layout.addWidget(self.filterTabWidget)
        # Right: Container for the FilterEditorView.
        self.filterEditorContainer = QWidget(self)
        self.filterEditorLayout = QVBoxLayout(self.filterEditorContainer)
        self.filterEditorContainer.setLayout(self.filterEditorLayout)
        filters_layout.addWidget(self.filterEditorContainer)
        # Update the FilterTabWidget with current filter names.
        # filter_names = [f.filter_name for f in self.model.filters] if self.model.filters else []
        # self.filterTabWidget.set_filters(filter_names)
        # # If filters exist, select the first one; otherwise, set currentFilterIndex to None.
        # if self.model.filters:
        #     self.currentFilterIndex = 0
        #     self._show_current_filter()
        # else:
        #     self.currentFilterIndex = None
        # Populate filter tabs from self.model.filters.
        filter_names = [f.filter_name for f in self.model.filters] if self.model.filters else []
        self.filterTabWidget.set_filters(filter_names)
        # If filters exist, select the first one; otherwise, clear the selection.
        if self.model.filters:
            self.currentFilterIndex = 0
            self.filterTabWidget.setCurrentRow(0)
            self._show_current_filter()
        else:
            self.currentFilterIndex = None
        # Connect signals.
        self.filterTabWidget.filterSelectedCallback.connect(self.on_filter_selected)
        self.filterTabWidget.filterAddRequestedCallback.connect(self.on_filter_add_requested)
        self.filterTabWidget.filterRenamedCallback.connect(self.on_filter_renamed)
        # Add the Filters group box to the main form layout.
        self.form_layout.addRow(self.filtersGroupBox)
        self._update_filters_visibility()

    def _show_current_filter(self):
        if self.currentFilterIndex is None or self.currentFilterIndex >= len(self.model.filters):
            return
        # Clear previous editor.
        if hasattr(self, "filterEditorLayout"):
            while self.filterEditorLayout.count():
                w = self.filterEditorLayout.takeAt(0).widget()
                if w is not None:
                    w.deleteLater()
        current_filter = self.model.filters[self.currentFilterIndex]
        self.currentFilterEditor = FilterEditorView(current_filter, self)
        self.filterEditorLayout.addWidget(self.currentFilterEditor)

    def on_filter_selected(self, index: int):
        if index < 0 or index >= len(self.model.filters):
            return
        self.currentFilterIndex = index
        self._show_current_filter()

    # def on_filter_add_requested(self):
    #     new_filter = FilterModel()
    #     self.model.filters.append(new_filter)
    #     self.filterTabWidget.add_filter_tab(new_filter.filter_name)
    #     self.currentFilterIndex = len(self.model.filters) - 1
    #     self._show_current_filter()

    def on_filter_add_requested(self):
        new_filter = FilterModel()
        self.model.filters.append(new_filter)
        self.filterTabWidget.add_filter_tab(new_filter.filter_name)
        self.currentFilterIndex = len(self.model.filters) - 1
        self._show_current_filter()


    def on_filter_renamed(self, index: int, new_name: str):
        if index < 0 or index >= len(self.model.filters):
            return
        self.model.filters[index].filter_name = new_name
        if self.currentFilterIndex == index and hasattr(self, "currentFilterEditor"):
            self.currentFilterEditor.update_from_model()

    def _update_filters_visibility(self):
        # Toggle the Filters group box based on the "filters_on" checkbox.
        if hasattr(self, "filtersGroupBox"):
            if getattr(self.model, "filters_on", False):
                self.filtersGroupBox.show()
            else:
                self.filtersGroupBox.hide()


# --------------------------------------------------------------------
# Setup Menu Models
# --------------------------------------------------------------------
@dataclass
class DataLibraryModel:
    loaded_files: list = field(default_factory=list)

@dataclass
class PlotLabelsModel:
    title: str = field(
        default="My Plot",
        metadata={"label": "Title:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    x_axis_label: str = field(
        default="X Axis",
        metadata={"label": "X Axis Label:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram"]}
    )
    y_axis_label: str = field(
        default="Y Axis",
        metadata={"label": "Y Axis Label:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram"]}
    )
    left_vertex_label: str = field(
        default="Left Vertex",
        metadata={"label": "Left Vertex Label:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )
    right_vertex_label: str = field(
        default="Right Vertex",
        metadata={"label": "Right Vertex Label:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )
    top_vertex_label: str = field(
        default="Top Vertex",
        metadata={"label": "Top Vertex Label:", "widget": QLineEdit, "plot_types": ["ternary"]}
    )

@dataclass
class AxisMembersModel:
    # Now each axis is a list (to allow multiple selections) and uses MultiFieldSelector.
    x_axis: list = field(default_factory=list, metadata={"label": "X Axis:", "widget": MultiFieldSelector, "plot_types": ["cartesian"]})
    y_axis: list = field(default_factory=list, metadata={"label": "Y Axis:", "widget": MultiFieldSelector, "plot_types": ["cartesian"]})
    left_axis: list = field(default_factory=list, metadata={"label": "Left Axis:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})
    right_axis: list = field(default_factory=list, metadata={"label": "Right Axis:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})
    top_axis: list = field(default_factory=list, metadata={"label": "Top Axis:", "widget": MultiFieldSelector, "plot_types": ["ternary"]})

@dataclass
class AdvancedPlotSettingsModel:
    background_color: str = field(
        default="#FFFFFF",
        metadata={"label": "Background Color:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    paper_color: str = field(
        default="#FFFFFF",
        metadata={"label": "Paper Color:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    line_width: float = field(
        default=1.0,
        metadata={"label": "Line Width:", "widget": QDoubleSpinBox, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    legend_position: str = field(
        default="top-right",
        metadata={"label": "Legend Position:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font_size: int = field(
        default=12,
        metadata={"label": "Font Size:", "widget": QDoubleSpinBox, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font: str = field(
        default="Arial",
        metadata={"label": "Font:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )
    font_color: str = field(
        default="#000000",
        metadata={"label": "Font Color:", "widget": QLineEdit, "plot_types": ["cartesian", "histogram", "ternary"]}
    )

@dataclass
class SetupMenuModel:
    data_library: DataLibraryModel = field(default_factory=DataLibraryModel)
    plot_labels: PlotLabelsModel = field(default_factory=PlotLabelsModel)
    axis_members: AxisMembersModel = field(default_factory=AxisMembersModel)
    advanced_settings: AdvancedPlotSettingsModel = field(default_factory=AdvancedPlotSettingsModel)

    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            data_library=DataLibraryModel(**d.get("data_library", {})),
            plot_labels=PlotLabelsModel(**d.get("plot_labels", {})),
            axis_members=AxisMembersModel(**d.get("axis_members", {})),
            advanced_settings=AdvancedPlotSettingsModel(**d.get("advanced_settings", {}))
        )

# --------------------------------------------------------------------
# Setup Menu Controller
# --------------------------------------------------------------------
def get_columns_from_file(file_path):
    if pd is None:
        return set()
    try:
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path, nrows=0)
        elif file_path.lower().endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path, nrows=0)
        else:
            return set()
        return set(df.columns)
    except Exception:
        return set()

class SetupMenuController:
    """
    Controller for the Setup Menu. Recomputes the intersection of column names
    from loaded data files and updates the available options for axis member selectors.
    """
    def __init__(self, model: SetupMenuModel, view: 'SetupMenuView'):
        self.model = model
        self.view = view

    def update_axis_options(self):
        common_columns = None
        for file_path in self.model.data_library.loaded_files:
            cols = get_columns_from_file(file_path)
            if common_columns is None:
                common_columns = cols
            else:
                common_columns = common_columns.intersection(cols)
        if common_columns is None:
            common_columns = set()
        common_list = sorted(common_columns)
        # Use the key "axis_members" (as set in build_form_section) to update options.
        axis_widgets = self.view.section_widgets.get("axis_members", {})
        for field_name, widget in axis_widgets.items():
            if isinstance(widget, MultiFieldSelector):
                widget.set_available_options(common_list)
                selected = widget.get_selected_fields()
                valid = [s for s in selected if s in common_list]
                widget.set_selected_fields(valid)

# --------------------------------------------------------------------
# Setup Menu View
# --------------------------------------------------------------------
class SetupMenuView(QWidget):
    def __init__(self, model: SetupMenuModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # Default plot type; will be updated by the controller.
        self.controller = None  # Will be set later by the main window.
        self.section_widgets = {}  # To hold per‑section widget mappings keyed by model attribute name.
        
        # Wrap all contents in a scroll area for vertical scrolling.
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.scroll.setWidget(self.content)
        self.content_layout = QVBoxLayout(self.content)
        self.content.setLayout(self.content_layout)
        
        # Data Library Section
        self.dataLibraryWidget = QWidget(self)
        data_library_layout = QVBoxLayout(self.dataLibraryWidget)
        self.dataLibraryWidget.setLayout(data_library_layout)
        data_library_label = QLabel("Loaded Data:")
        data_library_layout.addWidget(data_library_label)
        self.dataLibraryList = QListWidget(self)
        data_library_layout.addWidget(self.dataLibraryList)
        btn_layout = QHBoxLayout()
        self.addDataButton = QPushButton("Add Data", self)
        self.removeDataButton = QPushButton("Remove Data", self)
        btn_layout.addWidget(self.addDataButton)
        btn_layout.addWidget(self.removeDataButton)
        data_library_layout.addLayout(btn_layout)
        self.addDataButton.clicked.connect(self.add_data_file)
        self.removeDataButton.clicked.connect(self.remove_data_file)
        self.content_layout.addWidget(self.dataLibraryWidget)
        
        # Plot Labels Section
        self.plotLabelsWidget = self.build_form_section(self.model.plot_labels, "plot_labels")
        self.content_layout.addWidget(self.plotLabelsWidget)
        
        # Axis Members Section
        self.axisMembersWidget = self.build_form_section(self.model.axis_members, "axis_members")
        self.content_layout.addWidget(self.axisMembersWidget)
        
        # Advanced Settings Section
        self.advancedSettingsWidget = self.build_form_section(self.model.advanced_settings, "advanced_settings")
        self.content_layout.addWidget(self.advancedSettingsWidget)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.addWidget(self.scroll)
        self.setLayout(outer_layout)

        # Initialize to default plot type
        self.set_plot_type(self.current_plot_type)

    def set_controller(self, controller: SetupMenuController):
        self.controller = controller

    def build_form_section(self, section_model, model_attr_name):
        widget = QWidget(self)
        form_layout = QFormLayout(widget)
        widget.setLayout(form_layout)
        # Store the form layout so we can later access labels.
        if not hasattr(self, "section_form_layouts"):
            self.section_form_layouts = {}
        self.section_form_layouts[model_attr_name] = form_layout
        self.section_widgets[model_attr_name] = {}
        for f in fields(section_model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata or metadata["widget"] is None:
                continue
            widget_cls = metadata["widget"]
            label_text = metadata["label"]
            field_widget = widget_cls(self)
            value = getattr(section_model, f.name)
            if isinstance(field_widget, QLineEdit):
                field_widget.setText(str(value))
                field_widget.textChanged.connect(lambda text, fname=f.name, m=section_model: setattr(m, fname, text))
            elif isinstance(field_widget, QDoubleSpinBox):
                field_widget.setValue(float(value))
                field_widget.valueChanged.connect(lambda val, fname=f.name, m=section_model: setattr(m, fname, val))
            elif isinstance(field_widget, QCheckBox):
                field_widget.setChecked(bool(value))
                field_widget.stateChanged.connect(lambda state, fname=f.name, m=section_model: setattr(m, fname, bool(state)))
            elif isinstance(field_widget, QComboBox):
                field_widget.addItems([])
                field_widget.setCurrentText(str(value))
                field_widget.currentTextChanged.connect(lambda text, fname=f.name, m=section_model: setattr(m, fname, text))
            elif isinstance(field_widget, MultiFieldSelector):
                field_widget.set_selected_fields(value)
                # Connect selectionChanged to update the model
                field_widget.selectionChanged.connect(lambda sel, fname=f.name, m=section_model: setattr(m, fname, sel))
            form_layout.addRow(label_text, field_widget)
            self.section_widgets[model_attr_name][f.name] = field_widget
        return widget

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            form_layout = self.section_form_layouts.get(section)
            for fname, field_widget in widgets.items():
                # Retrieve metadata for this field.
                metadata = None
                for f in fields(section_model):
                    if f.name == fname:
                        metadata = f.metadata
                        break
                if metadata is None:
                    continue
                show_field = "plot_types" in metadata and self.current_plot_type in metadata["plot_types"]
                if show_field:
                    field_widget.show()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.show()
                else:
                    field_widget.hide()
                    if form_layout:
                        label = form_layout.labelForField(field_widget)
                        if label:
                            label.hide()

    def add_data_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Data File", "", "Data Files (*.csv *.xlsx)")
        if file_path:
            self.model.data_library.loaded_files.append(file_path)
            self.dataLibraryList.addItem(file_path)
            if self.controller:
                self.controller.update_axis_options()

    def remove_data_file(self):
        current_item = self.dataLibraryList.currentItem()
        if current_item:
            file_path = current_item.text()
            row = self.dataLibraryList.row(current_item)
            self.dataLibraryList.takeItem(row)
            if file_path in self.model.data_library.loaded_files:
                self.model.data_library.loaded_files.remove(file_path)
            if self.controller:
                self.controller.update_axis_options()

    def update_from_model(self):
        # Update custom Data Library list.
        self.dataLibraryList.clear()
        for path in self.model.data_library.loaded_files:
            self.dataLibraryList.addItem(path)
        # Update each section built by build_form_section.
        for section, widgets in self.section_widgets.items():
            section_model = getattr(self.model, section, None)
            if section_model is None:
                continue
            for fname, field_widget in widgets.items():
                for f in fields(section_model):
                    if f.name == fname:
                        value = getattr(section_model, fname)
                        if isinstance(field_widget, QLineEdit):
                            field_widget.setText(str(value))
                        elif isinstance(field_widget, QDoubleSpinBox):
                            field_widget.setValue(float(value))
                        elif isinstance(field_widget, QCheckBox):
                            field_widget.setChecked(bool(value))
                        elif isinstance(field_widget, QComboBox):
                            field_widget.setCurrentText(str(value))
                        elif isinstance(field_widget, MultiFieldSelector):
                            field_widget.set_selected_fields(value)
                        break


class WorkspaceManager:
    VERSION = "1.0"
    
    def __init__(self, traces: list, setup_model: SetupMenuModel, order=None):
        self.traces = traces
        self.setup_model = setup_model
        self.order = order if order is not None else [str(i) for i in range(len(traces))]
    
    def to_dict(self) -> dict:
        return {
            "version": self.VERSION,
            "order": self.order,
            "traces": [trace.to_dict() for trace in self.traces],
            "setup": self.setup_model.to_dict()
        }
    
    def save_to_file(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, d: dict):
        traces = [TraceEditorModel.from_dict(item) for item in d.get("traces", [])]
        setup = SetupMenuModel.from_dict(d.get("setup", {}))
        order = d.get("order", None)
        return cls(traces, setup, order=order)
    
    @classmethod
    def load_from_file(cls, filename: str):
        with open(filename, "r") as f:
            d = json.load(f)
        return cls.from_dict(d)
    
# --------------------------------------------------------------------
# MainWindow: Integrates TabPanel, CenterStack (for TraceEditor and SetupMenu), and Plot Window
# --------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quick Ternaries - Full Demo")
        self.resize(1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vlayout = QVBoxLayout(central_widget)
        main_vlayout.setContentsMargins(0, 0, 0, 0)

        top_banner = self._create_top_banner()
        main_vlayout.addWidget(top_banner)

        self.h_splitter = CustomSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(8)
        self.h_splitter.setStyleSheet("""
        QSplitter::handle {
            width: 5px;
            margin-left: 3px;
            margin-right: 3px;
        }
        """)
        main_vlayout.addWidget(self.h_splitter, 1)

        bottom_banner = self._create_bottom_banner()
        main_vlayout.addWidget(bottom_banner)

        # Left: TabPanel
        self.tabPanel = TabPanel()
        self.h_splitter.addWidget(self.tabPanel)

        # Center: QStackedWidget to hold both TraceEditorView and SetupMenuView.
        self.centerStack = QStackedWidget()
        # Instantiate the trace editor view with an initial dummy model.
        self.current_trace_model = TraceEditorModel()
        self.traceEditorView = TraceEditorView(self.current_trace_model)
        self.traceEditorView.traceNameChangedCallback = self.on_trace_name_changed
        self.centerStack.addWidget(self.traceEditorView)
        # Instantiate the setup menu view.
        self.setupMenuModel = SetupMenuModel()
        self.setupMenuView = SetupMenuView(self.setupMenuModel)
        self.centerStack.addWidget(self.setupMenuView)
        self.h_splitter.addWidget(self.centerStack)

        # Right: Plot Window (placeholder)
        self.plotView = QWebEngineView()
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")
        self.h_splitter.addWidget(self.plotView)

        # Connect TabPanel callbacks
        self.tabPanel.tabSelectedCallback = self.on_tab_selected
        self.tabPanel.tabRenamedCallback = self.on_tab_renamed
        self.tabPanel.tabRemovedCallback = self.on_tab_removed
        self.tabPanel.tabAddRequestedCallback = self.create_new_tab

        # Setup Menu special case
        self.setup_id = "setup-menu-id"
        self.tabPanel.id_to_widget[self.setup_id] = None
        
        self.current_tab_id = None
        self._create_initial_traces()

        # Start with Setup Menu selected.
        self.tabPanel.listWidget.setCurrentRow(0)
        self.current_tab_id = "setup-menu-id"
        self._show_setup_content()

        self.plotTypeSelector.currentTextChanged.connect(self.on_plot_type_changed)

        # Create and set up the Setup Menu Controller.
        self.setupController = SetupMenuController(self.setupMenuModel, self.setupMenuView)
        self.setupMenuView.set_controller(self.setupController)

    def _create_top_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        logo_label = QLabel("Quick Ternaries")
        logo_label.setStyleSheet("font-weight: bold; font-size: 16pt;")
        layout.addWidget(logo_label)
        layout.addStretch()
        self.plotTypeSelector = QComboBox()
        self.plotTypeSelector.addItems(["Ternary", "Cartesian", "Histogram"])
        layout.addWidget(self.plotTypeSelector)
        self.settingsButton = QPushButton("Settings")
        layout.addWidget(self.settingsButton)
        return container

    # def _create_bottom_banner(self):
    #     container = QWidget()
    #     layout = QHBoxLayout(container)
    #     layout.setContentsMargins(8, 2, 8, 2)
    #     self.previewButton = QPushButton("Preview")
    #     self.saveButton = QPushButton("Save")
    #     self.exportButton = QPushButton("Export")
    #     self.bootstrapButton = QPushButton("Bootstrap")
    #     layout.addWidget(self.previewButton)
    #     layout.addWidget(self.saveButton)
    #     layout.addWidget(self.exportButton)
    #     layout.addWidget(self.bootstrapButton)
    #     layout.addStretch()
    #     return container

    def _create_bottom_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        self.previewButton = QPushButton("Preview")
        self.saveButton = QPushButton("Save")
        self.loadButton = QPushButton("Load")  # New Load button added
        self.exportButton = QPushButton("Export")
        self.bootstrapButton = QPushButton("Bootstrap")
        layout.addWidget(self.previewButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.loadButton)
        layout.addWidget(self.exportButton)
        layout.addWidget(self.bootstrapButton)
        layout.addStretch()
        # Connect button signals
        self.saveButton.clicked.connect(self.save_workspace)
        self.loadButton.clicked.connect(self.load_workspace)
        return container


    def _create_initial_traces(self):
        for i in range(1, 4):
            new_label = f"Trace {i}"
            model = TraceEditorModel(
                trace_name=new_label,
                trace_color=["blue", "red", "green"][(i - 1) % 3],
                datafile=f"data{i}.csv",
                point_size=5.0 + i,
                point_opacity=1.0,
                line_on=True,
                line_style="solid",
                line_thickness=1.0
            )
            uid = self.tabPanel.add_tab(new_label, model)

    def on_tab_selected(self, unique_id: str):
        self._save_current_tab_data()
        self.current_tab_id = unique_id
        if unique_id == "setup-menu-id":
            self._show_setup_content()
        else:
            model = self.tabPanel.id_to_widget.get(unique_id)
            if isinstance(model, TraceEditorModel):
                self.traceEditorView.set_model(model)
                self._show_trace_editor()
            else:
                self.traceEditorView.set_model(TraceEditorModel())
                self._show_trace_editor()

    def on_tab_renamed(self, unique_id: str, new_label: str):
        if unique_id == "setup-menu-id":
            return
        model = self.tabPanel.id_to_widget.get(unique_id)
        if isinstance(model, TraceEditorModel):
            model.trace_name = new_label
        # Update the display text of the corresponding QListWidgetItem.
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if it and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                it.setText(new_label)
                break

    def on_tab_removed(self, unique_id: str):
        if unique_id == "setup-menu-id":
            return
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
        if unique_id == self.current_tab_id:
            self._save_current_tab_data()
            self.current_tab_id = "setup-menu-id"
            self.tabPanel.listWidget.setCurrentRow(0)
            self._show_setup_content()
        self.tabPanel.remove_tab_by_id(unique_id)

    def create_new_tab(self):
        new_trace_number = self._find_next_trace_number()
        new_label = f"Trace {new_trace_number}"
        model = TraceEditorModel(trace_name=new_label)
        uid = self.tabPanel.add_tab(new_label, model)
        self._save_current_tab_data()
        self.current_tab_id = uid
        self.traceEditorView.set_model(model)
        self._show_trace_editor()

    def _find_next_trace_number(self) -> int:
        pattern = re.compile(r"^Trace\s+(\d+)$")
        largest_number = 0
        for i in range(self.tabPanel.listWidget.count()):
            it = self.tabPanel.listWidget.item(i)
            if not it:
                continue
            text = it.text()
            match = pattern.match(text)
            if match:
                num = int(match.group(1))
                if num > largest_number:
                    largest_number = num
        return largest_number + 1

    def _save_current_tab_data(self):
        pass

    def _show_setup_content(self):
        self.centerStack.setCurrentWidget(self.setupMenuView)
        self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")

    def _show_trace_editor(self):
        self.centerStack.setCurrentWidget(self.traceEditorView)
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")

    def on_plot_type_changed(self, plot_type: str):
        plot_type_lower = plot_type.lower()
        self.traceEditorView.set_plot_type(plot_type_lower)
        self.setupMenuView.set_plot_type(plot_type_lower)

    def save_workspace(self):
        traces = []
        order = []
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.text() not in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                uid = item.data(Qt.ItemDataRole.UserRole)
                order.append(uid)
                model = self.tabPanel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel):
                    traces.append(model)
        workspace = WorkspaceManager(traces, self.setupMenuModel, order=order)
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workspace", "", "JSON Files (*.json)")
        if filename:
            workspace.save_to_file(filename)

    def load_workspace(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Workspace", "", "JSON Files (*.json)")
        if filename:
            workspace = WorkspaceManager.load_from_file(filename)
            # Clear existing trace tabs (except the setup-menu)
            keys_to_remove = [uid for uid in self.tabPanel.id_to_widget if uid != "setup-menu-id"]
            for uid in keys_to_remove:
                self.tabPanel.remove_tab_by_id(uid)
            # Add each loaded trace to the TabPanel in saved order.
            # (Assumes your WorkspaceManager now saves order correctly.)
            for trace_dict in workspace.to_dict().get("traces", []):
                model = TraceEditorModel.from_dict(trace_dict)
                self.tabPanel.add_tab(model.trace_name, model)
            # Update the SetupMenu model and refresh its view.
            self.setupMenuModel = workspace.setup_model
            self.setupMenuView.model = self.setupMenuModel
            self.setupMenuView.update_from_model()
            self.setupMenuView.set_plot_type(self.setupMenuView.current_plot_type)


    def on_trace_name_changed(self, new_name: str):
        # Update the display text of the currently selected tab in the sidebar.
        uid = self.current_tab_id
        for i in range(self.tabPanel.listWidget.count()):
            item = self.tabPanel.listWidget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == uid:
                item.setText(new_name)
                break


# --------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
