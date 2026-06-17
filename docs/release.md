# Release Checklist

Quick Ternaries releases are GitHub Releases. The launcher updater reads
`https://api.github.com/repos/ariessunfeld/quick-ternaries/releases/latest`,
compares the latest release tag to the installed package version, and installs
from the corresponding tag archive.

Use version tags in the form `vX.Y.Z`. The repository also has launcher tags,
so check that you are working with the latest version tag, not a launcher tag.

## Prepare

1. Start from an up-to-date `main`.

   ```bash
   git switch main
   git pull --ff-only
   git fetch --tags --prune-tags
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
   ls -lh dist
   ```

   The release should include both:

   ```text
   dist/quick_ternaries-X.Y.Z-py3-none-any.whl
   dist/quick_ternaries-X.Y.Z.tar.gz
   ```

## Publish

1. Commit the version bump and any release-prep metadata changes.

   ```bash
   git status --short
   git add setup.cfg
   git commit -m "Bump package version for vX.Y.Z release"
   git push origin main
   ```

2. Tag the exact commit on `main`.

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. Create the GitHub Release and upload the wheel and source distribution.

   ```bash
   gh release create vX.Y.Z \
     dist/quick_ternaries-X.Y.Z-py3-none-any.whl \
     dist/quick_ternaries-X.Y.Z.tar.gz \
     --repo ariessunfeld/quick-ternaries \
     --target main \
     --title vX.Y.Z \
     --notes "Release notes go here."
   ```

4. Verify that GitHub now reports the new release as latest.

   ```bash
   gh release view --repo ariessunfeld/quick-ternaries \
     --json tagName,name,publishedAt,url,assets
   ```

5. Smoke-test the updater path in a disposable environment if the release
   affects install metadata or launch behavior.

   ```bash
   python -m pip install --upgrade \
     https://github.com/ariessunfeld/quick-ternaries/archive/tags/vX.Y.Z.tar.gz
   quick-ternaries
   ```
