# Connect Codex or Claude Code

Quick Ternaries provides an optional local MCP adapter for inspecting a chosen
open desktop window. It exposes focused read tools, retains a connection after
the clipboard changes, and works independently of the window's lifetime. Released v1.4.0 is read-only; this development branch adds optional
[workspace editing and rendering](agent-editing.md). File import, save and export
remain in the human interface.
The desktop enforces access controls for both inspection and edits.

## Install and register

Install the optional extra in the **same Python environment as Quick Ternaries**.
For v1.4.0, use its exact release tag:

```sh
python -m pip install 'quick-ternaries[agent] @ https://github.com/ariessunfeld/quick-ternaries/archive/refs/tags/v1.4.0.tar.gz'
python -c 'import sys; print(sys.executable)'
```

For a source checkout: `python -m pip install -e '.[agent]'`.
Use the absolute Python path printed above in one of these commands:

```sh
codex mcp add quick-ternaries -- /absolute/path/to/python -m quick_ternaries.agent_api.mcp
claude mcp add --transport stdio --scope user quick-ternaries -- /absolute/path/to/python -m quick_ternaries.agent_api.mcp
```

On Windows use the absolute `python.exe` path, quoted if it contains spaces.
The examples use personal scope; choose project scope when sharing setup with a
team. These commands register
only the adapter executable; **never put connection tokens in host settings**.
Restart/reconnect the host's MCP connection after registration or an adapter
upgrade. The equivalent installed executable is `quick-ternaries-mcp`.
A running older desktop must be saved and restarted to load new application code.

The adapter must run on the same machine/network namespace as the app. A remote
SSH session, container, WSL environment or cloud task does not automatically have
access to the desktop's loopback interface or clipboard.

## Connect once

1. Open the desired window's **Agent API** panel.
2. Enable the read-only connection and click **Copy connection details**.
3. Tell the agent: “Use Quick Ternaries to connect from the clipboard, inspect my
   workspace overview, and tell me which traces and datasets are available.”
4. The agent calls `connect_from_clipboard`. It can keep reading after you copy
   other text. Keep the chosen desktop window open.

The adapter starts without accessing the clipboard; the tool call performs the
handoff. Each agent host starts a separate adapter. If the process exits, its
credentials disappear and another handoff is required. The app's Disconnect
button revokes all clients. Closing the settings panel keeps access enabled;
closing the desktop window ends it. There is no automatic window discovery.

MCP is a separate process built with the official Python SDK (`mcp>=2.3,<3`).
The SDK provides standard protocol handling, including its supported older
client versions. The desktop's local HTTP API is not itself an MCP endpoint.
Qt, scientific libraries, and the SDK are not imported just to install a skill;
normal desktop startup does not import the MCP SDK.

## Tools and context

| Tool | Purpose |
| --- | --- |
| `connect_from_clipboard` / `disconnect` | Attach to / detach from the explicitly chosen window |
| `get_capabilities` | Discover supported reads and coverage |
| `get_workspace_overview` | Current identity, counts, selection, first catalog pages |
| `get_plot_settings` | Title, plot type and axes |
| `list_traces` / `list_datasets` | Paginated identity catalogs |
| `get_trace` | Current requested sections, including heatmap and paginated filters |
| `get_dataset_schema` | Paginated column names/types and cached row count |
| `get_changes` | Bounded net changes since an explicit read cursor |

Focused reads always return current values. They never require the model to
remember an earlier delta. `get_changes` reports changed IDs; then read only the
relevant objects. Lost context or `resync_required` calls for a new overview and
focused reads. No full snapshot is automatically inserted every turn. MCP does
not control the host's conversation retention/compaction policy.

Read results include coverage limits. Raw data rows and full dataset paths are
excluded. Observation revisions are not whole-document revisions. Stored
settings and cached counts do not prove rendering completed or establish the
number of filtered points. See [the API contract](agent-api.md) for details.

