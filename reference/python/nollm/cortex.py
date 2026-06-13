from __future__ import annotations

from pathlib import Path
from typing import Any

from .filesystem import card_address, notebook_name, read_card, read_yaml_file


STATUS_PRIORITY = {
    "confirmed": 4,
    "candidate": 3,
    "draft": 2,
    "superseded": 1,
    "rejected": 1,
    "archived": 0,
}


def orient_notebook(path: Path, query_or_task: str) -> dict[str, Any]:
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    aliases_doc = read_yaml_file(path / "aliases.yaml")
    query = query_or_task.lower()
    terms = query_terms(query_or_task)
    anchors = anchors_doc.get("anchors", []) or []
    alias_map = aliases_doc.get("aliases", {}) if isinstance(aliases_doc.get("aliases", {}), dict) else {}

    matches: list[dict[str, Any]] = []
    direct_ids: set[str] = set()
    for anchor in anchors:
        anchor_id = str(anchor.get("id", ""))
        label = str(anchor.get("label") or anchor.get("title") or "")
        aliases = [str(item) for item in anchor.get("aliases", []) or []]
        definition = str(anchor.get("definition") or anchor.get("description") or "")

        if anchor_id and anchor_id.lower() in query:
            matches.append(anchor_match(anchor_id, 1.0, "id", f"Query contains anchor id {anchor_id}."))
            direct_ids.add(anchor_id)
            continue
        if label and label.lower() in query:
            matches.append(anchor_match(anchor_id, 0.9, "title", f"Query contains anchor title {label}."))
            direct_ids.add(anchor_id)
            continue
        alias_hit = next((alias for alias in aliases if alias and alias.lower() in query), None)
        if alias_hit:
            matches.append(anchor_match(anchor_id, 0.85, "alias", f"Query contains anchor alias {alias_hit}."))
            direct_ids.add(anchor_id)
            continue
        if definition and terms and any(term in definition.lower() for term in terms):
            matches.append(anchor_match(anchor_id, 0.55, "keyword", "Query overlaps anchor definition keywords."))

    for alias, value in alias_map.items():
        target = value.get("anchor") if isinstance(value, dict) else value
        if str(alias).lower() in query and target and not any(match["anchor"] == target for match in matches):
            matches.append(anchor_match(str(target), 0.85, "alias", f"Query contains alias {alias}."))
            direct_ids.add(str(target))

    if direct_ids:
        by_id = {str(anchor.get("id")): anchor for anchor in anchors}
        for direct_id in sorted(direct_ids):
            for neighbor in by_id.get(direct_id, {}).get("neighbors", []) or []:
                neighbor = str(neighbor)
                if neighbor in by_id and not any(match["anchor"] == neighbor for match in matches):
                    matches.append(anchor_match(neighbor, 0.4, "neighbor", f"Neighbor of matched anchor {direct_id}."))

    matches.sort(key=lambda item: (-float(item["confidence"]), item["anchor"]))
    return {
        "input": query_or_task,
        "memory_intent": "recall_surface" if matches else "orient_only",
        "candidate_anchors": [match["anchor"] for match in matches],
        "matched_anchors": matches,
        "new_anchor_needed": not bool(matches),
        "new_anchor_candidate": None,
        "read_depth": "surface" if matches else "none",
        "write_candidate": False,
        "write_intent": "none",
        "reason": "Matched existing anchors." if matches else "No existing anchor matched deterministically.",
        "warnings": [] if matches else ["No anchor matched; do not create anchors automatically."],
    }


def surface_anchor(path: Path, anchor_id: str, limit: int = 5) -> dict[str, Any]:
    anchor = find_anchor(path, anchor_id)
    cards = cards_for_anchor(path, anchor_id)
    counts: dict[str, dict[str, int]] = {}
    for front, _body in cards:
        if front.get("status") == "archived":
            continue
        card_type = str(front.get("type", "unknown"))
        status = str(front.get("status", "unknown"))
        counts.setdefault(card_type, {})
        counts[card_type][status] = counts[card_type].get(status, 0) + 1

    ordered = sorted(cards, key=lambda item: card_sort_key(item[0]))
    notebook = notebook_name(path)
    return {
        "anchor": anchor_id,
        "title": anchor.get("label") or anchor.get("title") or anchor_id,
        "status": anchor.get("status"),
        "scope": anchor.get("scope"),
        "aliases": anchor.get("aliases", []) or [],
        "neighbors": anchor.get("neighbors", []) or [],
        "active_card_counts": counts,
        "top_cards": [
            {
                "id": front.get("id"),
                "address": card_address(notebook, str(front.get("id"))),
                "title": front.get("title"),
                "type": front.get("type"),
                "status": front.get("status"),
                "claim": front.get("claim"),
            }
            for front, _body in ordered[:limit]
            if front.get("status") != "archived"
        ],
    }


