# Shared trace-color editing (development)

This extension is implemented on the development branch after v1.4.0. It is not
in the v1.4.0 release. Check `/v1/capabilities` on the actual running desktop:
`trace_color.read` advertises color state; `trace_color.edit` and permission
`edit_trace_color` appear only while the person enables **Allow agent trace color
edits (undoable)** in its Agent API panel. Every connection starts read-only.
Revoking editing takes effect before a buffered request executes. Disconnecting
revokes all access; re-enabling does not preserve edit permission.

## One command shared with the interface

The GUI color picker and local API both call `WorkspaceSession.set_color` on the
Qt GUI thread. The session owns the trace mapping and color history. Agent edits
update only the affected color preview and history controls: they do not switch
tabs, replace the editor, move focus, or overwrite text in other fields. Writes
are rejected while a modal editor is open or the workspace is loading.

**Undo color** and **Redo color** in the desktop cover both human and agent color
changes, with the actor in their accessible descriptions/tooltips. They leave
other fields alone. Native text undo retains its own shortcuts. Up to 100 color
changes are retained. Adding/removing a trace or replacing the workspace clears
color history; this is deliberately not general document undo. An unexpected
legacy color write also invalidates history when detected.

Valid saved trace UUIDs survive workspace save/load. Missing, invalid or duplicate
legacy IDs receive fresh UUIDs. Duplicating a trace creates a new UUID. Loading a
workspace changes its runtime `workspace_epoch` and clears history and receipts,
even if the file contains the same trace IDs. Color revisions/history are not
persisted. Dataset and observation cursor identities retain their existing scope.

## Read, then edit

`GET /v1/trace-colors/{trace_id}` returns `color_state`, containing `trace_id`,
`workspace_epoch`, `color`, `color_revision` and `revision_scope: trace_color`.
The revision is a nonnegative integer for that trace's color. A label or another
trace's color edit does not invalidate it. Color changes, undo and redo advance
it monotonically within the workspace epoch. Read cursors/fingerprints are never
write preconditions.

`POST /v1/commands/set-trace-color` accepts exactly this JSON shape:

```json
{
  "trace_id": "UUID from the trace catalog",
  "color": "#377eb8",
  "expected_color_revision": 0,
  "workspace_epoch": "UUID from the color-state read",
  "request_id": "new client-generated UUID"
}
```

Use actual UUIDs in place of the explanatory strings. Colors accept `#RRGGBB`
or `#AARRGGBB` (Qt's alpha-first format). The request requires authentication,
exact loopback Host, `Content-Type: application/json`, Content-Length, no Origin,
and no transfer encoding. The existing 16 KiB total request/3-second connection
limits still apply. There are no arbitrary field, actor, or evaluation arguments.

A successful response includes `receipt` with the color state at completion,
`request_id`, `actor: agent`, `applied`, `replayed`, and `render_required: true`.
Setting the same color is a no-op and creates no history entry. The user still
uses **Render Plot** to update the visualization; success does not certify a
completed render or visible output.

## Conflicts and retries

A stale color revision returns HTTP 409 `color_conflict` without mutation. The
raw response includes the current color state in `details`; clients report a
fixed safe error and can request fresh state with the focused read. Review the
intervening change before issuing a new intended edit with a new request UUID.
`workspace_changed`, `request_id_reused`, and `editor_busy` are also 409 errors.
Disabled edits return 405 `read_only`; loading returns 503 `workspace_busy`.

For an uncertain timeout/lost response, resend **the identical request UUID and
arguments**. A completed command's receipt is returned with `replayed: true`;
the change and history entry are not applied twice. In particular, a retry
cannot reverse a human undo. A receipt describes the original completion, so
read current state again before explaining what the workspace now contains.
Reusing a retained UUID with different arguments is rejected.

The workspace retains the last 128 successful command receipts across all
clients (including human color commands). Receipts survive connection restarts
while the workspace stays open, but not workspace replacement or app restart.
After eviction, the old expected revision still prevents a previously applied
color change from being applied again. A no-op retry may be revalidated as a
no-op. Clients must not silently substitute new IDs or revisions to make a
conflicting retry succeed. No client layer automatically retries writes.

## MCP, Python, and JSON-lines clients

MCP exposes `get_trace_color_state(trace_id)` and `set_trace_color(...)` with
UUIDs, strict nonnegative integer revisions and a constrained color string.
These tools reuse the same authenticated HTTP client and command layer. Their
presence in the tool list does not grant desktop permission.

Python uses `read(connection, "trace-colors/" + trace_id)` and
`set_trace_color(connection, **command)` from `quick_ternaries.agent_api.client`.
The persistent JSON-lines session accepts `{"op":"color_state","trace_id":"…"}`
and the command fields above with `"op":"set_trace_color"`. These operations
return full color states/receipts, never comparison deltas. Successful commands
clear the client's read-comparison cache; the next overview establishes a new
observation baseline. All entry points preserve existing credential redaction.

## Validation and remaining scope

Tests cover real Qt/HTTP/MCP requests, competing clients, human/agent interleaving,
focused typing/selection, undo/redo, retries after undo, request-ID collisions,
receipt eviction, permission revocation mid-request, modal/loading rejection,
malformed requests, and real workspace save/load with legacy IDs. They run in the
existing macOS/Windows/Linux Python matrix. Offscreen Qt tests do not certify
native screen-reader or OS clipboard behavior.

Other field commands, structural undo, complete document revisions, rendering
jobs, import/export, subscriptions and persistent discovery remain future work.
Expand by migrating each GUI mutation and its validation/history together.
