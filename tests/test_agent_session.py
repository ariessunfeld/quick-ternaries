"""Clipboard bootstrap and persistent-client input boundaries without a desktop."""

import io
import json
import subprocess
import sys

import pytest

from quick_ternaries.agent_api.contract import ApiError
from quick_ternaries.agent_api import session as module


@pytest.mark.parametrize("platform,wayland,expected", [
    ("darwin", False, "pbpaste"), ("win32", False, "powershell.exe"),
    ("linux", True, "wl-paste"), ("linux", False, "xclip"),
])
def test_clipboard_bootstrap_commands_are_portable_and_credentials_stay_in_memory(monkeypatch, platform, wayland, expected):
    details = {"url": "http://127.0.0.1:12345", "instance_id": "synthetic-instance",
               "token": "a" * 43, "protocol_version": 1}
    real_popen = subprocess.Popen
    commands = []
    def popen(command, **kwargs):
        commands.append(command)
        # Execute a harmless stand-in, preserving real pipe/process behavior.
        return real_popen([sys.executable, "-c", "import sys; sys.stdout.write(" + repr(json.dumps(details)) + ")"], **kwargs)
    monkeypatch.setattr(module.sys, "platform", platform)
    monkeypatch.setattr(module.shutil, "which", lambda name: name if name == "xclip" or wayland else None)
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    assert module.clipboard_connection() == details
    assert commands[0][0] == expected
    assert details["token"] not in str(commands)


@pytest.mark.parametrize("output,returncode,expected", [
    ("", 1, "clipboard_unavailable"), ("Copied other text", 0, "invalid_clipboard"),
    ("", 0, "invalid_clipboard"), ("x" * (module.MAX_INPUT_BYTES + 1), 0, "invalid_clipboard"),
], ids=["denied", "unrelated-text", "empty", "oversized"])
def test_clipboard_failures_distinguish_access_from_contents_without_echo(monkeypatch, output, returncode, expected):
    real_popen = subprocess.Popen
    def popen(command, **kwargs):
        return real_popen([sys.executable, "-c", "import sys; sys.stdout.write(" + repr(output) + "); sys.exit(" + str(returncode) + ")"], **kwargs)
    monkeypatch.setattr(module.sys, "platform", "darwin")
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    with pytest.raises(ApiError) as error:
        module.clipboard_connection()
    assert error.value.code == expected
    assert "Copied other text" not in str(error.value)


def test_clipboard_permission_error_is_redacted(monkeypatch):
    monkeypatch.setattr(module.sys, "platform", "darwin")
    def blocked(*args, **kwargs):
        raise PermissionError("private clipboard details")
    monkeypatch.setattr(module.subprocess, "Popen", blocked)
    with pytest.raises(ApiError) as error:
        module.clipboard_connection()
    assert error.value.code == "clipboard_unavailable"
    assert "private clipboard details" not in str(error.value)


def test_clipboard_timeout_terminates_reader(monkeypatch):
    real_popen = subprocess.Popen
    children = []
    def popen(command, **kwargs):
        child = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(module.sys, "platform", "darwin")
    monkeypatch.setattr(module.subprocess, "Popen", popen)
    with pytest.raises(ApiError) as error:
        module.clipboard_connection()
    assert error.value.code == "clipboard_unavailable"
    assert children[0].poll() is not None


def test_bad_session_commands_and_oversized_input_never_echo_secrets():
    secret = "synthetic-secret-never-echo"
    stream = io.StringIO("malformed " + secret + '\n{"op":"read"}\n{"op":"quit"}\n')
    output = io.StringIO()
    assert module.run_session(stream, output) == 0
    results = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [r.get("error") for r in results] == [None, "invalid_json", "not_connected", None]
    assert secret not in output.getvalue()
    output = io.StringIO()
    assert module.run_session(io.StringIO("x" * (module.MAX_INPUT_BYTES + 1)), output) == 1
    assert json.loads(output.getvalue().splitlines()[-1])["error"] == "command_too_large"


def test_interactive_session_refuses_credentials_that_terminal_would_echo():
    class Terminal(io.StringIO):
        def isatty(self):
            return True
    output = io.StringIO()
    assert module.run_session(Terminal('{"op":"connect","connection":{"token":"secret"}}\n{"op":"quit"}\n'), output) == 0
    assert "private_stdin_required" in output.getvalue()
    assert '"token"' not in output.getvalue()


def test_cache_has_bounded_memory_and_eviction_requires_fresh_results(monkeypatch):
    monkeypatch.setattr(module, "MAX_CACHE_BYTES", 1000)
    monkeypatch.setattr(module, "MAX_CACHE_ENTRIES", 2)
    session = module.Session()
    session.remember("a", {"value": "x" * 300})
    session.remember("b", {"value": "x" * 300})
    session.remember("c", {"value": "x" * 300})
    assert list(session.cache) == ["b", "c"]
    assert session.cache_bytes <= 1000
    session.remember("d", {"value": "x" * 2000})
    assert "d" not in session.cache
    session.close()
    assert session.cache_bytes == 0 and not session.cache
