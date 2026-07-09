from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nollm.grf.exporters import to_jsonable  # noqa: E402
from nollm.grf.facade import admit_request_from_mapping, capture_request_from_mapping, load_json_request, recall_query_from_mapping, GRFFacade  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="run_nollm_grf")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("capture", "admit", "recall", "replay"):
        item = sub.add_parser(name)
        item.add_argument("--workspace", required=True)
        item.add_argument("--request", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)

    try:
        facade = GRFFacade(Path(args.workspace))
        if args.command == "capture":
            result = facade.capture(capture_request_from_mapping(load_json_request(Path(args.request))))
        elif args.command == "admit":
            shard_id, source_window_id, policy_hint, recorded_at = admit_request_from_mapping(load_json_request(Path(args.request)))
            result = facade.admit(shard_id, source_window_id, policy_hint, recorded_at)
        elif args.command == "recall":
            result = facade.recall(recall_query_from_mapping(load_json_request(Path(args.request))))
        elif args.command == "replay":
            result = facade.replay_recall(recall_query_from_mapping(load_json_request(Path(args.request))))
        else:
            result = facade.validate_workspace()
        _emit({"ok": True, "result": to_jsonable(result)})
        return 0
    except Exception as exc:
        _emit({"ok": False, "error": {"code": exc.__class__.__name__, "message": "request failed"}})
        return 2


def _emit(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
