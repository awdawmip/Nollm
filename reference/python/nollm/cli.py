from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .filesystem import (
    append_ledger,
    card_address,
    find_card_path,
    init_notebook,
    notebook_name,
    read_card,
    read_ledger,
    render_card,
    utc_timestamp,
    write_card_file,
)
from .ids import card_id_for, next_event_id
from .models import CARD_DIRS, CARD_TYPES, SOURCE_KINDS, STATUSES, TRUST_VALUES, WRITE_STATUSES
from .recall import deterministic_recall
from .validation import validate_notebook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nollm")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("path")
    init.add_argument("--notebook", required=True)
    init.set_defaults(func=cmd_init)

    validate = sub.add_parser("validate")
    validate.add_argument("notebook_path")
    validate.set_defaults(func=cmd_validate)

    write = sub.add_parser("write")
    write.add_argument("notebook_path")
    write.add_argument("--type", required=True, choices=sorted(CARD_TYPES))
    write.add_argument("--title", required=True)
    write.add_argument("--claim", required=True)
    write.add_argument("--reason", required=True)
    write.add_argument("--anchor", action="append", default=[])
    write.add_argument("--source", required=True, choices=sorted(SOURCE_KINDS))
    write.add_argument("--trust", required=True, choices=sorted(TRUST_VALUES))
    write.add_argument("--status", default="candidate", choices=sorted(STATUSES))
    write.add_argument("--body", default="")
    write.set_defaults(func=cmd_write)

    read = sub.add_parser("read")
    read.add_argument("notebook_path")
    read.add_argument("card_id_or_address")
    read.set_defaults(func=cmd_read)

    status = sub.add_parser("status")
    status.add_argument("notebook_path")
    status.add_argument("card_id_or_address")
    status.add_argument("--to", required=True, choices=sorted(STATUSES))
    status.add_argument("--reason", required=True)
    status.add_argument("--human-approval")
    status.add_argument("--superseded-by")
    status.set_defaults(func=cmd_status)

    recall = sub.add_parser("recall")
    recall.add_argument("notebook_path")
    recall.add_argument("query_or_task")
    recall.set_defaults(func=cmd_recall)

    ledger = sub.add_parser("ledger")
    ledger.add_argument("notebook_path")
    ledger.add_argument("--limit", type=int, default=10)
    ledger.set_defaults(func=cmd_ledger)

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    init_notebook(Path(args.path), args.notebook)
    print(f"initialized notebook: {args.notebook} at {args.path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    issues = validate_notebook(Path(args.notebook_path))
    if issues:
        print("FAIL")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("PASS")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    if args.status not in WRITE_STATUSES:
        print("write refuses confirmed/superseded/rejected/archived status; use status command", file=sys.stderr)
        return 2
    path = Path(args.notebook_path)
    notebook = notebook_name(path)
    card_id = card_id_for(args.title, path / "cards")
    event_id = next_event_id(path / "ledger" / "events.jsonl")
    front = {
        "id": card_id,
        "title": args.title,
        "type": args.type,
        "anchors": args.anchor,
        "created": utc_timestamp(),
        "status": args.status,
        "claim": args.claim,
        "reason": args.reason,
        "source": args.source,
        "trust": args.trust,
        "evidence_refs": [],
        "implications": [],
        "do_not_infer": [],
        "ledger_event": event_id,
    }
    body = args.body or f"# {args.title}\n\n{args.claim}\n"
    card_path = path / "cards" / CARD_DIRS[args.type] / f"{card_id}.md"
    write_card_file(card_path, front, body)
    event = {
        "event_id": event_id,
        "op": "write_card",
        "actor": "cli_user",
        "actor_type": "human",
        "from_status": None,
        "to_status": args.status,
        "reason": args.reason,
        "timestamp": utc_timestamp(),
        "object_type": "card",
        "object_id": card_id,
        "address": card_address(notebook, card_id),
        "action": "create",
    }
    append_ledger(path, event)
    print(card_address(notebook, card_id))
    print(event_id)
    return 0


def cmd_read(args: argparse.Namespace) -> int:
    card_path = find_card_path(Path(args.notebook_path), args.card_id_or_address)
    print(card_path.read_text(encoding="utf-8"), end="")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    path = Path(args.notebook_path)
    if args.to == "confirmed" and not args.human_approval:
        print("--human-approval is required when confirming", file=sys.stderr)
        return 2
    if args.to == "superseded" and not args.superseded_by:
        print("--superseded-by is required when superseding", file=sys.stderr)
        return 2
    if args.to == "rejected" and not args.reason:
        print("--reason is required when rejecting", file=sys.stderr)
        return 2

    front, body, card_path = read_card(path, args.card_id_or_address)
    from_status = front.get("status")
    event_id = next_event_id(path / "ledger" / "events.jsonl")
    card_id = str(front["id"])
    notebook = notebook_name(path)
    event: dict[str, Any] = {
        "event_id": event_id,
        "op": "update_status",
        "actor": "cli_user",
        "actor_type": "human",
        "from_status": from_status,
        "to_status": args.to,
        "reason": args.reason,
        "timestamp": utc_timestamp(),
        "object_type": "card",
        "object_id": card_id,
        "address": card_address(notebook, card_id),
    }
    if args.human_approval:
        event["human_approval"] = args.human_approval
    if args.superseded_by:
        event["superseded_by"] = args.superseded_by.rstrip("/").split("/")[-1]
        front["superseded_by"] = event["superseded_by"]
    append_ledger(path, event)
    front["status"] = args.to
    front["ledger_event"] = event_id
    card_path.write_text(render_card(front, body), encoding="utf-8")
    print(f"{card_id}: {from_status} -> {args.to}")
    print(event_id)
    return 0


def cmd_recall(args: argparse.Namespace) -> int:
    digest, json_path, md_path = deterministic_recall(Path(args.notebook_path), args.query_or_task)
    print(f"json: {json_path}")
    print(f"markdown: {md_path}")
    print(f"cards_read: {len(digest['cards_read'])}")
    for warning in digest["warnings"]:
        print(f"warning: {warning}")
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    events = read_ledger(Path(args.notebook_path))[-args.limit :]
    for event in events:
        print(json.dumps(event, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