Errors set MCP's error flag and return a redacted code/message. See the
[session recovery table](agent-api-session.md#lifetime-and-recovery).

## Development editing tools

| Tool | Purpose |
| --- | --- |
| `get_edit_state` | Focused field values, validation schema and revisions; workspace history/order |
| `apply_edits` | Atomic changes to traces and plot settings, one Undo step |
| `change_trace_structure` | Create from loaded data, duplicate, delete or reorder |
| `change_history` | Guarded shared Undo/Redo after inspecting the latest entry/actor |
| `render_plot` / `get_render_status` | Queue a render, then verify completion and staleness |

The person enables **Allow workspace editing** in the desktop. Tools remain
visible while permission is off or the connected desktop is older; discover
capabilities first. Use the [editing contract](agent-editing.md) for schemas,
revisions, retry receipts and limits. `get_trace_color_state` and `set_trace_color`
remain convenience wrappers using the same history. These tools are not in v1.4.0.

For example: “Create two traces from my loaded dataset, set A/B/C as the apices,
filter one trace to Sample = Alpha, give them distinct styles, and render. Keep
my current editor selected and tell me what changed.” The agent inspects schemas,
creates traces, batches related edits, and checks the resulting render job.

## Install the skill

The tools work without a skill. The portable `quick-ternaries` skill teaches
selective reads, shared editing, scientific limits and recovery. It needs no
source checkout or repository AGENTS.md. Tool descriptions and live schemas
supply the current API contract; connection and fallback details load on demand.

With this development version installed, run **one** command for your agent:

```sh
quick-ternaries-mcp --install-skill codex
quick-ternaries-mcp --install-skill claude
```

These install to `~/.agents/skills/quick-ternaries` (Codex) and
`~/.claude/skills/quick-ternaries` (Claude Code), respectively. They work on macOS,
Windows and Linux. If the command is not on PATH, use the same absolute Python
as the MCP registration: `python -m quick_ternaries.agent_api.mcp --install-skill codex`.
An explicit directory ending in `quick-ternaries` is also supported, including a
project's `.agents/skills/quick-ternaries` or `.claude/skills/quick-ternaries`.
The v1.4.0 installer accepts explicit directories only.

MCP registration, skill installation and desktop access are separate steps:
installing guidance does not register a server or enable access. Keep just one
copy per host scope to avoid competing instructions. Codex users with an older
copy in `~/.codex/skills` can update that explicit path or move it outside the
skills folders before installing at the current personal location.

Codex discovers the name/description automatically; in CLI/IDE you can explicitly
invoke `$quick-ternaries`. Claude Code supports `/quick-ternaries`. If it does not
appear, restart the host. Start with:

> Use Quick Ternaries to connect from the clipboard and tell me which traces and
> datasets are available. Do not edit anything yet.

Then, with desktop editing enabled:

> Make an Alpha-only trace from my loaded dataset, use A/B/C as the apices, and
> render it. Preserve my current editor and explain what changed.

### Update, customize, or remove

After upgrading the app package, run the matching skill update explicitly:

```sh
quick-ternaries-mcp --update-skill codex
# Or --update-skill claude, or the explicit installed directory.
```

The installer records content hashes in `.quick-ternaries-skill.json`. Updates
verify every previously managed file before replacing the bundle, preserve
unrelated local additions, and remove retired bundled files. They also recognize
the exact original v1.4.0 bundle. Repeating an install or update is harmless.
The manifest is ownership bookkeeping, not a cryptographic signature.

A modified/missing managed file, conflicting local addition, or unknown existing
copy stops the update without overwriting it. Move that copy **outside all host
skill folders** for comparison, install a fresh bundle, and deliberately reconcile
your customizations. There is no force-overwrite switch. Symlinked skills can be
read by hosts, but this installer leaves them for you to manage at their source.

A failed directory replacement rolls back; if restoration also fails, the error
identifies the preserved backup. After a killed installer, inspect any sibling
`.quick-ternaries.staging-*/previous` backup and restore it if necessary before
removing `.quick-ternaries.install-lock` and retrying. Do not delete backups or
remove a lock while another installer is running.

Remove the installed `quick-ternaries` directory to uninstall the guidance.
To remove the server registration too, use `codex mcp remove quick-ternaries` or
`claude mcp remove --scope user quick-ternaries`. Neither action revokes other
clients; the desktop Disconnect button does that. Package upgrades do not silently
rewrite host skills or configuration.

### Distribution and maintenance

The single maintained source is
[`quick_ternaries/resources/quick-ternaries/`](../quick_ternaries/resources/quick-ternaries/SKILL.md).
The wheel and source archive include the complete bundle. To distribute it
without requiring the recipient to locate package resources:

```sh
quick-ternaries-mcp --export-skill quick-ternaries-skill.zip
```

Extract the archive into the chosen host's skills folder. Its top-level directory
is already `quick-ternaries`, with an update manifest and all references. Future
releases publish a versioned ZIP beside the wheel/source archive; v1.4.0 does not
have a separate skill asset. A skill archive does not include the app or register MCP.

This is a portable Agent Skills bundle with explicit local MCP registration.
A marketplace plugin can wrap the same source later. We do not claim public
plugin-directory availability or expose the desktop server over the internet
for distribution. The local machine/clipboard requirements still apply.

Maintainers should run the [skill validation scenarios](agent-skill-testing.md)
when changing instructions or host setup. Current primary host references:
[Codex skills](https://learn.chatgpt.com/docs/build-skills),
[Claude Code skills](https://code.claude.com/docs/en/skills),
[Claude Code MCP](https://code.claude.com/docs/en/mcp), and the
[Agent Skills specification](https://agentskills.io/specification).
