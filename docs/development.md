# Local Development and Bug-Report Workflow

## Run the checked-out source

The existing `qtvenv` environment is an editable installation of this
repository. It is the quickest way to run whichever branch is currently
checked out:

```bash
source qtvenv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
quick-ternaries
```

Reinstall after dependency, packaging, or command-entry-point changes. Ordinary
Python source edits are available immediately through the editable install.

Before testing a remote branch, fetch it and confirm the checkout:

```bash
git fetch origin
git status --short --branch
git switch BRANCH_NAME
git pull --ff-only
```

## Test the released package

Use a separate environment outside the repository to test the same wheel an end
user installs:

```bash
python3.14 -m venv ../quick-ternaries-release-venv
source ../quick-ternaries-release-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ./dist/quick_ternaries-X.Y.Z-py3-none-any.whl
quick-ternaries
```

Recreate the environment for each release smoke test. The supported Python
range is 3.11 through 3.14; reproduce version-specific reports with the
reporter's Python version and rely on CI for the complete version matrix.

## Use reporter-provided data

Store original reporter files under `local-test-data/reporter-bug-summary/`.
That location is ignored by Git so large workbooks cannot be committed by
accident. Keep reproduction notes next to the original file.

Once the behavior is understood, create the smallest durable regression:

- Prefer a pytest fixture that generates a dataframe or temporary workbook.
- Commit a minimized workbook under `tests/data/` only when sheets, headers,
  cell types, or other file structure are required for the failure.
- Never make CI depend on `local-test-data/`.

Run the smallest relevant test while implementing, then run the entire suite:

```bash
python -m pytest tests/path/to/test_file.py -q
python -m pytest
```

## Build launcher archives

Launcher ZIPs are generated from the tracked text files in `launcher/`:

```bash
python scripts/build_launchers.py
```

The four deterministic archives are written to `dist/launchers/`, which is
ignored by Git. Do not edit files inside a ZIP. Change the corresponding source
file, run the launcher tests, rebuild, and upload the generated archive:

```bash
python -m pytest tests/test_launcher_build.py -q
python scripts/build_launchers.py
```

The Windows-conda launcher source is in `launcher/windows-conda-launcher/`;
`environment.yml` and `updater.py` are added from the shared files in
`launcher/` during the build.
