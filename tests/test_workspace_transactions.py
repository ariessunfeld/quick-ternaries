"""Transaction invariants independent of Qt, sockets or widgets."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest

from quick_ternaries.workspace.schema import Field
from quick_ternaries.workspace.session import WorkspaceSession, WorkspaceError, Resource


def make_edit(core, uid, values):
    state = core.edit_state('trace', uid)
    return {'target': 'trace', 'trace_id': uid, 'changes': values,
            'expected_revisions': {k: state['field_revisions'][k] for k in values}}


def apply(core, edits, **kwargs):
    return core.apply(edits=edits, workspace_epoch=core.epoch, request_id=str(uuid4()), **kwargs)


@pytest.fixture
def workspace():
    core = WorkspaceSession()
    a = core.add_trace(SimpleNamespace(trace_name='A', trace_color='#000000', point_size=5))
    b = core.add_trace(SimpleNamespace(trace_name='B', trace_color='#ffffff', point_size=10))
    return core, a, b


def test_atomic_multi_object_validation_conflict_and_history(workspace):
    core, a, b = workspace
    edits = [make_edit(core, a, {'trace_color': '#abcdef', 'trace_name': 'Renamed'}),
             make_edit(core, b, {'point_size': 14})]
    invalid = deepcopy(edits)
    invalid[1]['changes']['point_size'] = -1
    with pytest.raises(WorkspaceError):
        apply(core, invalid)
    assert core.traces[a].trace_name == 'A' and core.history()['undo_count'] == 0
    core.human_edit('trace', b, {'point_size': 12})
    with pytest.raises(WorkspaceError) as error:
        apply(core, edits)
    assert error.value.code == 'edit_conflict'
    assert core.traces[a].trace_name == 'A'
    edits[1] = make_edit(core, b, {'point_size': 14})
    apply(core, edits)
    assert core.history()['undo_count'] == 2
    core.undo()
    assert core.traces[a].trace_name == 'A' and core.traces[b].point_size == 12
    core.redo()
    assert core.traces[a].trace_name == 'Renamed' and core.traces[b].point_size == 14


def test_field_granularity_aba_and_retry_after_undo(workspace):
    core, a, b = workspace
    pending = make_edit(core, a, {'trace_color': '#abcdef'})
    core.human_edit('trace', a, {'trace_name': 'Human name'})
    request = str(uuid4())
    receipt = core.apply(edits=[pending], workspace_epoch=core.epoch, request_id=request)
    core.undo()
    replay = core.apply(edits=[pending], workspace_epoch=core.epoch, request_id=request)
    assert replay == {**receipt, 'replayed': True}
    assert core.traces[a].trace_color == '#000000'
    with pytest.raises(WorkspaceError) as error:
        apply(core, [pending])
    assert error.value.code == 'edit_conflict'  # Undo restored value, not revision.
    assert core.traces[a].trace_name == 'Human name'


def test_noop_receipt_is_historical_too(workspace):
    core, a, _ = workspace
    edit = make_edit(core, a, {'trace_color': '#000000'})
    request = str(uuid4())
    result = core.apply(edits=[edit], workspace_epoch=core.epoch, request_id=request)
    core.human_edit('trace', a, {'trace_color': '#abcdef'})
    replay = core.apply(edits=[edit], workspace_epoch=core.epoch, request_id=request)
    assert replay == {**result, 'replayed': True}
    assert replay['changes'][0]['values']['trace_color'] == '#000000'
    assert not replay['applied']


def test_human_typing_coalesces_without_absorbing_an_agent_command(workspace):
    core, a, _ = workspace
    for text in ('H', 'He', 'Hello'):
        core.human_edit('trace', a, {'trace_name': text}, merge_key='gesture1')
    assert core.history()['undo_count'] == 1
    apply(core, [make_edit(core, a, {'trace_color': '#abcdef'})])
    core.human_edit('trace', a, {'trace_name': 'Hello!'}, merge_key='gesture1')
    assert core.history()['undo_count'] == 3
    core.undo()
    assert core.traces[a].trace_name == 'Hello'
    core.undo()
    assert core.traces[a].trace_color == '#000000'
    core.undo()
    assert core.traces[a].trace_name == 'A'


def test_trace_lifecycle_order_and_revision_survive_undo(workspace):
    core, a, b = workspace
    old = make_edit(core, a, {'point_size': 9})
    core.remove_trace(a, record=True)
    assert core.order == [b]
    core.undo()
    assert core.order == [a, b]
    with pytest.raises(WorkspaceError) as error:
        apply(core, [old])
    assert error.value.code == 'edit_conflict'
    core.reorder([b, a])
    core.undo()
    assert core.order == [a, b]
    c = core.add_trace(SimpleNamespace(trace_name='C', trace_color='#111111'), record=True)
    core.human_edit('trace', c, {'trace_color': '#222222'})
    core.undo()
    core.undo()
    assert c not in core.traces
    core.redo()
    core.redo()
    assert core.traces[c].trace_color == '#222222'


def test_guarded_history_rejects_newer_human_change_and_deduplicates(workspace):
    core, a, _ = workspace
    apply(core, [make_edit(core, a, {'point_size': 9})])
    old_revision = core.revision
    core.human_edit('trace', a, {'trace_name': 'Human'})
    with pytest.raises(WorkspaceError) as error:
        core.control(operation='undo', workspace_epoch=core.epoch, expected_revision=old_revision, request_id=str(uuid4()))
    assert error.value.code == 'edit_conflict'
    revision, request = core.revision, str(uuid4())
    result = core.control(operation='undo', workspace_epoch=core.epoch, expected_revision=revision, request_id=request)
    replay = core.control(operation='undo', workspace_epoch=core.epoch, expected_revision=revision, request_id=request)
    assert replay == {**result, 'replayed': True}
    assert core.traces[a].point_size == 9 and core.traces[a].trace_name == 'A'


def test_adapter_failure_rolls_back_whole_transaction(workspace):
    core, a, _ = workspace
    values = {'title': 'Original'}
    def write(changes):
        values.update(changes)
        if values['title'] == 'Fail':
            raise RuntimeError('adapter failure')
    core.register('plot', None, Resource(lambda: dict(values), write, {'title': Field('string')}))
    edits = [make_edit(core, a, {'trace_name': 'Changed'}),
             {'target': 'plot', 'trace_id': None, 'changes': {'title': 'Fail'}, 'expected_revisions': {'title': 0}}]
    with pytest.raises(RuntimeError):
        apply(core, edits)
    assert core.traces[a].trace_name == 'A' and values['title'] == 'Original'
    assert core.revision == 0 and core.history()['undo_count'] == 0


def test_additional_read_preconditions_protect_scientific_assumptions(workspace):
    core, a, _ = workspace
    edit = make_edit(core, a, {'trace_color': '#abcdef'})
    edit['expected_revisions']['point_size'] = 0
    core.human_edit('trace', a, {'point_size': 9})
    with pytest.raises(WorkspaceError) as error:
        apply(core, [edit])
    assert error.value.code == 'edit_conflict'
    assert core.traces[a].trace_color == '#000000'


@pytest.mark.parametrize('operation', ['edit', 'undo', 'create_trace'])
def test_success_receipt_precedes_observer_failure(workspace, operation):
    core, a, _ = workspace
    core.human_edit('trace', a, {'point_size': 9})
    def observer(event):
        raise RuntimeError('UI observer failed after commit')
    core.changed = observer
    request, revision = str(uuid4()), core.revision
    edit = make_edit(core, a, {'point_size': 12})
    def run():
        if operation == 'edit':
            return core.apply(edits=[edit], workspace_epoch=core.epoch, request_id=request)
        return core.control(operation=operation, workspace_epoch=core.epoch,
            expected_revision=revision, request_id=request,
            execute=(lambda: core.add_trace(SimpleNamespace(trace_name='New'), record=True, actor='agent'))
                    if operation == 'create_trace' else None)
    with pytest.raises(RuntimeError):
        run()
    state = core.edit_state()
    assert run()['replayed']
    assert core.edit_state() == state


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), 10**1000, '12', -1])
def test_numeric_fields_reject_invalid_values_atomically(workspace, value):
    core, a, _ = workspace
    with pytest.raises(WorkspaceError):
        apply(core, [make_edit(core, a, {'point_size': value, 'trace_name': 'Bad'})])
    assert core.traces[a].trace_name == 'A' and core.history()['undo_count'] == 0
