"""Exercise real loopback sockets and Qt event dispatch, including hostile input."""

from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import socket
import subprocess
import sys
from time import monotonic, sleep
from uuid import uuid4

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QThread, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox, QWidget

from quick_ternaries.agent_api.client import read
from quick_ternaries.agent_api.dialog import AgentConnectionDialog
from quick_ternaries.agent_api.server import DesktopApi, MAX_REQUEST_BYTES
from quick_ternaries.agent_api.snapshot import MAX_COLUMNS, MAX_FILTERS, MAX_TEXT, WorkspaceReader
from quick_ternaries.agent_api.contract import ApiError, TRACE_SECTIONS
from quick_ternaries.agent_api.session import Session
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.views.setup_menu_view import SetupMenuView
from quick_ternaries.views.tab_panel_widget import TabPanel


@pytest.fixture(scope="session")
def app():
    # Keep the single QApplication alive across later test modules and cached
    # QIcons. Destroying/recreating it mid-suite can crash inside native Qt.
    return QApplication.instance() or QApplication([])


def in_client_thread(app, callback):
    """Let Qt service sockets while a normal synchronous client makes a call."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(callback)
        deadline = monotonic() + 8
        while not future.done() and monotonic() < deadline:
            app.processEvents()
            # Yield Python's GIL as well as servicing Qt. QTest.qWait alone can
            # starve the Python client thread on Linux/other Python versions.
            sleep(0.001)
        assert future.done(), "Loopback request did not finish"
        return future.result()


def wait_for(app, predicate):
    deadline = monotonic() + 2
    while not predicate() and monotonic() < deadline:
        app.processEvents()
        sleep(0.001)
    assert predicate()


class Reader:
    def snapshot(self):
        assert QThread.currentThread() == QApplication.instance().thread()
        return {"title": "Live desktop"}


@pytest.fixture
def api(app):
    api = DesktopApi(lambda instance: Reader())
    assert not api.running
    api.start()
    yield api
    api.stop()
    api.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def request(api, *, path="/v1/workspace", method="GET", headers=None, body=None):
    details = api.connection_details()
    port = int(details["url"].rsplit(":", 1)[1])
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        fields = {"Authorization": "Bearer " + details["token"]}
        if headers is not None:
            fields.update(headers)
        client.request(method, path, body=body, headers=fields)
        response = client.getresponse()
        return response.status, response.read(), dict(response.getheaders())
    finally:
        client.close()


def test_authenticated_reads_are_on_gui_thread_with_no_cache_or_cors(app, api):
    status, body, headers = in_client_thread(app, lambda: request(api))
    assert status == 200
    result = json.loads(body)
    assert result["workspace"]["title"] == "Live desktop"
    assert result["instance_id"] == api.instance_id
    assert headers["cache-control"] == "no-store"
    assert headers["connection"] == "close"
    assert "access-control-allow-origin" not in headers
    capabilities = in_client_thread(app, lambda: read(api.connection_details(), "capabilities"))
    assert capabilities["permissions"] == ["read"]
    assert capabilities["identity_scope"] == "connection"


@pytest.mark.parametrize("options,status", [
    ({"headers": {"Authorization": ""}}, 401),
    ({"headers": {"Authorization": "Bearer wrong"}}, 401),
    ({"headers": {"Host": "evil.example"}}, 403),
    ({"headers": {"Host": "localhost"}}, 403),
    ({"headers": {"Origin": "https://evil.example"}}, 403),
    ({"headers": {"Origin": "null"}}, 403),
    ({"method": "POST", "body": "{}"}, 405),
    ({"method": "DELETE"}, 405),
    ({"method": "OPTIONS"}, 405),
    ({"method": "HEAD"}, 405),
    ({"body": "data"}, 400),
    ({"headers": {"Transfer-Encoding": "chunked"}}, 400),
    ({"path": "/v1/workspace?token=wrong"}, 400),
    ({"path": "/../../setup.cfg"}, 404),
    ({"path": "http://evil.example/v1/workspace"}, 403),
])
def test_rejects_invalid_requests_without_reading_workspace(app, api, options, status):
    def unexpected():
        pytest.fail("Rejected request reached the workspace")
    api._reader.snapshot = unexpected
    assert in_client_thread(app, lambda: request(api, **options))[0] == status


def raw_request(api, payload):
    port = int(api.connection_details()["url"].rsplit(":", 1)[1])
    with socket.create_connection(("127.0.0.1", port), timeout=5) as client:
        client.sendall(payload)
        result = bytearray()
        try:
            while data := client.recv(65536):
                result.extend(data)
        except ConnectionResetError:
            # Closing with unread oversized input may reset TCP on some OSes.
            pass
        return bytes(result)


@pytest.mark.parametrize("payload", [
    b"not HTTP\r\n\r\n",
    b"GET /v1/workspace HTTP/1.1\r\nHost: a\r\nHost: b\r\n\r\n",
    b"GET /v1/workspace HTTP/1.1\r\nHost: a\r\nContent-Length: nope\r\n\r\n",
])
def test_malformed_http_is_closed_and_server_survives(app, api, payload):
    result = in_client_thread(app, lambda: raw_request(api, payload))
    assert b"400" in result
    assert in_client_thread(app, lambda: request(api))[0] == 200


def test_request_size_and_slow_connection_limits(app, api, monkeypatch):
    payload = b"GET / HTTP/1.1\r\nHost: " + b"x" * MAX_REQUEST_BYTES
    result = in_client_thread(app, lambda: raw_request(api, payload))
    assert result == b"" or b"431" in result
    monkeypatch.setattr("quick_ternaries.agent_api.server.CONNECTION_TIMEOUT_MS", 50)
    assert in_client_thread(app, lambda: raw_request(api, b"GET /")) == b""
    assert in_client_thread(app, lambda: request(api))[0] == 200


def test_errors_are_redacted_and_responses_are_bounded(app, api):
    def broken():
        raise ValueError("private dataset contents")
    api._reader.snapshot = broken
    status, body, _ = in_client_thread(app, lambda: request(api))
    assert status == 500 and b"private" not in body
    api._reader.snapshot = lambda: {"huge": "x" * (1024 * 1024)}
    assert in_client_thread(app, lambda: request(api))[0] == 413


def test_stop_disconnects_clients_and_restart_rotates_identity_and_secret(app, api):
    old = api.connection_details()
    port = int(old["url"].rsplit(":", 1)[1])
    connection = socket.create_connection(("127.0.0.1", port), timeout=5)
    wait_for(app, lambda: len(api._connections) == 1)
    api.stop()
    try:
        assert connection.recv(1) == b""
    except ConnectionResetError:
        pass  # Windows reports an aborted socket as RST rather than EOF.
    connection.close()
    with pytest.raises(RuntimeError):
        api.connection_details()
    api.start()
    assert api.instance_id != old["instance_id"]
    assert api.connection_details()["token"] != old["token"]
    assert in_client_thread(app, lambda: request(api, headers={"Authorization": "Bearer " + old["token"]}))[0] == 401


def test_client_refuses_other_hosts_and_mismatched_instances(app, api):
    details = api.connection_details()
    for url in ("https://127.0.0.1:123", "http://example.com:123", "http://127.0.0.1:123/x"):
        with pytest.raises(ValueError):
            read({**details, "url": url})
    with pytest.raises(ValueError, match="instance changed"):
        in_client_thread(app, lambda: read({**details, "instance_id": "wrong"}))


def test_connection_limit_closes_excess_clients_and_frees_slots(app, api, monkeypatch):
    monkeypatch.setattr("quick_ternaries.agent_api.server.MAX_CONNECTIONS", 1)
    port = int(api.connection_details()["url"].rsplit(":", 1)[1])
    with socket.create_connection(("127.0.0.1", port), timeout=5) as held:
        wait_for(app, lambda: len(api._connections) == 1)
        assert in_client_thread(app, lambda: raw_request(api, b"GET /")) == b""
    wait_for(app, lambda: len(api._connections) == 0)
    assert in_client_thread(app, lambda: request(api))[0] == 200
    wait_for(app, lambda: len(api._connections) == 0)


def test_command_line_client_uses_stdin_and_ignores_proxy_environment(app, api, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:1")
    result = in_client_thread(app, lambda: subprocess.run(
        [sys.executable, "-m", "quick_ternaries.agent_api", "workspace"],
        input=json.dumps(api.connection_details()) + "\n", text=True,
        capture_output=True, timeout=5,
    ))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["workspace"]["title"] == "Live desktop"
    assert api.connection_details()["token"] not in result.stdout + result.stderr


@pytest.fixture
def window(app, tmp_path):
    window = QWidget()
    window.setupMenuModel = SetupMenuModel()
    window.plotTypeSelector = QComboBox(window)
    window.plotTypeSelector.addItems(["Ternary", "Cartesian"])
    window.tabPanel = TabPanel(window)
    path = tmp_path / "synthetic.csv"
    path.write_text("A,B,C,Sample\n70,20,10,Alpha\n20,70,10,Beta\n")
    metadata = DataFileMetadata(str(path), header_row=0)
    assert window.setupMenuModel.data_library.add_file(metadata)
    trace = TraceEditorModel(trace_name="Synthetic samples", datafile=metadata, filters_on=True,
                             filters=[FilterModel(filter_column="Sample", filter_operation="is", filter_value1="Alpha")])
    window.tabPanel.add_tab(trace.trace_name, trace)
    yield window
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_snapshot_tracks_human_edits_without_file_io_or_model_mutation(app, window, monkeypatch):
    reader = WorkspaceReader(window, str(uuid4()))
    initial = reader.snapshot()
    assert initial["datasets"][0]["row_count"] == 2
    assert [c["name"] for c in initial["datasets"][0]["columns"]] == ["A", "B", "C", "Sample"]
    trace = initial["traces"][0]
    assert trace["dataset_id"] == initial["datasets"][0]["id"]
    assert trace["filters"][0]["value1"] == "Alpha"
    assert str(window.setupMenuModel.data_library.loaded_files[0].file_path) not in json.dumps(initial)
    assert initial == reader.snapshot()
    view = SetupMenuView(window.setupMenuModel)
    view.setParent(window)
    title = view.section_widgets["plot_labels"]["title"]
    QTest.keyClicks(title, "Human edit")
    updated = reader.snapshot()
    assert updated["title"] == "Human edit"
    assert updated["snapshot_id"] != initial["snapshot_id"]
    assert updated["traces"][0]["id"] == trace["id"]
    library = window.setupMenuModel.data_library
    library.dataframe_manager.clear_cache()
    monkeypatch.setattr(library.dataframe_manager, "load_dataframe", lambda *_: pytest.fail("Read reloaded data"))
    assert reader.snapshot()["datasets"][0]["loaded"] is False
    view.close()


def test_snapshot_bounds_and_thread_guard(app, window):
    reader = WorkspaceReader(window, str(uuid4()))
    trace = next(t for t in window.tabPanel.id_to_widget.values() if isinstance(t, TraceEditorModel))
    trace.trace_name = "x" * (MAX_TEXT + 1)
    trace.filters = [FilterModel() for _ in range(MAX_FILTERS + 1)]
    window.setupMenuModel.axis_members.top_axis = ["A"] * (MAX_COLUMNS + 1)
    snapshot = reader.snapshot()
    assert snapshot["truncated"]
    assert len(snapshot["traces"][0]["name"]) == MAX_TEXT
    assert len(snapshot["traces"][0]["filters"]) == MAX_FILTERS
    assert len(snapshot["axes"]["top_axis"]) == MAX_COLUMNS
    with pytest.raises(RuntimeError, match="GUI thread"):
        in_client_thread(app, reader.snapshot)


def test_dialog_opt_in_live_read_disconnect_and_clipboard(app, window):
    dialog = AgentConnectionDialog(window)
    states = []
    dialog.connection_state_changed.connect(states.append)
    assert not dialog.api.running
    QTest.mouseClick(dialog.toggle, Qt.MouseButton.LeftButton)
    assert dialog.api.running and states[-1] == "Read only"
    result = in_client_thread(app, lambda: read(dialog.api.connection_details()))
    assert result["workspace"]["traces"][0]["name"] == "Synthetic samples"
    assert "1 reads" in dialog.activity.text()
    dialog.copy_details()
    assert json.loads(app.clipboard().text())["token"] == dialog.api.connection_details()["token"]
    dialog.stop()
    assert not dialog.api.running and not app.clipboard().text()
    assert states[-1] == "Off"
    dialog.toggle_connection()
    dialog.copy_details()
    app.clipboard().setText("user's next clipboard value")
    dialog.stop()
    assert app.clipboard().text() == "user's next clipboard value"
    dialog.close()


@pytest.fixture
def live_api(app, window):
    api = DesktopApi(lambda instance: WorkspaceReader(window, instance))
    api.start()
    yield api
    api.stop()
    api.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()


def test_focused_reads_include_heatmap_and_explicit_coverage(app, window, live_api):
    overview = in_client_thread(app, lambda: read(live_api.connection_details(), "overview"))
    assert "columns" not in overview["datasets"][0]
    assert "filters" not in overview["traces"][0]
    assert "heatmap" not in overview["traces"][0]
    uid = overview["traces"][0]["id"]
    model = window.tabPanel.id_to_widget[uid]
    focused = in_client_thread(app, lambda: read(live_api.connection_details(), "traces/" + uid, sections="heatmap"))
    assert set(focused["trace"]["heatmap"]) == set(TRACE_SECTIONS["heatmap"])
    assert focused["trace"]["heatmap"]["heatmap_colorscale"] == model.heatmap_colorscale
    assert "appearance" not in focused["trace"] and "datasets" not in focused
    assert focused["coverage"]["included"] == ["identity", "heatmap"]
    assert focused["coverage"]["partial"] and not focused["truncated"]
    assert "data_rows" in focused["coverage"]["excluded"]
    assert not focused["read_state"]["write_precondition"]


def test_observed_changes_independent_cursors_heatmap_removal_and_reorder(app, window, live_api):
    def fetch(endpoint="overview", **params):
        return in_client_thread(app, lambda: read(live_api.connection_details(), endpoint, **params))
    initial = fetch()
    cursor = initial["read_state"]["cursor"]
    uid = initial["traces"][0]["id"]
    assert fetch("changes", since=cursor)["changes"]["unchanged"]
    model = window.tabPanel.id_to_widget[uid]
    model.heatmap_on = True
    model.heatmap_column = "A"
    model.heatmap_min = 20
    model.heatmap_max = 70
    model.heatmap_colorscale = "Viridis"
    first = fetch("changes", since=cursor)
    assert first["changes"]["traces"]["changed"] == [uid]
    assert first["read_state"]["read_revision"] > initial["read_state"]["read_revision"]
    assert fetch("changes", since=cursor)["changes"] == first["changes"]  # Another reader's cursor is independent.
    current = first["read_state"]["cursor"]
    assert fetch("changes", since=current)["changes"]["unchanged"]
    added_id = window.tabPanel.add_tab("Other", TraceEditorModel(trace_name="Other"))
    assert fetch("changes", since=current)["changes"]["traces"]["added"] == [added_id]
    window.tabPanel.remove_tab_by_id(uid)
    removed = fetch("changes", since=current)
    assert removed["changes"]["traces"]["removed"] == [uid]
    assert "trace_order" in removed["changes"]["changed_sections"]
    with pytest.raises(ApiError) as error:
        fetch("traces/" + uid)
    assert error.value.code == "trace_not_found"


def test_cursor_expiry_workspace_replacement_and_loading_guard(app, window, live_api, monkeypatch):
    monkeypatch.setattr("quick_ternaries.agent_api.inspection.HISTORY_LIMIT", 2)
    def fetch(endpoint="overview", **params):
        return in_client_thread(app, lambda: read(live_api.connection_details(), endpoint, **params))
    initial = fetch()
    cursor = initial["read_state"]["cursor"]
    for title in ("One", "Two"):
        window.setupMenuModel.plot_labels.title = title
        current = fetch()
    expired = fetch("changes", since=cursor)
    assert expired["changes"]["resync_required"]
    assert len(live_api._inspection.history) == 2
    # Identical content in a replacement document still invalidates old cursors.
    window._agent_document_epoch = 1
    assert fetch("changes", since=current["read_state"]["cursor"])["changes"]["resync_required"]
    window._agent_loading_workspace = True
    with pytest.raises(ApiError) as error:
        fetch()
    assert error.value.code == "workspace_busy"
    window._agent_loading_workspace = False
    assert fetch()["read_state"]["document_epoch"] == 1


def test_paginated_columns_filters_and_catalogs_beyond_tracking_limits(app, window, live_api, monkeypatch):
    import pandas as pd
    import numpy as np
    def fetch(endpoint="overview", **params):
        return in_client_thread(app, lambda: read(live_api.connection_details(), endpoint, **params))
    first = fetch()
    uid = first["traces"][0]["id"]
    model = window.tabPanel.id_to_widget[uid]
    model.filters = [FilterModel(filter_value1=str(i)) for i in range(125)]
    page = fetch("traces/" + uid, sections="filters", offset=50, limit=50)
    assert page["trace"]["filters"]["items"][0]["value1"] == "50"
    assert page["trace"]["filters"]["next_offset"] == 100
    assert not page["truncated"]  # Deliberate pagination is not lossy value truncation.
    assert not page["read_state"]["tracking_complete"]
    assert fetch("changes", since=first["read_state"]["cursor"])["changes"]["resync_required"]
    library = window.setupMenuModel.data_library
    frame = pd.DataFrame(np.zeros((2, 150)), columns=["column" + str(i) for i in range(150)])
    monkeypatch.setattr(library.dataframe_manager, "get_dataframe", lambda _: frame)
    monkeypatch.setattr(library.dataframe_manager, "load_dataframe", lambda *_: pytest.fail("Reloaded data"))
    dataset = fetch("datasets/" + first["datasets"][0]["id"], offset=125, limit=20)["dataset"]
    assert dataset["columns"][0]["name"] == "column125"
    assert dataset["next_offset"] == 145 and dataset["column_count"] == 150
    assert "data" not in dataset
    monkeypatch.setattr("quick_ternaries.agent_api.snapshot.MAX_TRACES", 1)
    added = window.tabPanel.add_tab("Second", TraceEditorModel(trace_name="Second"))
    assert fetch("traces", offset=1, limit=1)["traces"][0]["id"] == added
    assert fetch("traces/" + added, sections="heatmap")["trace"]["id"] == added


@pytest.mark.parametrize("path", [
    "/v1/traces?limit=0", "/v1/traces?limit=101", "/v1/traces?offset=-1",
    "/v1/traces?offset=1000001", "/v1/traces?limit=1&limit=2", "/v1/overview?rows=true",
    "/v1/changes", "/v1/changes?since=", "/v1/capabilities?token=secret",
    "/v1/traces/not-an-id", "/v1/traces/" + str(uuid4()) + "?sections=heatmap,unknown",
    "/v1/traces/" + str(uuid4()) + "?sections=heatmap,heatmap",
])
def test_query_validation_happens_before_inspection(app, api, path):
    api._reader.snapshot = lambda: pytest.fail("Invalid query reached state")
    assert in_client_thread(app, lambda: request(api, path=path))[0] == 400


def test_session_clipboard_once_compact_comparisons_refresh_and_reconnect(app, window, live_api):
    clipboard = [live_api.connection_details()]
    reads = []
    def handoff():
        reads.append(True)
        return clipboard[0]
    session = Session(clipboard_reader=handoff)
    def execute(**command):
        return in_client_thread(app, lambda: session.execute(command))
    assert execute(op="connect", source="clipboard")["status"] == "connected"
    clipboard[0] = "Unrelated clipboard contents"
    overview = execute(op="read")["result"]
    uid = overview["traces"][0]["id"]
    command = dict(op="read", resource="trace", id=uid, sections=["heatmap"])
    assert execute(**command)["status"] == "snapshot"
    assert execute(**command)["status"] == "unchanged"
    from quick_ternaries.views.trace_editor_view import TraceEditorView
    view = TraceEditorView(window.tabPanel.id_to_widget[uid], window)
    # The same Qt controls the person uses update committed model fields.
    view.widgets["heatmap_min"].setValue(12.5)
    view.widgets["heatmap_log_transform"].setChecked(True)
    changed = execute(**command)
    assert changed["status"] == "changed"
    paths = {v["path"]: v for v in changed["changes"]}
    assert paths["/trace/heatmap/heatmap_min"]["after"] == 12.5
    assert paths["/trace/heatmap/heatmap_log_transform"]["after"] is True
    assert "datasets" not in changed
    assert execute(**command, refresh=True)["result"]["trace"]["heatmap"]["heatmap_min"] == 12.5
    assert len(reads) == 1
    # Focused reads must not advance the overview change baseline.
    changes = execute(op="read", resource="changes")["result"]
    assert changes["changes"]["traces"]["changed"] == [uid]
    old_token = session.connection["token"]
    live_api.stop()
    live_api.start()
    clipboard[0] = live_api.connection_details()
    assert execute(op="connect", source="clipboard")["status"] == "connected"
    assert session.connection["token"] != old_token and not session.cache
    assert execute(**command)["status"] == "snapshot"
    assert len(reads) == 2
    execute(op="disconnect")
    assert session.connection is None and not session.cache
    view.close()


def test_session_resync_drops_baselines_and_nonfinite_values_are_not_unchanged(app, window, live_api):
    session = Session()
    def execute(**command):
        return in_client_thread(app, lambda: session.execute(command))
    execute(op="connect", connection=live_api.connection_details())
    overview = execute(op="read")["result"]
    uid = overview["traces"][0]["id"]
    command = dict(op="read", resource="trace", id=uid, sections=["heatmap"])
    execute(**command)
    window._agent_document_epoch = 1
    result = execute(op="read", resource="changes")["result"]
    assert result["changes"]["resync_required"] and not session.cache and session.cursor is None
    with pytest.raises(ApiError) as error:
        execute(op="read", resource="changes")
    assert error.value.code == "no_baseline"
    window.tabPanel.id_to_widget[uid].heatmap_min = float("nan")
    result = execute(**command)
    assert result["result"]["truncated"]
    assert execute(**command)["status"] == "snapshot"


def test_session_revoked_access_clears_credentials_and_comparisons(app, live_api):
    session = Session()
    in_client_thread(app, lambda: session.execute({"op": "connect", "connection": live_api.connection_details()}))
    in_client_thread(app, lambda: session.execute({"op": "read"}))
    live_api._token = "different-token-" * 3
    with pytest.raises(ApiError) as error:
        in_client_thread(app, lambda: session.execute({"op": "read"}))
    assert error.value.code == "access_revoked"
    assert session.connection is None and not session.cache and session.cursor is None


def test_real_persistent_subprocess_multiple_commands_and_secret_redaction(app, window, live_api):
    process = subprocess.Popen([sys.executable, "-u", "-m", "quick_ternaries.agent_api", "session"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, encoding="utf-8")
    token = live_api.connection_details()["token"]
    outputs = []
    def receive():
        output = process.stdout.readline()
        outputs.append(output)
        assert token not in output
        return json.loads(output)
    def command(value):
        process.stdin.write(json.dumps(value) + "\n")
        process.stdin.flush()
        return in_client_thread(app, receive)
    try:
        assert in_client_thread(app, receive)["status"] == "ready"
        # Private pipe handoff simulates the one-time clipboard bootstrap.
        assert command({"op": "connect", "connection": live_api.connection_details()})["status"] == "connected"
        overview = command({"op": "read"})["result"]
        uid = overview["traces"][0]["id"]
        query = {"op": "read", "resource": "trace", "id": uid, "sections": ["heatmap"]}
        first = command(query)
        unchanged = command(query)
        assert unchanged["status"] == "unchanged"
        assert len(json.dumps(unchanged)) < len(json.dumps(first))
        window.tabPanel.id_to_widget[uid].heatmap_colorscale = "Viridis"
        delta = command(query)
        assert delta["status"] == "changed"
        assert delta["changes"] == [{"path": "/trace/heatmap/heatmap_colorscale", "before": "Inferno", "after": "Viridis"}]
        assert command({**query, "refresh": True})["status"] == "snapshot"
        assert command({"op": "read", "resource": "trace", "id": uid, "sections": ["invalid"]})["error"] == "invalid_query"
        assert command({"op": "quit"})["status"] == "closed"
        process.wait(timeout=5)
        assert process.returncode == 0
        assert token not in process.stderr.read()
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
