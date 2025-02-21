
import sys
import uuid
import re
from dataclasses import dataclass, field, fields

try:
    import pandas as pd
except ImportError:
    pd = None

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMessageBox,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QAbstractItemView, QSplitter,
    QPushButton, QLineEdit, QComboBox, QFormLayout,
    QDoubleSpinBox, QCheckBox, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QRect, QEvent, QPoint
from PySide6.QtWidgets import QSplitterHandle, QSplitter
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.available_options = []  # Options from the intersection of loaded files.
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
        # Show dialog to choose from available options not already selected.
        choices = [opt for opt in self.available_options if opt not in self.get_selected_fields()]
        if not choices:
            return
        item, ok = QInputDialog.getItem(self, "Select Field", "Available Fields:", choices, 0, False)
        if ok and item:
            self.listWidget.addItem(item)

    def remove_field(self):
        current_item = self.listWidget.currentItem()
        if current_item:
            row = self.listWidget.row(current_item)
            self.listWidget.takeItem(row)

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
        metadata={"label": "Heatmap On:", "widget": QCheckBox, "plot_types": ["ternary"]}
    )
    sizemap_on: bool = field(
        default=False,
        metadata={"label": "Sizemap On:", "widget": QCheckBox, "plot_types": ["ternary"]}
    )
    filters_on: bool = field(
        default=False,
        metadata={"label": "Filters On:", "widget": QCheckBox, "plot_types": ["ternary", "cartesian"]}
    )
    filters: list = field(
        default_factory=list,
        metadata={"label": "Filters:", "widget": None, "plot_types": ["ternary", "cartesian"]}
    )

class TraceEditorView(QWidget):
    def __init__(self, model: TraceEditorModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # default
        self.widgets = {}
        self.form_layout = QFormLayout()
        self.setLayout(self.form_layout)
        self._build_ui()
        self.set_plot_type(self.current_plot_type)
    
    def _build_ui(self):
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
                widget.textChanged.connect(
                    lambda text, fname=f.name: setattr(self.model, fname, text)
                )
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
                widget.valueChanged.connect(
                    lambda val, fname=f.name: setattr(self.model, fname, val)
                )
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
                widget.stateChanged.connect(
                    lambda state, fname=f.name: setattr(self.model, fname, bool(state))
                )
            elif isinstance(widget, QComboBox):
                widget.addItems(["solid", "dashed", "dotted"])
                widget.setCurrentText(str(value))
                widget.currentTextChanged.connect(
                    lambda text, fname=f.name: setattr(self.model, fname, text)
                )
            self.form_layout.addRow(label_text, widget)
    
    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type
        for f in fields(self.model):
            metadata = f.metadata
            if "plot_types" not in metadata or "widget" not in metadata:
                continue
            if metadata["widget"] is None:
                continue
            widget = self.widgets.get(f.name)
            label = self.form_layout.labelForField(widget)
            if plot_type in metadata["plot_types"]:
                widget.show()
                if label:
                    label.show()
            else:
                widget.hide()
                if label:
                    label.hide()

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
    
    def set_model(self, new_model: TraceEditorModel):
        self.model = new_model
        self.update_from_model()

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
        # Update available options for each MultiFieldSelector in the axis members section.
        axis_widgets = self.view.section_widgets.get("AxisMembersModel", {})
        for field_name, widget in axis_widgets.items():
            if isinstance(widget, MultiFieldSelector):
                widget.set_available_options(common_list)
                # Optionally, clear current selections if they are no longer valid:
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
        self.current_plot_type = "ternary"  # Default (can be updated)
        self.controller = None  # Will be set later by the main window.
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        self.section_widgets = {}  # To hold per-section widget mappings.

        # Section: Data Library
        self.dataLibraryWidget = QWidget(self)
        data_library_layout = QVBoxLayout(self.dataLibraryWidget)
        self.dataLibraryWidget.setLayout(data_library_layout)
        data_library_label = QLabel("Loaded Data:")
        data_library_layout.addWidget(data_library_label)
        self.dataLibraryList = QListWidget(self)
        data_library_layout.addWidget(self.dataLibraryList)
        btn_layout = QHBoxLayout()
        self.addDataButton = QPushButton("Add Data")
        self.removeDataButton = QPushButton("Remove Data")
        btn_layout.addWidget(self.addDataButton)
        btn_layout.addWidget(self.removeDataButton)
        data_library_layout.addLayout(btn_layout)
        self.addDataButton.clicked.connect(self.add_data_file)
        self.removeDataButton.clicked.connect(self.remove_data_file)
        self.layout.addWidget(self.dataLibraryWidget)
        
        # Section: Plot Labels
        self.plotLabelsWidget = self.build_form_section(self.model.plot_labels)
        self.layout.addWidget(self.plotLabelsWidget)
        
        # Section: Axis Members
        self.axisMembersWidget = self.build_form_section(self.model.axis_members)
        self.layout.addWidget(self.axisMembersWidget)
        
        # Section: Advanced Settings
        self.advancedSettingsWidget = self.build_form_section(self.model.advanced_settings)
        self.layout.addWidget(self.advancedSettingsWidget)
    
    def set_controller(self, controller: SetupMenuController):
        self.controller = controller

    def build_form_section(self, section_model):
        widget = QWidget(self)
        form_layout = QFormLayout(widget)
        widget.setLayout(form_layout)
        section_name = section_model.__class__.__name__
        self.section_widgets[section_name] = {}
        for f in fields(section_model):
            metadata = f.metadata
            if "label" not in metadata or "widget" not in metadata or metadata["widget"] is None:
                continue
            widget_cls = metadata["widget"]
            label_text = metadata["label"]
            field_widget = widget_cls(self)
            value = getattr(section_model, f.name)
            # For MultiFieldSelector, the value is a list.
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
                # For now, leave options empty; they may be updated later.
                field_widget.addItems([])
                field_widget.setCurrentText(str(value))
                field_widget.currentTextChanged.connect(lambda text, fname=f.name, m=section_model: setattr(m, fname, text))
            elif isinstance(field_widget, MultiFieldSelector):
                field_widget.set_selected_fields(value)
            form_layout.addRow(label_text, field_widget)
            self.section_widgets[section_name][f.name] = field_widget
        return widget

    def set_plot_type(self, plot_type: str):
        self.current_plot_type = plot_type
        # Update visibility for each section based on metadata.
        for section, widgets in self.section_widgets.items():
            for fname, widget in widgets.items():
                # Find metadata for this field.
                for f in fields(getattr(self.model, section.lower())):
                    if f.name == fname:
                        metadata = f.metadata
                        break
                else:
                    continue
                label = self.findChild(QLabel, fname)
                if "plot_types" in metadata and self.current_plot_type in metadata["plot_types"]:
                    widget.show()
                    if label:
                        label.show()
                else:
                    widget.hide()
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

    def _create_bottom_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)
        self.previewButton = QPushButton("Preview")
        self.saveButton = QPushButton("Save")
        self.exportButton = QPushButton("Export")
        self.bootstrapButton = QPushButton("Bootstrap")
        layout.addWidget(self.previewButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.exportButton)
        layout.addWidget(self.bootstrapButton)
        layout.addStretch()
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
