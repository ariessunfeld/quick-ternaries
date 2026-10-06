from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem
from quick_ternaries.views.accessibility import describe_control


class FilterTabWidget(QListWidget):
    filterSelectedCallback = Signal(int)
    filterAddRequestedCallback = Signal()
    filterRenamedCallback = Signal(int, str)
    filterRemoveRequestedCallback = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        describe_control(self, "trace.filters", "Trace filters",
                         "Enter or Space activates a row; Delete removes a filter; F2 renames it.")
        self.setDragDropMode(QListWidget.NoDragDrop)
        self.setEditTriggers(QListWidget.DoubleClicked)
        self.viewport().installEventFilter(self)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemActivated.connect(self._on_item_clicked)
        self.itemChanged.connect(self._on_item_changed)
        self.currentItemChanged.connect(self._on_current_item_changed)
        self.filters = []
        self._refresh_tabs()

    def keyPressEvent(self, event):
        item = self.currentItem()
        if (item is not None and self.state() != QListWidget.State.EditingState
                and event.modifiers() == Qt.KeyboardModifier.NoModifier):
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
                self.itemActivated.emit(item)
                return
            if self.row(item) < len(self.filters):
                if event.key() == Qt.Key.Key_Delete:
                    self.filterRemoveRequestedCallback.emit(self.row(item))
                    return
                if event.key() == Qt.Key.Key_F2:
                    self.editItem(item)
                    return
        super().keyPressEvent(event)

    # Add this method to handle changes in current item (including via arrow keys)
    def _on_current_item_changed(self, current, previous):
        """Handle selection changes, including those from keyboard navigation."""
        # TODO when checking, use Enum after refactoring to make more robust to changes in text
        if current and current.text() != "Add Filter (+)":
            index = self.row(current)
            self.filterSelectedCallback.emit(index)

    def _refresh_tabs(self):
        self.clear()
        for name in self.filters:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.addItem(item)
        add_item = QListWidgetItem("Add Filter (+)")
        add_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.addItem(add_item)

    def set_filters(self, filter_names: list):
        self.filters = filter_names.copy()
        self._refresh_tabs()
        if self.filters:
            self.setCurrentRow(0)

    def add_filter_tab(self, filter_name: str):
        self.filters.append(filter_name)
        self._refresh_tabs()
        self.setCurrentRow(len(self.filters) - 1)

    def update_filter_tab(self, index: int, new_name: str):
        if 0 <= index < len(self.filters):
            self.filters[index] = new_name
            item = self.item(index)
            if item:
                item.setText(new_name)

    def _on_item_clicked(self, item: QListWidgetItem):
        if item.text() == "Add Filter (+)":
            self.filterAddRequestedCallback.emit()
        else:
            index = self.row(item)
            self.filterSelectedCallback.emit(index)

    def _on_item_changed(self, item: QListWidgetItem):
        if item.text() == "Add Filter (+)":
            return
        index = self.row(item)
        self.filters[index] = item.text()
        self.filterRenamedCallback.emit(index, item.text())
