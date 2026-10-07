# Connect Codex or Claude Code

Quick Ternaries provides an optional local MCP adapter for inspecting a chosen
open desktop window. It exposes focused read tools, retains a connection after
the clipboard changes, and works independently of the window's lifetime. It
cannot edit, import, render, save or export. The desktop still enforces its
read-only API and access controls.

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
claude mcp add --transport stdio quick-ternaries -- /absolute/path/to/python -m quick_ternaries.agent_api.mcp
```

On Windows use the absolute `python.exe` path, quoted if it contains spaces.
Choose your host's user/project scope as appropriate. These commands register
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

## Optional skill

Tools work without a skill. The bundled skill teaches selective inspection,
scientific limitations, and recovery. Copy it into a host-discovered skill
folder, for example:

```sh
quick-ternaries-mcp --install-skill ~/.agents/skills/quick-ternaries
# Claude Code: choose ~/.claude/skills/quick-ternaries instead.
```

The destination is explicit; installation does not edit host settings or
silently overwrite a customized skill. It works from an installed wheel without
a source checkout. Review existing copies before updating them.
The maintained source is `quick_ternaries/resources/agent_skill/`.
