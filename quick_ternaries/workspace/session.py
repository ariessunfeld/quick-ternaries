"""First shared command slice: trace colors, scoped revisions and undo.

Other trace/setup fields still use their existing models. A color revision must
never be represented as a whole-document revision. All calls run on the owner's
thread (the Qt GUI thread in the desktop).
"""

from collections import OrderedDict
from dataclasses import dataclass
import re
from uuid import UUID, uuid4

HISTORY_LIMIT = 100
RECEIPT_LIMIT = 128


class WorkspaceError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass(frozen=True)
class ColorChange:
    trace_id: str
    before: str
    after: str
    actor: str


class WorkspaceSession:
    def __init__(self):
        self.traces = {}
        self.epoch = str(uuid4())
        self._colors = {}
        self._revisions = {}
        self._undo = []
        self._redo = []
        self._receipts = OrderedDict()
        self.changed = lambda trace_id: None

    def reset(self):
        """Replace document identity before loading; old requests cannot apply."""
        self.epoch = str(uuid4())
        self._colors.clear()
        self._revisions.clear()
        self._receipts.clear()
        self._clear_history()

    def _clear_history(self):
        self._undo.clear()
        self._redo.clear()

    def add_trace(self, model, trace_id=None):
        uid = str(UUID(trace_id)) if trace_id else str(uuid4())
        if uid in self.traces:
            raise WorkspaceError("duplicate_trace", "Trace identity is already present.")
        self.traces[uid] = model
        self._colors[uid] = model.trace_color
        self._revisions[uid] = 0
        self._clear_history()
        self.changed(uid)
        return uid

    def remove_trace(self, trace_id):
        self.traces.pop(trace_id, None)
        self._colors.pop(trace_id, None)
        self._revisions.pop(trace_id, None)
        self._clear_history()
        self.changed(trace_id)

    def color_state(self, trace_id):
        model = self.traces.get(trace_id)
        if model is None or not hasattr(model, "trace_color"):
            raise WorkspaceError("trace_not_found", "Trace unavailable. Refresh the catalog.")
        # Defensive boundary for a legacy caller that bypasses the command.
        # Such a change invalidates history rather than silently overwriting it.
        if self._colors.get(trace_id) != model.trace_color:
            self._colors[trace_id] = model.trace_color
            self._revisions[trace_id] = self._revisions.get(trace_id, 0) + 1
            self._clear_history()
        return {"workspace_epoch": self.epoch, "trace_id": trace_id,
                "color": model.trace_color, "color_revision": self._revisions[trace_id],
                "revision_scope": "trace_color"}

    def set_color(self, *, trace_id, color, expected_color_revision, workspace_epoch,
                  request_id, actor="human"):
        if (not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?", color)
                or type(expected_color_revision) is not int or expected_color_revision < 0
                or actor not in ("human", "agent")):
            raise WorkspaceError("invalid_command", "Use a hex color, nonnegative color revision and supported actor.")
        try:
            UUID(request_id)
            UUID(trace_id)
            UUID(workspace_epoch)
        except (ValueError, TypeError, AttributeError):
            raise WorkspaceError("invalid_command", "Use UUID identities from a current color-state read and a new request UUID.") from None
        args = (trace_id, color.lower(), expected_color_revision, workspace_epoch, actor)
        if workspace_epoch != self.epoch:
            raise WorkspaceError("workspace_changed", "Workspace was replaced. Read a new color state.")
        if request_id in self._receipts:
            old_args, receipt = self._receipts[request_id]
            if old_args != args:
                raise WorkspaceError("request_id_reused", "This request ID was already used with different arguments.")
            return {**receipt, "replayed": True}
        before = self.color_state(trace_id)
        if before["color_revision"] != expected_color_revision:
            raise WorkspaceError("color_conflict", "Trace color changed. Inspect the current value before trying again.", before)
        color = color.lower()
        applied = before["color"] != color
        if applied:
            self._undo.append(ColorChange(trace_id, before["color"], color, actor))
            self._undo = self._undo[-HISTORY_LIMIT:]
            self._redo.clear()
            self._assign(trace_id, color)
        result = {**self.color_state(trace_id), "applied": applied, "replayed": False,
                  "request_id": request_id, "actor": actor, "render_required": True}
        self._receipts[request_id] = (args, result)
        while len(self._receipts) > RECEIPT_LIMIT:
            self._receipts.popitem(last=False)
        if applied:
            self.changed(trace_id)
        return dict(result)

    def _assign(self, trace_id, color):
        self.traces[trace_id].trace_color = color
        self._colors[trace_id] = color
        self._revisions[trace_id] += 1

    def history(self):
        def label(change):
            return f"{change.actor.title()}: trace color"
        return {"undo_count": len(self._undo), "redo_count": len(self._redo),
                "undo_label": label(self._undo[-1]) if self._undo else "",
                "redo_label": label(self._redo[-1]) if self._redo else ""}

    def _move_history(self, *, redo):
        source, destination = (self._redo, self._undo) if redo else (self._undo, self._redo)
        if not source:
            raise WorkspaceError("history_empty", "No trace color change to redo." if redo else "No trace color change to undo.")
        change = source[-1]
        self.color_state(change.trace_id)
        if not source:  # An untracked legacy edit invalidated this history.
            raise WorkspaceError("color_conflict", "Color history was invalidated by an untracked change.")
        source.pop()
        self._assign(change.trace_id, change.after if redo else change.before)
        destination.append(change)
        self.changed(change.trace_id)
        return self.color_state(change.trace_id)

    def undo(self):
        return self._move_history(redo=False)

    def redo(self):
        return self._move_history(redo=True)
