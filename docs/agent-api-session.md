# Persistent inspection client

The [API guide](agent-api.md) defines coverage, endpoints, cursor scope and limits.
This guide describes how an agent keeps a reliable, economical client session.

The [editing extension](agent-editing.md) adds focused `edit_state`,
atomic `apply_edits`, trace lifecycle, `undo`/`redo`, `render_plot` and
`render_status` operations. Check the running desktop's capabilities before using them.

## Start and connect once

Use the installed app environment's Python. A host must retain the subprocess's
stdin and stdout between tool calls. Start:

```bash
python -u -m quick_ternaries.agent_api session
```

The first response is `{"status":"ready","connected":false}`. Have the person
enable Agent API access and copy connection details from the chosen window.
Copy any prompt/commands **before** copying those details. Then send this line
to the already-running process's stdin:

```json
{"op":"connect","source":"clipboard"}
```

The client reads the clipboard once, validates the endpoint/instance using the
capabilities route, and retains credentials in memory. Subsequent clipboard use
does not matter. `session --clipboard` does the same bootstrap at startup.
macOS uses `pbpaste`; Windows uses PowerShell; Linux uses `wl-paste` or `xclip`.
If a clipboard command is blocked, resolve the host's execution permissions.
Do not disable authentication or repeatedly ask the person to copy credentials
when access to the clipboard itself is denied.

For hosts without clipboard support, the connect command can carry a
`connection` object through a private, noninteractive stdin pipe instead of a
`source`. Never put credentials in process arguments, shell history, repository
files, chat transcripts or an interactive terminal that echoes input. The
session rejects credential objects on a TTY; use clipboard handoff there.

## Query only relevant state

Each input and response occupies one JSON line. Example sequence (replace IDs
with values from the overview or catalog):

```json
{"op":"read","resource":"overview"}
{"op":"read","resource":"plot"}
{"op":"read","resource":"trace","id":"TRACE_ID","sections":["heatmap"]}
{"op":"read","resource":"changes"}
{"op":"read","resource":"trace","id":"TRACE_ID","sections":["filters"],"offset":0,"limit":20}
{"op":"read","resource":"dataset","id":"DATASET_ID","offset":0,"limit":20}
{"op":"read","resource":"trace","id":"TRACE_ID","sections":["heatmap"],"refresh":true}
{"op":"quit"}
```

`read` defaults to `overview`. Other resources: `traces`, `datasets`,
`capabilities`, and the explicit broad `workspace` read. Catalog/object pages
accept integer offset/limit. Trace sections are a list of names from capabilities.
`changes` can accept `since` explicitly; otherwise it uses the last overview or
change-check cursor. A focused read does not consume other objects' changes.

The first focused read returns `status: snapshot` with the current result.
Repeating the same query returns `unchanged` or a small `changed` result with
JSON-pointer paths and before/after scalar values. List/structural changes return
a fresh result. Comparisons cover only the same requested query and included
fields. Compact replies retain included coverage and its partial flag; a full
result also lists excluded categories. Truncated values are never suppressed as
unchanged. `refresh: true`
always returns current requested values; use it after lost/compacted context or
when explaining the current configuration. The client caches at most 32 results
and 2 MiB, outside the model's conversation. Eviction produces a fresh snapshot
on the next read. It does not remove information already in the conversation.

On `resync_required`, cached comparisons and the cursor are cleared. Read a new
overview and relevant objects. A cursor/fingerprint is never a whole-document
revision or a future write precondition. Excluded settings/data/render state
must remain unknown, even when a change check reports no exposed changes.

The JSON command limit is 16 KiB. Oversized input ends the session; malformed
JSON or invalid commands return a redacted error and allow another command.

## Lifetime and recovery

`{"op":"disconnect"}` drops credentials and comparisons while leaving the
client process ready to reconnect. `quit`, stdin EOF or process exit ends the
client. Explicit reconnect always clears old state before validating new access.
Closing a client does not turn off the desktop's toggle or other clients.
Desktop **Disconnect agent access** revokes all clients on that connection.

| Error | Next step |
| --- | --- |
| `clipboard_unavailable` | Check execution/OS permissions or availability of the clipboard reader. |
| `invalid_clipboard` | Clipboard is readable but not connection JSON. Copy connection details again. |
| `local_access_denied` | Resolve the host's permission to reach loopback. |
| `access_revoked` / `instance_changed` | Credentials are dropped. Explicitly connect again to the chosen window. |
| `connection_unavailable` | Check the app and Agent API toggle/address. This alone does not prove clipboard failure. |
| `connection_timeout` / `workspace_busy` | Wait for workspace loading/dialogs to finish, then retry. |
| `trace_not_found` / `dataset_not_found` | Refresh the overview/catalog before selecting another object. |
| `no_baseline` | Read an overview before requesting changes. |

Errors never repeat raw clipboard contents, arbitrary server error text or
exception details. Diagnose using the code, not by printing the token.

This is a JSON-lines CLI protocol, **not MCP**. The [official-SDK MCP adapter](agent-mcp.md) reuses the Python client logic
and is preferred for supported hosts. This CLI requires a persistent command
execution session. If their host kills that session, a new explicit handoff is required;
the clipboard is not a credential store. The one-shot CLI remains useful for
isolated reads but is not the recommended repeated-inspection workflow.
