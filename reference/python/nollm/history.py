from __future__ import annotations

from pathlib import Path
from typing import Any

from .filesystem import card_address, find_card_path, notebook_name, read_ledger


def ledger_query(
    notebook_path: Path,
    *,
    object_id: str | None = None,
    object_type: str | None = None,
    op: str | None = None,
    actor: str | None = None,
    actor_type: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    filters = {
        "object_id": object_id,
        "object_type": object_type,
        "op": op,
        "actor": actor,
        "actor_type": actor_type,
        "since": since,
        "until": until,
        "limit": limit,
    }
    events = [
        compact_ledger_event(event)
        for event in read_ledger(notebook_path)
        if ledger_event_matches(event, filters)
    ]
    events.sort(key=event_sort_key)
    limited = events[:limit]
    return {
        "ok": True,
        "notebook": notebook_name(notebook_path),
        "filters": filters,
        "event_count": len(limited),
        "events": limited,
    }


def object_history(
    notebook_path: Path,
    target: str,
    *,
    op: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    card_path = find_card_path(notebook_path, target)
    card_id = card_path.stem
    notebook = notebook_name(notebook_path)
    events = [
        compact_history_event(event)
        for event in read_ledger(notebook_path)
        if str(event.get("object_id")) == card_id and (op is None or event.get("op") == op)
    ]
    events.sort(key=event_sort_key)
    limited = events[:limit]
    return {
        "ok": True,
        "notebook": notebook,
        "object_id": card_id,
        "address": card_address(notebook, card_id),
        "event_count": len(limited),
        "events": limited,
    }


def ledger_event_matches(event: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key in ("object_id", "object_type", "op", "actor", "actor_type"):
        expected = filters.get(key)
        if expected is not None and str(event.get(key)) != str(expected):
            return False
    timestamp = str(event.get("timestamp", ""))
    since = filters.get("since")
    until = filters.get("until")
    if since is not None and timestamp < str(since):
        return False
    if until is not None and timestamp > str(until):
        return False
    return True


def compact_ledger_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(event.get("event_id", "")),
        "timestamp": str(event.get("timestamp", "")),
        "op": str(event.get("op", "")),
        "actor": str(event.get("actor", "")),
        "actor_type": str(event.get("actor_type", "")),
        "object_type": str(event.get("object_type", "")),
        "object_id": str(event.get("object_id", "")),
    }


def compact_history_event(event: dict[str, Any]) -> dict[str, Any]:
    result = {
        "event_id": str(event.get("event_id", "")),
        "timestamp": str(event.get("timestamp", "")),
        "op": str(event.get("op", "")),
        "actor": str(event.get("actor", "")),
        "actor_type": str(event.get("actor_type", "")),
        "reason": str(event.get("reason", "")),
        "from_status": event.get("from_status"),
        "to_status": event.get("to_status"),
    }
    if event.get("op") == "annotate_card":
        result["annotation_type"] = str(event.get("annotation_type", ""))
        result["annotation"] = str(event.get("annotation", ""))
    return result


def event_sort_key(event: dict[str, Any]) -> tuple[str, str]:
    return (str(event.get("timestamp", "")), str(event.get("event_id", "")))
