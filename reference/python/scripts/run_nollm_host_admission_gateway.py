#!/usr/bin/env python3
"""Run the HAG1 file-first explicit admission gateway."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from nollm.dream_geometry.host_admission_gateway import admit_from_text, canonical_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nollm HAG1 host admission gateway")
    sub = parser.add_subparsers(dest="command", required=True)
    admit = sub.add_parser("admit")
    admit.add_argument("--workspace", required=True)
    admit.add_argument("--request", required=True)
    args = parser.parse_args(argv)

    try:
        text = Path(args.request).read_text(encoding="utf-8")
        envelope = admit_from_text(Path(args.workspace), text)
    except Exception:
        envelope = {
            "ok": False,
            "action": "admit",
            "request_id": None,
            "error": {"code": "HAG_INTERNAL_ERROR", "message": "request was rejected"},
        }
    sys.stdout.write(canonical_json(envelope) + "\n")
    return 0 if envelope.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
