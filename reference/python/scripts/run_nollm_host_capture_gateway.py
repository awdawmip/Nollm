"""HCG1 file-first capture gateway CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from nollm.dream_geometry.host_capture_gateway import capture_from_text, read_from_text
from nollm.dream_geometry.host_capture_gateway.errors import HCG_INVALID_REQUEST
from nollm.dream_geometry.host_capture_gateway.serialization import canonical_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nollm HCG1 host capture gateway")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("capture", "read"):
        command = subparsers.add_parser(name)
        command.add_argument("--workspace", required=True)
        command.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    try:
        request_text = Path(args.request).read_text(encoding="utf-8")
    except OSError:
        payload = {
            "ok": False,
            "operation": args.command,
            "request_id": None,
            "error": {"code": HCG_INVALID_REQUEST, "message": "request rejected"},
        }
        sys.stdout.write(canonical_json(payload))
        return 2
    workspace = Path(args.workspace).resolve()
    payload = capture_from_text(workspace, request_text) if args.command == "capture" else read_from_text(workspace, request_text)
    sys.stdout.write(canonical_json(payload))
    return 0 if payload.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
