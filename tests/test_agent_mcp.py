"""MCP contract through the official SDK, real stdio, and Qt loopback API."""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from time import sleep

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from quick_ternaries.agent_api.mcp import create_server, install_skill
from quick_ternaries.agent_api.session import Session
from test_agent_api import app, window, live_api, in_client_thread


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_official_sdk_reads_and_explicit_changes(app, window, live_api, mode):
    details = live_api.connection_details()
    copies = []
    def clipboard():
        copies.append(True)
        return details
    session = Session(clipboard)
    server = create_server(session)

    async def scenario():
        async with Client(server, mode=mode) as client:
            tools = (await client.list_tools()).tools
            names = {t.name for t in tools}
            assert names == {"connect_from_clipboard", "disconnect", "get_capabilities", "get_workspace_overview",
                             "get_plot_settings", "list_traces", "list_datasets", "get_trace", "get_dataset_schema", "get_changes", "get_trace_color_state", "set_trace_color"}
            assert all(t.annotations.read_only_hint for t in tools if t.name not in ("connect_from_clipboard", "disconnect", "set_trace_color"))
            missing = await client.call_tool("get_workspace_overview")
            assert missing.is_error and missing.structured_content["error"] == "not_connected"
            connected = await client.call_tool("connect_from_clipboard")
            assert not connected.is_error
            overview = (await client.call_tool("get_workspace_overview")).structured_content["result"]
            for tool in ("get_plot_settings", "list_traces", "list_datasets", "get_capabilities"):
                assert not (await client.call_tool(tool)).is_error
            dataset_id = overview["datasets"][0]["id"]
            assert not (await client.call_tool("get_dataset_schema", {"dataset_id": dataset_id})).is_error
            uid = overview["traces"][0]["id"]
            args = {"trace_id": uid, "sections": ["heatmap"]}
            for _ in range(2):
                current = await client.call_tool("get_trace", args)
                assert not current.is_error
                assert current.structured_content["status"] == "snapshot"
                assert "heatmap" in current.structured_content["result"]["trace"]
            changes = await client.call_tool("get_changes", {"since": overview["read_state"]["cursor"]})
            assert changes.structured_content["result"]["changes"]["unchanged"]
            for name, arguments in [("get_trace", {"trace_id": "invalid", "sections": ["heatmap"]}),
                                    ("get_trace", {"trace_id": uid, "sections": ["arbitrary"]}),
                                    ("list_traces", {"limit": 101}), ("list_traces", {"limit": True}),
                                    ("get_changes", {})]:
                assert (await client.call_tool(name, arguments)).is_error
            assert len(copies) == 1
            assert details["token"] not in connected.model_dump_json()
            assert not (await client.call_tool("disconnect")).is_error
            assert (await client.call_tool("get_plot_settings")).is_error
    in_client_thread(app, lambda: asyncio.run(scenario()))
    assert session.connection is None


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_stdio_real_desktop_no_repeated_clipboard_or_secret_output(app, window, live_api, tmp_path, mode):
    wrapper = tmp_path / 'server.py'
    wrapper.write_text('''import json, os
from quick_ternaries.agent_api.mcp import create_server
from quick_ternaries.agent_api.session import Session
def clipboard():
    return json.loads(os.environ.pop("QT_TEST_CONNECTION"))
create_server(Session(clipboard)).run(transport="stdio")
''')
    details = live_api.connection_details()
    params = StdioServerParameters(command=sys.executable, args=[str(wrapper)], env={
        **os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1]),
        "QT_TEST_CONNECTION": json.dumps(details),
    })
    async def scenario():
        async with Client(params, mode=mode, read_timeout_seconds=5) as client:
            assert len((await client.list_tools()).tools) == 12
            assert not (await client.call_tool("connect_from_clipboard")).is_error
            for _ in range(3):
                result = await client.call_tool("get_workspace_overview")
                assert not result.is_error
                assert details["token"] not in result.model_dump_json()
            assert not (await client.call_tool("disconnect")).is_error
            assert (await client.call_tool("get_workspace_overview")).is_error
    in_client_thread(app, lambda: asyncio.run(scenario()))


def test_adapters_do_not_share_attachment_or_cache(app, live_api):
    first = create_server(Session(lambda: live_api.connection_details()))
    second = create_server()
    async def scenario():
        async with Client(first) as a, Client(second) as b:
            assert not (await a.call_tool("connect_from_clipboard")).is_error
            assert (await b.call_tool("get_workspace_overview")).is_error
            assert not (await a.call_tool("get_workspace_overview")).is_error
    in_client_thread(app, lambda: asyncio.run(scenario()))


def test_reconnect_read_calls_are_serialized_and_unexpected_errors_redacted():
    class ConcurrentSession:
        active = False
        def execute(self, command):
            assert not self.active
            self.active = True
            try:
                sleep(0.02)
                if command["op"] == "disconnect":
                    raise RuntimeError("private token and data")
                return {"status": "snapshot"}
            finally:
                self.active = False
    async def scenario():
        async with Client(create_server(ConcurrentSession())) as client:
            results = await asyncio.gather(*(client.call_tool("get_workspace_overview") for _ in range(4)))
            assert all(not r.is_error for r in results)
            error = await client.call_tool("disconnect")
            assert error.is_error
            assert error.structured_content["error"] == "adapter_error"
            assert "private" not in error.model_dump_json()
    asyncio.run(scenario())


def test_bundled_skill_install_preserves_existing_customizations(tmp_path):
    target = tmp_path / 'skill'
    install_skill(target)
    assert (target / 'references/connection.md').exists()
    install_skill(target)
    customized = target / 'SKILL.md'
    customized.write_text('custom instructions')
    with pytest.raises(ValueError, match='Existing skill differs'):
        install_skill(target)
    assert customized.read_text() == 'custom instructions'


def test_mcp_module_import_and_skill_install_do_not_import_qt_or_sdk(tmp_path):
    script = '''import sys
from quick_ternaries.agent_api.mcp import install_skill
assert 'mcp' not in sys.modules
assert not any(k.startswith('PySide6') for k in sys.modules)
install_skill(sys.argv[1])
'''
    result = subprocess.run([sys.executable, '-c', script, str(tmp_path/'skill')], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_mcp_revocation_clears_attachment_and_reports_tool_error(app, live_api):
    details = live_api.connection_details()
    session = Session(lambda: details)
    server = create_server(session)
    async def connect():
        async with Client(server) as client:
            assert not (await client.call_tool("connect_from_clipboard")).is_error
    in_client_thread(app, lambda: asyncio.run(connect()))
    live_api._token = "revoked-" * 8
    async def read():
        async with Client(server) as client:
            result = await client.call_tool("get_workspace_overview")
            assert result.is_error
            assert result.structured_content["error"] == "access_revoked"
            assert details["token"] not in result.model_dump_json()
    in_client_thread(app, lambda: asyncio.run(read()))
    assert session.connection is None and not session.cache