def focus_cards(
    path: Path,
    anchor_id: str | None = None,
    card_type: str | None = None,
    status: str | None = None,
    limit: int = 5,
    include_body: bool = False,
    query_or_task: str | None = None,
) -> dict[str, Any]:
    if anchor_id:
        find_anchor(path, anchor_id)
    cards = cards_for_anchor(path, anchor_id) if anchor_id else all_cards(path)
    terms = query_terms(query_or_task or "")
    scored: list[tuple[int, int, dict[str, Any], str]] = []
    for front, body in cards:
        if card_type and front.get("type") != card_type:
            continue
        if status and front.get("status") != status:
            continue
        if not status and front.get("status") == "archived":
            continue
        score = 0
        if terms:
            haystack = " ".join(
                [
                    str(front.get("title", "")),
                    str(front.get("claim", "")),
                    " ".join(front.get("anchors", []) or []),
                    body,
                ]
            ).lower()
            score = sum(1 for term in terms if term in haystack)
            if not score and not anchor_id:
                continue
        scored.append((STATUS_PRIORITY.get(str(front.get("status")), 0), score, front, body))

    scored.sort(key=lambda item: (item[0], item[1], str(item[2].get("id", ""))), reverse=True)
    notebook = notebook_name(path)
    selected = []
    warnings = []
    for _priority, _score, front, body in scored[:limit]:
        item = {
            "id": front.get("id"),
            "address": card_address(notebook, str(front.get("id"))),
            "title": front.get("title"),
            "type": front.get("type"),
            "status": front.get("status"),
            "anchors": front.get("anchors", []) or [],
            "claim": front.get("claim"),
            "source": front.get("source"),
            "trust": front.get("trust"),
            "do_not_infer": front.get("do_not_infer", []) or [],
        }
        if "layer" in front:
            item["layer"] = front["layer"]
        if "anchor_fields" in front:
            item["anchor_fields"] = front["anchor_fields"]
        if "scale_links" in front:
            item["scale_links"] = summarize_scale_links(front["scale_links"])
        if include_body:
            item["body"] = body
        selected.append(item)
        if front.get("status") == "candidate":
            warnings.append(f"Candidate card included: {front.get('id')}")
        if front.get("type") == "hypothesis":
            warnings.append(f"Hypothesis card included: {front.get('id')}")

    return {
        "anchor": anchor_id,
        "filters": {"type": card_type, "status": status, "limit": limit, "include_body": include_body},
        "cards": selected,
        "warnings": warnings,
    }


def anchor_match(anchor_id: str, confidence: float, match_type: str, reason: str) -> dict[str, Any]:
    return {"anchor": anchor_id, "confidence": confidence, "match_type": match_type, "reason": reason}


def summarize_scale_links(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    return {key: len(links) if isinstance(links, list) else links for key, links in value.items()}


def query_terms(query_or_task: str) -> list[str]:
    return [term for term in query_or_task.lower().replace("_", " ").replace(":", " ").split() if len(term) > 2]


def find_anchor(path: Path, anchor_id: str) -> dict[str, Any]:
    for anchor in read_yaml_file(path / "anchors.yaml").get("anchors", []) or []:
        if anchor.get("id") == anchor_id:
            return anchor
    raise ValueError(f"unknown anchor: {anchor_id}")


def cards_for_anchor(path: Path, anchor_id: str | None) -> list[tuple[dict[str, Any], str]]:
    cards = []
    for front, body in all_cards(path):
        if anchor_id in (front.get("anchors", []) or []):
            cards.append((front, body))
    return cards


def all_cards(path: Path) -> list[tuple[dict[str, Any], str]]:
    cards = []
    for card_path in (path / "cards").rglob("*.md"):
        front, body, _ = read_card(path, card_path.stem)
        cards.append((front, body))
    return cards


def card_sort_key(front: dict[str, Any]) -> tuple[int, str]:
    return (STATUS_PRIORITY.get(str(front.get("status")), 0), str(front.get("id", "")))
