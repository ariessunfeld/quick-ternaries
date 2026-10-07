"""Small HTTP/1.1 adapter on Qt's event loop, with h11 handling HTTP syntax."""

import json
import secrets
from uuid import uuid4

import h11
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QHostAddress, QNetworkProxy, QTcpServer
from quick_ternaries.workspace.session import HISTORY_LIMIT, RECEIPT_LIMIT, WorkspaceError
from .contract import ApiError
from .inspection import Inspection, capabilities, parse_target

MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_CONNECTIONS = 8
CONNECTION_TIMEOUT_MS = 3000


class DesktopApi(QObject):
    """One token and instance ID per enable; zero network activity until start()."""

    read_completed = Signal(str)
    edit_completed = Signal(str)

    def __init__(self, reader_factory, parent=None, workspace_session=None, workspace_controller=None):
        super().__init__(parent)
        self._reader_factory = reader_factory
        self.workspace_session = workspace_session
        self.workspace_controller = workspace_controller
        self.edit_enabled = False
        self._listener = QTcpServer(self)
        self._listener.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self._listener.setMaxPendingConnections(MAX_CONNECTIONS)
        self._listener.newConnection.connect(self._accept)
        self._connections = set()
        self._token = None
        self.instance_id = None
        self._reader = None

    @property
    def running(self):
        return self._listener.isListening()

    def start(self):
        if self.running:
            return
        self.instance_id = str(uuid4())
        self._token = secrets.token_urlsafe(32)
        self._reader = self._reader_factory(self.instance_id)
        self._inspection = Inspection(self._reader)
        if not self._listener.listen(QHostAddress.SpecialAddress.LocalHost, 0):
            self.stop()
            raise OSError("Could not start the local agent connection")

    def stop(self):
        self._listener.close()
        self.edit_enabled = False
        if self.workspace_controller is not None:
            self.workspace_controller.render.cancel_pending()
        for connection in tuple(self._connections):
            connection.socket.abort()
        self._token = None
        self._reader = None
        self._inspection = None

    def connection_details(self):
        if not self.running:
            raise RuntimeError("Agent connection is disabled")
        return {"protocol_version": 1, "instance_id": self.instance_id,
                "url": f"http://127.0.0.1:{self._listener.serverPort()}",
                "token": self._token}

    def _accept(self):
        while self._listener.hasPendingConnections():
            socket = self._listener.nextPendingConnection()
            if len(self._connections) >= MAX_CONNECTIONS:
                socket.abort()
                socket.deleteLater()
                continue
            connection = _Connection(self, socket)
            self._connections.add(connection)
            if socket.bytesAvailable():
                connection._read()

    def validate_request(self, request):
        """Validate transport and permission before buffering or executing a command."""
        headers = {}
        for key, value in request.headers:
            if key in headers:
                return 400, {"error": "duplicate_header"}
            headers[key] = value
        expected_host = f"127.0.0.1:{self._listener.serverPort()}".encode()
        if headers.get(b"host") != expected_host or b"origin" in headers:
            return 403, {"error": "local_clients_only"}
        expected_auth = f"Bearer {self._token}".encode()
        if not self.running or not secrets.compare_digest(headers.get(b"authorization", b""), expected_auth):
            return 401, {"error": "unauthorized"}
        if request.method == b"POST":
            if not self.edit_enabled or self.workspace_session is None:
                return 405, {"error": "read_only"}
            if (b"transfer-encoding" in headers or headers.get(b"content-type") != b"application/json"
                    or not 0 < int(headers.get(b"content-length", b"0")) <= MAX_REQUEST_BYTES):
                return 400, {"error": "invalid_command"}
        elif request.method != b"GET":
            return 405, {"error": "read_only"}
        elif b"transfer-encoding" in headers or headers.get(b"content-length", b"0") != b"0":
            return 400, {"error": "request_body_not_supported"}
        return None

    def handle(self, request, body=b""):
        rejected = self.validate_request(request)
        if rejected:
            return rejected
        common = {"protocol_version": 1, "instance_id": self.instance_id}
        try:
            path, params = parse_target(request.target.decode("ascii"))
            if request.method == b"POST":
                return self._command(path, params, body, common)
            if path == '/v1/edit-state':
                self._reader.prepare()
                if self.workspace_session is None or params.keys() - {'target', 'trace_id', 'fields'}:
                    raise ApiError('invalid_query', 'Use target, trace_id and optional fields.')
                state = self.workspace_session.edit_state(params.get('target', 'workspace'), params.get('trace_id'))
                if 'fields' in params:
                    names = params['fields'].split(',')
                    if 'values' not in state or not names or set(names) - state['values'].keys():
                        raise ApiError('invalid_query', 'Request editable field names from the schema.')
                    for key in ('values', 'schema', 'field_revisions'):
                        state[key] = {k: state[key][k] for k in names}
                result = {**common, 'state': state}
            elif path == '/v1/render-status' and self.workspace_controller is not None:
                if params:
                    raise ApiError('invalid_query', 'Render status takes no parameters.')
                result = {**common, 'render': self.workspace_controller.render.status()}
            elif path.startswith("/v1/trace-colors/"):
                if params or self.workspace_session is None:
                    raise ApiError("invalid_query", "Color reads take only a trace ID.")
                self._reader.prepare()
                try:
                    result = {**common, "color_state": self.workspace_session.color_state(path.removeprefix("/v1/trace-colors/"))}
                except WorkspaceError:
                    raise ApiError("trace_not_found", "Trace unavailable.", 404) from None
            elif path == "/v1/capabilities":
                if params:
                    raise ApiError("invalid_query", "Capabilities takes no parameters.")
                result = {**common, **capabilities()}
                if self.workspace_session is not None:
                    result["capabilities"].extend(["trace_color.read", "workspace.edit_state"])
                    result["endpoints"] = [*result["endpoints"], "/v1/trace-colors/{id}", "/v1/edit-state"]
                    result["identity_scope"] = "mixed"
                    result["identity_scopes"] = {"traces": "saved_workspace_uuid", "datasets": "connection",
                                                  "workspace_epoch": "loaded_document_lifetime"}
                    if self.edit_enabled:
                        result["capabilities"].extend(["trace_color.edit", "workspace.edit", "workspace.history"])
                        result["permissions"].append("edit_workspace")
                        result["endpoints"].extend('/v1/commands/' + name for name in
                            ('set-trace-color', 'apply-edits', 'undo', 'redo'))
                    result['editing'] = {'revision_scope': 'per_field', 'atomic_batches': True,
                        'history_limit': HISTORY_LIMIT, 'receipt_limit': RECEIPT_LIMIT,
                        'trace_ids_persist_on_save': True, 'max_edits': 32}
                    if self.workspace_controller is not None:
                        result['capabilities'].append('render.status')
                        result['endpoints'].append('/v1/render-status')
                        if self.edit_enabled:
                            result['capabilities'].extend(['trace.lifecycle', 'plot.render'])
                            result['endpoints'].extend('/v1/commands/' + name for name in
                                ('create-trace', 'duplicate-trace', 'delete-trace', 'reorder-traces', 'render-plot'))

            else:
                result = {**common, **self._inspection.query(path, params)}
        except WorkspaceError as error:
            return (404 if error.code == "trace_not_found" else 400), {"error": error.code, "message": str(error)}
        except ApiError as error:
            return error.status, {"error": error.code, "message": str(error)}
        except Exception:
            # Never send exception details, local paths, or model contents.
            return 500, {"error": "snapshot_unavailable"}
        self.read_completed.emit(path)
        return 200, result

    def _command(self, path, params, body, common):
        from PySide6.QtWidgets import QApplication
        # The GUI commits a color picker on close. While a modal is active,
        # leave that unfinished choice alone and ask the client to retry later.
        if QApplication.activeModalWidget() is not None:
            return 409, {"error": "editor_busy"}
        self._reader.prepare()
        if params:
            return 400, {'error': 'invalid_command'}
        try:
            command = json.loads(body)
            if not isinstance(command, dict):
                raise ValueError()
        except (ValueError, UnicodeError, RecursionError):
            return 400, {'error': 'invalid_command'}
        operation = path.removeprefix('/v1/commands/').replace('-', '_')
        try:
            if operation == 'set_trace_color':
                required = {'trace_id', 'color', 'expected_color_revision', 'workspace_epoch', 'request_id'}
                if set(command) != required:
                    raise ValueError()
                if self.workspace_controller:
                    self.workspace_controller.guard_edits([{'target': 'trace', 'trace_id': command['trace_id'],
                                                            'changes': {'trace_color': command['color']}}])
                receipt = self.workspace_session.set_color(**command, actor='agent')
            elif operation == 'apply_edits':
                if set(command) != {'edits', 'workspace_epoch', 'request_id'}:
                    raise ValueError()
                if self.workspace_controller:
                    self.workspace_controller.guard_edits(command['edits'])
                receipt = self.workspace_session.apply(**command, actor='agent')
            elif operation in ('undo', 'redo', 'create_trace', 'duplicate_trace', 'delete_trace', 'reorder_traces'):
                fields = {'workspace_epoch', 'request_id', 'expected_revision'}
                structural = operation not in ('undo', 'redo')
                if structural:
                    fields.add('arguments')
                if set(command) != fields:
                    raise ValueError()
                if structural and self.workspace_controller is None:
                    return 404, {'error': 'unknown_endpoint'}
                focus = QApplication.focusWidget()
                from PySide6.QtWidgets import QLineEdit
                if operation in ('undo', 'redo') and (self.workspace_controller.pending_editor() if self.workspace_controller
                        else isinstance(focus, QLineEdit) and focus.isModified()):
                    raise WorkspaceError('editor_busy', 'Let the person finish editing before changing workspace history.')
                execute = (lambda: self.workspace_controller.trace_command(operation, command['arguments'], self._reader)) if structural else None
                receipt = self.workspace_session.control(operation=operation, execute=execute, **command)
            elif operation == 'render_plot' and self.workspace_controller is not None:
                if set(command) != {'workspace_epoch', 'request_id', 'expected_revision'}:
                    raise ValueError()
                from PySide6.QtWidgets import QLineEdit
                focus = QApplication.focusWidget()
                if self.workspace_controller.pending_editor():
                    raise WorkspaceError('editor_busy', 'Let the person finish editing before rendering.')
                receipt = self.workspace_controller.render.request(**command)
            else:
                return 404, {'error': 'unknown_endpoint'}
        except WorkspaceError as error:
            status = 400 if error.code == 'invalid_command' else 404 if error.code in ('trace_not_found', 'dataset_not_found') else 409
            return status, {'error': error.code, 'message': str(error), 'details': error.details}
        except (ValueError, TypeError, KeyError, AttributeError):
            return 400, {'error': 'invalid_command'}
        self.edit_completed.emit(operation.replace('_', ' ').capitalize())
        return 200, {**common, 'receipt': receipt}



