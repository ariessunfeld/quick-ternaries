# Repository working agreements

## Releases and updater compatibility

- Before preparing or publishing any package release, creating a version tag,
  or publishing launcher assets, **read `docs/release.md` in full** and follow
  its applicable checklist. Read the proposed release notes and verify that
  their feature and validation claims match the actual release contents.
- The release guide is the canonical procedure. Do not infer a release process
  from previous commands, a remembered version number, or this short summary.
- Package release tags must be exactly `vX.Y.Z` and match `setup.cfg`. Keep tags,
  display titles, and release-note text separate: updaters use `tag_name`, not
  the GitHub release display title. Verify the live fields after publication.
- Read the package and launcher updater implementations before changing update
  behavior. Test the previous released updater against the candidate package;
  a fresh install alone is not an upgrade test. Run the title/tag contract tests
  and the upgrade smoke test described in the release guide.
- Require passing applicable CI before publishing. Verify uploaded artifacts,
  the exact tagged commit, and the published update path afterward. Report
  failures or incomplete checks accurately; do not claim a release is verified
  solely because uploading succeeded.
- Keep release-specific instructions in `docs/release.md`; keep this mandatory
  reading rule here so coding agents discover it. `CONTRIBUTING.md` is the
  human-oriented entry point and links to the same guide.
