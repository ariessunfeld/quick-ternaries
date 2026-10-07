"""Workspace transactions, optimistic concurrency and history, independent of Qt.

Adapters register typed resources. A transaction validates every candidate before
writing any model, records one history entry, then emits one change notification.
Observation cursors, field revisions and document history have distinct lifetimes.
"""

from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from uuid import UUID, uuid4

from .schema import Field, TRACE_FIELDS, field_label

HISTORY_LIMIT = 100
RECEIPT_LIMIT = 128
MAX_EDITS = 32


class WorkspaceError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code, self.details = code, details or {}


@dataclass
class Resource:
    read: Callable[[], dict]
    write: Callable[[dict], None]
    fields: dict[str, Field]
    validate: Callable[[dict, set, str], None] = lambda values, changed, actor: None


@dataclass
class Change:
    target: str
    trace_id: str | None
    before: dict
    after: dict


@dataclass
class Command:
    changes: list[Change]
    label: str
    actor: str
    merge_key: object = None


class WorkspaceSession:
    def __init__(self):
        self.traces = {}
        self.order = []
        self.epoch = str(uuid4())
        self.revision = 0
        self._resources = {}
        self._known = {}
        self._revisions = {}
        self._undo, self._redo = [], []
        self._receipts = OrderedDict()
        self.changed = lambda event: None
        self._deferred_notifications = None
        self.trace_resource = self._default_trace_resource

    @staticmethod
    def _default_trace_resource(model):
        schema = {k: f for k, f in TRACE_FIELDS.items() if hasattr(model, k) and k != 'filters'}
        return Resource(lambda: {k: deepcopy(getattr(model, k)) for k in schema},
                        lambda values: [setattr(model, k, deepcopy(v)) for k, v in values.items()], schema)

    def register(self, target, trace_id, resource, *, restored=False):
        key = (target, trace_id)
        self._resources[key] = resource
        self._known[key] = deepcopy(resource.read())
        self._revisions[key] = {k: self.revision + 1 if restored else 0 for k in resource.fields}

    def reset(self):
        self.epoch = str(uuid4())
        self.revision = 0
        self._receipts.clear()
        self._clear_history()
        for key, resource in self._resources.items():
            self._known[key] = deepcopy(resource.read())
            self._revisions[key] = {k: 0 for k in resource.fields}

    def _clear_history(self):
        self._undo.clear()
        self._redo.clear()

    def add_trace(self, model, trace_id=None, *, record=False, actor='human'):
        uid = str(UUID(trace_id)) if trace_id else str(uuid4())
        if uid in self.traces:
            raise WorkspaceError('duplicate_trace', 'Trace identity is already present.')
        if record:
            self._commit([Change('structure', None, {'models': {uid: None}, 'order': list(self.order)},
                                 {'models': {uid: model}, 'order': [*self.order, uid]})], 'Add trace', actor)
        else:
            self.traces[uid] = model
            self.order.append(uid)
            self.register('trace', uid, self.trace_resource(model))
            self._clear_history()
        return uid

    def remove_trace(self, trace_id, *, record=False, actor='human'):
        if trace_id not in self.traces:
            return
        if record:
            self._commit([Change('structure', None, {'models': {trace_id: self.traces[trace_id]}, 'order': list(self.order)},
                                 {'models': {trace_id: None}, 'order': [i for i in self.order if i != trace_id]})], 'Delete trace', actor)
        else:
            self.traces.pop(trace_id, None)
            self.order = [i for i in self.order if i != trace_id]
            for mapping in (self._resources, self._known, self._revisions):
                mapping.pop(('trace', trace_id), None)
            self._clear_history()

    def reorder(self, order, *, actor='human'):
        if (not isinstance(order, list) or not all(isinstance(uid, str) for uid in order)
                or len(order) != len(self.order) or set(order) != set(self.order)):
            raise WorkspaceError('invalid_command', 'Supply every trace ID exactly once.')
        if order != self.order:
            self._commit([Change('structure', None, {'models': {}, 'order': list(self.order)},
                                 {'models': {}, 'order': list(order)})], 'Reorder traces', actor)

    def committed_value(self, target, trace_id, field):
        return deepcopy(self._known[(target, trace_id)][field])

    def _resource(self, target, trace_id):
        key = (target, trace_id)
        if key not in self._resources:
            raise WorkspaceError('trace_not_found' if target == 'trace' else 'invalid_command', 'Editable object is unavailable.')
        resource = self._resources[key]
        current = resource.read()
        changed = [k for k in resource.fields if current[k] != self._known[key][k]]
        if changed:
            # A legacy path changed exposed fields outside commands. Never apply
            # history over such changes. Migrated view updates avoid this path.
            self.revision += 1
            for field in changed:
                self._revisions[key][field] += 1
            self._known[key] = deepcopy(current)
            self._clear_history()
        return resource, current

    def edit_state(self, target='workspace', trace_id=None):
        if target not in ('workspace', 'plot', 'trace') or (target != 'trace' and trace_id is not None):
            raise WorkspaceError('invalid_command', 'Use a trace ID only with the trace target.')
        if target == 'workspace':
            self.synchronize()
            return {'workspace_epoch': self.epoch, 'workspace_revision': self.revision,
                    'trace_order': list(self.order), 'revision_scope': 'editable_workspace', 'history': self.history()}
        resource, values = self._resource(target, trace_id)
        return {'workspace_epoch': self.epoch, 'workspace_revision': self.revision,
                'target': target, 'trace_id': trace_id, 'values': deepcopy(values), 'revision_scope': 'per_field',
                'field_revisions': dict(self._revisions[(target, trace_id)]),
                'schema': {k: f.describe() for k, f in resource.fields.items()}}

    def synchronize(self):
        for key in list(self._resources):
            self._resource(*key)

    def _envelope(self, workspace_epoch, request_id):
        try:
            UUID(workspace_epoch)
            UUID(request_id)
        except (ValueError, TypeError, AttributeError):
            raise WorkspaceError('invalid_command', 'Use the current workspace epoch and a new request UUID.') from None
        if workspace_epoch != self.epoch:
            raise WorkspaceError('workspace_changed', 'Workspace was replaced. Read current state.')

    def _replay(self, request_id, arguments):
        if request_id in self._receipts:
            old, receipt = self._receipts[request_id]
            if old != arguments:
                raise WorkspaceError('request_id_reused', 'Request ID already used with different arguments.')
            return {**deepcopy(receipt), 'replayed': True}

    def _remember(self, request_id, arguments, result):
        self._receipts[request_id] = (deepcopy(arguments), deepcopy(result))
        while len(self._receipts) > RECEIPT_LIMIT:
            self._receipts.popitem(last=False)
        return result

    def apply(self, *, edits, workspace_epoch, request_id, actor='agent', merge_key=None):
        self._envelope(workspace_epoch, request_id)
        if actor not in ('human', 'agent') or not isinstance(edits, list) or not 1 <= len(edits) <= MAX_EDITS:
            raise WorkspaceError('invalid_command', 'Provide 1–32 typed edits.')
        arguments = {'edits': edits, 'actor': actor, 'workspace_epoch': workspace_epoch}
        replay = self._replay(request_id, arguments)
        if replay is not None:
            return replay
        changes, returned, touched = [], [], set()
        for edit in edits:
            if not isinstance(edit, dict) or set(edit) != {'target', 'trace_id', 'changes', 'expected_revisions'}:
                raise WorkspaceError('invalid_command', 'Each edit needs target, trace_id, changes and expected_revisions.')
            target, uid, values, expected = (edit[k] for k in ('target', 'trace_id', 'changes', 'expected_revisions'))
            if target not in ('trace', 'plot') or (target == 'plot' and uid is not None):
                raise WorkspaceError('invalid_command', 'Use a trace ID or the plot target with trace_id=null.')
            if target == 'trace' and not isinstance(uid, str):
                raise WorkspaceError('invalid_command', 'Trace ID must be a string.')
            key = (target, uid)
            if key in touched:
                raise WorkspaceError('invalid_command', 'Combine each object’s fields into one edit.')
            touched.add(key)
            resource, current = self._resource(target, uid)
            if (not isinstance(values, dict) or not values or values.keys() - resource.fields.keys()
                    or not isinstance(expected, dict) or values.keys() - expected.keys()
                    or expected.keys() - resource.fields.keys()):
                raise WorkspaceError('invalid_command', 'Use editable fields and a revision for each changed field.')
            normalized = {}
            for field in expected:
                if type(expected[field]) is not int or expected[field] < 0:
                    raise WorkspaceError('invalid_command', 'Field revisions must be nonnegative integers.')
                if expected[field] != self._revisions[key][field]:
                    raise WorkspaceError('edit_conflict', 'A requested field changed. Inspect it before another edit.',
                                         {'target': target, 'trace_id': uid, 'field': field})
            for field, value in values.items():
                try:
                    normalized[field] = resource.fields[field].validate(deepcopy(value))
                except (ValueError, TypeError):
                    raise WorkspaceError('invalid_command', f'Invalid value for {field}. Read its editable schema.') from None
            candidate = {**current, **normalized}
            resource.validate(candidate, set(normalized), actor)
            returned.append(Change(target, uid, {}, normalized))
            effective = {k: v for k, v in normalized.items() if v != current[k]}
            if effective:
                changes.append(Change(target, uid, {k: deepcopy(current[k]) for k in effective}, effective))
        label = ('Change ' + field_label(next(iter(changes[0].after)))
                 if len(changes) == 1 and len(changes[0].after) == 1 else 'Edit workspace')
        if changes:
            self._commit(changes, label, actor, merge_key=merge_key, notify=False)
        result = {'workspace_epoch': self.epoch, 'workspace_revision': self.revision,
                  'request_id': request_id, 'actor': actor, 'applied': bool(changes), 'replayed': False,
                  'changes': [{'target': c.target, 'trace_id': c.trace_id, 'values': deepcopy(c.after),
                               'field_revisions': {k: self._revisions[(c.target, c.trace_id)][k] for k in c.after}}
                              for c in returned], 'render_required': True}
        self._remember(request_id, arguments, result)
        if changes:
            self._notify(changes, actor)
        return result

    def human_edit(self, target, trace_id, changes, *, merge_key=None):
        state = self.edit_state(target, trace_id)
        return self.apply(edits=[{'target': target, 'trace_id': trace_id, 'changes': changes,
                                 'expected_revisions': {k: state['field_revisions'][k] for k in changes}}],
                          workspace_epoch=self.epoch, request_id=str(uuid4()), actor='human', merge_key=merge_key)

    def _write(self, change, values):
        if change.target == 'structure':
            for uid, model in values['models'].items():
                if model is None:
                    self.traces.pop(uid, None)
                    for mapping in (self._resources, self._known, self._revisions):
                        mapping.pop(('trace', uid), None)
                else:
                    self.traces[uid] = model
                    self.register('trace', uid, self.trace_resource(model), restored=True)
            self.order = list(values['order'])
        else:
            self._resources[(change.target, change.trace_id)].write(deepcopy(values))

    def _apply_changes(self, changes, reverse=False):
        done = []
        try:
            for change in changes:
                done.append(change)
                self._write(change, change.before if reverse else change.after)
        except Exception:
            for change in reversed(done):
                self._write(change, change.after if reverse else change.before)
            raise
        self.revision += 1
        for change in changes:
            if change.target != 'structure':
                key = (change.target, change.trace_id)
                self._known[key] = deepcopy(self._resources[key].read())
                for field in change.after:
                    self._revisions[key][field] += 1

    def _commit(self, changes, label, actor, *, merge_key=None, notify=True):
        self._apply_changes(changes)
        previous = self._undo[-1] if self._undo else None
        if (merge_key is not None and previous and previous.merge_key == merge_key
                and previous.actor == actor == 'human' and len(changes) == len(previous.changes) == 1
                and changes[0].target == previous.changes[0].target
                and changes[0].trace_id == previous.changes[0].trace_id
                and changes[0].after.keys() == previous.changes[0].after.keys()):
            previous.changes[0].after = deepcopy(changes[0].after)
            if previous.changes[0].before == previous.changes[0].after:
                self._undo.pop()
        else:
            self._undo.append(Command(changes, label, actor, merge_key))
            self._undo = self._undo[-HISTORY_LIMIT:]
        self._redo.clear()
        if notify:
            self._notify(changes, actor)

    def _notify(self, changes, actor):
        event = {'actor': actor, 'workspace_revision': self.revision,
                 'changes': [{'target': c.target, 'trace_id': c.trace_id, 'fields': list(c.after)} for c in changes]}
        if self._deferred_notifications is not None:
            self._deferred_notifications.append(event)
        else:
            self.changed(event)

    def history(self):
        return {'undo_count': len(self._undo), 'redo_count': len(self._redo),
                'undo_label': self._undo[-1].label if self._undo else '',
                'redo_label': self._redo[-1].label if self._redo else '',
                'undo_actor': self._undo[-1].actor if self._undo else None,
                'redo_actor': self._redo[-1].actor if self._redo else None,
                'entries': [{'label': c.label, 'actor': c.actor} for c in self._undo[-20:]]}

    def _move_history(self, redo):
        self.synchronize()
        source, destination = (self._redo, self._undo) if redo else (self._undo, self._redo)
        if not source:
            raise WorkspaceError('history_empty', 'No workspace change to redo.' if redo else 'No workspace change to undo.')
        command = source[-1]
        changes = command.changes if redo else list(reversed(command.changes))
        self._apply_changes(changes, reverse=not redo)
        source.pop()
        destination.append(command)
        self._notify(changes, 'redo' if redo else 'undo')
        return self.edit_state()

    def undo(self):
        return self._move_history(False)

    def redo(self):
        return self._move_history(True)

    def control(self, *, operation, workspace_epoch, request_id, expected_revision, arguments=None, execute=None):
        """Guard undo/redo and structural commands with a document revision."""
        self._envelope(workspace_epoch, request_id)
        args = {'operation': operation, 'arguments': arguments, 'expected_revision': expected_revision,
                'workspace_epoch': workspace_epoch}
        replay = self._replay(request_id, args)
        if replay is not None:
            return replay
        self.synchronize()
        if type(expected_revision) is not int or expected_revision < 0:
            raise WorkspaceError('invalid_command', 'Expected workspace revision must be a nonnegative integer.')
        if expected_revision != self.revision:
            raise WorkspaceError('edit_conflict', 'Workspace changed. Read current state before changing its history or structure.')
        self._deferred_notifications = []
        try:
            if execute is None and operation not in ('undo', 'redo'):
                raise WorkspaceError('invalid_command', 'Unknown workspace operation.')
            result = execute() if execute else (self.undo() if operation == 'undo' else self.redo())
            notifications = self._deferred_notifications
        finally:
            self._deferred_notifications = None
        receipt = {'workspace_epoch': self.epoch, 'workspace_revision': self.revision, 'request_id': request_id,
                   'applied': True, 'replayed': False, 'result': result, 'render_required': True}
        self._remember(request_id, args, receipt)
        for event in notifications:
            self.changed(event)
        return receipt

    # Compatibility for the first development prototype; all work uses the same
    # generic transaction/history engine. No separate color stack exists.
    def color_state(self, trace_id):
        state = self.edit_state('trace', trace_id)
        return {'workspace_epoch': self.epoch, 'trace_id': trace_id, 'color': state['values']['trace_color'],
                'color_revision': state['field_revisions']['trace_color'], 'revision_scope': 'trace_color'}

    def set_color(self, *, trace_id, color, expected_color_revision, workspace_epoch, request_id, actor='human'):
        try:
            receipt = self.apply(edits=[{'target': 'trace', 'trace_id': trace_id, 'changes': {'trace_color': color},
                                        'expected_revisions': {'trace_color': expected_color_revision}}],
                                 workspace_epoch=workspace_epoch, request_id=request_id, actor=actor)
        except WorkspaceError as error:
            if error.code == 'edit_conflict':
                raise WorkspaceError('color_conflict', str(error), self.color_state(trace_id)) from None
            raise
        change = receipt['changes'][0] if receipt['changes'] else None
        state = ({'workspace_epoch': workspace_epoch, 'trace_id': trace_id, 'color': change['values']['trace_color'],
                  'color_revision': change['field_revisions']['trace_color'], 'revision_scope': 'trace_color'}
                 if change else self.color_state(trace_id))
        return {**state, **{k: receipt[k] for k in ('request_id', 'actor', 'applied', 'replayed', 'render_required')}}
