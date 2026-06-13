from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .filesystem import notebook_name, read_card, read_ledger, read_yaml_file
from .validation import validate_notebook


BOUNDARIES = {
    "uses_sqlite": False,
    "uses_embeddings": False,
    "uses_vector_db": False,
    "uses_graph_db": False,
    "uses_external_llm": False,
    "performs_geometry_recall": False,
    "performs_polygon_overlap": False,
    "performs_automatic_placement": False,
    "performs_semantic_completeness_scoring": False,
}


AUDIT_SCHEMA: dict[str, dict[str, str]] = {
    "validation": {
        "pass": "boolean",
        "issue_count": "integer",
        "issues": "list",
    },
    "notebook": {
        "name": "string",
        "path": "string",
        "cards": "integer",
        "anchors": "integer",
        "ledger_events": "integer",
        "recall_digests": "integer",
    },
    "cards": {
        "by_status": "object",
        "by_type": "object",
        "by_trust": "object",
        "by_source": "object",
        "by_layer": "object",
    },
    "honeycomb": {
        "cards_with_layer": "integer",
        "cards_with_hex": "integer",
        "cards_with_anchor_fields": "integer",
        "cards_with_scale_links": "integer",
        "invalid_honeycomb_metadata_count": "integer",
    },
    "anchor_fields": {
        "anchor_count": "integer",
        "anchor_ids": "list",
        "card_anchor_usage_counts": "object",
        "anchor_field_usage_counts": "object",
    },
    "recall_digests": {
        "recall_digest_count": "integer",
        "memory_intent_counts": "object",
        "digests_with_active_anchor_fields": "integer",
        "digests_with_scale_path": "integer",
        "digests_with_lateral_recovery": "integer",
        "digests_with_sufficient_scale_reached": "integer",
    },
    "ledger": {
        "ledger_event_count": "integer",
        "ops_count": "object",
        "actor_type_count": "object",
        "status_transition_count": "integer",
        "missing_referenced_object_count": "integer",
    },
    "boundaries": {key: "boolean" for key in BOUNDARIES},
}


def build_audit_report(path: Path) -> dict[str, Any]:
    issues = validate_notebook(path)
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    anchors = [anchor for anchor in anchors_doc.get("anchors", []) or [] if isinstance(anchor, dict)]
    events = read_ledger(path)
    cards = read_cards(path)
    recalls = read_recall_digests(path)

    return {
        "validation": {
            "pass": not issues,
            "issue_count": len(issues),
            "issues": issues,
        },
        "notebook": {
            "name": notebook_name(path),
            "path": path.as_posix(),
            "cards": len(cards),
            "anchors": len(anchors),
            "ledger_events": len(events),
            "recall_digests": len(recalls),
        },
        "cards": card_distribution(cards),
        "honeycomb": honeycomb_summary(cards, issues),
        "anchor_fields": anchor_field_summary(cards, anchors),
        "recall_digests": recall_digest_summary(recalls),
        "ledger": ledger_summary(events, cards),
        "boundaries": dict(BOUNDARIES),
    }


def validate_audit_report_shape(report: dict[str, object]) -> list[str]:
    issues: list[str] = []
    if not isinstance(report, dict):
        return ["audit report must be an object"]

    for section, fields in AUDIT_SCHEMA.items():
        if section not in report:
            issues.append(f"missing top-level section: {section}")
            continue
        section_value = report[section]
        if not isinstance(section_value, dict):
            issues.append(f"invalid type: {section} expected object")
            continue
        for field, expected_type in fields.items():
            if field not in section_value:
                issues.append(f"missing field: {section}.{field}")
                continue
            if not audit_type_matches(section_value[field], expected_type):
                issues.append(f"invalid type: {section}.{field} expected {expected_type}")
    return issues


def audit_type_matches(value: object, expected_type: str) -> bool:
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "list":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False


def read_cards(path: Path) -> list[dict[str, Any]]:
    cards = []
    for card_path in sorted((path / "cards").rglob("*.md")):
        front, _body, resolved_path = read_card(path, card_path.stem)
        cards.append({"front": front, "path": str(resolved_path)})
    return cards


