# Connection and recovery

Use this reference for initial setup, missing tools, or attachment errors. Normal
workspace tasks need only SKILL.md and the tools' live descriptions and schemas.
No source checkout, repository AGENTS.md, or developer documentation is required.

## Locate and register the adapter

The adapter is a local stdio process. It does not launch a window. It must run on
the same machine and network namespace as the desktop, with clipboard and
loopback access. A cloud task, SSH session, container or WSL environment does not
automatically share the desktop connection. Use a local agent session in that case.

Find the installed Quick Ternaries Python environment from the person's context
or launcher setup. If that is unknown, ask for it; do not invent a checkout or
create a second installation to operate the already-running window. In the
identified environment, this command prints the executable and package version:

```sh
python -c "import sys; from importlib.metadata import version; print(sys.executable); print(version('quick-ternaries'))"
```

The server command is that absolute executable followed by
`-m quick_ternaries.agent_api.mcp`, or its adjacent `quick-ternaries-mcp` executable.
It requires the optional `agent` extra. If it is missing from a released install,
install the same release's extra using that Python; replace VERSION with the
printed release version:

```sh
python -m pip install "quick-ternaries[agent] @ https://github.com/ariessunfeld/quick-ternaries/archive/refs/tags/vVERSION.tar.gz"
```

For an existing development install, use its known checkout and `.[agent]`.
Coordinate environment changes with the person first if the app is running.
Installation is needed only for setup; never update packages merely to connect.

Register the absolute executable with the chosen host. Quote paths containing
spaces (on Windows this is `python.exe`). These examples use personal scope so
the same connection works across projects:

```sh
codex mcp add quick-ternaries -- /absolute/path/to/python -m quick_ternaries.agent_api.mcp
claude mcp add --transport stdio --scope user quick-ternaries -- /absolute/path/to/python -m quick_ternaries.agent_api.mcp
```

Respect an existing registration; if it points to a removed environment, repair
that path rather than adding a second server. Inspect registration with
`codex mcp get quick-ternaries` or `claude mcp get quick-ternaries`. Reload the
host's MCP connection after a registration or adapter upgrade. No token, port,
or workspace identity belongs in host configuration. The app's local HTTP URL
is not an MCP server URL.

## Attach to the chosen window

1. Have the person open **Settings → Agent API** in that window (the top-bar
   **Agent API** button on older releases), enable the read-only
   connection and click **Copy connection details**. Copy any prompts first.
2. Call `connect_from_clipboard` once; it retains the secret in memory. Never
   inspect or echo the clipboard to diagnose it.
3. Read capabilities and overview. Check the returned workspace identity before
   acting. For edits the person also enables **Allow workspace editing**.
4. Continue with focused tools. Subsequent clipboard changes do not disconnect.

| Error | Recovery |
| --- | --- |
| `not_connected` | Perform the explicit handoff above. |
| `clipboard_unavailable` | Resolve host/OS clipboard access. macOS uses pbpaste, Windows PowerShell, Linux wl-paste or xclip. |
| `invalid_clipboard` | Copy connection details again; do not print the clipboard. |
| `local_access_denied` | Resolve permission to reach loopback on the desktop's machine. |
| `connection_unavailable` | Check the app and its connection toggle. |
| `access_revoked` / `instance_changed` | Explicitly reconnect to the chosen window. |
| `workspace_busy` / `editor_busy` / `connection_timeout` | Let loading/dialogs or typing finish. Retry an uncertain edit with the identical request UUID and arguments. |
| `read_only` | Workspace editing is not enabled; the person controls it in the desktop panel. |
| `edit_conflict` / `color_conflict` | Inspect current edit state and the intervening change before a new edit. |
| `workspace_changed` | Refresh identities and edit state; do not reuse the old epoch. |
| `request_id_reused` | Do not reuse a successful request UUID with different arguments. |
| `trace_not_found` / `dataset_not_found` | Refresh identity catalogs before selecting another object. |

After a repeated unchanged failure, report the specific blocker and needed
recovery; do not spin, scan for other windows, or disable authentication.
An adapter restart loses credentials. Separate agent hosts need separate handoffs.
There is no automatic window discovery or persistent credential store.
