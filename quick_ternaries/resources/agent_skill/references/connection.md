# Connection and recovery

The MCP server command is `quick-ternaries-mcp`, or the installed app environment's
absolute Python path followed by `-m quick_ternaries.agent_api.mcp`. It requires
the optional `agent` extra. This is a local stdio server; it does not launch a
window or make a cloud container able to reach the person's computer.

Find the existing installation from task context. Do not invent a developer
checkout or temporary environment. If installation or host registration is
needed, follow the matching release's `docs/agent-mcp.md` from the Quick Ternaries
repository, or ask for the app environment. Avoid updating a running app's
shared environment without coordinating with the person.

Host registration uses a command with an absolute executable path. No token,
port, or workspace-specific configuration belongs in host settings. Configure
Codex with `codex mcp add quick-ternaries -- /absolute/python -m
quick_ternaries.agent_api.mcp`; Claude Code uses `claude mcp add --transport stdio
quick-ternaries -- /absolute/python -m quick_ternaries.agent_api.mcp`.

1. Have the person open the desired window's Agent API panel, enable read-only
   access and copy connection details.
2. Call `connect_from_clipboard`; the adapter retains the secret in memory.
3. Read capabilities/overview. Check the returned instance and workspace identity.
4. Continue with focused tools. Copying other text afterward is fine.

| Error | Recovery |
| --- | --- |
| `not_connected` | Perform the explicit handoff above. |
| `clipboard_unavailable` | Resolve host/OS clipboard access. Linux needs wl-paste or xclip. |
| `invalid_clipboard` | Copy connection details again; do not print the clipboard. |
| `local_access_denied` | Resolve permission to reach loopback on the desktop's machine. |
| `connection_unavailable` | Check the app and its connection toggle. |
| `access_revoked` / `instance_changed` | Explicitly reconnect to the chosen window. |
| `workspace_busy` / `editor_busy` / `connection_timeout` | Let loading/dialogs finish; retry an uncertain edit using the identical request UUID and arguments. |
| `read_only` | Workspace editing is not enabled. The person controls permission in the desktop panel. |
| `edit_conflict` / `color_conflict` | Read current edit state and review the intervening change before a new edit. |
| `workspace_changed` | Refresh the overview and edit state; do not reuse the old workspace epoch. |
| `request_id_reused` | Do not reuse a successful request UUID with different arguments. |
| `trace_not_found` / `dataset_not_found` | Refresh identity catalogs before selecting another object. |

If the host restarts the adapter, its credentials are lost; repeat the handoff.
Separate agent hosts run separate adapters and need separate handoffs. This
release has no automatic discovery or persistent credential store.

For a host without MCP, the package also includes a persistent JSON-lines CLI:
`python -u -m quick_ternaries.agent_api session`. Its commands and private-pipe
handoff are described in the matching release's `docs/agent-api-session.md`.
Prefer MCP when available; do not improvise repeated one-shot clipboard clients.
