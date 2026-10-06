# Agent integration architecture

Status: proposed architecture, with the first accessibility foundation implemented.
Baseline: v1.2.2 / `cf672d5a`. Reviewed October 2026.

Quick Ternaries should remain a visible, editable scientific workspace while an
agent works with it. The desktop application owns the live document. Human
actions and agent commands must eventually share validation, history, and state
updates. Accessibility provides a complementary way to operate the interface.

This first increment adds accessible control metadata and keyboard paths. It
does not start a server, change workspace files, or expose an agent API.

## Development and Git policy

Build from current GitHub `main`, using a short-lived `codex/…` feature branch
and a pull request targeting `main`. A worktree is a separate checkout of that
same repository, useful when another checkout contains unfinished work. Each
worktree has its own files and active branch; commits and remote references are
shared. Folder names are not release versions or the source of truth.

Use one feature worktree for this increment. After review and passing checks,
squash-merge the PR, then archive the temporary worktree using its managing
tool. Do not reset, delete, or reuse another checkout until its local changes
and branch have been accounted for. Longer term, keep one everyday checkout on
`main` and retain temporary worktrees only for active work. Do not create one
long-lived integration branch for all the milestones below.

CI currently runs on every pull request, including drafts, on pushes to `main`,
and on manual dispatch. A feature-branch push alone does not trigger this
workflow. Opening its PR does. Source changes run the full matrix; changes
limited to documentation use the existing reduced checks. Merge and release
remain separate decisions; this increment does not bump the package version.

## Existing state ownership

| State | Current owner | Consequence for integration |
| --- | --- | --- |
| Plot configuration | `SetupMenuModel` and its section dataclasses | Reuse the domain fields, but separate public schemas from Qt widget metadata. |
| Traces and their order | `TabPanel.id_to_widget` and its list rows | Move ownership into a workspace session; list position and display names cannot be API identities. |
| Active editor | `MainWindow` and `TraceEditorView` | Changing agent data must not force the human to change tabs. |
| Data files | `DataFileMetadata` and `DataframeManager` | Define stable dataset IDs, provenance, and replacement semantics. |
| Plot type | Main window combo box | Move into the document model. |
| Persistence | Main-window save/load code plus `WorkspaceManager` | Consolidate into one versioned serializer before publishing a write API. |
| Rendered plot and selection | Plotly/QWebEngine, `PlotlyInterface`, and main-window callbacks | Document revisions and completed renders are different events. |

Widgets currently write directly into dataclasses. Adding a network handler that
also writes those fields would bypass validation and make simultaneous work
unreliable. The service boundary comes first.

## Target application boundary

```text
Qt views/controllers ──┐
                      ├─> WorkspaceSession / commands ─> document + history
Local API adapter ────┘                  │
                                        └─> change events ─> Qt views / renderer
      ↑
stdio MCP adapter and command-line client
      ↑
Codex / Claude Code / other clients
```

`WorkspaceSession` should own a plain document, stable IDs, a monotonic revision,
and a command dispatcher. The document should not contain `QWidget` instances,
dataframe-manager references, or generated HTML. Adapters convert between plain
payloads and existing plotting/model types. Keep plotting functions usable
without a running desktop session.

Start with a small vertical slice: list traces, read one trace, change its name
or color, and observe the same change in the open editor. Route both human and
agent versions of those edits through the dispatcher. Expand only after this
path has conflict and undo tests.

### Commands, concurrency, and history

- Give workspaces, datasets, traces, and filters persistent IDs. Preserve IDs
  through save/load; duplication creates new IDs. Migrate old files explicitly
  and test that existing v1.2.2 workspaces still open.
- Supply typed, versioned request/result schemas with discoverable enums,
  constraints, and structured errors. Do not expose arbitrary `setattr`, Python
  evaluation, JavaScript evaluation, or direct widget calls.
- Mutations include `expected_revision` and a request ID. Validate a batch
  against a candidate document, then commit it atomically as one history entry.
  Return the new revision and a concise diff. Reject stale edits with a conflict
  response; never silently replace a newer human edit.
