from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .annotation import append_annotation, list_annotations
from .audit import build_audit_report, compare_audit_reports, render_audit_json, render_audit_markdown, validate_audit_report_shape
from .filesystem import (
    append_ledger,
    card_address,
    find_card_path,
    init_notebook,
    notebook_name,
    read_card,
    read_ledger,
    read_yaml_file,
    render_card,
    utc_timestamp,
    write_card_file,
)
from .cortex import focus_cards, orient_notebook, surface_anchor
from .ids import card_id_for, next_event_id
from .history import ledger_query, object_history
from .models import CARD_DIRS, CARD_TYPES, SOURCE_KINDS, STATUSES, STATUS_TRANSITIONS, TRUST_VALUES, WRITE_STATUSES
from .recall import deterministic_recall
from .review import build_review_queue
from .tool_api import dispatch_tool_request, error_response, load_tool_manifest
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

    orient = sub.add_parser("orient")
    orient.add_argument("notebook_path")
    orient.add_argument("query_or_task")
    orient.set_defaults(func=cmd_orient)

    surface = sub.add_parser("surface")
    surface.add_argument("notebook_path")
    surface.add_argument("--anchor", required=True)
    surface.add_argument("--limit", type=int, default=5)
    surface.set_defaults(func=cmd_surface)

    focus = sub.add_parser("focus")
    focus.add_argument("notebook_path")
    focus.add_argument("--anchor", required=True)
    focus.add_argument("--type")
    focus.add_argument("--status")
    focus.add_argument("--limit", type=int, default=5)
    focus.add_argument("--include-body", action="store_true")
    focus.set_defaults(func=cmd_focus)

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
    ledger.add_argument("--object-id")
    ledger.add_argument("--object-type")
    ledger.add_argument("--op")
    ledger.add_argument("--actor")
    ledger.add_argument("--actor-type")
    ledger.add_argument("--since")
    ledger.add_argument("--until")
    ledger.set_defaults(func=cmd_ledger)

    history = sub.add_parser("history")
    history.add_argument("notebook_path")
    history.add_argument("card_id_or_address")
    history.add_argument("--op")
    history.add_argument("--limit", type=int, default=20)
    history.set_defaults(func=cmd_history)

    audit = sub.add_parser("audit")
    audit.add_argument("notebook_path")
    audit.add_argument("--format", choices=["json", "markdown"], default="json")
    audit.add_argument("--out")
    audit.set_defaults(func=cmd_audit)

    audit_check = sub.add_parser("audit-check")
    audit_check.add_argument("notebook_path")
    audit_check.add_argument("--against", required=True)
    audit_check.set_defaults(func=cmd_audit_check)

    review = sub.add_parser("review")
    review.add_argument("notebook_path")
    review.add_argument("--status", action="append", choices=sorted(STATUSES))
    review.add_argument("--type", choices=sorted(CARD_TYPES))
    review.add_argument("--anchor")
    review.add_argument("--trust", choices=sorted(TRUST_VALUES))
    review.add_argument("--limit", type=int, default=20)
    review.set_defaults(func=cmd_review)

    inspect = sub.add_parser("inspect")
    inspect.add_argument("notebook_path")
    inspect.add_argument("--status", action="append", choices=sorted(STATUSES))
    inspect.add_argument("--type", choices=sorted(CARD_TYPES))
    inspect.add_argument("--anchor")
    inspect.add_argument("--trust", choices=sorted(TRUST_VALUES))
    inspect.add_argument("--limit", type=int, default=20)
    inspect.set_defaults(func=cmd_review)

    annotate = sub.add_parser("annotate")
    annotate.add_argument("notebook_path")
    annotate.add_argument("card_id_or_address")
    annotate.add_argument("--note", required=True)
    annotate.add_argument("--annotation-type", default="note")
    annotate.add_argument("--actor", default="operator")
    annotate.add_argument("--actor-type", default="human")
    annotate.set_defaults(func=cmd_annotate)

    annotations = sub.add_parser("annotations")
    annotations.add_argument("notebook_path")
    annotations.add_argument("card_id_or_address")
    annotations.add_argument("--annotation-type")
    annotations.add_argument("--limit", type=int, default=20)
    annotations.set_defaults(func=cmd_annotations)

    tools = sub.add_parser("tools")
    tools.set_defaults(func=cmd_tools)

    tool = sub.add_parser("tool")
    tool.add_argument("request_json_file")
    tool.set_defaults(func=cmd_tool)

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


def cmd_orient(args: argparse.Namespace) -> int:
    print(json.dumps(orient_notebook(Path(args.notebook_path), args.query_or_task), indent=2, ensure_ascii=False))
    return 0


def cmd_surface(args: argparse.Namespace) -> int:
    try:
        surface = surface_anchor(Path(args.notebook_path), args.anchor, args.limit)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(surface, indent=2, ensure_ascii=False))
    return 0


