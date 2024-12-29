import sys
import uuid
import re

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QMessageBox,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QAbstractItemView, QSplitter,
    QPushButton, QLineEdit, QTextEdit, QComboBox
)
from PySide6.QtCore import Qt, QRect, QEvent, QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QCursor
from PySide6.QtWidgets import QSplitterHandle, QSplitter
from PySide6.QtGui import QPainter, QColor

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


class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.orientation = orientation
        self.setCursor(Qt.CursorShape.SplitHCursor if orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor)


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.GlobalColor.black)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))  # Transparent background

        # Draw grip dots
        grip_color = QColor(128, 128, 128)  # Grey
        painter.setBrush(grip_color)

        if self.orientation == Qt.Orientation.Horizontal:
            # Vertical dots for horizontal splitter
            width = self.width()
            center_x = width // 2
            dot_radius = 3.5
            spacing = 10
            self._draw_dots(painter, center_x, spacing, dot_radius, vertical=True)
        else:
            # Horizontal dots for vertical splitter
            height = self.height()
            center_y = height // 2
            dot_radius = 3.5
            spacing = 10
            self._draw_dots(painter, center_y, spacing, dot_radius, vertical=False)

    def _draw_dots(self, painter, center, spacing, radius, vertical=True):
        """Helper to draw 3 dots vertically or horizontally."""
        for i in range(-1, 2):  # Three dots
            if vertical:
                painter.drawEllipse(center - radius, self.height() // 2 + i * spacing - radius, radius * 2, radius * 2)
            else:
                painter.drawEllipse(self.width() // 2 + i * spacing - radius, center - radius, radius * 2, radius * 2)

    def enterEvent(self, event):
        """Ensure the cursor changes when hovering over the handle."""
        self.setCursor(Qt.CursorShape.SplitHCursor if self.orientation == Qt.Orientation.Horizontal else Qt.CursorShape.SplitVCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Ensure the cursor resets when leaving the handle."""
        self.unsetCursor()  # Optional, can keep the resize cursor
        super().leaveEvent(event)


class CustomSplitter(QSplitter):
    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)


# --------------------------------------------------------------------
# Data Model for Each Trace
# --------------------------------------------------------------------
class Trace:
    """Simple data model representing a trace."""
    def __init__(self, name: str):
        self.name = name
        self.color = "blue"
        self.description = "This is a description..."
        # Expand with more fields as needed

# --------------------------------------------------------------------
# TabListWidget: QLISTWIDGET that supports pinned top/bottom items,
# reordering, rename by double-click, removal icon.
# --------------------------------------------------------------------
class TabListWidget(QListWidget):
    """
    A custom QListWidget that:
    - Pins 'Setup Menu' at top
    - Pins 'Add Trace (+)' at bottom
    - Middle items are reorderable/renameable
    - We do NOT store QWidget pointers in item data, only a unique ID string
      to avoid QVariant serialization issues.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)

        # We'll filter drop events to re-pin items after dropping
        self.viewport().installEventFilter(self)

    def eventFilter(self, source, event):
        """Intercept drop events so we can fix pinned items afterwards."""
        if event.type() == QEvent.Type.Drop and source is self.viewport():
            self.dropEvent(event)
            return True
        return super().eventFilter(source, event)

    def dropEvent(self, event):
        """
        Let Qt handle the reorder, then re-pin the top (Setup Menu) and bottom (Add Trace).
        We'll do so by removing any pinned item that moved, re-creating them in the correct spot.
        Also re-select the previously selected item.
        """
        # 1) Remember which item was selected
        selected_item = self.currentItem()

        # 2) Let Qt handle the reordering
        super().dropEvent(event)

        # 3) Re-select the previously selected item (if it still exists)
        if selected_item:
            row = self.row(selected_item)
            if row != -1:
                self.setCurrentRow(row)
                self.itemClicked.emit(selected_item)

        # 4) Force the Setup Menu back to index 0 if needed
        if self.item(0) is None or self.item(0).text() != SETUP_MENU_LABEL:
            self._remove_pinned_items(SETUP_MENU_LABEL)
            setup_item = self._create_setup_item()
            self.insertItem(0, setup_item)

        # 5) Force the Add Trace item to the bottom if needed
        if self.item(self.count() - 1) is None or self.item(self.count() - 1).text() != ADD_TRACE_LABEL:
            self._remove_pinned_items(ADD_TRACE_LABEL)
            add_item = self._create_add_item()
            self.addItem(add_item)

    def _remove_pinned_items(self, label):
        """Remove items matching `label` from the list, if found outside pinned position."""
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
        """Block dragging pinned items."""
        current_item = self.currentItem()
        if current_item and current_item.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return  # do nothing
        super().startDrag(supportedActions)

    def mimeData(self, items):
        """Block pinned items from being dragged at all."""
        if items:
            for it in items:
                if it.text() in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
                    return None
        return super().mimeData(items)

# --------------------------------------------------------------------
# TabPanel: Holds the TabListWidget plus handles pinned items,
# dynamic style, etc.
# --------------------------------------------------------------------
class TabPanel(QWidget):
    """
    Shows a pinned "Setup Menu" at the top, pinned "Add Trace (+)" at the bottom,
    and reorderable middle items that the user can rename or remove via an icon.

    We store the 'content widget' in a dict instead of item data to avoid QVariant issues.
    We store only a unique ID string in the item data so drag-and-drop can serialize it safely.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.listWidget = TabListWidget()
        self.listWidget.itemSelectionChanged.connect(self._on_item_selection_changed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.listWidget)

        # Callbacks
        self.tabSelectedCallback = None      # (unique_id) -> ...
        self.tabRenamedCallback = None       # (unique_id, new_label) -> ...
        self.tabRemovedCallback = None       # (unique_id) -> ...
        self.tabAddRequestedCallback = None  # () -> ...

        # We map unique_id -> content widget or model object
        self.id_to_widget = {}

        # Setup pinned top item
        setup_item = self._create_setup_item()
        self.listWidget.addItem(setup_item)

        # Setup pinned bottom item
        add_item = self._create_add_item()
        self.listWidget.addItem(add_item)

        # Build a remove icon (X)
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

        # Hook up signals
        self.listWidget.itemClicked.connect(self._on_item_clicked)
        self.listWidget.itemChanged.connect(self._on_item_changed)

        # Connect to palette changes for dynamic styling
        app = QApplication.instance()
        if app:
            app.paletteChanged.connect(self.on_palette_changed)
        self.apply_dynamic_style()

    def _on_item_selection_changed(self):
        """
        Called whenever the selection changes. If Qt auto-selects a tab (e.g. after deletion),
        we invoke the same callback as a normal single-click so the editor is updated.
        """
        selected_items = self.listWidget.selectedItems()
        if len(selected_items) == 1:
            item = selected_items[0]
            label = item.text()
            # If pinned, we typically do nothing here, but you could handle Setup Menu similarly.
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
        """Build and apply a style sheet from the current system palette."""
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
        """If the system switches dark/light mode, re-apply style."""
        self.apply_dynamic_style()

    def add_tab(self, title: str, content_or_model) -> str:
        """
        Insert a new reorderable/renameable tab above 'Add Trace' and return its unique ID.
        We'll store the object (widget or model reference) in a dictionary keyed by this ID.
        """
        unique_id = str(uuid.uuid4())
        self.id_to_widget[unique_id] = content_or_model

        new_item = QListWidgetItem(title)
        new_item.setFlags(new_item.flags() | Qt.ItemFlag.ItemIsEditable)
        new_item.setIcon(self.removeIcon)
        new_item.setData(Qt.ItemDataRole.UserRole, unique_id)

        insert_index = self.listWidget.count() - 1
        self.listWidget.insertItem(insert_index, new_item)
        self.listWidget.setCurrentItem(new_item)
        return unique_id

    def select_tab_by_id(self, unique_id: str):
        """Programmatically select the item matching a given unique_id."""
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None:
                item_id = it.data(Qt.ItemDataRole.UserRole)
                if item_id == unique_id:
                    self.listWidget.setCurrentItem(it)
                    break

    # def remove_tab_by_id(self, unique_id: str):
    #     """Remove the item and dictionary entry for the given ID."""
    #     for i in range(self.listWidget.count()):
    #         it = self.listWidget.item(i)
    #         if it is not None and it.data(Qt.ItemDataRole.UserRole) == unique_id:
    #             self.listWidget.takeItem(i)
    #             self.id_to_widget.pop(unique_id, None)
    #             return

    # def remove_tab_by_id(self, unique_id: str):
    #     """Remove the item and dictionary entry for the given ID."""
    #     for i in range(self.listWidget.count()):
    #         it = self.listWidget.item(i)
    #         if it is not None and it.data(Qt.ItemDataRole.UserRole) == unique_id:
    #             self.listWidget.takeItem(i)
    #             self.id_to_widget.pop(unique_id, None)
    #             break

    #     # MINIMAL FIX: Re-emit a click on the *now* current item (if any)
    #     current_row = self.listWidget.currentRow()
    #     if current_row != -1:
    #         current_item = self.listWidget.item(current_row)
    #         if current_item:
    #             self.listWidget.itemClicked.emit(current_item)

    def remove_tab_by_id(self, unique_id: str):
        # 1) Remember which item is currently selected
        old_selected_item = self.listWidget.currentItem()
        old_selected_uid = None
        if old_selected_item:
            old_selected_uid = old_selected_item.data(Qt.ItemDataRole.UserRole)

        # 2) Remove the specified item
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if it is not None and it.data(Qt.ItemDataRole.UserRole) == unique_id:
                self.listWidget.takeItem(i)
                self.id_to_widget.pop(unique_id, None)
                break

        # 3) If we removed a DIFFERENT item than the currently selected one,
        #    Qt might forcibly select something else. Undo that by restoring the old selection.
        if old_selected_uid != unique_id:
            # If old_selected_item still exists in the list, re-select it
            if old_selected_item and self.listWidget.row(old_selected_item) != -1:
                self.listWidget.setCurrentItem(old_selected_item)
            else:
                # Or fallback to the first item if the old item is gone
                if self.listWidget.count() > 0:
                    self.listWidget.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem):
        label = item.text()
        # Setup Menu pinned
        if label == SETUP_MENU_LABEL:
            # If Setup Menu is clicked, let's invoke tabSelectedCallback with a special ID
            if self.tabSelectedCallback:
                self.tabSelectedCallback("setup-menu-id")
            return
        # Add Trace pinned
        if label == ADD_TRACE_LABEL:
            if self.tabAddRequestedCallback:
                self.tabAddRequestedCallback()
            return

        # Possibly the user clicked the remove icon
        if self._clicked_on_remove_icon(item):
            # Confirm removal
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabRemovedCallback:
                self.tabRemovedCallback(uid)
        else:
            # Normal tab selection
            uid = item.data(Qt.ItemDataRole.UserRole)
            if self.tabSelectedCallback:
                self.tabSelectedCallback(uid)

    def _on_item_changed(self, item: QListWidgetItem):
        """When user renames an item via double-click."""
        label = item.text()
        if label in (SETUP_MENU_LABEL, ADD_TRACE_LABEL):
            return  # pinned items, ignore
        uid = item.data(Qt.ItemDataRole.UserRole)
        if uid and self.tabRenamedCallback:
            self.tabRenamedCallback(uid, label)

        # MINIMAL FIX: Re-emit "itemClicked" so the MainWindow sees this item as re-selected
        self.listWidget.itemClicked.emit(item)

    def _clicked_on_remove_icon(self, item: QListWidgetItem) -> bool:
        """
        Check if the user clicked in the bounding box of the icon (16x16) at the left side.
        """
        pos = self.listWidget.viewport().mapFromGlobal(QCursor.pos())
        item_rect = self.listWidget.visualItemRect(item)

        # We'll create a 16x16 box, left-aligned within the item
        icon_size = 16
        margin_left = 20  # tweak if needed
        icon_left = item_rect.left() + margin_left
        icon_top = item_rect.top() + (item_rect.height() - icon_size) // 2

        icon_rect = QRect(icon_left, icon_top, icon_size, icon_size)
        return icon_rect.contains(pos)

# --------------------------------------------------------------------
# TraceEditor: A panel that shows and persists data for the current Trace.
# --------------------------------------------------------------------
class TraceEditor(QWidget):
    """
    Demonstrates how to display/edit data for a Trace object.
    Switching to another Trace persists changes in the old one, then
    loads the new one.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_trace = None  # type: Trace or None

        # Layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Fields: name, color, description
        # Name
        self.nameLine = QLineEdit()
        layout.addWidget(QLabel("Trace Name:"))
        layout.addWidget(self.nameLine)

        # Color
        self.colorLine = QLineEdit()
        layout.addWidget(QLabel("Trace Color:"))
        layout.addWidget(self.colorLine)

        # Description
        layout.addWidget(QLabel("Description:"))
        self.descText = QTextEdit()
        layout.addWidget(self.descText)

        layout.addStretch()

        # Connect signals to update the model as user types:
        self.nameLine.textEdited.connect(self.on_field_changed)
        self.colorLine.textEdited.connect(self.on_field_changed)
        self.descText.textChanged.connect(self.on_field_changed)

    def set_trace(self, trace: Trace):
        """
        Set a new trace as the "current" one, and load its fields into the UI.
        If trace is None, clear the UI.
        """
        self.current_trace = trace
        self.load_current_trace()

    def load_current_trace(self):
        """Load UI fields from self.current_trace."""
        if not self.current_trace:
            self.nameLine.setText("")
            self.colorLine.setText("")
            self.descText.setPlainText("")
        else:
            self.nameLine.setText(self.current_trace.name)
            self.colorLine.setText(self.current_trace.color)
            self.descText.setPlainText(self.current_trace.description)

    def on_field_changed(self):
        """Whenever a field changes, update self.current_trace if possible."""
        if self.current_trace:
            self.current_trace.name = self.nameLine.text()
            self.current_trace.color = self.colorLine.text()
            self.current_trace.description = self.descText.toPlainText()

# --------------------------------------------------------------------
# MainWindow: with top banner, bottom banner, middle QSplitter
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

        # Top banner
        top_banner = self._create_top_banner()
        main_vlayout.addWidget(top_banner)

        # Middle: a horizontal splitter with 3 panels
        self.h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.h_splitter = CustomSplitter(Qt.Orientation.Horizontal)
        self.h_splitter.setHandleWidth(8)
        self.h_splitter.setStyleSheet("""
        QSplitter::handle {
            width: 5px; /* or height if vertical splitter */
            margin-left: 3px;        /* Add margin on the left */
            margin-right: 3px;                   
        }
        """)

        main_vlayout.addWidget(self.h_splitter, 1)

        # Bottom banner
        bottom_banner = self._create_bottom_banner()
        main_vlayout.addWidget(bottom_banner)

        # Left: TabPanel
        self.tabPanel = TabPanel()
        self.h_splitter.addWidget(self.tabPanel)

        # Middle: TraceEditor
        self.traceEditor = TraceEditor()
        self.h_splitter.addWidget(self.traceEditor)

        # Right: Plot Window (QWebEngineView placeholder)
        self.plotView = QWebEngineView()
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")
        self.h_splitter.addWidget(self.plotView)

        # Connect tabPanel callbacks
        self.tabPanel.tabSelectedCallback = self.on_tab_selected
        self.tabPanel.tabRenamedCallback = self.on_tab_renamed
        self.tabPanel.tabRemovedCallback = self.on_tab_removed
        self.tabPanel.tabAddRequestedCallback = self.create_new_tab

        # Create the content/model for "Setup Menu"
        self.setup_id = "setup-menu-id"
        self.tabPanel.id_to_widget[self.setup_id] = None  # no real model for setup
        # We'll display a special label for the "Setup Menu"
        setup_label = QLabel("Setup Menu Content")
        setup_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setup_label.setStyleSheet("QLabel { font-size: 16pt; }")
        self.setupLabel = setup_label  # store reference

        # We'll keep track of the "current" ID so we can save old tab's data on switch
        self.current_tab_id = None

        # Add a few initial traces
        self._create_initial_traces()

        # Start with Setup Menu selected
        self.tabPanel.listWidget.setCurrentRow(0)
        self.current_tab_id = "setup-menu-id"
        self._show_setup_content()

    # ----------------------------------------------------------------
    # Banner creation
    # ----------------------------------------------------------------
    def _create_top_banner(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 2, 8, 2)

        # Left: "Quick Ternaries" label
        logo_label = QLabel("Quick Ternaries")
        logo_label.setStyleSheet("font-weight: bold; font-size: 16pt;")
        layout.addWidget(logo_label)

        layout.addStretch()

        # Right: plot type selector + settings button
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

    # ----------------------------------------------------------------
    # Initial Data
    # ----------------------------------------------------------------
    def _create_initial_traces(self):
        # For demonstration, create 3 initial Traces
        for i in range(1, 4):
            t = Trace(f"Trace {i}")
            t.color = ["blue", "red", "green"][ (i-1) % 3 ]
            t.description = f"Trace {i} is a sample. Color: {t.color}"
            # Add to tab panel
            uid = self.tabPanel.add_tab(t.name, t)
            # No separate "content widget" for the right side, because we handle in the editor

    # ----------------------------------------------------------------
    # Tab Callbacks
    # ----------------------------------------------------------------
    def on_tab_selected(self, unique_id: str):
        """
        Called when user selects a tab (or Setup Menu).
        We'll persist the old tab's changes, then load the new tab's data.
        """
        # 1) Save old tab's data
        self._save_current_tab_data()

        # 2) Switch to the new tab
        self.current_tab_id = unique_id
        if unique_id == "setup-menu-id":
            self._show_setup_content()
        else:
            # It's a real trace ID
            trace_obj = self.tabPanel.id_to_widget.get(unique_id)
            if isinstance(trace_obj, Trace):
                self.traceEditor.set_trace(trace_obj)
                self._show_trace_editor()
            else:
                # fallback
                self.traceEditor.set_trace(None)
                self._show_trace_editor()

    def on_tab_renamed(self, unique_id: str, new_label: str):
        """
        Update the underlying Trace's name if applicable.
        """
        if unique_id == "setup-menu-id":
            return
        trace_obj = self.tabPanel.id_to_widget.get(unique_id)
        if isinstance(trace_obj, Trace):
            trace_obj.name = new_label
            # The editor will refresh next time we select this tab

    def on_tab_removed(self, unique_id: str):
        """
        Called when user clicks the remove icon on a tab. We confirm deletion.
        """
        if unique_id == "setup-menu-id":
            return  # pinned
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this tab?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        # user confirmed
        # If it's the currently selected tab, switch to Setup Menu
        if unique_id == self.current_tab_id:
            self._save_current_tab_data()
            self.current_tab_id = "setup-menu-id"
            self.tabPanel.listWidget.setCurrentRow(0)
            self._show_setup_content()

        # Remove from dictionary and tab list
        self.tabPanel.remove_tab_by_id(unique_id)

    def create_new_tab(self):
        """
        Called by tabAddRequestedCallback when user clicks 'Add Trace (+)' item.
        We'll find the largest "Trace X" used so far and do "Trace X+1".
        """
        new_trace_number = self._find_next_trace_number()
        new_label = f"Trace {new_trace_number}"

        # Create the new Trace object
        t = Trace(new_label)

        # Insert it into the TabPanel
        uid = self.tabPanel.add_tab(new_label, t)

        # Immediately switch to it
        self._save_current_tab_data()
        self.current_tab_id = uid
        self.traceEditor.set_trace(t)
        self._show_trace_editor()

    def _find_next_trace_number(self) -> int:
        """
        Scan all current tab texts to find the largest integer X from "Trace X".
        Returns X+1, or 1 if none are found.
        """
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

    # ----------------------------------------------------------------
    # Helper methods
    # ----------------------------------------------------------------
    def _save_current_tab_data(self):
        """
        If the current tab is a real trace, ensure we store
        any unsaved changes from the editor into the model.
        """
        if self.current_tab_id and self.current_tab_id != "setup-menu-id":
            # The editor updates the trace live on text change,
            # so no special "save" is needed if we've been doing it immediately.
            # But if we had a manual "save" approach, we'd call it here.
            pass

    def _show_setup_content(self):
        """
        Switch the right panel to show "Setup Menu Content"
        and the middle panel to an empty editor.
        """
        # Middle panel: just clear the editor
        self.traceEditor.set_trace(None)
        # Right panel: show setup label or a specialized widget
        self.plotView.setHtml("<h3>Setup Menu (no plot)</h3>")

    def _show_trace_editor(self):
        """
        Switch the right panel to the QWebEngineView (plot).
        Middle panel is the trace editor.
        """
        self.plotView.setHtml("<h3>Plot Window</h3><p>QWebEngineView placeholder</p>")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
