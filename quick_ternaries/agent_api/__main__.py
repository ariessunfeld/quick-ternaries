"""Read JSON connection details from stdin, never from process arguments."""

import argparse
import json
import sys

from .client import read


def main():
    parser = argparse.ArgumentParser(description="Read a chosen Quick Ternaries desktop instance")
    parser.add_argument("endpoint", choices=("capabilities", "workspace"))
    args = parser.parse_args()
    try:
        connection = json.loads(sys.stdin.readline(8193))
        print(json.dumps(read(connection, args.endpoint), indent=2, ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Avoid echoing credentials or malformed input in diagnostics.
        print(f"Could not read the agent API ({type(error).__name__}). Check connection details "
              "and that access is enabled in the desktop.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