class _Connection(QObject):
    def __init__(self, api, socket):
        super().__init__(api)
        self.api = api
        self.socket = socket
        socket.setParent(self)
        socket.setReadBufferSize(MAX_REQUEST_BYTES + 1)
        self.protocol = h11.Connection(h11.SERVER, max_incomplete_event_size=MAX_REQUEST_BYTES)
        self.received = 0
        self.responded = False
        self.head_request = False
        self.request = None
        self.body = bytearray()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)
        self.timer.start(CONNECTION_TIMEOUT_MS)
        socket.disconnected.connect(self._closed)
        socket.readyRead.connect(self._read)

    def _timeout(self):
        self.socket.abort()

    def _closed(self):
        self.timer.stop()
        self.api._connections.discard(self)
        self.deleteLater()

    def _read(self):
        if self.responded:
            return
        data = bytes(self.socket.read(MAX_REQUEST_BYTES + 1))
        self.received += len(data)
        if self.received > MAX_REQUEST_BYTES:
            self._respond(431, {"error": "request_too_large"})
            return
        try:
            self.protocol.receive_data(data)
            while not self.responded:
                event = self.protocol.next_event()
                if event is h11.NEED_DATA:
                    break
                if isinstance(event, h11.Request):
                    self.head_request = event.method == b"HEAD"
                    rejected = self.api.validate_request(event)
                    if rejected:
                        self._respond(*rejected)
                    elif event.method == b"GET":
                        self._respond(*self.api.handle(event))
                    else:
                        self.request = event
                elif isinstance(event, h11.Data) and self.request is not None:
                    self.body.extend(event.data)
                elif isinstance(event, h11.EndOfMessage) and self.request is not None:
                    self._respond(*self.api.handle(self.request, bytes(self.body)))
                else:
                    self._respond(400, {"error": "invalid_request"})
        except h11.RemoteProtocolError:
            self._respond(400, {"error": "invalid_request"})

    def _respond(self, status, result):
        self.responded = True
        try:
            body = json.dumps(result, allow_nan=False, separators=(",", ":")).encode()
        except (TypeError, ValueError):
            status, body = 500, b'{"error":"snapshot_unavailable"}'
        if len(body) > MAX_RESPONSE_BYTES:
            status, body = 413, b'{"error":"snapshot_too_large"}'
        response = h11.Response(status_code=status, headers=[
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode()), (b"connection", b"close"),
            (b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff"),
        ])
        try:
            wire = self.protocol.send(response)
            if not self.head_request:
                wire += self.protocol.send(h11.Data(data=body))
            wire += self.protocol.send(h11.EndOfMessage())
        except h11.LocalProtocolError:
            self.socket.abort()
            return
        self.socket.write(wire)
        # Qt flushes queued output before closing. The absolute timer also bounds
        # clients that stop reading. No keep-alive, pipelining, or request bodies.
        self.socket.disconnectFromHost()
