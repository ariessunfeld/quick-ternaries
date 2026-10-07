# Agent integration architecture

Status: accessibility foundation released in v1.3.0; read-only desktop
connection and optional MCP adapter available in v1.4.0. Reviewed October 2026.

Quick Ternaries remains a visible, editable scientific workspace while an agent
works alongside the person. The desktop owns the live document; local clients
submit structured commands. Accessibility complements the API for remaining
dialogs and visual checks.

v1.4.0 ships [focused read-only inspection](agent-api.md), bounded observation
cursors and the optional [MCP adapter](agent-mcp.md). This development branch adds
[workspace editing](agent-editing.md): atomic multi-object edits, trace lifecycle,
shared undo/redo, scientific settings and explicit render jobs. It replaces the
initial color-only prototype. No package version is changed by this PR.

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

## Implemented application boundary

```text
Codex / Claude Code ─> local stdio MCP adapter ─┐
Python / JSON-lines CLI client ────────────────┴─> authenticated loopback API
                                                           │
Mouse / keyboard ─> Qt views ─> DesktopWorkspace adapter <──┘
                                       │
                       WorkspaceSession transactions + history
                                       │
                         existing models + ordered trace IDs
                                       │
                  targeted Qt refresh / explicit RenderService job
                                       │
                        scientific plot services ─> QWebEngine
```

`workspace/session.py` is a Qt-independent transaction engine. Explicit resource
adapters read and write model fields; `workspace/schema.py` defines the allowlist
and value constraints without Qt widget metadata. Validation runs against all
candidate resources before any write. Atomic commits advance per-field and
workspace revisions, record one command, and emit one change event. Successful
receipts are saved before observer notification so a UI failure cannot turn a
network retry into another mutation. Tests exercise rollback and that ordering.

`workspace/desktop.py` binds the existing dataclasses and routes native editing
through the same commands. The session owns trace identity/order/history;
`TabPanel.id_to_widget` aliases its mapping. Plot type now lives in
`SetupMenuModel`, with the dropdown as its view. Scientific services retain their
existing inputs; the transport never calls arbitrary setters, evaluates Python,
or exposes a scripting endpoint.

`workspace/render.py` supplies the Render button and API with one lifecycle.
Each window owns a temporary HTML directory. Rendering checks the requested
revision before starting and reports the Plotly initialization result separately
from model acceptance. Construction still runs on the GUI thread; queued jobs
are not background computation. Large-plot responsiveness needs a later immutable
snapshot/worker design, not an unsafe worker touching live Qt models.

### Collaboration and history

- Per-field optimistic revisions allow unrelated human and agent edits to coexist.
  A stale member rejects an entire batch. Filters and nested mappings are whole
  fields, deliberately without a second identity/revision scheme.
- Structural commands and agent Undo/Redo require the latest workspace revision.
  Restoring a deleted trace preserves its UUID but advances field revisions,
  preventing stale commands from becoming valid again after undo.
- Agent updates preserve the human's selected trace, focus, cursor and unrelated
  text. Dirty focused text, numeric input, filters and scientific editors are
  protected; modal dialogs and workspace loading also block agent writes.
- Human typing coalesces by editing gesture; an intervening agent command breaks
  the merge. Standard Edit menu actions and platform shortcuts operate shared
  history. Native focused text undo remains local to that editor.
- History is bounded to 100 commands. Successful request receipts are bounded to
  128 across clients and are scoped to the loaded workspace epoch. Replays return
  historical results, including after a human undo. They never masquerade as a
  fresh read. See the editing contract for eviction/no-op/render limitations.
- File import/removal/rebinding and workspace loading establish a new epoch and
  clear undo history. They are outside document-edit undo. Unexpected direct
  writes to exposed fields invalidate history rather than overwriting them.

The existing workspace file format is retained. Valid trace IDs persist;
legacy/duplicate IDs migrate during load. Epochs, revisions, render jobs,
permissions and credentials are runtime state, not serialized workspace state.
Raw dataset contents and source-point provenance are not covered by editable
field revisions. Dataset IDs retain their connection scope.

### Transport, tools and context

The API starts only after explicit user action, binds IPv4 loopback on an ephemeral
port and uses a per-instance bearer token. It rejects browser origins, incorrect
hosts, oversized/slow requests, unexpected fields and unsupported operations.
Every connection starts read-only; a visible workspace-editing toggle grants the
bounded command surface. Revocation is rechecked at execution. A queued agent
render is cancelled on revocation; closing the window disconnects all clients.

