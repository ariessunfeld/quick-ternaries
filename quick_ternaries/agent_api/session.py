"""Persistent JSON-lines client. Credentials and comparison cache stay in memory.

This is a small CLI protocol, not MCP. A host retains this subprocess's stdin
and stdout across tool calls; only requested results enter its model context.
"""

from collections import OrderedDict
import json
import shutil
import subprocess
import sys

from .client import read, validate_connection
from .contract import ApiError

MAX_INPUT_BYTES = 16 * 1024
MAX_CACHE_BYTES = 2 * 1024 * 1024
MAX_CACHE_ENTRIES = 32


def clipboard_connection():
    if sys.platform == "darwin":
        command = ["pbpaste"]
    elif sys.platform == "win32":
        command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                   "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-Clipboard -Raw"]
    elif shutil.which("wl-paste"):
        command = ["wl-paste", "--no-newline"]
    elif shutil.which("xclip"):
        command = ["xclip", "-selection", "clipboard", "-o"]
    else:
        raise ApiError("clipboard_unavailable", "No supported clipboard reader is available. Use a private stdin handoff.")
    try:
        # Bound even hostile/unexpected clipboard contents, and never relay stderr.
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(process.stdout.read, MAX_INPUT_BYTES + 1)
                try:
                    content = future.result(timeout=3)
                    if len(content) > MAX_INPUT_BYTES:
                        process.kill()
                        raise ApiError("invalid_clipboard", "Clipboard does not contain bounded connection JSON. Copy connection details again.")
                    returncode = process.wait(timeout=1)
                except (FutureTimeout, subprocess.TimeoutExpired):
                    process.kill()
                    raise ApiError("clipboard_unavailable", "Clipboard access did not complete. Check execution permissions.") from None
        if returncode:
            raise ApiError("clipboard_unavailable", "Clipboard access failed. Check execution permissions before copying again.")
    except OSError:
        raise ApiError("clipboard_unavailable", "Clipboard access failed. Check execution permissions.") from None
    try:
        connection = json.loads(content.decode("utf-8-sig"))
        validate_connection(connection)
        return connection
    except (ValueError, UnicodeError):
        raise ApiError("invalid_clipboard", "Clipboard is readable but is not connection JSON. Copy connection details again.") from None


def differences(before, after, path=""):
    """Small scalar deltas; lists/structural changes trigger a fresh result."""
    if before == after:
        return []
    if isinstance(before, dict) and isinstance(after, dict) and before.keys() == after.keys():
        changes = []
        for key in before:
            changes.extend(differences(before[key], after[key], path + "/" + key.replace("~", "~0").replace("/", "~1")))
            if len(changes) > 32:
                raise OverflowError()
        return changes
    if isinstance(before, (dict, list)) or isinstance(after, (dict, list)):
        raise OverflowError()
    return [{"path": path, "before": before, "after": after}]


