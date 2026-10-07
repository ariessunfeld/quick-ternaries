"""Exercise the complete window in a fresh interpreter, including cold caches."""

import json
import logging
import os
from pathlib import Path
import subprocess
import sys


def test_window_starts_without_image_exports_or_optional_science_imports(tmp_path):
    script = """
import json
import sys
from time import perf_counter

start = perf_counter()
from PySide6.QtGui import QAccessible
from PySide6.QtWidgets import QApplication, QWidget
from quick_ternaries.app import MainWindow
import plotly.io as pio
imports_done = perf_counter()

exports = []
def unexpected_export(*args, **kwargs):
    exports.append(True)
    raise AssertionError('Startup must not export Plotly images')
pio.to_image = unexpected_export

app = QApplication([])
construction_start = perf_counter()
window = MainWindow()
window.show()
app.processEvents()
assert window.isVisible()
assert window.windowTitle() == 'Quick Ternaries'
identifiers = [widget.accessibleIdentifier() for widget in window.findChildren(QWidget)
               if widget.accessibleIdentifier()]
assert len(identifiers) == len(set(identifiers)), identifiers
render = QAccessible.queryAccessibleInterface(window.previewButton)
assert render.text(QAccessible.Text.Identifier) == 'workspace.render'
assert render.text(QAccessible.Text.Name) == window.previewButton.text()
assert not exports, exports
assert 'scipy.stats' not in sys.modules
assert 'matplotlib' not in sys.modules
assert 'h11' not in sys.modules
assert 'mcp' not in sys.modules
assert window.agent_dialog is None
window.agentButton.click()
assert not window.agent_dialog.api.running
window.agent_dialog.toggle.click()
assert window.agent_dialog.api.running
assert window.agent_dialog.api._reader.snapshot()['trace_count'] == 0
print('STARTUP_RESULT ' + json.dumps({
    'imports_seconds': imports_done - start,
    'window_seconds': perf_counter() - construction_start,
    'total_seconds': perf_counter() - start,
    'icon_exports': len(exports),
}))
window.close()
assert not window.agent_dialog.api.running
"""
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.update(QT_QPA_PLATFORM="offscreen", MPLBACKEND="Agg")
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(project_root), env.get("PYTHONPATH")]))
    # Simulate a new install's empty Python/Matplotlib caches without disturbing
    # developer caches. Timings are diagnostic, not a machine-dependent deadline.
    env["PYTHONPYCACHEPREFIX"] = str(tmp_path / "pycache")
    env["MPLCONFIGDIR"] = str(tmp_path / "matplotlib")
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=tmp_path, env=env,
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    line = next(line for line in result.stdout.splitlines() if line.startswith("STARTUP_RESULT "))
    timings = json.loads(line.removeprefix("STARTUP_RESULT "))
    logging.getLogger(__name__).info("Startup timings (%s): %s", sys.platform, timings)
