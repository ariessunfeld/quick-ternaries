"""Small HTTP/1.1 adapter on Qt's event loop, with h11 handling HTTP syntax."""

import json
import secrets
from uuid import uuid4

import h11
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QHostAddress, QNetworkProxy, QTcpServer
from .contract import ApiError
from .inspection import Inspection, capabilities, parse_target

MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_CONNECTIONS = 8
CONNECTION_TIMEOUT_MS = 3000


class DesktopApi(QObject):
    """One token and instance ID per enable; zero network activity until start()."""

    read_completed = Signal(str)

    def __init__(self, reader_factory, parent=None):
        super().__init__(parent)
        self._reader_factory = reader_factory
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

    def handle(self, request):
        """Validate connection boundaries before calling the workspace reader."""
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
        if request.method != b"GET":
            return 405, {"error": "read_only"}
        if b"transfer-encoding" in headers or headers.get(b"content-length", b"0") != b"0":
            return 400, {"error": "request_body_not_supported"}
        common = {"protocol_version": 1, "instance_id": self.instance_id}
        try:
            path, params = parse_target(request.target.decode("ascii"))
            if path == "/v1/capabilities":
                if params:
                    raise ApiError("invalid_query", "Capabilities takes no parameters.")
                result = {**common, **capabilities()}
            else:
                result = {**common, **self._inspection.query(path, params)}
        except ApiError as error:
            return error.status, {"error": error.code, "message": str(error)}
        except Exception:
            # Never send exception details, local paths, or model contents.
            return 500, {"error": "snapshot_unavailable"}
        self.read_completed.emit(path)
        return 200, result


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
            event = self.protocol.next_event()
            if isinstance(event, h11.Request):
                self.head_request = event.method == b"HEAD"
                self._respond(*self.api.handle(event))
            elif event is not h11.NEED_DATA:
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
