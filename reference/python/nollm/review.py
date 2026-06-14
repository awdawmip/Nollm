from __future__ import annotations

from pathlib import Path
from typing import Any

from .annotation import annotation_counts_by_card
from .filesystem import card_address, notebook_name, read_card


DEFAULT_REVIEW_STATUSES = ["candidate", "draft"]
STATUS_PRIORITY = {"draft": 0, "candidate": 1}


def build_review_queue(
    notebook_path: Path,
    statuses: list[str] | None = None,
    card_type: str | None = None,
    anchor: str | None = None,
    trust: str | None = None,
    limit: int = 20,
) -> dict[str, object]:
    review_statuses = statuses or list(DEFAULT_REVIEW_STATUSES)
    notebook = notebook_name(notebook_path)
    annotation_counts = annotation_counts_by_card(notebook_path)
    cards = []
    for card_path in sorted((notebook_path / "cards").rglob("*.md")):
        front, _body, _resolved_path = read_card(notebook_path, card_path.stem)
        if not include_card(front, review_statuses, card_type, anchor, trust):
            continue
        card_id = str(front.get("id", ""))
        cards.append(review_card(notebook, front, annotation_counts.get(card_id, 0)))

    cards.sort(key=review_sort_key)
    limited_cards = cards[: max(limit, 0)]
    return {
        "ok": True,
        "notebook": notebook,
        "review_filters": {
            "statuses": review_statuses,
            "type": card_type,
            "anchor": anchor,
            "trust": trust,
            "limit": limit,
        },
        "review_count": len(limited_cards),
        "cards": limited_cards,
    }


def include_card(
    front: dict[str, Any],
    statuses: list[str],
    card_type: str | None,
    anchor: str | None,
    trust: str | None,
) -> bool:
    if str(front.get("status")) not in statuses:
        return False
    if card_type is not None and front.get("type") != card_type:
        return False
    if anchor is not None and anchor not in [str(item) for item in front.get("anchors", []) or []]:
        return False
    if trust is not None and front.get("trust") != trust:
        return False
    return True


def review_card(notebook: str, front: dict[str, Any], annotation_count: int = 0) -> dict[str, object]:
    card_id = str(front.get("id", ""))
    anchor_fields = front.get("anchor_fields", {})
    return {
        "address": card_address(notebook, card_id),
        "id": card_id,
        "title": str(front.get("title", "")),
        "type": str(front.get("type", "")),
        "status": str(front.get("status", "")),
        "trust": str(front.get("trust", "")),
        "source": str(front.get("source", "")),
        "anchors": [str(anchor) for anchor in front.get("anchors", []) or []],
        "anchor_fields": sorted(str(key) for key in anchor_fields) if isinstance(anchor_fields, dict) else [],
        "ledger_event": str(front.get("ledger_event", "")),
        "created": str(front.get("created", "")),
        "annotation_count": annotation_count,
        "review_reason": review_reason(front),
    }


def review_reason(front: dict[str, Any]) -> str:
    status = str(front.get("status", ""))
    if status in {"candidate", "draft"}:
        return f"status:{status}"
    if front.get("trust") == "unverified":
        return "trust:unverified"
    if front.get("source") == "llm_inference":
        return "source:llm_inference"
    return "metadata:review"


def review_sort_key(card: dict[str, object]) -> tuple[int, str, str]:
    status = str(card.get("status", ""))
    created = str(card.get("created", ""))
    address = str(card.get("address", ""))
    return (STATUS_PRIORITY.get(status, 99), created, address)
