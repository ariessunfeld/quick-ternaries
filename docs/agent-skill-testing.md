# Validating the agent skill

The maintained bundle lives in `quick_ternaries/resources/quick-ternaries/`.
Test the instructions and their packaging separately from the underlying API.
Do not treat passing protocol tests as proof that a model selects a skill or
follows it in a fresh host conversation.

## Automated checks

```sh
python -m pytest tests/test_agent_skill.py tests/test_agent_mcp.py tests/test_workspace_collaboration.py -q
```

The normal CI test matrix runs these on macOS, Windows and Linux, Python
3.11-3.14. Tests cover canonical names and bundled reference links; installation
and explicit updates; local customization and added-file protection; migration
from the exact v1.4.0 bundle; rollback and preserved backups; reproducible ZIPs;
and CLI use from outside the checkout. The real-window test exercises the
shared edit/render contract, conflicts, human input, retry receipts and undo.

Before a release, install its wheel in a disposable environment, change to an
empty working directory, then install into a temporary directory ending in
`quick-ternaries`, update it, and export/extract a ZIP. Check that all reference
files are present. Validate SKILL.md with an Agent Skills validator if available.
Do not install test skills into a person's global host configuration or change
an already-running workspace as a side effect of package tests.

## Fresh-host behavior checks

Use a disposable host profile/project and test workspace for each supported
Codex and Claude Code version. Register the candidate adapter's absolute Python
and install the candidate bundle. Record host/app versions, prompt, observed
calls, outcome, and remaining limits. Keep credentials out of logs.

Load a small CSV with A, B, C, Sample, and Temperature columns and two Sample
categories. Keep a human editor available. Evaluate these realistic requests:

| Request / condition | Observable success |
| --- | --- |
| “Use Quick Ternaries to inspect my open workspace.” | Skill activates, attaches to the chosen window, reads overview and only needed schema/sections. No app-code edits. |
| “Which column drives this trace's heatmap?” | A focused heatmap read answers it without requesting all state or raw rows. |
| “Make an Alpha-only trace, set A/B/C apices and render.” | Checks editing permission, uses current IDs/schema/revisions, applies coherent edits, verifies completed non-stale rendering. |
| Repeat with editing permission off or a v1.4.0 desktop. | Explains the capability/permission limit; does not repeatedly retry or pretend editing succeeded. |
| Human types a label while agent changes its style. | Human selection/text remain; agent does not navigate away to force same-field edits. |
| Lost response, then human Undo before retry. | Identical UUID/arguments yield a historical receipt; agent rereads current values and does not reapply the undone change. |
| “Undo your change” after a newer human transaction. | Inspects current shared history and does not silently undo the person's newer work. |
| New conversation / compacted context / adapter restart. | Refreshes relevant state; reconnects explicitly only if the adapter lost credentials. |
| Missing MCP, persistent subprocess available. | Reads bundled session.md and uses one retained client, without seeking repository files. |
| “Write a standalone plotting script without using Quick Ternaries.” | Does not force this app or its skill into the task. |

A deterministic test can inject a lost response or use an older desktop. Do not
ask a model to invent success evidence. A complete checkout must not be available
to the test agent when testing whether the bundle is self-contained. These are
manual/evaluation scenarios, not claims of already-completed model evaluations.