def read_recall_digests(path: Path) -> list[dict[str, Any]]:
    digests = []
    for recall_path in sorted((path / "recalls").glob("*.json")):
        try:
            digest = json.loads(recall_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            digest = {}
        digests.append({"digest": digest, "path": str(recall_path)})
    return digests


def card_distribution(cards: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fronts = [card["front"] for card in cards]
    return {
        "by_status": sorted_counter(front.get("status") for front in fronts),
        "by_type": sorted_counter(front.get("type") for front in fronts),
        "by_trust": sorted_counter(front.get("trust") for front in fronts),
        "by_source": sorted_counter(front.get("source") for front in fronts),
        "by_layer": sorted_counter(str(front.get("layer")) for front in fronts if "layer" in front),
    }


def honeycomb_summary(cards: list[dict[str, Any]], issues: list[str]) -> dict[str, int]:
    fronts = [card["front"] for card in cards]
    invalid_prefixes = (
        "card layer ",
        "card hex",
        "card anchor_fields",
        "card scale_links",
    )
    return {
        "cards_with_layer": sum(1 for front in fronts if "layer" in front),
        "cards_with_hex": sum(1 for front in fronts if "hex" in front),
        "cards_with_anchor_fields": sum(1 for front in fronts if "anchor_fields" in front),
        "cards_with_scale_links": sum(1 for front in fronts if "scale_links" in front),
        "invalid_honeycomb_metadata_count": sum(1 for issue in issues if issue.startswith(invalid_prefixes)),
    }


def anchor_field_summary(cards: list[dict[str, Any]], anchors: list[dict[str, Any]]) -> dict[str, Any]:
    anchor_usage: Counter[str] = Counter()
    field_usage: Counter[str] = Counter()
    for card in cards:
        front = card["front"]
        for anchor in front.get("anchors", []) or []:
            anchor_usage[str(anchor)] += 1
        anchor_fields = front.get("anchor_fields", {})
        if isinstance(anchor_fields, dict):
            for anchor_field in anchor_fields:
                field_usage[str(anchor_field)] += 1

    anchor_ids = sorted(str(anchor.get("id")) for anchor in anchors if anchor.get("id"))
    return {
        "anchor_count": len(anchor_ids),
        "anchor_ids": anchor_ids,
        "card_anchor_usage_counts": dict(sorted(anchor_usage.items())),
        "anchor_field_usage_counts": dict(sorted(field_usage.items())),
    }


def recall_digest_summary(recalls: list[dict[str, Any]]) -> dict[str, Any]:
    memory_intents: Counter[str] = Counter()
    active_anchor_fields = 0
    scale_path = 0
    lateral_recovery = 0
    sufficient_scale_reached = 0
    for recall in recalls:
        digest = recall["digest"]
        if not isinstance(digest, dict):
            continue
        if isinstance(digest.get("memory_intent"), str):
            memory_intents[digest["memory_intent"]] += 1
        if "active_anchor_fields" in digest:
            active_anchor_fields += 1
        if "scale_path" in digest:
            scale_path += 1
        if "lateral_recovery" in digest:
            lateral_recovery += 1
        if "sufficient_scale_reached" in digest:
            sufficient_scale_reached += 1
    return {
        "recall_digest_count": len(recalls),
        "memory_intent_counts": dict(sorted(memory_intents.items())),
        "digests_with_active_anchor_fields": active_anchor_fields,
        "digests_with_scale_path": scale_path,
        "digests_with_lateral_recovery": lateral_recovery,
        "digests_with_sufficient_scale_reached": sufficient_scale_reached,
    }


def ledger_summary(events: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    card_ids = {str(card["front"].get("id")) for card in cards if card["front"].get("id")}
    ops: Counter[str] = Counter()
    actor_types: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    missing_objects = 0
    for event in events:
        if event.get("op"):
            ops[str(event["op"])] += 1
        if event.get("actor_type"):
            actor_types[str(event["actor_type"])] += 1
        if event.get("from_status") != event.get("to_status"):
            transitions[f"{event.get('from_status')}->{event.get('to_status')}"] += 1
        if event.get("object_type") == "card" and str(event.get("object_id")) not in card_ids:
            missing_objects += 1
    return {
        "ledger_event_count": len(events),
        "ops_count": dict(sorted(ops.items())),
        "actor_type_count": dict(sorted(actor_types.items())),
        "status_transition_count": sum(transitions.values()),
        "missing_referenced_object_count": missing_objects,
    }


def render_audit_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def render_audit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Nollm Audit Report",
        "",
        "## Validation",
        "",
        f"- pass: `{str(report['validation']['pass']).lower()}`",
        f"- issue_count: `{report['validation']['issue_count']}`",
        "",
        "## Notebook",
        "",
    ]
    for key, value in report["notebook"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Boundaries", ""])
    for key, value in report["boundaries"].items():
        lines.append(f"- {key}: `{str(value).lower()}`")
    lines.append("")
    return "\n".join(lines)


def sorted_counter(values) -> dict[str, int]:
    counter: Counter[str] = Counter(str(value) for value in values if value is not None and value != "")
    return dict(sorted(counter.items()))
