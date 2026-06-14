from __future__ import annotations

from pathlib import Path
from typing import Any

from .filesystem import (
    append_ledger,
    card_address,
    find_card_path,
    ledger_address,
    notebook_name,
    read_card,
    read_ledger,
    utc_timestamp,
)
from .ids import next_event_id
from .models import ACTOR_TYPES, ANNOTATION_TYPES


def append_annotation(
    notebook_path: Path,
    target: str,
    note: str,
    *,
    annotation_type: str = "note",
    actor: str = "operator",
    actor_type: str = "human",
) -> dict[str, Any]:
    if annotation_type not in ANNOTATION_TYPES:
        raise ValueError(f"invalid annotation_type: {annotation_type}")
    if actor_type not in ACTOR_TYPES:
        raise ValueError(f"invalid actor_type: {actor_type}")
    if not note.strip():
        raise ValueError("annotation note must not be empty")

    front, _body, _card_path = read_card(notebook_path, target)
    card_id = str(front["id"])
    status = str(front.get("status", ""))
    notebook = notebook_name(notebook_path)
    event_id = next_event_id(notebook_path / "ledger" / "events.jsonl")
    event = {
        "event_id": event_id,
        "op": "annotate_card",
        "actor": actor,
        "actor_type": actor_type,
        "timestamp": utc_timestamp(),
        "object_type": "card",
        "object_id": card_id,
        "address": card_address(notebook, card_id),
        "from_status": status,
        "to_status": status,
        "reason": "operator_annotation",
        "annotation_type": annotation_type,
        "annotation": note,
    }
    append_ledger(notebook_path, event)
    return {
        "ok": True,
        "event_id": event_id,
        "address": ledger_address(notebook, event_id),
        "object_id": card_id,
        "annotation_type": annotation_type,
    }


def list_annotations(
    notebook_path: Path,
    target: str,
    *,
    annotation_type: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    if annotation_type is not None and annotation_type not in ANNOTATION_TYPES:
        raise ValueError(f"invalid annotation_type: {annotation_type}")
    if limit < 0:
        raise ValueError("limit must be non-negative")

    card_path = find_card_path(notebook_path, target)
    card_id = card_path.stem
    notebook = notebook_name(notebook_path)
    annotations = []
    for event in read_ledger(notebook_path):
        if event.get("op") != "annotate_card":
            continue
        if str(event.get("object_id")) != card_id:
            continue
        if annotation_type is not None and event.get("annotation_type") != annotation_type:
            continue
        annotations.append(
            {
                "event_id": str(event.get("event_id", "")),
                "timestamp": str(event.get("timestamp", "")),
                "actor": str(event.get("actor", "")),
                "actor_type": str(event.get("actor_type", "")),
                "annotation_type": str(event.get("annotation_type", "")),
                "annotation": str(event.get("annotation", "")),
            }
        )

    annotations.sort(key=lambda event: (event["timestamp"], event["event_id"]))
    limited = annotations[:limit]
    return {
        "ok": True,
        "notebook": notebook,
        "object_id": card_id,
        "address": card_address(notebook, card_id),
        "annotation_count": len(limited),
        "annotations": limited,
    }


def annotation_counts_by_card(notebook_path: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in read_ledger(notebook_path):
        if event.get("op") != "annotate_card":
            continue
        card_id = str(event.get("object_id", ""))
        if not card_id:
            continue
        counts[card_id] = counts.get(card_id, 0) + 1
    return dict(sorted(counts.items()))
