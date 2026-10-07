"""Standard-library client: explicit instance selection, no proxy or redirects."""

import http.client
import json
import socket
from urllib.parse import urlencode, urlsplit
from uuid import UUID

from .contract import ApiError

MAX_RESPONSE_BYTES = 1024 * 1024


def validate_connection(connection):
    try:
        url = urlsplit(connection["url"])
        token = connection["token"]
        valid = (url.scheme == "http" and url.hostname == "127.0.0.1" and url.port is not None
                 and 1 <= url.port <= 65535 and url.username is None and url.password is None
                 and not (url.path or url.query or url.fragment) and connection["protocol_version"] == 1
                 and isinstance(token, str) and 32 <= len(token) <= 256
                 and all(c.isascii() and (c.isalnum() or c in "-_") for c in token)
                 and isinstance(connection["instance_id"], str))
        if not valid:
            raise ValueError()
        return url.port
    except (ValueError, KeyError, TypeError, AttributeError):
        raise ApiError("invalid_connection", "Invalid connection details. Copy them again from the chosen window.") from None


def read(connection, endpoint="workspace", **params):
    allowed = ("capabilities", "workspace", "overview", "plot", "changes", "traces", "datasets")
    if endpoint not in allowed:
        try:
            kind, uid = endpoint.split("/")
            if kind not in ("traces", "datasets", "trace-colors"):
                raise ValueError()
            UUID(uid)
        except (ValueError, AttributeError):
            raise ApiError("invalid_query", "Unknown read endpoint.") from None
    query = "?" + urlencode(params) if params else ""
    return _request(connection, "GET", f"/v1/{endpoint}{query}")


def set_trace_color(connection, **command):
    """One explicit command; never automatically retries an uncertain result."""
    return _request(connection, "POST", "/v1/commands/set-trace-color", command)


def _request(connection, method, path, command=None):
    port = validate_connection(connection)
    # Direct loopback connection; proxy environment variables are never consulted.
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        headers = {"Authorization": f"Bearer {connection['token']}"}
        body = None
        if command is not None:
            try:
                body = json.dumps(command, allow_nan=False).encode()
            except (TypeError, ValueError):
                raise ApiError("invalid_command", "Command must contain JSON-compatible values.") from None
            if len(body) > 8192:
                raise ApiError("invalid_command", "Command exceeds the input limit.")
            headers["Content-Type"] = "application/json"
        client.request(method, path, body=body, headers=headers)
        response = client.getresponse()
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ApiError("response_too_large", "Response exceeds the API limit. Use a focused read.")
        if response.status == 401:
            raise ApiError("access_revoked", "Credentials are no longer accepted. Reconnect from the chosen window.", 401)
        try:
            result = json.loads(body)
            if not isinstance(result, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            raise ApiError("invalid_response", "The local server returned an invalid response.") from None
        if response.status != 200:
            # Never repeat arbitrary server text from a misidentified local service.
            known = {
                "read_only": "Agent color editing is disabled in the desktop connection panel.",
                "editor_busy": "A modal editor is open. Wait for the person to finish, then retry the same request.",
                "color_conflict": "Trace color changed. Read its current color state before deciding on another edit.",
                "workspace_changed": "Workspace was replaced. Read a new overview and color state.",
                "request_id_reused": "Request ID was already used with different arguments.",
                "invalid_command": "Invalid command. Check the editing contract and capabilities.",
                "trace_not_found": "Trace unavailable. Refresh the overview.",
                "dataset_not_found": "Dataset unavailable. Refresh the overview.",
                "invalid_query": "Unsupported query parameters. Check the API guide.",
                "workspace_busy": "Workspace loading is in progress. Retry after it finishes.",
                "snapshot_too_large": "Response too large. Request a smaller section or page.",
                "snapshot_unavailable": "The desktop could not inspect its current settings.",
                "unknown_endpoint": "This desktop does not support the endpoint. Check capabilities.",
            }
            code = result.get("error")
            if not isinstance(code, str) or code not in known:
                code = "request_rejected"
            raise ApiError(code, known.get(code, "The desktop rejected this request."), response.status)
        if (result.get("instance_id") != connection["instance_id"]
                or result.get("protocol_version") != 1):
            raise ApiError("instance_changed", "Connection instance changed; reconnect in the desktop.")
        return result
    except PermissionError:
        raise ApiError("local_access_denied", "Local network access was denied by the execution environment.") from None
    except (socket.timeout, TimeoutError):
        raise ApiError("connection_timeout", "The desktop did not respond in time. Retry after any dialog or loading completes.") from None
    except (OSError, http.client.HTTPException):
        raise ApiError("connection_unavailable", "Cannot reach this desktop connection. Check the app and Agent API panel.") from None
    finally:
        client.close()