The optional official-SDK MCP process and persistent JSON-lines client reuse the
same authenticated HTTP client. They retain credentials in memory after one
explicit clipboard handoff and never automatically discover a different window.
MCP is an adapter, not another app state store. Normal desktop startup does not
import the SDK. The bundled portable skill teaches attachment, focused reads,
edit preconditions, retries, shared history and honest render verification.

Inspection cursors describe bounded net changes to a projection, not command
history. Clients request an overview, relevant objects and small edit-state
field subsets. No full snapshot is injected every turn. After context compaction
or cursor expiry, read current relevant state. There is no subscription/event
stream in this increment.

## Remaining boundaries

File import/export/save and source-point contour creation remain human UI actions.
A future file-command increment needs explicit destination/overwrite semantics,
provenance and artifact receipts. A versioned document serializer can consolidate
the remaining legacy persistence paths. Automatic discovery needs owner-only
credentials and Windows ACL validation. Background rendering, durable history,
per-filter IDs and semantic plot/data summaries remain separate improvements.
These limits do not prevent the current loaded-data workflow: agents can create
traces, configure apices, filters and appearance, render, and collaborate on edits
in the same visible window.

## Accessibility and computer use

The current dependency range is already `pyside6>=6.10,<7`.
`QWidget.accessibleIdentifier` was introduced in Qt 6.9, so this work needs no
Qt upgrade or compatibility shim.

The v1.3.0 accessibility foundation provides:

- Semantic names and stable identifiers for main workspace controls, generated
  setup/trace fields, filter fields, and composite-control children.
- Descriptions that expose selected colors, marker shapes, and data files;
  checkable shape menu actions expose the current selection.
- Focus proxies for composite controls so keyboard focus reaches their
  interactive child.
- Direct focus shortcuts: Ctrl+Alt+T for the trace list, Ctrl+Alt+C for the
  current filter's column, and Ctrl+Alt+O for its operation. On macOS, use
  Command+Option in place of Ctrl+Alt. Tooltips and accessible descriptions
  show the platform's shortcut notation. These avoid depending on the OS's
  choice of controls included in ordinary Tab navigation.
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

This is an initial coverage pass. Dynamic scaling/formula/error controls now also have semantic names and stable
identifiers. Selection dialogs, notifications, and Plotly's content need a
subsequent audit.
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

### Initial native macOS smoke test

Using Codex computer use with Python 3.11.14 and Qt 6.11.2, the test imported
this synthetic CSV through the file/header dialogs, assigned A/B/C to the three
apices, created and renamed a trace, and rendered five points:

```csv
A,B,C,Sample
70,20,10,Alpha
20,70,10,Beta
20,20,60,Gamma
33,33,34,Delta
50,25,25,Epsilon
```

The test then enabled filters, created and named a filter, selected `Sample`,
and visually verified `is Alpha` produced one point, `is not Alpha` produced
four, and `is No such sample` produced zero. Save/reopen preserved the setup
and trace. File import, field edits, and rendering used native accessibility
actions; trace/filter creation and dropdown selection needed keyboard paths.

Observed limitation: this native tool sometimes returned invalid list elements,
omitted list rows, or did not open a combo box when asked to click it. Fresh
snapshots and direct keyboard focus paths allowed the workflow to continue.
This is a reproducible follow-up for the native Qt bridge/tool interaction,
not evidence that all list actions or screen readers work. The plot exposed
titles, axes, and toolbar labels, but not a reliable semantic point count;
the point-count checks above used screenshots. Windows UIA, Linux AT-SPI,
and screen-reader smoke tests remain outstanding.

The editing integration test now drives the real desktop through HTTP and the
official MCP SDK: create from synthetic data, configure apices/style/category
filters atomically, preserve focused human typing, reject stale writes, undo/redo,
duplicate/delete traces, change scientific settings, render and reload a saved
workspace. A Plotly initialization check verifies actual rendering. Separate
transaction tests cover validation rollback, observer failure, read dependencies,
retry receipts and restored-object revisions. CI runs the full existing matrix;
native screen-reader audits remain distinct from these automated tests.

## References

- [Qt widget accessibility](https://doc.qt.io/qt-6/accessible-qwidget.html)
- [Qt accessible identifiers](https://doc.qt.io/qt-6/qwidget.html#accessibleIdentifier-prop)
- [Qt threads and QObject ownership](https://doc.qt.io/qt-6/threads-qobject.html)
- [Codex MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
- [Claude Code MCP configuration](https://code.claude.com/docs/en/mcp)
- [MCP specification](https://modelcontextprotocol.io/specification/latest)
- [Agent Skills specification](https://agentskills.io/specification)
- [GitHub Actions workflow triggers](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
