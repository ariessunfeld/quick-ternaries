# Shared workspace editing

The desktop and local agent connection share workspace transactions, history,
trace lifecycle, and rendering.
Check the running desktop's capabilities. **Allow workspace editing** in its
**Settings → Agent API** panel grants `edit_workspace`; each new connection starts read-only.
Revocation is checked again before a buffered request executes and cancels
queued agent renders. Closing the panel keeps the connection; Disconnect or
closing the window revokes all clients.

## One workspace, two participants

The Qt interface and local API call the same `WorkspaceSession`. Its transaction
engine has no Qt dependency. `DesktopWorkspace` binds explicit schemas to the
existing model dataclasses and updates affected controls on the GUI thread.
Plot services and persistence keep using those models. MCP and the persistent
Python/CLI client are transport adapters, not owners of a second document.

Supported edits include trace names, visibility, points/lines/outlines,
heatmaps/sizemaps, filters, density contours, transforms and uncertainties;
plot type, labels, apices/axes/hover columns, legend, fonts, backgrounds, ranges,
scaling and chemical formulas. `get_edit_state` is the authority on the running
version's fields, constraints and revisions. Filters and nested scientific
mappings are replaced as whole fields; they do not have per-item revisions.
Create traces from loaded datasets; duplicate regular traces; delete and reorder
traces. File import, source-point contour creation, datasource replacement,
save and export use the existing human interface.

**Edit > Undo/Redo** and normal platform shortcuts share a history of up to 100
transactions, with contextual labels and actor information. A batch is one undo
step; continuous human typing coalesces until focus or another command changes.
Focused text editors retain native text undo. Trace creation, deletion and order
are undoable. There is no special history toolbar or persistent status row.

Agent changes preserve the selected trace, existing editor, cursor and selection
when their fields are unrelated. Deleting the selected trace returns to Setup.
An agent cannot overwrite a modified focused editor (including numeric input),
change history while the person is typing, or edit through a modal dialog.
Semantic validation rejects incomplete agent configurations; human editors may
hold intermediate values while the person works. Rendering validates the whole
plot using the existing scientific services.

## Focused state and atomic edits

`GET /v1/edit-state?target=workspace` returns `workspace_epoch`,
`workspace_revision`, trace order and recent history. The revision covers editable
fields and structure, not raw data values, view selection, unsaved editor buffers,
or external files. `target=plot` or `target=trace&trace_id=UUID` returns values,
per-field revisions and schemas. Add `fields=trace_color,point_size` for a focused
read. Observation cursors from inspection are **not write preconditions**.

`POST /v1/commands/apply-edits` accepts:

```json
{
  "workspace_epoch": "UUID from edit-state",
  "request_id": "new client-generated UUID",
  "edits": [
    {
      "target": "trace",
      "trace_id": "UUID from the trace catalog",
      "changes": {"trace_color": "#377eb8", "point_size": 10},
      "expected_revisions": {"trace_color": 0, "point_size": 0}
    },
    {
      "target": "plot",
      "trace_id": null,
      "changes": {"top_axis": ["A"], "left_axis": ["B"], "right_axis": ["C"]},
      "expected_revisions": {"top_axis": 0, "left_axis": 0, "right_axis": 0}
    }
  ]
}
```

Replace the illustrative UUIDs and revisions with actual reads. Supply 1–32
edits, one per object. Every changed field needs its exact expected revision;
additional field revisions can guard assumptions used to construct the change.
All candidates validate before any model write. One stale field rejects the
entire batch; unrelated human edits do not conflict. Undo/redo advance revisions,
including when a value returns to its original value. Adapter write failures
roll the batch back. Unknown fields and arbitrary attribute/evaluation requests
are rejected. Colors use `#RRGGBB` or Qt's alpha-first `#AARRGGBB`.

A receipt contains the resulting values/revisions for requested fields, actor,
request ID, `applied`, `replayed`, and `render_required`. No-op edits have no
history entry. A successful edit does not claim that the visible plot updated.

## Structure, history and rendering

These POST routes take `workspace_epoch`, `request_id` and `expected_revision`
from the workspace state. Structural routes additionally require `arguments`:

