import uuid

from PySide6.QtCore import (
    QEvent, 
    QRect, 
    Qt
)
from PySide6.QtGui import (
    QCursor,
    QIcon,
    QPainter,
    QPixmap
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget
)

from quick_ternaries.utils.constants import (
    ADD_TRACE_LABEL,
    SETUP_MENU_LABEL
)

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
        if (
            self.item(self.count() - 1) is None
            or self.item(self.count() - 1).text() != ADD_TRACE_LABEL
        ):
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

        self.tabSelectedCallback = None  # (unique_id) -> ...
        self.tabRenamedCallback = None  # (unique_id, new_label) -> ...
        self.tabRemovedCallback = None  # (unique_id) -> ...
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

        self.is_programmatic_change = False

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
        self.listWidget.blockSignals(True)
        self.listWidget.setCurrentItem(new_item)
        self.listWidget.blockSignals(False)
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
        
        # Only emit itemClicked if the change wasn't programmatic
        # This is the key change to prevent focus loss
        if not self.is_programmatic_change:
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