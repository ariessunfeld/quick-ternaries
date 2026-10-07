"""Exercise the real window in isolation from other tests' QApplication lifetime."""

import os
from pathlib import Path
import subprocess
import sys


def test_human_agent_interleaving_preserves_typing_history_and_saved_identity(tmp_path):
    script = r'''
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from time import monotonic, sleep
from uuid import UUID, uuid4
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QAccessible
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QColorDialog, QFileDialog, QMessageBox
from quick_ternaries.app import MainWindow
from quick_ternaries.agent_api.client import read, set_trace_color
from quick_ternaries.agent_api.contract import ApiError
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.trace_editor_model import TraceEditorModel

app = QApplication([])
window = MainWindow()
window.show()
app.processEvents()

def remote(callback):
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(callback)
        deadline = monotonic() + 8
        while not future.done() and monotonic() < deadline:
            app.processEvents()
            sleep(.001)
        assert future.done()
        return future.result()

path = Path('synthetic.csv').resolve()
path.write_text('A,B,C,Sample\n70,20,10,Alpha\n20,70,10,Beta\n')
metadata = DataFileMetadata(str(path), header_row=0)
assert window.setupMenuModel.data_library.add_file(metadata)
model = TraceEditorModel(trace_name='Live sample', trace_color='#000000', datafile=metadata)
uid = window.tabPanel.add_tab(model.trace_name, model)
second_model = TraceEditorModel(trace_name='Other sample', trace_color='#111111', datafile=metadata)
other_id = window.tabPanel.add_tab(second_model.trace_name, second_model)
window.tabPanel.select_tab_by_id(uid)
window.on_tab_selected(uid)
window.agentButton.click()
dialog = window.agent_dialog
assert not dialog.allow_edit.isEnabled()
dialog.toggle.click()
assert dialog.allow_edit.isEnabled() and not dialog.allow_edit.isChecked()
dialog.allow_edit.click()
assert dialog.api.edit_enabled
details = dialog.api.connection_details()
dialog.close()
app.processEvents()
core = window.workspace_session

def args(trace_id=uid, color='#123456'):
    state = remote(lambda: read(details, 'trace-colors/' + trace_id))['color_state']
    return dict(trace_id=trace_id, color=color, workspace_epoch=state['workspace_epoch'],
                expected_color_revision=state['color_revision'], request_id=str(uuid4()))

stale = args()
# A real button interaction follows the color-picker acceptance path.
button = window.traceEditorView.widgets['trace_color']
with patch.object(QColorDialog, 'getColor', return_value=QColor('#ff0000')):
    QTest.mouseClick(button.button, Qt.MouseButton.LeftButton)
assert model.trace_color == '#ff0000'
assert core.history()['undo_label'] == 'Human: trace color'
try:
    remote(lambda: set_trace_color(details, **stale))
    raise AssertionError('Stale agent write accepted')
except ApiError as error:
    assert error.code == 'color_conflict'

pending = args()
name = window.traceEditorView.widgets['trace_name']
window.activateWindow()
app.processEvents()
name.setFocus()
name.selectAll()
QTest.keyClicks(name, 'Still typing a label')
name.setSelection(6, 6)
app.processEvents()
assert app.focusWidget() is name
before = (name.text(), name.cursorPosition(), name.selectionStart(), name.selectedText(), window.current_tab_id)
result = remote(lambda: set_trace_color(details, **pending))
assert result['receipt']['render_required']
assert window.traceEditorView.widgets['trace_name'] is name
assert app.focusWidget() is name
assert before == (name.text(), name.cursorPosition(), name.selectionStart(), name.selectedText(), window.current_tab_id)
assert model.trace_name == 'Still typing a label'
assert button.getColor() == '#123456'
assert core.history()['undo_label'] == 'Agent: trace color'
assert 'Agent' in window.undoColorButton.accessibleDescription()
accessible = QAccessible.queryAccessibleInterface(window.undoColorButton)
assert accessible.text(QAccessible.Text.Identifier) == 'workspace.undo_color'

# Native text undo remains independent of color history (no global Ctrl+Z override).
name.undo()
assert core.history()['undo_count'] == 2
assert model.trace_color == '#123456'
name.redo()
QTest.mouseClick(window.undoColorButton, Qt.MouseButton.LeftButton)
assert model.trace_color == '#ff0000'
assert button.getColor() == '#ff0000'
assert model.trace_name == 'Still typing a label'
replayed = remote(lambda: set_trace_color(details, **pending))
assert replayed['receipt']['replayed']
assert model.trace_color == '#ff0000'  # A retry cannot reverse human undo.
QTest.mouseClick(window.redoColorButton, Qt.MouseButton.LeftButton)
assert model.trace_color == '#123456'
QTest.mouseClick(window.undoColorButton, Qt.MouseButton.LeftButton)
QTest.mouseClick(window.undoColorButton, Qt.MouseButton.LeftButton)
assert model.trace_color == '#000000'
assert not window.undoColorButton.isEnabled()

# Background trace edits cannot change the selected trace or its visible color.
background = args(other_id, '#abcdef')
remote(lambda: set_trace_color(details, **background))
assert second_model.trace_color == '#abcdef'
assert window.current_tab_id == uid and button.getColor() == '#000000'
assert window.traceEditorView.model is model
assert window.redoColorButton.isEnabled() is False

# Round-trip the actual workspace format, including data and the saved IDs.
workspace_path = Path('workspace.json').resolve()
with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(workspace_path), '')):
    window.save_workspace()
saved = json.loads(workspace_path.read_text())
assert saved['order'] == [uid, other_id]
old_command = args()
with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(workspace_path), '')), \
     patch.object(QMessageBox, 'critical', side_effect=AssertionError('Workspace load failed')):
    window.load_workspace()
assert uid in core.traces and other_id in core.traces
assert core.traces[other_id].trace_color == '#abcdef'
assert core.history()['undo_count'] == core.history()['redo_count'] == 0
try:
    remote(lambda: set_trace_color(details, **old_command))
    raise AssertionError('Old workspace command accepted')
except ApiError as error:
    assert error.code == 'workspace_changed'

# Legacy/malformed identity lists get fresh, valid, distinct IDs on load.
for order in ([uid, uid], [], ['invalid', None]):
    saved['order'] = order
    workspace_path.write_text(json.dumps(saved))
    with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(workspace_path), '')), \
         patch.object(QMessageBox, 'critical', side_effect=AssertionError('Legacy load failed')):
        window.load_workspace()
    ids = [key for key in core.traces if key != 'setup-menu-id']
    assert len(ids) == len(set(ids)) == 2
    assert all(UUID(key) for key in ids)

dialog.stop()
dialog.toggle.click()
assert not dialog.api.edit_enabled and not dialog.allow_edit.isChecked()
window.close()
assert not dialog.api.running
print('SHARED_COLOR_GUI_OK')
'''
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "MPLBACKEND": "Agg"}
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(root), env.get("PYTHONPATH")]))
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'SHARED_COLOR_GUI_OK' in result.stdout