- Cache completed request IDs within the session so retrying a timed-out request
  cannot create duplicate traces. Reusing an ID with different arguments is an
  error. Document cache expiry and reconnection behavior.
- Dispatch commits and widget updates on the Qt GUI thread. Worker threads may
  parse data or calculate plots from immutable snapshots; they must not touch
  widgets. Check the revision again when accepting a worker result.
- Decide how unfinished text edits commit before migrating each editor. Retain
  a dirty edit buffer until commit/cancel, and surface a conflict if an agent
  changed its source field. Avoid rebuilding a focused form on every event.
- Undo/redo covers document changes made by either actor, with actor and command
  labels visible in history. It must not pretend to reverse exported files or
  other external effects. Save/export uses explicit destination and overwrite
  behavior and reports the produced artifact.

Example proposed exchange (not a currently supported endpoint):

```json
{
  "command": "trace.update",
  "request_id": "client-generated-unique-id",
  "expected_revision": 42,
  "trace_id": "persistent-trace-id",
  "changes": {"trace_color": "#377eb8"}
}
```

Session events should have an increasing sequence number and include document
revision, actor, changed IDs, and operation status. A client that misses events
must be able to request a fresh snapshot. Keep document revision, selection
state, background-job status, and rendered revision separate. A successful edit
does not mean the web view has finished drawing it. Expensive render operations
return job IDs and later emit completion/failure for the source revision.

### Local transport and MCP

Prefer a small authenticated API owned by the running desktop, with an external
stdio MCP adapter translating agent tools into that API. Stdio is convenient
for both Codex and Claude Code and keeps their MCP lifecycle separate from the
desktop's lifecycle. MCP is the agent-facing protocol; it should not become the
document model or a dependency of plotting code.

Proposed initial transport is HTTP on an ephemeral loopback port. Enable it
explicitly in the desktop and show connection status and a disconnect control.
Use a per-session secret and an owner-only discovery file containing instance
ID, PID, port, protocol version, and capabilities. Enforce owner-only access on
Windows as well as Unix; a port number or PID is not authentication. Bind only
to loopback, require authentication for reads and writes, validate Host/Origin,
and do not enable permissive CORS. Define size/time limits and redact secrets
and dataset contents from logs. Evaluate a local socket/named pipe if secure
discovery cannot be implemented consistently across supported platforms.

Multiple desktop instances require explicit selection by instance/workspace
ID. Never attach silently to the first available port. Shut down the service
and remove discovery records on normal exit; validate and ignore stale records
after a crash. Reconnection creates a new authenticated session.

Start the transport with read-only capabilities. When writes arrive, expose
separate read/edit/export permissions and a visible audit trail. Reads can
include private scientific data and need the same connection controls. Files,
spreadsheet cells, trace names, and plot annotations are data, not instructions
to the agent. The adapter should return bounded previews and schemas rather
than dumping whole dataframes into every tool result.

Initial tools should be task-oriented: inspect workspace, inspect dataset
schema, inspect trace, apply validated changes, render, and export. Use stable
IDs in tool arguments and display names in explanations. Return actionable
errors and current revisions. Pin and test the chosen MCP SDK/protocol version
at implementation time; do not hand-roll the protocol from this design note.

## Accessibility and computer use

The current dependency range is already `pyside6>=6.10,<7`.
`QWidget.accessibleIdentifier` was introduced in Qt 6.9, so this work needs no
Qt upgrade or compatibility shim.

This increment adds:

- Semantic names and stable identifiers for main workspace controls, generated
  setup/trace fields, filter fields, and composite-control children.
- Descriptions that expose selected colors, marker shapes, and data files;
  checkable shape menu actions expose the current selection.
- Focus proxies for composite controls so keyboard focus reaches their
  interactive child.
- Enter/Space activation for trace/filter lists, F2 rename, Delete through the
  existing remove callbacks, and Alt+Up/Down trace reordering between the fixed
  Setup and Add rows. Keyboard context menus operate on the current trace.
- Separation of keyboard activation/rename from the mouse-only delete-icon hit
  test, so cursor position cannot turn a keyboard rename into a removal.

