# Read-only agent API improvement plan

Active branch: `codex/agent-api-readonly`; draft PR #39. Baseline: `42f39365`.
Updated 2026-10-06. This file is the durable execution checklist; update it as
work finishes so a resumed agent can continue without relying on chat history.

## Outcome and boundaries

Address the terminal trial: clipboard access failed under the sandbox; repeated
short-lived clients lost credentials; full snapshots repeated irrelevant data;
heatmap changes were invisible; an unchanged partial projection was ambiguous.

Keep the desktop API opt-in and read-only. Do not restart the user's running
window or disturb their workspace/client. No Qt/scientific dependency changes,
release, merge, automatic credential discovery, or write endpoints in this work.
Use this existing worktree and PR. Preserve other checkouts and their changes.

## Implementation sequence

- [x] Focused read contract: compact overview; individual trace sections including
  all heatmap controls; paginated dataset columns and filters; explicit included
  and excluded coverage. Preserve the existing workspace endpoint for inspection.
- [x] Change tracking: bounded connection-scoped cursors, observed read revisions,
  changed/added/deleted object IDs, coalesced net changes and explicit resync when
  a cursor expires or a workspace is replaced. Scope claims to exposed fields;
  these are not document revisions or future write preconditions. No background
  polling or model notifications on each keystroke.
- [x] Persistent client: packaged JSON-lines stdio session that retains credentials
  in memory after one handoff; subsequent commands never reread the clipboard.
  Compact results, focused comparisons, explicit refresh, reconnect and quit.
  Distinguish clipboard unavailable/invalid, bad credentials, disconnected app,
  changed instance, invalid request, and expired cursor without echoing secrets.
  This session protocol is not MCP; the future MCP adapter can reuse the client.
- [x] Portable skill and documentation: use the skill-creator guidance; teach
  session lifetime, compact-first reads, coverage, freshness, and scientific
  limitations. Keep maintained schemas in the API guide rather than the skill.
- [x] Tests: real TCP and persistent subprocess scenarios, clipboard replacement,
  live heatmap/filter edits, unchanged reads, independent clients, cursor expiry,
  object deletion/workspace replacement, pagination and malformed requests,
  redaction/limits, and existing read-only/auth/lifecycle regression coverage.
- [ ] Validation: focused suite, full local suite, package/entry-point check,
  then push and require the existing macOS/Windows/Linux Python 3.11–3.14 CI
  matrix on the final PR head. Update PR title/body around the final change.

## Acceptance scenarios

1. Connect once, overwrite the clipboard, then successfully make multiple reads
   using the same client process without copying credentials again.
2. Fetch an overview; read one trace's heatmap settings; change its column,
   colorscale, bounds or transform in the model; fetch a focused result showing
   the change without retransmitting dataset schemas or other traces.
3. Repeated reads with no exposed changes return a compact unchanged result;
   a forced refresh returns current requested values after context compaction.
4. Changes outside the exposed schema are never claimed absent. Cursors and
   fingerprints cannot be mistaken for whole-document write guards.
5. Disconnect/restart invalidates old credentials/cursors; explicit reconnect
   resets client caches. No token reaches stdout, command arguments or files.

## Progress and evidence

- Plan saved before implementation. Initial PR baseline passed 196 local tests
  and 18 CI jobs. Implementation is ready for the draft PR's cross-platform CI.
- First expanded socket/session suite passed 47 tests. Full local Python 3.12
  suite passed **229 tests** including clipboard diagnostics and revocation;
  evidence is in `/private/tmp/qt-api-full.log`.
- Portable skill created at `skills/quick-ternaries/SKILL.md` and validated with
  the skill-creator validator. Personal agent configuration is unchanged.
- Final focused suite passed **61 tests** after compact-response refinements.
  The wheel built successfully using the normal isolated build, contains all
  nine API modules, and its extracted package passed a session startup/quit
  smoke test from outside the checkout with isolated Python import paths.
- Read-only observation revisions deliberately cover the bounded public schema;
  focused reads can access objects/pages beyond the tracking limits. Truncated
  tracking results require resync, never an unqualified unchanged claim.
- Pending: commit/push, check final-head cross-platform CI, and update PR #39's
  description and this record with the results. The user's open app is still
  running the earlier code; save/restart is needed to use these new endpoints.

## Follow-on work

Shared document ownership, durable IDs, serializer migration, real document
revisions, validated commands/undo, official-SDK MCP packaging, secure discovery,
and native Windows/Linux accessibility audits remain separate milestones.
