from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cortex import focus_cards, orient_notebook, surface_anchor
from .filesystem import notebook_name, recall_address
from .ids import next_recall_id
from .models import RECALL_KEYS


def deterministic_recall(path: Path, query_or_task: str) -> tuple[dict[str, Any], Path, Path]:
    notebook = notebook_name(path)
    orientation = orient_notebook(path, query_or_task)
    anchors_used = list(orientation.get("candidate_anchors", []))
    surfaces = [surface_anchor(path, anchor_id, limit=5) for anchor_id in anchors_used]
    focused = []
    warnings = list(orientation.get("warnings", []))
    for anchor_id in anchors_used:
        result = focus_cards(path, anchor_id=anchor_id, limit=5, query_or_task=query_or_task)
        focused.extend(result["cards"])
        warnings.extend(result["warnings"])
    used_fallback = False
    if not focused:
        result = focus_cards(path, limit=5, query_or_task=query_or_task)
        focused.extend(result["cards"])
        warnings.extend(result["warnings"])
        used_fallback = bool(focused)

    seen = set()
    selected = []
    for card in focused:
        if card["address"] not in seen:
            selected.append(card)
            seen.add(card["address"])
    cards_read = [card["address"] for card in selected]
    active_anchor_fields = selected_anchor_fields(selected)
    scale_path = selected_scale_path(selected)
    open_questions = [str(card.get("claim")) for card in selected if card.get("type") == "question" and card.get("claim")]
    anchors_discovered_from_cards = sorted(
        {
            anchor
            for card in selected
            for anchor in (card.get("anchors", []) or [])
        }
    ) if used_fallback else []
    fallback_warning = (
        "No anchor coordinate matched; selected cards come from a bounded lexical scan and are lower-confidence."
        if used_fallback
        else ""
    )
    if fallback_warning:
        warnings.append(fallback_warning)

    memory_intent = "orient_only"
    if selected:
        memory_intent = "recall_focus"
    elif anchors_used or surfaces:
        memory_intent = "recall_surface"

    digest = {
        "query_or_task": query_or_task,
        "memory_intent": memory_intent,
        "anchors_used": anchors_used,
        "cards_read": cards_read,
        "recalled_points": [str(card.get("claim")) for card in selected if card.get("claim")],
        "warnings": warnings,
        "do_not_assume": sorted(
            {
                item
                for card in selected
                for item in (card.get("do_not_infer", []) or [])
            }
        ),
        "source_addresses": cards_read,
        "open_questions": open_questions,
        "active_anchor_fields": active_anchor_fields,
        "scale_path": scale_path,
        "lateral_recovery": [],
        "sufficient_scale_reached": bool(selected),
        "orientation": orientation,
        "surfaces_read": surfaces,
        "focus_filters": {"limit": 5, "include_body": False},
        "fallback_mode": "lexical_card_scan" if used_fallback else "none",
        "fallback_reason": "No anchor matched; bounded lexical card scan selected cards." if used_fallback else "",
        "fallback_warning": fallback_warning,
        "anchors_discovered_from_cards": anchors_discovered_from_cards,
    }
    for key in RECALL_KEYS:
        digest.setdefault(key, [] if key != "query_or_task" and key != "memory_intent" else "")

    recalls_dir = path / "recalls"
    recalls_dir.mkdir(exist_ok=True)
    recall_id = next_recall_id(recalls_dir)
    digest["address"] = recall_address(notebook, recall_id)
    json_path = recalls_dir / f"{recall_id}.json"
    md_path = recalls_dir / f"{recall_id}.md"
    json_path.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown_digest(digest), encoding="utf-8")
    return digest, json_path, md_path


def render_markdown_digest(digest: dict[str, Any]) -> str:
    lines = ["# Recall Digest", ""]
    for key in RECALL_KEYS:
        lines.append(f"## {key}")
        lines.append("")
        value = digest.get(key)
        if isinstance(value, list):
            if value:
                lines.extend(render_list_item(item) for item in value)
            else:
                lines.append("- none")
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)


def selected_anchor_fields(cards: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            str(anchor_field)
            for card in cards
            for anchor_field in ((card.get("anchor_fields") or {}).keys() if isinstance(card.get("anchor_fields"), dict) else [])
        }
    )


def selected_scale_path(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for card in cards:
        if "layer" not in card:
            continue
        anchor_fields = card.get("anchor_fields") if isinstance(card.get("anchor_fields"), dict) else {}
        items.append(
            {
                "layer": card["layer"],
                "card": card["address"],
                "anchor_fields": sorted(str(key) for key in anchor_fields.keys()),
                "note": "metadata-only; Core did not perform geometry-based recall",
            }
        )
    return sorted(items, key=lambda item: (item["layer"], item["card"]))


def render_list_item(item: Any) -> str:
    if isinstance(item, str) and item.startswith("nollm://"):
        return f"- `{item}`"
    if isinstance(item, (dict, list)):
        return f"- `{json.dumps(item, ensure_ascii=False, sort_keys=True)}`"
    return f"- {item}"
