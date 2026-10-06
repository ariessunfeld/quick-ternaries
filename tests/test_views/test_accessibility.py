"""Exercise the real Qt accessibility interfaces and keyboard event paths."""

from dataclasses import fields

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QAccessible
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit

from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.views.setup_menu_view import SetupMenuView
from quick_ternaries.views.trace_editor_view import TraceEditorView
from quick_ternaries.views.filter_editor_view import FilterEditorView
from quick_ternaries.views.tab_panel_widget import TabPanel
from quick_ternaries.views.widgets.filter_tab_widget import FilterTabWidget


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


def assert_accessible(widget, identifier, name):
    interface = QAccessible.queryAccessibleInterface(widget)
    assert interface is not None
    assert widget.accessibleName() == name
    if isinstance(widget, QComboBox):
        assert interface.text(QAccessible.Text.Name) in (name, widget.currentText())
        assert interface.text(QAccessible.Text.Description) == name
        assert interface.text(QAccessible.Text.Value) == widget.currentText()
    else:
        assert interface.text(QAccessible.Text.Name) == name
    assert interface.text(QAccessible.Text.Identifier) == identifier
    assert interface.role() != QAccessible.Role.NoRole


def test_generated_setup_fields_expose_names_identifiers_and_values(qt_app):
    model = SetupMenuModel()
    view = SetupMenuView(model)
    for section, widgets in view.section_widgets.items():
        for field in fields(getattr(model, section)):
            if field.name in widgets and field.metadata.get("label"):
                assert_accessible(widgets[field.name], f"setup.{section}.{field.name}",
                                  field.metadata["label"].rstrip(":"))
    apex = view.section_widgets["axis_members"]["top_axis"]
    assert_accessible(apex.addButton, "setup.axis_members.top_axis.add", "Add to Top Apex")
    assert apex.focusProxy() is apex.listWidget
    title = view.section_widgets["plot_labels"]["title"]
    QTest.keyClicks(title, "Accessible plot")
    assert model.plot_labels.title == title.text()
    interface = QAccessible.queryAccessibleInterface(title)
    assert interface.text(QAccessible.Text.Value) == title.text()
    view.close()


def test_composite_trace_controls_expose_current_values_and_survive_rebuild(qt_app):
    view = TraceEditorView(TraceEditorModel())
    color = view.widgets["trace_color"]
    assert_accessible(color.button, "trace.trace_color.choose", "Choose Point Color")
    color.setColor("#123456")
    assert "#123456" in QAccessible.queryAccessibleInterface(color.button).text(QAccessible.Text.Description)
    assert color.focusProxy() is color.button
    shapes = view.widgets["point_shape"]
    shapes.setShape("star")
    assert "star" in QAccessible.queryAccessibleInterface(shapes.button).text(QAccessible.Text.Description)
    assert [action.text() for action in shapes.menu.actions() if action.isChecked()] == ["star"]
    datafile = view.widgets["datafile"]
    assert_accessible(datafile.change_button, "trace.datafile.choose", "Choose Datafile")
    datafile.setDatafile("example.xlsx")
    assert "example.xlsx" in datafile.change_button.accessibleDescription()
    scale = view.widgets["heatmap_colorscale"]
    assert scale.focusProxy() is scale.comboBox
    assert_accessible(scale.comboBox, "trace.heatmap_colorscale.select", "Heatmap Colorscale")
    old_identifier = view.widgets["trace_name"].accessibleIdentifier()
    view.set_model(TraceEditorModel(trace_name="Second trace"))
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert view.widgets["trace_name"].accessibleIdentifier() == old_identifier
    assert QAccessible.queryAccessibleInterface(view.widgets["trace_name"]).text(QAccessible.Text.Value) == "Second trace"
    view.close()


def test_trace_keyboard_actions_preserve_pinned_rows_and_use_callbacks(qt_app, monkeypatch):
    panel = TabPanel()
    panel.show()
    qt_app.processEvents()
    selected, removed, added, renamed = [], [], [], []
    panel.tabSelectedCallback = selected.append
    panel.tabRemovedCallback = removed.append
    panel.tabRenamedCallback = lambda uid, name: renamed.append((uid, name))
    panel.tabAddRequestedCallback = lambda: added.append(True)
    first = panel.add_tab("First", TraceEditorModel())
    second = panel.add_tab("Second", TraceEditorModel())
    # Keyboard activation must never use the cursor's remove-icon hit test.
    monkeypatch.setattr(panel, "_clicked_on_remove_icon", lambda item: True)
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Return)
    assert selected[-1] == second and not removed
    QTest.keyClick(panel.listWidget, Qt.Key.Key_F2)
    editor = panel.listWidget.findChild(QLineEdit)
    assert editor is not None
    editor.selectAll()
    QTest.keyClicks(editor, "Renamed trace")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert renamed == [(second, "Renamed trace")] and not removed
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Up, Qt.KeyboardModifier.AltModifier)
    assert panel.listWidget.item(1).data(Qt.ItemDataRole.UserRole) == second
    assert panel.listWidget.currentRow() == 1
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Up, Qt.KeyboardModifier.AltModifier)
    assert panel.listWidget.currentRow() == 1
    assert panel.listWidget.item(2).data(Qt.ItemDataRole.UserRole) == first
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Delete)
    assert removed == [second]
    assert second in panel.id_to_widget  # Existing callback owns confirmation/deletion.
    panel.listWidget.setCurrentRow(0)
    assert selected[-1] == "setup-menu-id"
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Delete)
    assert removed == [second]
    panel.listWidget.setCurrentRow(panel.listWidget.count() - 1)
    assert not added  # Merely selecting Add must not mutate the document.
    QTest.keyClick(panel.listWidget, Qt.Key.Key_Space)
    assert added == [True]
    panel.close()


def test_filter_keyboard_activation_and_dynamic_value_metadata(qt_app):
    tabs = FilterTabWidget()
    added, removed = [], []
    tabs.filterAddRequestedCallback.connect(lambda: added.append(True))
    tabs.filterRemoveRequestedCallback.connect(removed.append)
    tabs.set_filters(["Example"])
    QTest.keyClick(tabs, Qt.Key.Key_Delete)
    assert removed == [0]
    tabs.setCurrentRow(1)
    QTest.keyClick(tabs, Qt.Key.Key_Return)
    assert added == [True]
    view = FilterEditorView(FilterModel())
    assert_accessible(view.widgets["filter_value1"], "trace.filter.filter_value1", "Filter value A")
    view.update_filter_value_widgets()
    assert_accessible(view.widgets["filter_value1"], "trace.filter.filter_value1", "Filter value A")
    view.close()
    tabs.close()


def test_direct_focus_shortcuts_reach_filter_dropdowns(qt_app):
    view = FilterEditorView(FilterModel())
    view.show()
    view.activateWindow()
    qt_app.processEvents()
    name = view.widgets["filter_name"]
    name.setFocus()
    for key, field in [(Qt.Key.Key_C, "filter_column"), (Qt.Key.Key_O, "filter_operation")]:
        QTest.keyClick(name, key, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
        qt_app.processEvents()
        assert QApplication.focusWidget() is view.widgets[field]
    view.close()


def test_direct_focus_shortcut_reaches_trace_list(qt_app):
    panel = TabPanel()
    panel.show()
    panel.activateWindow()
    qt_app.processEvents()
    panel.listWidget.clearFocus()
    QTest.keyClick(panel, Qt.Key.Key_T,
                   Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
    qt_app.processEvents()
    assert QApplication.focusWidget() is panel.listWidget
    panel.close()