class Session:
    def __init__(self, clipboard_reader=clipboard_connection):
        self.clipboard_reader = clipboard_reader
        self.connection = None
        self.cache = OrderedDict()
        self.cache_bytes = 0
        self.cursor = None
        self.epoch = None

    def close(self):
        self.connection = None
        self.clear_cache()

    def clear_cache(self):
        self.cache.clear()
        self.cache_bytes = 0
        self.cursor = None
        self.epoch = None

    def remember(self, key, result):
        if key in self.cache:
            self.cache_bytes -= self.cache.pop(key)[1]
        size = len(json.dumps(result).encode())
        if size > MAX_CACHE_BYTES:
            return
        self.cache[key] = (result, size)
        self.cache_bytes += size
        while len(self.cache) > MAX_CACHE_ENTRIES or self.cache_bytes > MAX_CACHE_BYTES:
            _, (_, size) = self.cache.popitem(last=False)
            self.cache_bytes -= size

    def execute(self, command):
        if not isinstance(command, dict):
            raise ApiError("invalid_command", "Expected a JSON command object.")
        op = command.get("op")
        if op in ("quit", "disconnect"):
            if set(command) != {"op"}:
                raise ApiError("invalid_command", "Disconnect and quit take no parameters.")
            self.close()
            return {"status": "closed" if op == "quit" else "disconnected"}
        if op == "connect":
            if set(command) not in ({"op", "source"}, {"op", "connection"}):
                raise ApiError("invalid_command", "Connect using source=clipboard or a private stdin connection object.")
            self.close()
            if "source" in command:
                if command["source"] != "clipboard":
                    raise ApiError("invalid_command", "Unsupported connection source.")
                connection = self.clipboard_reader()
            else:
                connection = command["connection"]
            validate_connection(connection)
            capabilities = read(connection, "capabilities")
            self.connection = {key: connection[key] for key in ("url", "token", "protocol_version", "instance_id")}
            return {"status": "connected", "capabilities": capabilities,
                    "connection_lifetime": "this_process_until_disconnect_or_desktop_revocation"}
        if op != "read" or command.keys() - {"op", "resource", "id", "sections", "offset", "limit", "since", "refresh"}:
            raise ApiError("invalid_command", "Use connect, read, disconnect, or quit. See the session guide.")
        if self.connection is None:
            raise ApiError("not_connected", "Connect once before requesting reads.")
        resource = command.get("resource", "overview")
        if resource not in ("overview", "plot", "trace", "traces", "dataset", "datasets", "changes", "capabilities", "workspace"):
            raise ApiError("invalid_command", "Unknown read resource.")
        if type(command.get("refresh", False)) is not bool:
            raise ApiError("invalid_command", "refresh must be true or false.")
        params = {}
        allowed = {"op", "resource", "refresh"}
        endpoint = resource
        if resource in ("trace", "dataset"):
            uid = command.get("id")
            if not isinstance(uid, str):
                raise ApiError("invalid_command", "A focused object read requires its ID from the overview or catalog.")
            endpoint = resource + "s/" + uid
            allowed.add("id")
        if resource in ("trace", "traces", "dataset", "datasets"):
            allowed.update(("offset", "limit"))
            for key in ("offset", "limit"):
                if key in command:
                    if type(command[key]) is not int:
                        raise ApiError("invalid_command", "Page offsets and limits must be integers.")
                    params[key] = command[key]
        if resource == "trace":
            allowed.add("sections")
            if "sections" in command:
                sections = command["sections"]
                if not isinstance(sections, list) or not all(isinstance(s, str) for s in sections):
                    raise ApiError("invalid_command", "sections must be a list of section names.")
                params["sections"] = ",".join(sections)
        if resource == "changes":
            allowed.add("since")
            since = command.get("since", self.cursor)
            if not isinstance(since, str) or not since:
                raise ApiError("no_baseline", "Read an overview first, or provide a previous read cursor.")
            params["since"] = since
        if command.keys() - allowed:
            raise ApiError("invalid_command", "Some parameters do not apply to this resource.")
        try:
            result = read(self.connection, endpoint, **params)
        except ApiError as error:
            if error.code in ("access_revoked", "instance_changed"):
                self.close()
            raise
        state = result.get("read_state", {})
        epoch = state.get("document_epoch")
        if epoch != self.epoch:
            self.clear_cache()
            self.epoch = epoch
        # Only changes/overview establish or advance the global change baseline.
        # A focused read of one trace must not consume changes to another trace.
        if resource in ("overview", "changes"):
            self.cursor = state.get("cursor")
        if resource == "changes" and result.get("changes", {}).get("resync_required"):
            self.clear_cache()
            self.epoch = epoch
        if resource in ("changes", "capabilities", "workspace"):
            return {"status": "snapshot", "result": result}
        key = json.dumps([endpoint, params], sort_keys=True)
        old = self.cache.get(key, (None, 0))[0]
        self.remember(key, result)
        common = {"resource": resource, "query": params, "id": command.get("id"),
                  "fingerprint": result.get("fingerprint"), "read_state": state,
                  "coverage": {"included": result.get("coverage", {}).get("included", []), "partial": True}}
        if old and not command.get("refresh", False) and not (old.get("truncated") or result.get("truncated")):
            if old.get("fingerprint") == result.get("fingerprint"):
                return {"status": "unchanged", **common}
            try:
                ignored = {"fingerprint", "read_state", "protocol_version", "instance_id"}
                delta = differences({k: v for k, v in old.items() if k not in ignored},
                                    {k: v for k, v in result.items() if k not in ignored})
                if delta and len(json.dumps(delta).encode()) <= 8192:
                    return {"status": "changed", **common, "changes": delta}
            except OverflowError:
                pass
        return {"status": "snapshot", "result": result}


def run_session(stdin=None, stdout=None, *, use_clipboard=False):
    stdin, stdout = stdin or sys.stdin, stdout or sys.stdout
    session = Session()

    def emit(value):
        print(json.dumps(value, ensure_ascii=False, allow_nan=False), file=stdout, flush=True)

    def execute(command):
        try:
            return session.execute(command)
        except ApiError as error:
            return {"status": "error", "error": error.code, "message": str(error)}
        except Exception:
            return {"status": "error", "error": "client_error", "message": "The client could not process this command."}

    try:
        emit(execute({"op": "connect", "source": "clipboard"}) if use_clipboard else {"status": "ready", "connected": False})
        while True:
            line = stdin.readline(MAX_INPUT_BYTES + 1)
            if not line:
                return 0
            if len(line.encode()) > MAX_INPUT_BYTES:
                emit({"status": "error", "error": "command_too_large"})
                return 1
            try:
                command = json.loads(line)
            except (ValueError, RecursionError):
                emit({"status": "error", "error": "invalid_json"})
                continue
            if isinstance(command, dict) and "connection" in command and stdin.isatty():
                emit({"status": "error", "error": "private_stdin_required",
                      "message": "Use clipboard handoff in an interactive terminal to avoid echoing credentials."})
                continue
            result = execute(command)
            emit(result)
            if result.get("status") == "closed":
                return 0
    finally:
        session.close()
