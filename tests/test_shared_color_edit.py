"""Shared command semantics and actual Qt/HTTP/MCP interleavings."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import socket
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtWidgets import QDialog
from mcp import Client

from quick_ternaries.workspace.session import WorkspaceSession, WorkspaceError, RECEIPT_LIMIT
from quick_ternaries.agent_api.client import read, set_trace_color
from quick_ternaries.agent_api.contract import ApiError
from quick_ternaries.agent_api.mcp import create_server
from quick_ternaries.agent_api.server import DesktopApi, MAX_REQUEST_BYTES
from quick_ternaries.agent_api.session import Session
from quick_ternaries.agent_api.snapshot import WorkspaceReader
from test_agent_api import app, window, in_client_thread, request, raw_request, wait_for


def command(core, uid, color="#123456", **overrides):
    state = core.color_state(uid)
    return {"trace_id": uid, "color": color, "workspace_epoch": state["workspace_epoch"],
            "expected_color_revision": state["color_revision"], "request_id": str(uuid4()), **overrides}


@pytest.fixture
def core():
    core = WorkspaceSession()
    uid = core.add_trace(SimpleNamespace(trace_color="#000000", trace_name="Original"))
    return core, uid


def test_shared_history_revisions_and_unrelated_fields(core):
    core, uid = core
    stale = command(core, uid)
    core.set_color(**command(core, uid, "#ff0000"), actor="human")
    with pytest.raises(WorkspaceError) as error:
        core.set_color(**stale, actor="agent")
    assert error.value.code == "color_conflict"
    assert error.value.details["color"] == "#ff0000"
    fresh = command(core, uid)
    core.traces[uid].trace_name = "Human typing"
    core.set_color(**fresh, actor="agent")
    assert core.history()["undo_label"] == "Agent: trace color"
    assert core.undo()["color"] == "#ff0000"
    assert core.undo()["color"] == "#000000"
    assert core.redo()["color"] == "#ff0000"
    assert core.redo()["color"] == "#123456"
    assert core.color_state(uid)["color_revision"] == 6
    assert core.traces[uid].trace_name == "Human typing"


def test_retry_returns_original_receipt_even_after_human_undo(core):
    core, uid = core
    args = command(core, uid)
    receipt = core.set_color(**args, actor="agent")
    core.undo()
    assert core.set_color(**args, actor="agent") == {**receipt, "replayed": True}
    assert core.color_state(uid)["color"] == "#000000"
    assert core.history()["undo_count"] == 0
    assert core.history()["redo_count"] == 1
    with pytest.raises(WorkspaceError) as error:
        core.set_color(**{**args, "color": "#ffffff"}, actor="agent")
    assert error.value.code == "request_id_reused"


def test_noop_and_bounded_receipt_expiry_do_not_silently_reapply(core):
    core, uid = core
    first = command(core, uid)
    core.set_color(**first)
    for _ in range(RECEIPT_LIMIT):
        result = core.set_color(**command(core, uid))
        assert not result["applied"]
    assert len(core._receipts) == RECEIPT_LIMIT
    assert core.history()["undo_count"] == 1
    with pytest.raises(WorkspaceError) as error:
        core.set_color(**first)
    assert error.value.code == "color_conflict"


def test_replaced_workspace_and_removed_trace_reject_old_commands(core):
    core, uid = core
    old = command(core, uid)
    core.reset()
    with pytest.raises(WorkspaceError) as error:
        core.set_color(**old)
    assert error.value.code == "workspace_changed"
    core.remove_trace(uid)
    core.add_trace(SimpleNamespace(trace_color="#000000"), uid)
    assert core.color_state(uid)["color_revision"] == 0
    core.set_color(**command(core, uid))
    core.remove_trace(uid)
    assert core.history()["undo_count"] == 0
    with pytest.raises(WorkspaceError):
        core.undo()


@pytest.mark.parametrize("change", [
    {"color": "red"}, {"color": "#00112233xx"}, {"expected_color_revision": True},
    {"expected_color_revision": -1}, {"request_id": "bad"}, {"trace_id": None},
    {"workspace_epoch": []},
])
def test_invalid_commands_do_not_mutate(core, change):
    core, uid = core
    with pytest.raises(WorkspaceError) as error:
        core.set_color(**command(core, uid, **change))
    assert error.value.code == "invalid_command"
    assert core.color_state(uid)["color_revision"] == 0
    assert core.history()["undo_count"] == 0


def test_legacy_color_bypass_invalidates_history(core):
    core, uid = core
    core.set_color(**command(core, uid))
    core.traces[uid].trace_color = "blue"
    with pytest.raises(WorkspaceError) as error:
        core.undo()
    assert error.value.code == "color_conflict"
    assert core.color_state(uid)["color"] == "blue"


@pytest.fixture
def editing_api(app, window):
    core = window.tabPanel.workspace_session
    api = DesktopApi(lambda instance: WorkspaceReader(window, instance), workspace_session=core)
    api.start()
    yield api
    api.stop()
    api.deleteLater()
    app.processEvents()


def test_real_requests_opt_in_conflict_retry_and_two_agent_race(app, editing_api):
    api = editing_api
    core = api.workspace_session
    uid = next(iter(core.traces))
    args = command(core, uid)
    details = api.connection_details()
    with pytest.raises(ApiError) as error:
        in_client_thread(app, lambda: set_trace_color(details, **args))
    assert error.value.code == "read_only"
    assert core.history()["undo_count"] == 0
    api.edit_enabled = True
    caps = in_client_thread(app, lambda: read(details, "capabilities"))
    assert "edit_trace_color" in caps["permissions"]
    assert caps["identity_scopes"]["traces"] == "saved_workspace_uuid"
    assert "/v1/commands/set-trace-color" in caps["endpoints"]
    state = in_client_thread(app, lambda: read(details, "trace-colors/" + uid))["color_state"]
    assert state == core.color_state(uid)
    def race():
        def submit(color):
            try:
                return set_trace_color(details, **{**args, "color": color, "request_id": str(uuid4())})
            except ApiError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(submit, ["#abcdef", "#123456"]))
    results = in_client_thread(app, race)
    assert results.count("color_conflict") == 1
    assert sum(isinstance(r, dict) for r in results) == 1
    assert core.color_state(uid)["color_revision"] == 1
    assert core.history()["undo_count"] == 1
    receipt = next(r["receipt"] for r in results if isinstance(r, dict))
    retry = {**args, "color": receipt["color"], "request_id": receipt["request_id"]}
    core.undo()
    replay = in_client_thread(app, lambda: set_trace_color(details, **retry))
    assert replay["receipt"] == {**receipt, "replayed": True}
    assert core.history()["undo_count"] == 0
    api.edit_enabled = False
    with pytest.raises(ApiError, match="disabled"):
        in_client_thread(app, lambda: set_trace_color(details, **retry))


@pytest.mark.parametrize("options,status", [
    ({"headers": {"Origin": "https://evil.example"}}, 403),
    ({"headers": {"Authorization": "Bearer bad"}}, 401),
    ({"headers": {"Content-Type": "text/plain"}}, 400),
    ({"body": "not-json"}, 400),
    ({"body": "{}"}, 400),
    ({"body": json.dumps({"color": "#123456", "actor": "human"})}, 400),
    ({"body": "x" * MAX_REQUEST_BYTES}, 431),
    ({"path": "/v1/commands/arbitrary"}, 404),
    ({"headers": {"Transfer-Encoding": "chunked"}}, 400),
])
def test_write_transport_rejections_preserve_state(app, editing_api, options, status):
    api = editing_api
    api.edit_enabled = True
    core = api.workspace_session
    uid = next(iter(core.traces))
    state = core.color_state(uid)
    kwargs = {"path": "/v1/commands/set-trace-color", "method": "POST", "body": json.dumps(command(core, uid)),
              **options, "headers": {"Content-Type": "application/json", **options.get("headers", {})}}
    assert in_client_thread(app, lambda: request(api, **kwargs))[0] == status
    assert core.color_state(uid) == state


def test_partial_body_permission_revocation_modal_and_loading(app, editing_api, window):
    api = editing_api
    api.edit_enabled = True
    core = api.workspace_session
    uid = next(iter(core.traces))
    details = api.connection_details()
    body = json.dumps(command(core, uid)).encode()
    host = details["url"].removeprefix("http://")
    headers = (f"POST /v1/commands/set-trace-color HTTP/1.1\r\nHost: {host}\r\n"
               f"Authorization: Bearer {details['token']}\r\nContent-Type: application/json\r\n"
               f"Content-Length: {len(body)}\r\n\r\n").encode()
    with socket.create_connection(("127.0.0.1", int(host.split(":")[1])), timeout=3) as client:
        client.sendall(headers + body[:1])
        wait_for(app, lambda: any(c.request is not None for c in api._connections))
        api.edit_enabled = False
        def finish():
            client.sendall(body[1:])
            return client.recv(4096)
        assert b"405" in in_client_thread(app, finish)
    api.edit_enabled = True
    dialog = QDialog(window)
    dialog.setModal(True)
    dialog.show()
    app.processEvents()
    try:
        with pytest.raises(ApiError) as error:
            in_client_thread(app, lambda: set_trace_color(details, **command(core, uid)))
        assert error.value.code == "editor_busy"
    finally:
        dialog.close()
    window._agent_loading_workspace = True
    with pytest.raises(ApiError) as error:
        in_client_thread(app, lambda: set_trace_color(details, **command(core, uid)))
    assert error.value.code == "workspace_busy"
    window._agent_loading_workspace = False
    assert core.history()["undo_count"] == 0


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_mcp_edit_protocol_and_retry(app, editing_api, mode):
    api = editing_api
    api.edit_enabled = True
    core = api.workspace_session
    uid = next(iter(core.traces))
    session = Session(lambda: api.connection_details())
    async def scenario():
        async with Client(create_server(session), mode=mode) as client:
            assert not (await client.call_tool("connect_from_clipboard")).is_error
            state = (await client.call_tool("get_trace_color_state", {"trace_id": uid})).structured_content["color_state"]
            args = {"trace_id": uid, "color": "#abcdef", "expected_color_revision": state["color_revision"],
                    "workspace_epoch": state["workspace_epoch"], "request_id": str(uuid4())}
            edited = await client.call_tool("set_trace_color", args)
            assert not edited.is_error
            assert edited.structured_content["receipt"]["applied"]
            repeated = await client.call_tool("set_trace_color", args)
            assert repeated.structured_content["receipt"]["replayed"]
            stale = await client.call_tool("set_trace_color", {**args, "request_id": str(uuid4())})
            assert stale.is_error and stale.structured_content["error"] == "color_conflict"
            for change in ({"color": "blue"}, {"expected_color_revision": True}, {"request_id": "bad"}):
                assert (await client.call_tool("set_trace_color", {**args, **change})).is_error
            assert api.connection_details()["token"] not in edited.model_dump_json()
    in_client_thread(app, lambda: asyncio.run(scenario()))
    assert core.history()["undo_count"] == 1


def test_response_lost_after_commit_retries_once_across_connection_restart(app, editing_api):
    api = editing_api
    api.edit_enabled = True
    core = api.workspace_session
    uid = next(iter(core.traces))
    args = command(core, uid)
    details = api.connection_details()
    host = details['url'].removeprefix('http://')
    body = json.dumps(args).encode()
    head = (f"POST /v1/commands/set-trace-color HTTP/1.1\r\nHost: {host}\r\n"
            f"Authorization: Bearer {details['token']}\r\nContent-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n\r\n").encode()
    with socket.create_connection(('127.0.0.1', int(host.split(':')[1])), timeout=3) as client:
        client.sendall(head + body)
        wait_for(app, lambda: core.color_state(uid)['color_revision'] == 1)
        # Deliberately discard the HTTP response, like a client losing its socket.
    api.stop()
    api.start()
    assert not api.edit_enabled
    api.edit_enabled = True
    replay = in_client_thread(app, lambda: set_trace_color(api.connection_details(), **args))
    assert replay['receipt']['replayed']
    assert core.history()['undo_count'] == 1
    assert core.color_state(uid)['color_revision'] == 1


def test_history_is_bounded_and_new_command_after_undo_discards_redo(core):
    core, uid = core
    for index in range(105):
        core.set_color(**command(core, uid, f'#{index+1:06x}'))
    assert core.history()['undo_count'] == 100
    core.undo()
    assert core.history()['redo_count'] == 1
    core.set_color(**command(core, uid, '#abcdef'))
    assert core.history()['redo_count'] == 0
    assert core.history()['undo_count'] == 100
