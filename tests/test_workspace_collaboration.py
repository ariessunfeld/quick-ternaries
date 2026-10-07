"""Real-window collaboration through official MCP, Qt editors, and rendering."""
import os
from pathlib import Path
import subprocess
import sys


def test_workspace_collaboration_in_real_window(tmp_path):
    script = r'''
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from time import monotonic, sleep
from uuid import uuid4
from unittest.mock import patch

from mcp import Client
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QToolBar, QStatusBar
from quick_ternaries.app import MainWindow
from quick_ternaries.agent_api.mcp import create_server
from quick_ternaries.agent_api.session import Session
from quick_ternaries.agent_api.client import read, command
from quick_ternaries.agent_api.contract import ApiError
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata

app = QApplication([])
window = MainWindow()
window.show()
app.processEvents()
assert not window.findChildren(QToolBar)
assert not window.findChildren(QStatusBar)
commands = window.workspace_commands
core = window.workspace_session
assert commands.undoAction.objectName() == 'workspace.undo'
assert commands.undoAction.shortcuts() and commands.redoAction.shortcuts()

def remote(callback):
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(callback)
        deadline = monotonic() + 15
        while not future.done() and monotonic() < deadline:
            app.processEvents()
            sleep(.001)
        assert future.done(), 'Agent request did not complete'
        return future.result()

def wait(predicate, seconds=20):
    deadline = monotonic() + seconds
    while not predicate() and monotonic() < deadline:
        app.processEvents()
        sleep(.005)
    assert predicate(), commands.render.status()

path = Path('synthetic.csv').resolve()
path.write_text('A,B,C,Sample,Temperature\n70,20,10,Alpha,400\n20,70,10,Beta,600\n10,20,70,Alpha,800\n')
metadata = DataFileMetadata(str(path), header_row=0)
assert window.setupMenuModel.data_library.add_file(metadata)
window.setupController.update_axis_options()
window.settingsButton.click()
window.settings_dialog.agentButton.click()
dialog = window.agent_dialog
dialog.toggle.click()
assert not dialog.api.edit_enabled
dialog.allow_edit.click()
assert dialog.api.edit_enabled
assert window.settings_dialog.agentButton.text() == 'Agent API: Editing'
details = dialog.api.connection_details()
dialog.close()
window.settings_dialog.close()
window.activateWindow()
app.processEvents()
server = create_server(Session(lambda: details))

async def create_and_configure():
    async with Client(server) as client:
        assert not (await client.call_tool('connect_from_clipboard')).is_error
        overview = (await client.call_tool('get_workspace_overview')).structured_content['result']
        workspace = (await client.call_tool('get_edit_state')).structured_content['state']
        created = await client.call_tool('change_trace_structure', dict(operation='create_trace',
            arguments={'source_id': overview['datasets'][0]['id'], 'name': 'Agent sample'},
            workspace_epoch=workspace['workspace_epoch'], expected_revision=workspace['workspace_revision'], request_id=str(uuid4())))
        assert not created.is_error, created
        uid = created.structured_content['receipt']['result']['trace_id']
        state = (await client.call_tool('get_edit_state', {'target': 'trace', 'trace_id': uid})).structured_content['state']
        plot = (await client.call_tool('get_edit_state', {'target': 'plot'})).structured_content['state']
        changes = {'trace_name': 'Alpha samples', 'trace_color': '#377eb8', 'point_size': 12,
                   'heatmap_on': True, 'heatmap_column': 'Temperature', 'heatmap_min': 400, 'heatmap_max': 800,
                   'filters_on': True, 'filters': [{'filter_name': 'Alpha only', 'filter_column': 'Sample',
                       'filter_operation': 'is', 'filter_value1': 'Alpha', 'filter_value2': ''}]}
        axes = {'title': 'Agent and human', 'top_axis': ['A'], 'left_axis': ['B'], 'right_axis': ['C']}
        edits = [{'target': 'trace', 'trace_id': uid, 'changes': changes,
                  'expected_revisions': {k: state['field_revisions'][k] for k in changes}},
                 {'target': 'plot', 'trace_id': None, 'changes': axes,
                  'expected_revisions': {k: plot['field_revisions'][k] for k in axes}}]
        result = await client.call_tool('apply_edits', dict(edits=edits, workspace_epoch=state['workspace_epoch'], request_id=str(uuid4())))
        assert not result.is_error, result
        # Focused edit-state reads keep schemas and values small.
        small = await client.call_tool('get_edit_state', {'target': 'trace', 'trace_id': uid, 'fields': ['point_size']})
        assert list(small.structured_content['state']['values']) == ['point_size']
        return uid
uid = remote(lambda: asyncio.run(create_and_configure()))
assert window.current_tab_id == 'setup-menu-id'  # Agent never steals selection.
model = core.traces[uid]
assert model.point_size == 12 and model.filters[0].filter_column == 'Sample'
assert window.setupMenuModel.axis_members.top_axis == ['A']
assert core.history()['undo_count'] >= 2
assert core.history()['undo_label'] == 'Edit workspace'
commands.undoAction.trigger()
assert model.point_size != 12 and window.setupMenuModel.plot_labels.title == ''
commands.redoAction.trigger()
assert model.point_size == 12 and window.setupMenuModel.plot_labels.title == 'Agent and human'

window.tabPanel.select_tab_by_id(uid)
window.on_tab_selected(uid)
app.processEvents()
assert core.history()['undo_label'] == 'Edit workspace', 'Opening the editor created or invalidated history'
name = window.traceEditorView.widgets['trace_name']
window.activateWindow()
name.setFocus()
name.selectAll()
QTest.keyClicks(name, 'Human label in progress')
name.setSelection(6, 5)
app.processEvents()
assert app.focusWidget() is name
before = (name.text(), name.cursorPosition(), name.selectionStart(), name.selectedText(), window.current_tab_id)

def patch_trace(values, request_id=None, state=None):
    state = state or remote(lambda: read(details, 'edit-state', target='trace', trace_id=uid))['state']
    payload = dict(edits=[{'target': 'trace', 'trace_id': uid, 'changes': values,
                          'expected_revisions': {k: state['field_revisions'][k] for k in values}}],
                   workspace_epoch=state['workspace_epoch'], request_id=request_id or str(uuid4()))
    return payload
payload = patch_trace({'point_size': 18, 'trace_color': '#123456'})
remote(lambda: command(details, 'apply_edits', **payload))
assert before == (name.text(), name.cursorPosition(), name.selectionStart(), name.selectedText(), window.current_tab_id)
assert app.focusWidget() is name and window.traceEditorView.widgets['trace_name'] is name
assert window.traceEditorView.widgets['trace_color'].getColor() == '#123456'
try:
    busy = patch_trace({'trace_name': 'Overwrite'})
    remote(lambda: command(details, 'apply_edits', **busy))
    raise AssertionError('Agent overwrote pending human input')
except ApiError as error:
    assert error.code == 'editor_busy'
# Native text undo remains native and does not undo the agent's appearance edit.
QTest.keySequence(name, QKeySequence(QKeySequence.StandardKey.Undo))
assert model.point_size == 18 and model.trace_name == 'Alpha samples'
QTest.keySequence(name, QKeySequence(QKeySequence.StandardKey.Redo))
assert model.trace_name == 'Human label in progress'
window.previewButton.setFocus()
app.processEvents()
# A standard menu action shares history with agents.
commands.undoAction.trigger()
assert model.point_size == 12 and model.trace_name == 'Human label in progress'
commands.undoAction.trigger()
assert model.trace_name == 'Alpha samples'
replay = remote(lambda: command(details, 'apply_edits', **payload))
assert replay['receipt']['replayed'] and model.point_size == 12
commands.redoAction.trigger()
commands.redoAction.trigger()
assert model.point_size == 18
# Native workspace shortcuts operate when a text editor has no local undo.
QTest.keySequence(window.previewButton, QKeySequence(QKeySequence.StandardKey.Undo))
assert model.point_size == 12
QTest.keySequence(window.previewButton, QKeySequence(QKeySequence.StandardKey.Redo))
assert model.point_size == 18
# A fresh command cannot reuse an old same-field revision after undo/redo.
try:
    remote(lambda: command(details, 'apply_edits', **{**payload, 'request_id': str(uuid4())}))
    raise AssertionError('Stale field revisions accepted')
except ApiError as error:
    assert error.code == 'edit_conflict'

# A partially typed number is also protected without blocking unrelated fields.
window.traceEditorView.widgets['show_advanced_settings_on'].setChecked(True)
size = window.traceEditorView.widgets['point_size']
size.setFocus()
size.lineEdit().selectAll()
QTest.keyClicks(size.lineEdit(), '23')
size.lineEdit().setModified(True)
try:
    busy = patch_trace({'point_size': 24})
    remote(lambda: command(details, 'apply_edits', **busy))
    raise AssertionError('Agent overwrote unfinished number')
except ApiError as error:
    assert error.code == 'editor_busy'
window.previewButton.setFocus()
app.processEvents()
remote(lambda: command(details, 'apply_edits', **patch_trace({'point_size': 18})))

# Human filters enter the same history, with no model writes on editor rebuild.
view = window.traceEditorView
count = len(model.filters)
view.on_filter_add_requested()
assert len(model.filters) == count + 1
window.previewButton.setFocus()
commands.undoAction.trigger()
assert len(model.filters) == count
commands.redoAction.trigger()
assert len(model.filters) == count + 1
with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
    view.on_filter_remove_requested(count)
assert len(model.filters) == count
commands.undoAction.trigger()
assert len(model.filters) == count + 1
commands.redoAction.trigger()
assert len(model.filters) == count

# Trace lifecycle is reversible and preserves existing work/identity.
state = remote(lambda: read(details, 'edit-state'))['state']
created = remote(lambda: command(details, 'duplicate_trace', arguments={'source_id': uid, 'name': 'Copy'},
    workspace_epoch=state['workspace_epoch'], expected_revision=state['workspace_revision'], request_id=str(uuid4())))
other = created['receipt']['result']['trace_id']
assert other != uid and window.current_tab_id == uid
assert core.traces[other].filters is not model.filters
assert core.traces[other].error_entry_model is not model.error_entry_model
commands.undoAction.trigger()
assert other not in core.traces
commands.redoAction.trigger()
assert other in core.traces
state = remote(lambda: read(details, 'edit-state'))['state']
remote(lambda: command(details, 'delete_trace', arguments={'trace_id': other}, workspace_epoch=state['workspace_epoch'],
                       expected_revision=state['workspace_revision'], request_id=str(uuid4())))
assert other not in core.traces and window.current_tab_id == uid
commands.undoAction.trigger()
assert other in core.traces

# Real Plotly render, including browser initialization and retry deduplication.
state = remote(lambda: read(details, 'edit-state'))['state']
render_args = dict(workspace_epoch=state['workspace_epoch'], expected_revision=state['workspace_revision'], request_id=str(uuid4()))
queued = remote(lambda: command(details, 'render_plot', **render_args))
wait(lambda: commands.render.status()['status'] in ('rendered', 'failed'))
status = remote(lambda: read(details, 'render-status'))['render']
assert status['status'] == 'rendered', status
assert not status['stale']
again = remote(lambda: command(details, 'render_plot', **render_args))
assert again['receipt']['replayed']
assert commands.render.status()['job_id'] == queued['receipt']['result']['job_id']
assert Path(commands.render.directory.name).is_dir()
assert not window.findChildren(QStatusBar)

# Plot/scientific settings share the same transaction and survive reload.
plot = remote(lambda: read(details, 'edit-state', target='plot'))['state']
values = {'plot_type': 'cartesian', 'x_axis': ['A'], 'y_axis': ['B'], 'font_size': 18,
          'scaling_factors': {'x_axis': {'A': 2}}, 'formulas': {'x_axis': {'A': 'SiO2'}}}
args = dict(edits=[{'target': 'plot', 'trace_id': None, 'changes': values,
                   'expected_revisions': {k: plot['field_revisions'][k] for k in values}}],
            workspace_epoch=plot['workspace_epoch'], request_id=str(uuid4()))
remote(lambda: command(details, 'apply_edits', **args))
assert window.plotTypeSelector.currentText() == 'Cartesian'
assert window.setupMenuModel.column_scaling.scaling_factors['x_axis']['A'] == 2
assert commands.render.status()['stale']
commands.undoAction.trigger()
assert window.plotTypeSelector.currentText() == 'Ternary'
commands.redoAction.trigger()
assert window.plotTypeSelector.currentText() == 'Cartesian'

# Persist data/identities, then invalidate old epoch and history on replacement.
workspace_path = Path('workspace.json').resolve()
with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(workspace_path), '')):
    window.save_workspace()
saved = json.loads(workspace_path.read_text())
assert saved['order'] == core.order
old = patch_trace({'point_size': 22})
with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(workspace_path), '')), \
     patch.object(QMessageBox, 'critical', side_effect=AssertionError('Load failed')):
    window.load_workspace()
assert uid in core.traces and core.traces[uid].point_size == 18
assert window.plotTypeSelector.currentText() == 'Cartesian'
assert window.setupMenuModel.chemical_formulas.formulas['x_axis']['A'] == 'SiO2'
assert window.setupMenuModel.advanced_settings.font_size == 18
assert core.history()['undo_count'] == core.history()['redo_count'] == 0
try:
    remote(lambda: command(details, 'apply_edits', **old))
    raise AssertionError('Old workspace command accepted')
except ApiError as error:
    assert error.code == 'workspace_changed'
# Native axis convenience is part of the same reversible gesture.
old_hover = list(window.setupMenuModel.axis_members.hover_data)
commands.edit_plot({'x_axis': ['C']})
assert 'C' in window.setupMenuModel.axis_members.hover_data
commands.undoAction.trigger()
assert window.setupMenuModel.axis_members.hover_data == old_hover
assert window.setupMenuModel.axis_members.x_axis == ['A']
# A render validation failure returns a job outcome and never opens an agent modal.
commands.edit_plot({'x_axis': []})
state = core.edit_state()
with patch.object(QMessageBox, 'warning', side_effect=AssertionError('Agent opened a modal')):
    failed = remote(lambda: command(details, 'render_plot', workspace_epoch=state['workspace_epoch'],
        expected_revision=state['workspace_revision'], request_id=str(uuid4())))
    wait(lambda: commands.render.status()['status'] == 'failed')
assert commands.render.status()['error'] in ('render_failed', 'render_validation_failed')
# Revocation also cancels an agent render that has not started yet.
commands.render.queue('agent')
dialog._set_edit_permission(False)
assert commands.render.status()['status'] == 'cancelled'
app.processEvents()
assert commands.render.status()['status'] == 'cancelled'
# Historical workspaces with malformed/duplicate IDs still load with fresh UUIDs.
saved['order'] = ['legacy', 'legacy']
workspace_path.write_text(json.dumps(saved))
with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(workspace_path), '')):
    window.load_workspace()
assert len(set(core.order)) == 2
from uuid import UUID
assert all(UUID(item) for item in core.order)
window.close()
assert not dialog.api.running
print('WORKSPACE_COLLABORATION_OK')
'''
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'MPLBACKEND': 'Agg'}
    env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(root), env.get('PYTHONPATH')]))
    result = subprocess.run([sys.executable, '-u', '-X', 'faulthandler', '-c', script], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'WORKSPACE_COLLABORATION_OK' in result.stdout
