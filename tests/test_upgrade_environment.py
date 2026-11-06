"""Upgrade probes inherit dependencies without importing the source checkout."""

import os
from pathlib import Path
import subprocess
import venv

from scripts import check_upgrade


def test_virtualenv_dependencies_do_not_shadow_candidate_or_run_parent_hooks(tmp_path, monkeypatch):
    parent = tmp_path / 'parent-packages'
    parent.mkdir()
    (parent / 'validated_dependency.py').write_text('VALUE = 17\n')
    (parent / 'candidate.py').write_text("VALUE = 'parent'\n")
    # Processing a parent editable-install hook would invalidate the test.
    (parent / 'editable.pth').write_text("import os; os.environ['PARENT_HOOK_RAN'] = 'yes'\n")
    child = tmp_path / 'probe'
    venv.EnvBuilder(with_pip=False).create(child)
    python = child / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    monkeypatch.setattr(check_upgrade.sysconfig, 'get_path', lambda _: str(parent))
    check_upgrade.inherit_validated_dependencies(python)
    site = subprocess.check_output([str(python), '-I', '-c',
        "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip()
    (Path(site) / 'candidate.py').write_text("VALUE = 'child'\n")
    subprocess.run([str(python), '-I', '-c',
        "import os, candidate, validated_dependency; "
        "assert candidate.VALUE == 'child'; "
        "assert validated_dependency.VALUE == 17; "
        "assert 'PARENT_HOOK_RAN' not in os.environ"], cwd=tmp_path, check=True)
