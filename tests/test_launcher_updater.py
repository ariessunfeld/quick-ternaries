"""Keep both shipped launcher updaters independent of release display titles."""

import importlib.util
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
UPDATERS = ["launcher/updater.py", "launcher/quick-ternaries-mac-conda-launcher/updater.py"]


@pytest.mark.parametrize("path", UPDATERS)
@pytest.mark.parametrize("os_name,python", [("posix", "python3"), ("nt", "python")])
@pytest.mark.parametrize("proxy", [False, True])
def test_previous_version_launcher_uses_tag_not_title(path, os_name, python, proxy, monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("launcher_under_test", ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = {"tag_name": "v1.3.0", "name": "v1.3.0 — Accessible controls 🚀",
               "body": "Release notes are not a version."}
    monkeypatch.setattr(module.requests, "get", lambda url: SimpleNamespace(json=lambda: payload))
    monkeypatch.setattr(module, "version", lambda name: "1.2.2")
    # Replace this module's os binding, not process-wide os.name/Path behavior.
    monkeypatch.setattr(module, "os", SimpleNamespace(name=os_name))
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    has_proxy = hasattr(module, "can_connect_to_proxy")
    if has_proxy:
        monkeypatch.setattr(module, "can_connect_to_proxy", lambda url: proxy)
    commands = []
    monkeypatch.setattr(module.subprocess, "run", lambda command, **kwargs:
                        commands.append(command) or subprocess.CompletedProcess(command, 0))
    module.update_to_latest("ariessunfeld", "quick-ternaries", "quick-ternaries", tmp_path / "update.log")
    expected_proxy = " --proxy=http://proxyout.lanl.gov:8080" if proxy and has_proxy else ""
    assert commands == [f"{python} -m pip install{expected_proxy} --upgrade "
                        "https://github.com/ariessunfeld/quick-ternaries/archive/tags/v1.3.0.tar.gz"]
