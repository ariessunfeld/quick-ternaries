import hashlib
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = PROJECT_ROOT / "scripts" / "build_launchers.py"


EXPECTED_MEMBERS = {
    "quick-ternaries-mac-launcher.zip": {
        "updater.py",
        "requirements.txt",
        "quick-ternaries_mac.command",
    },
    "quick-ternaries-windows-launcher.zip": {
        "updater.py",
        "requirements.txt",
        "quick-ternaries_windows.bat",
    },
    "quick-ternaries-mac-conda-launcher.zip": {
        "environment.yml",
        "quick-ternaries_mac_conda.command",
        "updater.py",
    },
    "QuickTernaries.zip": {
        "QuickTernaries/setup.bat",
        "QuickTernaries/TemplateLauncher.bat",
        "QuickTernaries/environment.yml",
        "QuickTernaries/updater.py",
    },
}


def _build(output_dir):
    subprocess.run(
        [sys.executable, BUILD_SCRIPT, "--output-dir", output_dir],
        cwd=PROJECT_ROOT,
        check=True,
    )


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_launcher_build_is_complete_and_deterministic(tmp_path):
    _build(tmp_path)
    first_hashes = {path.name: _sha256(path) for path in tmp_path.glob("*.zip")}

    _build(tmp_path)
    second_hashes = {path.name: _sha256(path) for path in tmp_path.glob("*.zip")}

    assert first_hashes == second_hashes
    assert first_hashes.keys() == EXPECTED_MEMBERS.keys()

    for archive_name, expected_members in EXPECTED_MEMBERS.items():
        with ZipFile(tmp_path / archive_name) as archive:
            assert set(archive.namelist()) == expected_members


def test_launcher_archives_contain_current_source_files(tmp_path):
    _build(tmp_path)

    with ZipFile(tmp_path / "quick-ternaries-mac-launcher.zip") as archive:
        assert archive.read("updater.py") == (PROJECT_ROOT / "launcher/updater.py").read_bytes()
        assert archive.read("requirements.txt") == (
            PROJECT_ROOT / "launcher/requirements.txt"
        ).read_bytes()

    with ZipFile(tmp_path / "QuickTernaries.zip") as archive:
        assert archive.read("QuickTernaries/setup.bat") == (
            PROJECT_ROOT / "launcher/windows-conda-launcher/setup.bat"
        ).read_bytes()
        assert archive.read("QuickTernaries/environment.yml") == (
            PROJECT_ROOT / "launcher/environment.yml"
        ).read_bytes()
