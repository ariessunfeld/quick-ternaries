"""Read JSON connection details from stdin, never from process arguments."""

import argparse
import json
import sys

from .client import read
from .contract import ApiError
from .session import clipboard_connection, run_session


def main():
    parser = argparse.ArgumentParser(description="Read a chosen Quick Ternaries desktop instance")
    parser.add_argument("endpoint", choices=("session", "capabilities", "overview", "plot", "workspace",
                                             "trace", "traces", "dataset", "datasets", "changes"))
    parser.add_argument("--clipboard", action="store_true", help="Read connection details from the clipboard once")
    parser.add_argument("--id", help="Trace or dataset ID from the overview")
    parser.add_argument("--sections", help="Comma-separated trace sections")
    parser.add_argument("--offset", type=int)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--since", help="Change cursor from an earlier read")
    args = parser.parse_args()
    if args.endpoint == "session":
        if any(value is not None for value in (args.id, args.sections, args.offset, args.limit, args.since)):
            parser.error("Session queries are JSON commands on stdin, not command-line options")
        return run_session(use_clipboard=args.clipboard)
    try:
        connection = clipboard_connection() if args.clipboard else json.loads(sys.stdin.readline(8193))
        endpoint = args.endpoint
        if endpoint in ("trace", "dataset"):
            if not args.id:
                raise ApiError("invalid_query", "A trace or dataset read requires --id.")
            endpoint += "s/" + args.id
        elif args.id:
            raise ApiError("invalid_query", "--id applies only to trace or dataset reads.")
        params = {key: getattr(args, key) for key in ("sections", "offset", "limit", "since")
                  if getattr(args, key) is not None}
        print(json.dumps(read(connection, endpoint, **params), indent=2, ensure_ascii=False))
    except ApiError as error:
        print(json.dumps({"error": error.code, "message": str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"error": "invalid_connection", "message": "Check the connection JSON on stdin."}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
