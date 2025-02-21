import sys
import uuid
import re
from dataclasses import dataclass, field, fields

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMessageBox,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QAbstractItemView, QSplitter,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QFormLayout,
    QDoubleSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QRect, QEvent, QPoint
from PySide6.QtWidgets import QSplitterHandle, QSplitter
from PySide6.QtGui import QIcon, QPixmap, QPainter, QCursor, QColor

# If you have PySide6-WebEngine installed, import QWebEngineView:
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    QWebEngineView = QLabel  # fallback if no PySide6-WebEngine is available

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

        # Draw grip dots
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

        # Map unique_id -> trace editor model
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
# New Trace Editor Model (using Dataclasses with metadata)
# --------------------------------------------------------------------
@dataclass
class TraceEditorModel:
    trace_name: str = field(
        default="Default Trace",
        metadata={
            "label": "Trace Name:",
            "widget": QLineEdit,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    datafile: str = field(
        default="",
        metadata={
            "label": "Datafile:",
            "widget": QLineEdit,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    trace_color: str = field(
        default="blue",
        metadata={
            "label": "Trace Color:",
            "widget": QLineEdit,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    point_size: float = field(
        default=5.0,
        metadata={
            "label": "Point Size:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    point_opacity: float = field(
        default=1.0,
        metadata={
            "label": "Point Opacity:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    line_on: bool = field(
        default=True,
        metadata={
            "label": "Line On:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    line_style: str = field(
        default="solid",
        metadata={
            "label": "Line Style:",
            "widget": QComboBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    line_thickness: float = field(
        default=1.0,
        metadata={
            "label": "Line Thickness:",
            "widget": QDoubleSpinBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    heatmap_on: bool = field(
        default=False,
        metadata={
            "label": "Heatmap On:",
            "widget": QCheckBox,
            "plot_types": ["ternary"]
        }
    )
    sizemap_on: bool = field(
        default=False,
        metadata={
            "label": "Sizemap On:",
            "widget": QCheckBox,
            "plot_types": ["ternary"]
        }
    )
    filters_on: bool = field(
        default=False,
        metadata={
            "label": "Filters On:",
            "widget": QCheckBox,
            "plot_types": ["ternary", "cartesian"]
        }
    )
    filters: list = field(
        default_factory=list,
        metadata={
            "label": "Filters:",  # Not rendered by default.
            "widget": None,
            "plot_types": ["ternary", "cartesian"]
        }
    )

# --------------------------------------------------------------------
# New Trace Editor View
# --------------------------------------------------------------------
class TraceEditorView(QWidget):
    """
    A view that builds its UI dynamically from the TraceEditorModel metadata.
    The UI is built once (or rebuilt on plot type change) and when switching traces,
    the widget values are simply updated.
    """
    def __init__(self, model: TraceEditorModel, parent=None):
        super().__init__(parent)
        self.model = model
        self.current_plot_type = "ternary"  # default
        self.widgets = {}  # mapping of field name to widget instance
        
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
                # Example: for line_style.
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
# MainWindow: Integrates TabPanel, TraceEditorView, and Plot Window
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

        # Middle: TraceEditorView (initially using a dummy model)
        self.current_trace_model = TraceEditorModel()
        self.traceEditorView = TraceEditorView(self.current_trace_model)
        self.h_splitter.addWidget(self.traceEditorView)

        # Right: Plot Window (placeholder)
        self.plotView = QWebEngineView()
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")
        self.h_splitter.addWidget(self.plotView)

        # Connect TabPanel callbacks
        self.tabPanel.tabSelectedCallback = self.on_tab_selected
        self.tabPanel.tabRenamedCallback = self.on_tab_renamed
        self.tabPanel.tabRemovedCallback = self.on_tab_removed
        self.tabPanel.tabAddRequestedCallback = self.create_new_tab

        # Setup Menu configuration (special case)
        self.setup_id = "setup-menu-id"
        self.tabPanel.id_to_widget[self.setup_id] = None
        setup_label = QLabel("Setup Menu Content")
        setup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setup_label.setStyleSheet("QLabel { font-size: 16pt; }")
        self.setupLabel = setup_label

        self.current_tab_id = None
        self._create_initial_traces()

        self.tabPanel.listWidget.setCurrentRow(0)
        self.current_tab_id = "setup-menu-id"
        self._show_setup_content()

        # Connect top banner plot type selector
        self.plotTypeSelector.currentTextChanged.connect(self.on_plot_type_changed)

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
        # Create three initial traces using TraceEditorModel.
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
        # Save current model if needed.
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
        # With live updating in the view, no special action is required.
        pass

    def _show_setup_content(self):
        self.traceEditorView.set_model(TraceEditorModel())
        self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")

    def _show_trace_editor(self):
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")

    def on_plot_type_changed(self, plot_type: str):
        # Update view based on plot type.
        # Assuming the combo box text is in title case.
        self.traceEditorView.set_plot_type(plot_type.lower())

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
