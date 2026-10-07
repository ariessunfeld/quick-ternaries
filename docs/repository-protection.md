# Repository protections

`main` is the trunk. Work on a short-lived branch, open a PR, and squash or
rebase it after validation. Repository settings enforce the following policy;
this document describes those settings rather than replacing them.

## Changes to main

- The `Main history and CI` ruleset requires linear history, blocks force pushes
  and deletion, and requires the GitHub Actions `CI passed` check against the
  current base. There are no bypass actors for this ruleset, including the owner.
- The `Main code review` ruleset requires a PR, one approving code-owner review,
  resolution of review threads, and approval of the latest reviewable push.
  New commits invalidate old approvals.
- `.github/CODEOWNERS` names `@ariessunfeld` for every file, including workflows
  and CODEOWNERS itself. Collaborators cannot merge their own approval or remove
  this requirement through an unreviewed PR.
- Only `ariessunfeld` can bypass the review rule, and only through a PR. This
  lets the owner merge owner-authored work without approving his own PR. It does
  not bypass CI or permit direct pushes to `main`.

`CI passed` is an always-running aggregate of the scope check, all applicable
macOS/Windows/Linux and Python install/test jobs, and the conda launcher check.
It fails for failed or cancelled required jobs and missing/invalid scope output.
Documentation-only changes can deliberately skip installation jobs and still
pass. Require this aggregate rather than optional matrix job names, which may
not exist when a matrix is skipped. The check is restricted to the GitHub Actions
integration; a status posted with a user token is not an equivalent result.

Keep the existing additional upgrade checks passing whenever they apply, as
required by the release checklist. They do not replace the mandatory CI check.

## Tags and publishing

The `Release tags controlled by owner` ruleset restricts creation, updates, and
deletion of **all tags** to `ariessunfeld`. This includes version tags and the
existing launcher tags. Protecting only `v*` would leave other tag names that
the updater can parse unprotected. Ordinary contributor branches remain usable.

The `pypi` environment accepts only branch `main` and tags `v*`, and requires
approval from `ariessunfeld`. Self-approval is allowed for that account so an
owner-initiated release is possible. GitHub's repository owner retains
administrative recovery authority. Follow the
[release checklist](release.md) and obtain Ari's explicit approval for a specific
release before an agent approves its deployment on his behalf.

## Limits and recovery

These settings separate development, review, and publishing responsibilities.
The owner account and owner-authorized credentials retain administrative access.
Protect GitHub and PyPI accounts with strong two-factor authentication and
review third-party application access.

Release immutability is intentionally disabled. GitHub's collaborator write role
still permits editing or deleting mutable release assets and metadata. Tag
protection secures the source refs used by the current updater; the separate
PyPI approval gate controls new PyPI uploads. They do not make downloadable
GitHub release assets immutable. Further separation of release management needs
a separate permissions decision.

If a credential is exposed, revoke or rotate it first. Deleting a release or
rewriting history cannot retract copies already downloaded, cloned, or cached.
The owner can remove mutable releases and use the owner-only tag exception for
necessary cleanup. Any exceptional change to main's history protections should
be deliberate, narrowly scoped, and restored immediately afterward. Never
weaken protections as a routine response to failing CI.
