"""Exercise real Qt controls, shared commands and native workspace persistence."""

import os
from pathlib import Path
import subprocess
import sys


def test_advanced_heatmap_in_real_window(tmp_path):
    script = r'''
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog
from quick_ternaries.app import MainWindow
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.workspace.session import WorkspaceError
from quick_ternaries.agent_api.contract import TRACE_SECTIONS

app = QApplication([])
window = MainWindow()
window.show()
window.activateWindow()
app.processEvents()
core, commands = window.workspace_session, window.workspace_commands
path = Path('heatmap-data.csv').resolve()
path.write_text('SiO2,MgO,C\n10,1,5\n20,2,6\n30,3,7\n')
metadata = DataFileMetadata(str(path), header_row=0)
assert window.setupMenuModel.data_library.add_file(metadata)
window.setupController.update_axis_options()
commands.edit_plot({'top_axis': ['SiO2'], 'left_axis': ['MgO'], 'right_axis': ['C'],
                    'x_axis': ['SiO2'], 'y_axis': ['MgO']})
model = TraceEditorModel(datafile=metadata, trace_name='Heatmap sample')
uid = core.add_trace(model, record=True)
window.on_tab_selected(uid)
view = window.traceEditorView
view.widgets['heatmap_on'].setChecked(True)
assert model.heatmap_column == 'SiO2'
assert (model.heatmap_min, model.heatmap_max) == (10, 30)
assert not model.heatmap_calculation_on
assert view.widgets['heatmap_min'].decimals() == 2
assert not view.advanced_heatmap_container.isVisible()
before = deepcopy(model.to_dict())
view.update_from_model()
assert model.to_dict() == before, 'Refreshing must not migrate or reset saved settings'
view.widgets['heatmap_use_advanced'].setChecked(True)
view.widgets['heatmap_calculation_on'].setChecked(True)
assert model.heatmap_columns == ['SiO2']
assert model.heatmap_formulas == {'SiO2': 'SiO2'}
assert (model.heatmap_min, model.heatmap_max) == (10, 30)
assert view.heatmapCalculation.isVisible()
assert not view.widgets['heatmap_column'].isEnabled()
core.undo()
assert not model.heatmap_calculation_on and model.heatmap_columns == []
core.redo()
assert model.heatmap_calculation_on and model.heatmap_columns == ['SiO2']
old_formulas = view.heatmapCalculation.formulas.axis_sections['heatmap']
old_scales = view.heatmapCalculation.scaling.axis_sections['heatmap']
with patch.object(QInputDialog, 'getItem', return_value=('MgO', True)):
    view.heatmapCalculation.selector.addButton.click()
assert model.heatmap_columns == ['SiO2', 'MgO']
assert old_formulas.isHidden() and old_scales.isHidden()
assert view.widgets['heatmap_min'].decimals() == 10
view.heatmapCalculation.scaling.scale_inputs[('heatmap', 'SiO2')].setValue(2)
assert model.heatmap_scales == {'SiO2': 2}
assert window.setupMenuModel.column_scaling.get_scale('top_axis', 'SiO2') == 1
core.undo()
assert model.heatmap_scales == {}
core.redo()
assert model.heatmap_scales == {'SiO2': 2}
view.widgets['heatmap_range_mode'].setCurrentText('Full dataset')
assert view.widgets['heatmap_max'].isReadOnly()
assert view.widgets['heatmap_min'].value() == 21
assert view.widgets['heatmap_max'].value() == 63
assert (model.heatmap_min, model.heatmap_max) == (10, 30), 'Auto bounds must not overwrite stored manual bounds'
commands.edit_trace(model, {'filters_on': True, 'filters': [{'filter_name': 'subset',
    'filter_column': 'SiO2', 'filter_operation': '<', 'filter_value1': '30', 'filter_value2': ''}]})
view.widgets['heatmap_range_mode'].setCurrentText('Filtered data')
assert view.widgets['heatmap_max'].value() == 42
view.widgets['heatmap_use_advanced'].setChecked(False)
assert model.heatmap_calculation_on and model.heatmap_range_mode == 'Filtered data'
assert not view.advanced_heatmap_container.isVisible()
assert view.heatmapStatus.isVisible()
view.widgets['heatmap_use_advanced'].setChecked(True)
view.widgets['heatmap_range_mode'].setCurrentText('Manual')
assert not view.widgets['heatmap_max'].isReadOnly()
assert view.widgets['heatmap_max'].value() == 30
view.heatmapCalculation.molar.setChecked(True)
assert model.heatmap_molar and not model.convert_from_wt_to_molar
formula = view.heatmapCalculation.formulas.formula_inputs[('heatmap', 'SiO2')]
formula.setFocus()
app.processEvents()
formula.selectAll()
QTest.keyClicks(formula, 'invalid!')
assert model.heatmap_formulas['SiO2'] == 'invalid!'
assert 'valid chemical formula' in view.heatmapStatus.text()
with patch.object(window, '_render_warning') as warning:
    assert not window._render_plot()
    assert warning.call_args.args[1] == 'Invalid Heatmap'
formula.setModified(True)
try:
    commands.guard_edits([{'target': 'trace', 'trace_id': uid, 'changes': {'heatmap_scales': {}}}])
    raise AssertionError('An agent must not replace a pending formula edit')
except WorkspaceError as exc:
    assert exc.code == 'editor_busy'
formula.setText('SiO2')
formula.clearFocus()
app.processEvents()

# Agent edits use the same fields, validation, history and visible controls.
def agent_edit(changes):
    state = core.edit_state('trace', uid)
    return core.apply(workspace_epoch=state['workspace_epoch'], request_id=str(uuid4()),
        edits=[{'target': 'trace', 'trace_id': uid, 'changes': changes,
                'expected_revisions': {k: state['field_revisions'][k] for k in changes}}])
try:
    agent_edit({'heatmap_formulas': {'SiO2': 'bad!', 'MgO': 'MgO'}})
    raise AssertionError('Invalid chemical formulas must reject agent transactions')
except WorkspaceError as exc:
    assert exc.code == 'invalid_command'
agent_edit({'heatmap_scales': {'SiO2': 3}, 'heatmap_range_mode': 'Filtered data'})
assert view.heatmapCalculation.scaling.scale_inputs[('heatmap', 'SiO2')].value() == 3
assert all(k in TRACE_SECTIONS['heatmap'] for k in ('heatmap_columns', 'heatmap_formulas', 'heatmap_range_mode'))
core.undo()
assert model.heatmap_scales == {'SiO2': 2}
core.redo()
assert model.heatmap_scales == {'SiO2': 3}

# Real duplication command must not share mutable scientific settings.
copy_id = commands.trace_command('duplicate_trace', {'source_id': uid, 'name': 'Copy'}, None)['trace_id']
duplicate = core.traces[copy_id]
assert duplicate.heatmap_columns == model.heatmap_columns
assert duplicate.heatmap_columns is not model.heatmap_columns
assert duplicate.heatmap_scales is not model.heatmap_scales
assert duplicate.heatmap_formulas is not model.heatmap_formulas

# Exercise the application's save path, not only dataclass serialization.
saved = Path('advanced-workspace.json').resolve()
expected = {k: deepcopy(getattr(model, k)) for k in TRACE_SECTIONS['heatmap']}
with patch.object(QFileDialog, 'getSaveFileName', return_value=(str(saved), 'JSON Files (*.json)')):
    window.save_workspace()
with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(saved), 'JSON Files (*.json)')):
    window.load_workspace()
loaded = next(m for m in core.traces.values() if m is not None and m.trace_name == 'Heatmap sample')
assert {k: getattr(loaded, k) for k in expected} == expected
new_uid = next(k for k, m in core.traces.items() if m is loaded)
window.on_tab_selected(new_uid)
assert window.traceEditorView.widgets['heatmap_max'].isReadOnly()

# Save/load/refresh must not silently repair invalid or missing input columns.
window.workspace_commands.edit_trace(loaded, {'heatmap_columns': ['absent']})
assert loaded.heatmap_columns == ['absent']
assert 'missing' in window.traceEditorView.heatmapStatus.text()

# The native loader must preserve an old file's edited limits, even with the
# old advanced-settings disclosure open. New controls remain disabled.
old_file = json.loads(saved.read_text())
new_fields = ('heatmap_calculation_on', 'heatmap_columns', 'heatmap_scales',
              'heatmap_formulas', 'heatmap_molar', 'heatmap_range_mode')
for trace in old_file['traces']:
    for field in new_fields:
        trace.pop(field)
    trace.update(heatmap_min=.125, heatmap_max=99.625)
saved.write_text(json.dumps(old_file))
with patch.object(QFileDialog, 'getOpenFileName', return_value=(str(saved), 'JSON Files (*.json)')):
    window.load_workspace()
legacy = next(m for m in core.traces.values() if m is not None and m.trace_name == 'Heatmap sample')
assert not legacy.heatmap_calculation_on and not legacy.heatmap_molar
assert legacy.heatmap_range_mode == 'Manual'
assert (legacy.heatmap_min, legacy.heatmap_max) == (.125, 99.625)
window.close()
print('HEATMAP_WORKSPACE_OK')
'''
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'MPLBACKEND': 'Agg', 'PYTHONPATH': str(root)}
    result = subprocess.run([sys.executable, '-u', '-X', 'faulthandler', '-c', script],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'HEATMAP_WORKSPACE_OK' in result.stdout
