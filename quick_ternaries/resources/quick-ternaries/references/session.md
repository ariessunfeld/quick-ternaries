# Persistent JSON-lines fallback

Read this only when MCP is unavailable and the host can keep a subprocess's
stdin/stdout alive across tool calls. Use the installed app environment's Python.
If the host cannot retain a process, use computer use or arrange MCP setup.

```sh
python -u -m quick_ternaries.agent_api session
```

Wait for `{"status":"ready","connected":false}`. After the person copies the
chosen window's connection details, send one JSON line to that same process:

```json
{"op":"connect","source":"clipboard"}
```

Credentials stay in memory. Do not print the clipboard or send credentials in
shell arguments, files, host configuration, or chat. If clipboard access fails,
use the recovery table in connection.md; a raw credential object is only suitable
for a private noninteractive stdin pipe managed outside the conversation.

## Focused reads

Each command and response occupies one line. Replace example IDs with current
returned IDs; `limit` is 1-100 and `offset` starts at zero.

```json
{"op":"read","resource":"capabilities"}
{"op":"read","resource":"overview","refresh":true}
{"op":"read","resource":"trace","id":"TRACE_UUID","sections":["heatmap"],"refresh":true}
{"op":"read","resource":"dataset","id":"DATASET_UUID","offset":0,"limit":20,"refresh":true}
{"op":"read","resource":"changes","since":"READ_CURSOR_UUID"}
```

Other focused resources are `plot`, `traces`, and `datasets`. Trace section names
come from capabilities; offset/limit also page filters. Follow `next_offset` only
as needed. Reads return `status: snapshot` with values under `result`. Without
`refresh: true`, repeated identical queries may return `unchanged` or scalar
`changes` instead. The cache lives outside the conversation; use refresh after
compaction or when explaining current values. On `resync_required`, start with
a fresh overview. Read cursors cannot substitute for edit revisions.

## Supported edits and rendering

Check capabilities and the person's editing permission first. These operations
return `state` or `receipt` directly, rather than the read `result` wrapper.

```json
{"op":"edit_state","target":"trace","trace_id":"TRACE_UUID","fields":["point_size"]}
{"op":"edit_state","target":"plot","fields":["title","top_axis","left_axis","right_axis"]}
{"op":"edit_state","target":"workspace"}
```

Field state provides `values`, `schema`, `field_revisions`, `workspace_epoch` and
`workspace_revision`. Use the live schema for allowed fields, bounds and filter
shapes. To change one trace's point size, replace the placeholder UUIDs and
revision with the values just read; choose a new request UUID for the intended
command (the example revision 0 is not a default):

```json
{"op":"apply_edits","edits":[{"target":"trace","trace_id":"TRACE_UUID","changes":{"point_size":12},"expected_revisions":{"point_size":0}}],"workspace_epoch":"EPOCH_UUID","request_id":"NEW_REQUEST_UUID"}
```

Batch related object edits in the same `edits` list for one atomic Undo step;
use `target: "plot"` and `trace_id: null` for plot fields. Extra read dependencies
can be guarded in `expected_revisions`. Structural commands use `op` equal to
`create_trace`, `duplicate_trace`, `delete_trace`, or `reorder_traces`, with:

- `arguments`: `{ "source_id": "DATASET_UUID", "name": "Label" }` for creation;
  duplication uses a trace UUID instead. Deletion uses `{ "trace_id": "TRACE_UUID" }`;
  reordering uses `{ "trace_ids": ["ALL_TRACE_UUIDS_IN_ORDER"] }`.
- `workspace_epoch`, `expected_revision` from fresh workspace edit state, and a
  new `request_id`. The same preconditions apply to `undo`, `redo`, and
  `render_plot`, which take no `arguments` field.

After visual edits, read workspace edit state, send `render_plot` with that epoch
and revision, then query `{"op":"render_status"}` until completion or failure.
Check `stale`; queued/loading does not prove a rendered visualization.
Inspect the shared history's latest actor before authorized undo/redo. On a lost
response, retry the identical command and request ID; inspect conflicts before
issuing a new command. A replayed receipt describes history, not current values.
The SKILL.md collaboration and scientific-evidence rules apply to this transport.

`{"op":"disconnect"}` forgets credentials but keeps the client running;
`{"op":"quit"}` or stdin EOF exits it. Neither revokes other clients. A process
restart requires a new handoff. Commands are limited to 16 KiB per JSON line;
write payloads also have an 8 KiB HTTP body limit. Keep batches focused.