def cmd_focus(args: argparse.Namespace) -> int:
    try:
        focus = focus_cards(
            Path(args.notebook_path),
            anchor_id=args.anchor,
            card_type=args.type,
            status=args.status,
            limit=args.limit,
            include_body=args.include_body,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(focus, indent=2, ensure_ascii=False))
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    if args.status not in WRITE_STATUSES:
        print("write refuses confirmed/superseded/rejected/archived status; use status command", file=sys.stderr)
        return 2
    path = Path(args.notebook_path)
    if not args.anchor:
        print("write requires at least one --anchor", file=sys.stderr)
        return 2
    known_anchors = anchor_ids(path)
    missing_anchors = [anchor for anchor in args.anchor if anchor not in known_anchors]
    if missing_anchors:
        print(f"unknown anchor(s): {', '.join(missing_anchors)}", file=sys.stderr)
        return 2
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
    if (from_status, args.to) not in STATUS_TRANSITIONS:
        print(f"invalid status transition: {from_status} -> {args.to}", file=sys.stderr)
        return 2
    if args.to == "confirmed" and front.get("source") == "llm_inference":
        print("cannot confirm a card with source llm_inference; change the source before confirming", file=sys.stderr)
        return 2
    event_id = next_event_id(path / "ledger" / "events.jsonl")
    card_id = str(front["id"])
    notebook = notebook_name(path)
    trust_before = front.get("trust")
    trust_after = "human-approved" if args.to == "confirmed" and args.human_approval else trust_before
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
        "trust_before": trust_before,
        "trust_after": trust_after,
    }
    if args.human_approval:
        event["human_approval"] = args.human_approval
    if args.superseded_by:
        try:
            superseded_path = find_card_path(path, args.superseded_by)
        except (FileNotFoundError, ValueError) as exc:
            print(f"--superseded-by must resolve to an existing card: {exc}", file=sys.stderr)
            return 2
        if superseded_path.stem == card_id:
            print("--superseded-by must not refer to the same card", file=sys.stderr)
            return 2
        event["superseded_by"] = superseded_path.stem
        front["superseded_by"] = event["superseded_by"]
    append_ledger(path, event)
    front["status"] = args.to
    front["trust"] = trust_after
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
    try:
        response = ledger_query(
            Path(args.notebook_path),
            object_id=args.object_id,
            object_type=args.object_type,
            op=args.op,
            actor=args.actor,
            actor_type=args.actor_type,
            since=args.since,
            until=args.until,
            limit=args.limit,
        )
    except ValueError as exc:
        print(json.dumps(error_response("ledger", "invalid_request", str(exc)), indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    try:
        response = object_history(
            Path(args.notebook_path),
            args.card_id_or_address,
            op=args.op,
            limit=args.limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps(error_response("history", "invalid_request", str(exc)), indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    report = build_audit_report(Path(args.notebook_path))
    if args.format == "markdown":
        output = render_audit_markdown(report)
    else:
        output = render_audit_json(report)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def cmd_audit_check(args: argparse.Namespace) -> int:
    try:
        expected = json.loads(Path(args.against).read_text(encoding="utf-8-sig"))
    except OSError as exc:
        print(json.dumps(audit_check_error("unreadable_snapshot", str(exc)), indent=2, ensure_ascii=False))
        return 2
    except json.JSONDecodeError as exc:
        print(json.dumps(audit_check_error("invalid_snapshot_json", str(exc)), indent=2, ensure_ascii=False))
        return 2
    actual = build_audit_report(Path(args.notebook_path))
    expected_issues = validate_audit_report_shape(expected)
    actual_issues = validate_audit_report_shape(actual)
    if expected_issues or actual_issues:
        response = audit_check_error(
            "invalid_audit_schema",
            "Snapshot or current audit report does not match the audit schema.",
        )
        response["schema_issues"] = {
            "expected": expected_issues,
            "actual": actual_issues,
        }
        print(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
        return 2
    response = compare_audit_reports(expected, actual)
    print(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if response["matches"] else 1


def audit_check_error(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "matches": False,
        "drift_count": 0,
        "drifts": [],
        "ignored_fields": ["notebook.path"],
        "error": {
            "code": code,
            "message": message,
        },
    }


def cmd_review(args: argparse.Namespace) -> int:
    if args.limit < 0:
        print("--limit must be non-negative", file=sys.stderr)
        return 2
    response = build_review_queue(
        Path(args.notebook_path),
        statuses=args.status,
        card_type=args.type,
        anchor=args.anchor,
        trust=args.trust,
        limit=args.limit,
    )
    print(json.dumps(response, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_annotate(args: argparse.Namespace) -> int:
    try:
        result = append_annotation(
            Path(args.notebook_path),
            args.card_id_or_address,
            args.note,
            annotation_type=args.annotation_type,
            actor=args.actor,
            actor_type=args.actor_type,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps(error_response("annotate", "invalid_request", str(exc)), indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_annotations(args: argparse.Namespace) -> int:
    try:
        result = list_annotations(
            Path(args.notebook_path),
            args.card_id_or_address,
            annotation_type=args.annotation_type,
            limit=args.limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(json.dumps(error_response("annotations", "invalid_request", str(exc)), indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    print(json.dumps(load_tool_manifest(), indent=2, ensure_ascii=False))
    return 0


def cmd_tool(args: argparse.Namespace) -> int:
    try:
        request = json.loads(Path(args.request_json_file).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        response = error_response("", "invalid_json", str(exc))
        print(json.dumps(response, indent=2, ensure_ascii=False))
        return 1
    response = dispatch_tool_request(request)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0 if response.get("ok") else 1


def anchor_ids(path: Path) -> set[str]:
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    return {
        str(anchor.get("id"))
        for anchor in anchors_doc.get("anchors", []) or []
        if isinstance(anchor, dict) and anchor.get("id")
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
