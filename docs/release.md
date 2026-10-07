# Release Checklist

Quick Ternaries releases are GitHub Releases. The launcher updater reads
`https://api.github.com/repos/ariessunfeld/quick-ternaries/releases/latest`,
compares the latest release tag to the installed package version, and installs
from the corresponding tag archive.

Use version tags in the form `vX.Y.Z`. The repository also has launcher tags,
so check that you are working with the latest version tag, not a launcher tag.

The GitHub **tag** (`tag_name`), **display title** (`name`), and release notes
are separate fields. All current package/launcher updaters use `tag_name`.
A title such as `v1.3.0 — Keyboard navigation and accessibility` is safe when
the tag is exactly `v1.3.0`. Never put descriptive text in the version tag.
Release notes do not configure the updater; this guide and automated tests
enforce the publishing procedure.

## Prepare

1. Start from a clean checkout of up-to-date `main` and create a release branch.
   Preserve unrelated work in other checkouts; do not reset or stash it as part
   of releasing.

   ```bash
   git switch main
   git pull --ff-only
   git fetch --tags
   git switch -c codex/release-X-Y-Z
   ```

2. Choose the next semantic version.

   Patch releases fix bugs, minor releases add user-visible features, and major
   releases can break compatibility. Update `setup.cfg` only after deciding the
   version.

3. Refresh the local environment and run checks.

   ```bash
   python -m pip install -e ".[test]" build
   python -m pip check
   python -m pytest -q
   ```

4. Build release artifacts.

   ```bash
   python -m build --sdist --wheel
   python -m quick_ternaries.agent_api.mcp --export-skill dist/quick-ternaries-skill-X.Y.Z.zip
   ls -lh dist
   ```

   The release should include all three artifacts:

   ```text
   dist/quick_ternaries-X.Y.Z-py3-none-any.whl
   dist/quick_ternaries-X.Y.Z.tar.gz
   dist/quick-ternaries-skill-X.Y.Z.zip
   ```

   Build the skill ZIP with the candidate package installed; the exporter uses
   its bundled resources, never a second hand-maintained copy. Follow
   [skill validation](agent-skill-testing.md): verify installation/update/export
   from the wheel outside the checkout and exercise the host setup and behavior
   scenarios for supported Codex/Claude versions. Record automated and manual
   evidence separately. Update development-only wording in the integration docs
   when preparing the release; do not claim earlier tags include new tools.

5. Test upgrades using the previous release's code, before publishing.

   Run the updater contract tests and the isolated upgrade smoke test:

   ```bash
   python -m pytest tests/test_utils/test_updater.py tests/test_launcher_updater.py -q
   python scripts/check_upgrade.py --from-ref v1.2.2 --wheel-dir dist
   ```

   Replace `v1.2.2` with the previous package release when preparing a newer
   release. Fetch that exact tag if it is missing locally. The script builds
   that release, installs it in disposable environments, executes its package
   CLI and both launcher updater variants, then verifies the candidate version
   and entry point. It substitutes only GitHub's release metadata and the
   artifact download location; pip performs the real installation. Dependencies
   come from the already validated parent environment, so this test complements
   the full install matrix rather than repeating dependency downloads.

   The focused upgrade CI workflow runs this on macOS, Windows, and Linux.
   Keep its `PREVIOUS_RELEASE` baseline current when bumping the package version.
   Review the release notes against the tagged changes and actual check results.

## Publish

1. Commit the version bump and release-prep metadata changes on the release
   branch. Push it and open a pull request against `main`. Require the applicable
   install, test, and upgrade checks to pass before merging.

   ```bash
   git status --short
   git add setup.cfg
   git commit -m "Bump package version for vX.Y.Z release"
   git push -u origin codex/release-X-Y-Z
   gh pr create --base main --head codex/release-X-Y-Z
   ```

2. After the release pull request is merged, update the clean checkout to
   `main`. Build the final artifacts from that merged commit into a fresh output
   directory, and rerun the candidate upgrade smoke test against them. Tag that
   exact commit, not the earlier release-branch commit.

   ```bash
   git switch main
   git pull --ff-only
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. Create the GitHub Release and upload the wheel, source distribution, and portable skill ZIP.

   ```bash
   gh release create vX.Y.Z \
     dist/quick_ternaries-X.Y.Z-py3-none-any.whl \
     dist/quick_ternaries-X.Y.Z.tar.gz \
     dist/quick-ternaries-skill-X.Y.Z.zip \
     --repo ariessunfeld/quick-ternaries \
     --target main \
     --title vX.Y.Z \
     --notes-file /path/to/reviewed-release-notes.md
   ```

4. Verify that GitHub now reports the new release as latest.

   ```bash
   gh release view --repo ariessunfeld/quick-ternaries \
     --json tagName,name,publishedAt,url,assets
   ```

   Verify `tagName` is exactly `vX.Y.Z`, independently of `name`. Download the
   wheel, source archive and skill ZIP and compare their SHA-256 digests to the tested
   local artifacts. Confirm the tag resolves to the intended commit on `main`.

5. Smoke-test the published updater path from the previous version in a
   disposable environment. The normal launcher activation must put that
   environment's Python first on PATH.

   ```bash
   python -m pip install \
     https://github.com/ariessunfeld/quick-ternaries/archive/tags/vPREVIOUS.tar.gz
   quick-ternaries --update
   python -m pip show quick-ternaries
   python -m pip check
   ```

   Substitute the real previous tag, verify the installed version becomes the
   newly published version, and start the application. Unlike the candidate CI
   test, this checks GitHub's live latest-release selection and archive URL.
   Keep live-network smoke checks in the release process: ordinary PR tests
   must not change behavior when a different release becomes "latest".

## Launcher Releases

Launcher archives are generated from tracked source files. Never modify a ZIP
by hand or use a cloud-only copy as the source of truth.

1. Update the launcher source files and run the tests.

   ```bash
   python -m pytest tests/test_launcher_build.py -q
   python scripts/build_launchers.py
   ```

2. Inspect the generated files under `dist/launchers/`.

   ```text
   quick-ternaries-mac-launcher.zip
   quick-ternaries-windows-launcher.zip
   quick-ternaries-mac-conda-launcher.zip
   QuickTernaries.zip
   ```

3. Upload the appropriate generated file to its existing launcher release.
   Use `--clobber` only after confirming the tag and filename.

   ```bash
   gh release upload mac-launcher \
     dist/launchers/quick-ternaries-mac-launcher.zip \
     --repo ariessunfeld/quick-ternaries --clobber
   ```

   The corresponding tags are `windows-launcher`, `mac-conda-launcher`, and
   `windows-conda-launcher-2025-02-25`.

4. Download the published asset and compare its SHA-256 digest with the local
   generated archive before considering the launcher update complete.
