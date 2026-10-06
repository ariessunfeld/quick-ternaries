# Local Development and Bug-Report Workflow

The [agent integration architecture](agent-integration.md) describes the planned
live API, shared command boundary, accessibility work, and staged validation.

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

## Keep startup previews inexpensive

Color-scale previews use Qt gradients with Plotly's color stops. Marker previews
are bundled SVGs under `quick_ternaries/resources/markers/`, generated from
Plotly's own marker paths. Keep these assets in both the wheel and source
distribution (see `setup.cfg`). Window construction must not call Plotly's image
exporter: doing so starts Kaleido/Chrome repeatedly before the window appears.

After changing the supported marker list, regenerate the SVGs and review them:

```bash
python scripts/build_marker_icons.py
python -m pytest tests/test_views/test_preview_icons.py tests/test_startup.py -q
```

Regeneration needs Kaleido and, for Kaleido 1.x, Chrome. Displaying the controls
does not. Actual chart image exports still use the normal Plotly export path.
SciPy statistics and Matplotlib load only when a contour or correlation plot
needs them.

The startup regression opens the complete window in a separate interpreter with
empty Python and Matplotlib caches, rejects any image-export attempts, and logs
timings on every CI platform. These timings are diagnostics, not a fixed speed
requirement; they do not simulate a cold OS disk cache or antivirus scanning.

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
