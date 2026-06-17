import io
import json
import subprocess

import pytest

from quick_ternaries import updater


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def fake_release_opener(tag_name):
    def opener(request, timeout):
        assert request.full_url == updater.LATEST_RELEASE_API
        assert timeout == updater.DEFAULT_TIMEOUT_SECONDS
        return FakeResponse(
            {
                "tag_name": tag_name,
                "html_url": f"https://github.com/example/releases/tag/{tag_name}",
            }
        )

    return opener


@pytest.mark.parametrize(
    ("candidate", "current", "expected"),
    [
        ("v1.1.0", "1.0.1", True),
        ("1.10.0", "1.9.9", True),
        ("v1.1.0", "1.1.0", False),
        ("v1.1.0", "1.1.1", False),
        ("v1.1", "1.1.0", False),
    ],
)
def test_is_newer_version_compares_numeric_parts(candidate, current, expected):
    assert updater.is_newer_version(candidate, current) is expected


def test_fetch_latest_release_builds_install_url():
    release = updater.fetch_latest_release(opener=fake_release_opener("v1.2.3"))

    assert release.tag_name == "v1.2.3"
    assert release.version == "1.2.3"
    assert release.install_url == (
        "https://github.com/ariessunfeld/quick-ternaries/archive/tags/"
        "v1.2.3.tar.gz"
    )


def test_fetch_latest_release_rejects_missing_tag():
    def opener(request, timeout):
        return FakeResponse({"html_url": "https://example.test/release"})

    with pytest.raises(updater.UpdateError, match="tag name"):
        updater.fetch_latest_release(opener=opener)


def test_run_update_command_skips_when_current(monkeypatch):
    stdout = io.StringIO()
    runner_calls = []

    monkeypatch.setattr(updater, "installed_version", lambda: "1.1.0")

    exit_code = updater.run_update_command(
        stdout=stdout,
        runner=lambda command: runner_calls.append(command),
        opener=fake_release_opener("v1.1.0"),
    )

    assert exit_code == 0
    assert runner_calls == []
    assert "already up to date" in stdout.getvalue()


def test_run_update_command_invokes_pip_for_newer_release(monkeypatch):
    stdout = io.StringIO()
    runner_calls = []

    monkeypatch.setattr(updater, "installed_version", lambda: "1.0.1")

    def runner(command):
        runner_calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    exit_code = updater.run_update_command(
        stdout=stdout,
        runner=runner,
        opener=fake_release_opener("v1.1.0"),
    )

    assert exit_code == 0
    assert runner_calls == [
        [
            updater.sys.executable,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "https://github.com/ariessunfeld/quick-ternaries/archive/tags/"
            "v1.1.0.tar.gz",
        ]
    ]
    assert "Update complete" in stdout.getvalue()


def test_run_update_command_returns_pip_failure(monkeypatch):
    stderr = io.StringIO()

    monkeypatch.setattr(updater, "installed_version", lambda: "1.0.1")

    def runner(command):
        return subprocess.CompletedProcess(command, 17)

    exit_code = updater.run_update_command(
        stderr=stderr,
        runner=runner,
        opener=fake_release_opener("v1.1.0"),
    )

    assert exit_code == 17
    assert "update failed" in stderr.getvalue()


def test_main_update_path_uses_updater_without_launching_gui(monkeypatch):
    from quick_ternaries import main as main_module

    monkeypatch.setattr(updater, "run_update_command", lambda: 23)

    assert main_module.main(["--update"]) == 23