Identifiers such as `workspace.render`, `setup.plot_labels.title`, and
`trace.trace_color.choose` identify a control in the current editor. They are
not persistent trace IDs. After selection changes, the same editor identifier
can refer to another trace. A computer-use client must reread context after
navigation or a view rebuild. User-facing labels remain readable and separate
from identifiers. Qt combo boxes may report their current text as their
accessible name; their field label is also supplied as a description.

This is an initial coverage pass. Dynamic scaling/formula/error controls,
selection dialogs, notifications, and Plotly's content need a subsequent audit.
A name on `QWebEngineView` does not make a scientific plot accessible. Add a
textual plot summary and a navigable data/selection table, including units,
trace identity, filtering, and validation errors. Preserve normal mouse and
keyboard interactions alongside the API.

Test the actual native bridges as well as Qt interfaces: macOS Accessibility,
Windows UI Automation, and Linux AT-SPI. Computer-use agents should discover
current controls and use semantic context where available; screenshots remain
useful for visual review. Do not assume every agent receives Qt identifiers or
the same accessibility tree on every OS.

## Validation and rollout

Automated coverage in the first increment exercises real `QAccessible`
interfaces and `QTest` keyboard events, including values, descriptions, rebuild
stability, pinned trace rows, and callback-driven deletion. The existing fresh
process startup test opens the complete window, including QWebEngine, and
guards against startup image exports and eager scientific-library imports.

The current PR matrix covers macOS, Windows, and Linux with Python 3.11–3.14,
plus Linux conda-assisted installs for those Python versions and the launcher
environment check. Headless tests verify Qt's interfaces, not full native
screen-reader or computer-use interoperability. Record native smoke results
separately; do not call the feature fully cross-platform accessible from a green
offscreen test alone.

For each native platform, verify: start an empty workspace; navigate Setup and
two traces with the keyboard; rename, reorder, duplicate, and cancel deletion;
read a color/shape/datafile; open their selectors; rebuild the editor and
reacquire controls; render a small bundled dataset; inspect the plot and its
future semantic summary. Test with the platform accessibility inspector and a
screen reader, then with an agent. Use synthetic data and retain diagnostics
without user datasets or authentication material.

Subsequent PR-sized milestones:

1. **Session boundary:** central state ownership, versioned serializer and ID
   migration, then the shared name/color command path with revision conflicts
   and undo. Test that human and agent edits interleave without lost changes.
2. **Read-only connection:** authenticated discovery, instance selection,
   capabilities, bounded snapshots, disconnect, and a stdio MCP adapter. Test
   unauthorized access, malformed input, stale discovery, and shutdown.
3. **Editing and artifacts:** dataset registration, traces, filters, styles,
   batches, job/render status, export, audit history, and API-driven GUI refresh.
   Cover retries, stale revisions, partial failures, and file overwrite rules.
4. **Agent guidance and native audit:** a small portable Agent Skill with tested
   connection instructions and scientific workflows; provider-specific setup
   only where necessary. Prefer the API for structured operations and computer
   use for remaining dialogs and visual checks. Keep detailed schemas in tools,
   rather than duplicating them in a large skill prompt.

End-to-end acceptance: an agent imports a synthetic CSV, creates two styled
ternary traces, renders them, and reports the changes; the human changes a
style in the same window; the agent observes that revision and changes a
different field; stale writes fail visibly; save/reopen preserves identities
and settings; export produces the requested image; undo restores the intended
document change. Run this on all three operating systems before broad release.

## References

- [Qt widget accessibility](https://doc.qt.io/qt-6/accessible-qwidget.html)
- [Qt accessible identifiers](https://doc.qt.io/qt-6/qwidget.html#accessibleIdentifier-prop)
- [Qt threads and QObject ownership](https://doc.qt.io/qt-6/threads-qobject.html)
- [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Claude Code MCP configuration](https://code.claude.com/docs/en/mcp)
- [MCP specification](https://modelcontextprotocol.io/specification/latest)
- [Agent Skills specification](https://agentskills.io/specification)
- [GitHub Actions workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