| Route under `/v1/commands/` | Arguments / effect |
| --- | --- |
| `create-trace` | `{"source_id":"loaded dataset UUID","name":"Samples"}` |
| `duplicate-trace` | `{"source_id":"regular trace UUID","name":"Copy"}` |
| `delete-trace` | `{"trace_id":"trace UUID"}` |
| `reorder-traces` | `{"trace_ids":["every trace UUID in desired order"]}` |
| `undo`, `redo` | No arguments; inspect the latest shared history and actor first |
| `render-plot` | No arguments; queue a render of that revision |

Structural commands and history require the current workspace revision so they
cannot silently undo or delete through intervening human work. Saved valid trace
UUIDs survive reload; duplicates receive new IDs; malformed legacy IDs migrate.
Loading a workspace or changing its data library/source starts a new epoch and
clears history and receipts. File changes cannot be undone by model history.
An unexpected direct write to an exposed field invalidates history when detected.
History and runtime revisions are not persisted in workspace files.

`GET /v1/render-status` reports the latest job, source epoch/revision, and a
`stale` flag. Rendering reuses the human Render button's service and creates no
undo entry. Jobs progress through queued/building/loading to `rendered`, `failed`
or `cancelled`. `rendered` confirms Plotly's initialization promise completed;
Z-map reports only `view_loaded`. Editing during a completed render makes it
stale; changing the document before queued work starts cancels that job.
Scientific construction still runs on the GUI thread and can pause interaction
for large plots. Background rendering from immutable snapshots is future work.
Each window owns its temporary HTML directory; windows do not overwrite each
other's output. Render errors are redacted and agent failures do not open modal
warning dialogs. Visual inspection is still needed for scientific/visual claims.

## Conflicts, retries and transport

`edit_conflict`, `workspace_changed`, `request_id_reused`, `editor_busy` and
`render_busy` return HTTP 409 without starting the requested change. Read-only
access returns 405; loading returns 503 `workspace_busy`. Refresh relevant state
and inspect intervening work before creating a new intended edit. Let the person
finish pending input; never force an overwrite to resolve `editor_busy`.

After a lost response, retry the **identical request UUID and arguments**.
Successful receipts are stored before UI notification and replayed without
reapplying a change or undoing a later human undo. A replay describes historical
completion: reread before reporting current state. Reusing a retained UUID with
different arguments is rejected. The last 128 successful receipts are retained
across clients and connection restarts within the workspace epoch. After eviction,
preconditions are checked again; mutating commands' advanced revisions reject old
writes. No-op and render requests do not advance revisions, so deduplication of
those requests is guaranteed only while their receipts remain retained. No client
layer silently retries writes or substitutes new IDs/revisions.

Existing authentication, exact loopback Host, Origin rejection, 16 KiB total
request limit and 3-second connection deadline still apply. POST requires JSON,
Content-Length and no transfer encoding. The bundled client's command body limit
is 8 KiB; keep batches concise. Local edits run serially on the GUI thread.

## MCP, Python and JSON-lines clients

MCP exposes `get_edit_state`, `apply_edits`, `change_trace_structure`,
`change_history`, `render_plot` and `get_render_status` alongside focused reads.
Tool availability does not grant desktop permission. The former
`get_trace_color_state` / `set_trace_color` convenience tools delegate to the same
transaction engine; they have no separate history.

Python uses `read(connection, "edit-state", target="trace", trace_id=uid)` and
`command(connection, "apply_edits", **payload)`. JSON-lines uses the same payload
with `"op":"apply_edits"`; other operations are `edit_state`, `render_status`,
`create_trace`, `duplicate_trace`, `delete_trace`, `reorder_traces`, `undo`, `redo`
and `render_plot`. Focused edit reads always return full requested values.
Commands clear the client's observation-comparison cache; none exposes credentials.

Automated tests cover the real window, HTTP and official MCP SDK with synthetic
data, atomic batches, retries, focused typing/numbers, native shortcuts, filters,
structure, transforms, save/load migration and actual Plotly initialization.
The existing cross-platform matrix runs these tests; offscreen testing does not
certify native screen-reader interoperability.
