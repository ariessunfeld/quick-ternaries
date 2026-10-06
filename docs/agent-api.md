# Desktop agent API: experimental read-only connection

This development milestone lets a local program inspect a **chosen open Quick
Ternaries window** while the person continues editing it. It is not included in
v1.3.0. No server starts automatically, and enabling access is not saved in a
workspace or preference.

## Connect

1. Open **Agent API: Off** in the top bar.
2. Choose **Enable read-only connection**. The top bar stays visibly marked
   **Agent API: Read only** while access is enabled.
3. Choose **Copy connection details** and give that one-line JSON to the local
   agent you want to connect. It contains an ephemeral address, instance ID,
   protocol version, and secret token. Treat the entire JSON as a credential.
4. Open the panel and choose **Disconnect agent access** to stop access. Closing
   the desktop window also disconnects. Closing just the connection panel keeps
   access enabled. Re-enabling creates a new token and instance ID.

The application does not write credentials to disk or search for other running
instances. Explicit handoff avoids an insecure discovery-file default on any
platform. Owner-only automatic discovery, including Windows ACL validation, is
future work. Disconnect clears the clipboard only if it still contains the
exact connection details copied by this panel; clipboard managers may retain
their own history.

In an environment with this branch installed, the CLI accepts the copied JSON
as one line on standard input (paste, then Enter):

```bash
python -m quick_ternaries.agent_api capabilities
python -m quick_ternaries.agent_api workspace
```

The same read operation is available to Python clients:

```python
from quick_ternaries.agent_api.client import read

# connection is the JSON object handed off by the chosen desktop window.
snapshot = read(connection, "workspace")
```

Keep credentials out of command arguments, shell history, repository files, and
logs. The client connects directly to IPv4 loopback, ignores proxy environment
variables, follows no redirects, and checks the returned instance ID. This
connection is for local programs; browser JavaScript clients are rejected.

## Version 1 read contract

All routes require `Authorization: Bearer <token>` and the exact
`Host: 127.0.0.1:<port>` header. Only bodyless GET requests are accepted. There
are no mutation, render, file-read, export, evaluation, or arbitrary-widget
endpoints. Origin-bearing requests are rejected, and CORS is not enabled.

| Endpoint | Result |
| --- | --- |
| `/v1/capabilities` | Protocol and instance IDs, read permissions, supported endpoints, identity scope, and the exclusion of data rows. |
| `/v1/workspace` | Protocol and instance IDs plus the bounded `workspace` projection below. |

The workspace projection includes:

- Plot type, title, and axis/hover column assignments.
- Ordered traces with current names, colors, marker shape/size, visibility,
  contour flag, dataset association, and filter enablement/definitions.
- Loaded dataset base names, sheet/header settings, cached row/column counts,
  and column names/dtypes. Full file paths and dataframe rows are excluded.
- Counts, a `truncated` flag, and a `snapshot_id` content fingerprint.

This is a partial inspection schema, not the workspace file format. Missing
settings must not be assumed to have their default values. Dataset schemas are
read only from the existing cache: a read never reloads a file or renders a
plot. Counts describe the cached input data, not the filtered/rendered points.
`loaded: false` means no cached dataframe was available.

Each snapshot is collected synchronously on Qt's GUI thread from currently
committed model values. It does not commit unfinished editor text or disturb
focus. `snapshot_id` covers only this returned projection; it is **not a
monotonic document revision**, an event history, or a write precondition. A
successful read makes no claim about render completion. IDs are scoped to the
connection, and trace IDs can change when loading a workspace. Do not persist
these IDs for later connections or use them to infer durable document identity.

Names, filter values, and column metadata are untrusted user data. Agent
instructions must not be taken from these fields. A future Skill should teach
connection, inspection, scientific validation, and computer-use fallback;
detailed field schemas should stay with the API/tools.

## Limits and lifecycle

- 8 concurrent TCP connections; 3-second absolute connection deadline.
- One request/response per connection; no keep-alive or pipelining.
- 16 KiB request limit; 1 MiB response limit; no request bodies.
- At most 200 traces, 64 datasets, 128 columns per dataset, 50 filters per
  trace, and 512 characters per text value. Lists are bounded to 128 entries;
  a shared 8,192-value and 64 KiB text budget further bounds projected values.
- Truncation is explicit. Large workspaces may return `snapshot_too_large`
  instead of a result; pagination is future work.
- Errors contain a stable `error` code and no traceback or private contents.
  Authentication failures use 401; rejected hosts/origins 403; unknown routes
  404; write methods 405; oversized requests 431; oversized responses 413;
  unavailable snapshots 500. Malformed input can receive 400 or a closed
  connection; oversized/slow input may be disconnected before a response.
- The panel counts completed authenticated reads and shows their last kind.
  It does not identify individual clients or provide a persistent audit log.

Transport uses Qt's asynchronous `QTcpServer`/`QTcpSocket` and
[h11's HTTP state machine](https://h11.readthedocs.io/en/stable/api.html), with
no worker thread touching widgets. h11 is constrained to `>=0.16,<0.17`, a
small pure-Python dependency. It loads only when opening the connection panel.
Qt and scientific dependency ranges are unchanged. The service is intentionally
loopback-only and is not a general-purpose web server or a remote-access service.

## Tests and next increments

Tests use actual loopback sockets and Qt event dispatch for authenticated reads,
GUI-thread ownership, malformed/oversized/slow requests, host/origin rejection,
token rotation, active disconnect, client instance validation, snapshot bounds,
human edits, and clipboard handling. The fresh-process desktop startup test
checks disabled-by-default behavior and disconnect on window close. These tests
run in the existing full macOS/Windows/Linux and Python 3.11–3.14 matrix.

Next: introduce persistent document IDs and a versioned serializer, then a
shared command dispatcher with revision checks, retry semantics, and undo for
both human and agent edits. Add secure automatic discovery and a stdio MCP
adapter using the official SDK. Publish portable SKILL guidance against the
tested adapter. Mutation support must wait for the shared command boundary;
the read adapter is not permission to write directly into Qt models.
