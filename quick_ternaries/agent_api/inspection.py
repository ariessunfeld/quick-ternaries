"""Focused queries and bounded net-change cursors for observed public settings.

This is deliberately not a document event log or a future write precondition.
Unobserved intermediate edits, data values and excluded settings are not tracked.
"""

from collections import OrderedDict
import hashlib
import json
from urllib.parse import parse_qsl, urlsplit
from uuid import uuid4, UUID

from .contract import ApiError, SECTION_NAMES, TRACE_SECTIONS, coverage

HISTORY_LIMIT = 32
ENDPOINTS = ["/v1/capabilities", "/v1/overview", "/v1/plot", "/v1/traces",
             "/v1/traces/{id}", "/v1/datasets", "/v1/datasets/{id}",
             "/v1/changes", "/v1/workspace"]


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def invalid():
    raise ApiError("invalid_query", "Unsupported endpoint parameters. Read the API query contract.")


def parse_target(target):
    try:
        url = urlsplit(target)
        if url.scheme or url.netloc or url.fragment:
            invalid()
        pairs = parse_qsl(url.query, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
        if len(dict(pairs)) != len(pairs):
            invalid()
        return url.path, dict(pairs)
    except (ValueError, UnicodeError):
        invalid()


def page(params, default=20):
    values = []
    for key, fallback, maximum, minimum in (("offset", 0, 1_000_000, 0), ("limit", default, 100, 1)):
        raw = params.get(key, str(fallback))
        if not raw.isascii() or not raw.isdecimal() or len(raw) > 7:
            invalid()
        value = int(raw)
        if not minimum <= value <= maximum:
            invalid()
        values.append(value)
    return values


class Inspection:
    def __init__(self, reader):
        self.reader = reader
        self.history = OrderedDict()
        self.revision = 0
        self.epoch = None
        self.current = None
        self.cursor = None

    def observe(self, snapshot):
        epoch = getattr(self.reader, "document_epoch", 0)
        if self.epoch != epoch:
            self.history.clear()
            self.current = None
            self.epoch = epoch
        index = {
            "plot": fingerprint({k: snapshot.get(k) for k in ("title", "plot_type", "axes")}),
            "selection": snapshot.get("selected_trace_id"),
            "trace_order": [v["id"] for v in snapshot.get("traces", [])],
            "dataset_order": [v["id"] for v in snapshot.get("datasets", [])],
            "counts": [snapshot.get("trace_count"), snapshot.get("dataset_count")],
            "traces": {v["id"]: fingerprint(v) for v in snapshot.get("traces", [])},
            "datasets": {v["id"]: fingerprint(v) for v in snapshot.get("datasets", [])},
            "complete": not snapshot.get("truncated", False),
        }
        if index != self.current:
            self.revision += 1
            self.current = index
            self.cursor = str(uuid4())
            self.history[self.cursor] = index
            while len(self.history) > HISTORY_LIMIT:
                self.history.popitem(last=False)
        return {"cursor": self.cursor, "read_revision": self.revision,
                "tracking_complete": index["complete"], "document_epoch": epoch,
                "scope": "bounded_public_projection", "write_precondition": False}

    def changes(self, since):
        previous = self.history.get(since)
        if previous is None:
            return {"resync_required": True, "reason": "unknown_or_expired_cursor",
                    "instruction": "Read overview and relevant objects again."}
        if not previous["complete"] or not self.current["complete"]:
            return {"resync_required": True, "reason": "tracking_projection_truncated",
                    "instruction": "Use paginated catalogs and focused reads; changes outside tracking limits are unknown."}
        result = {"resync_required": False, "unchanged": previous == self.current,
                  "changed_sections": [key for key in ("plot", "selection", "trace_order", "dataset_order", "counts")
                                       if previous[key] != self.current[key]]}
        for kind in ("traces", "datasets"):
            old, new = previous[kind], self.current[kind]
            result[kind] = {"added": sorted(new.keys() - old.keys()), "removed": sorted(old.keys() - new.keys()),
                            "changed": sorted(key for key in old.keys() & new.keys() if old[key] != new[key])}
        return result

    def query(self, path, params):
        endpoint = path.removeprefix("/v1/")
        if path not in ENDPOINTS and not endpoint.startswith(("traces/", "datasets/")):
            raise ApiError("unknown_endpoint", "Unknown read endpoint.", 404)
        allowed = {
            "workspace": set(), "overview": set(), "plot": set(),
            "traces": {"offset", "limit"}, "datasets": {"offset", "limit"},
            "changes": {"since"},
        }.get(endpoint)
        uid = None
        if allowed is None:
            try:
                kind, uid = endpoint.split("/")
                UUID(uid)
            except (ValueError, AttributeError):
                invalid()
            allowed = {"offset", "limit", "sections"} if kind == "traces" else {"offset", "limit"}
        if params.keys() - allowed:
            invalid()
        offset, limit = page(params, default=50 if uid else 20)
        sections = params.get("sections", ",".join(SECTION_NAMES)).split(",")
        if any(section not in SECTION_NAMES for section in sections) or len(set(sections)) != len(sections):
            invalid()
        if endpoint == "changes" and not params.get("since"):
            invalid()
        snapshot = self.reader.snapshot()
        state = self.observe(snapshot)
        if endpoint == "workspace":
            result = {"workspace": snapshot}
        elif endpoint == "changes":
            result = {"changes": self.changes(params["since"]),
                      "coverage": snapshot.get("coverage", coverage(["bounded_public_projection"]))}
        elif endpoint == "plot":
            result = {"plot": {key: snapshot[key] for key in ("title", "plot_type", "axes")},
                      "truncated": snapshot["truncated"], "coverage": coverage(["title", "plot_type", "axes"])}
        elif endpoint == "overview":
            traces, datasets = self.reader.catalog("traces"), self.reader.catalog("datasets")
            result = {"overview": {key: snapshot[key] for key in ("title", "plot_type", "trace_count", "dataset_count", "selected_trace_id")},
                      "traces": traces["traces"], "datasets": datasets["datasets"],
                      "next_trace_offset": traces["next_offset"], "next_dataset_offset": datasets["next_offset"],
                      "truncated": snapshot["truncated"] or traces["truncated"] or datasets["truncated"],
                      "coverage": coverage(["overview", "trace_identity_page", "dataset_summary_page"])}
        elif endpoint in ("traces", "datasets"):
            result = self.reader.catalog(endpoint, offset, limit)
        elif endpoint.startswith("traces/"):
            result = self.reader.trace(uid, sections, offset, limit)
        else:
            result = self.reader.dataset(uid, offset, limit)
        return {**result, "read_state": state, "fingerprint": fingerprint(result)}


def capabilities():
    return {"capabilities": ["workspace.read", "focused.read", "changes.read"], "permissions": ["read"],
            "identity_scope": "connection", "data_rows": False, "endpoints": ENDPOINTS,
            "trace_sections": ["identity", *TRACE_SECTIONS, "filters"],
            "coverage": coverage(["title", "plot_type", "axes", "trace_sections", "dataset_schema"]),
            "changes": {"scope": "bounded_public_projection", "history_limit": HISTORY_LIMIT,
                        "semantics": "net_changes_between_reads", "write_precondition": False}}
