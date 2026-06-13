from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .filesystem import read_card, read_ledger, read_yaml_file
from .honeycomb import layer_rotation_degrees, layer_scale
from .models import CARD_TYPES, RECALL_KEYS, SOURCE_KINDS, STATUSES, TRUST_VALUES

ANCHOR_FIELD_ROLES = {"primary", "supporting", "adjacent", "boundary", "recovery", "warning"}
HEX_KEYS = {"q", "r", "rotation", "scale"}
SCALE_LINK_KEYS = {"coarser", "finer", "overlaps", "recovery"}
FLOAT_TOLERANCE = 1e-6
MEMORY_INTENTS = {
    "read_none",
    "orient_only",
    "recall_surface",
    "recall_focus",
    "write_candidate",
    "ask_user_confirmation",
}


def validate_notebook(path: Path) -> list[str]:
    issues: list[str] = []
    anchors_doc = read_yaml_file(path / "anchors.yaml")
    aliases_doc = read_yaml_file(path / "aliases.yaml")
    anchors = {anchor.get("id") for anchor in anchors_doc.get("anchors", [])}
    anchors.discard(None)

    for anchor in anchors_doc.get("anchors", []):
        status = anchor.get("status")
        if status and status not in STATUSES:
            issues.append(f"invalid anchor status: {anchor.get('id')} -> {status}")

    aliases = aliases_doc.get("aliases", {})
    if isinstance(aliases, dict):
        for alias, value in aliases.items():
            target = value.get("anchor") if isinstance(value, dict) else value
            if target not in anchors:
                issues.append(f"alias targets unknown anchor: {alias} -> {target}")

    events = read_ledger(path)
    event_ids: set[str] = set()
    creation_events: set[str] = set()
    status_events: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        event_id = event.get("event_id")
        if not event_id:
            issues.append("ledger event missing event_id")
        elif event_id in event_ids:
            issues.append(f"duplicate ledger event id: {event_id}")
        else:
            event_ids.add(event_id)
        if event.get("op") == "write_card":
            creation_events.add(str(event.get("object_id")))
        if event.get("from_status") != event.get("to_status") and event.get("from_status") is not None:
            status_events.setdefault(str(event.get("object_id")), []).append(event)

    card_records = []
    for card_path in (path / "cards").rglob("*.md"):
        front, _body, _ = read_card(path, card_path.stem)
        card_records.append((card_path, front))
    card_ids = {str(front.get("id") or card_path.stem) for card_path, front in card_records}

    for card_path, front in card_records:
        card_id = str(front.get("id") or card_path.stem)
        status = front.get("status")
        card_type = front.get("type")
        trust = front.get("trust")
        source = front.get("source")

        if status not in STATUSES:
            issues.append(f"card has invalid status: {card_id} -> {status}")
        if card_type not in CARD_TYPES:
            issues.append(f"card has invalid type: {card_id} -> {card_type}")
        if trust and trust not in TRUST_VALUES:
            issues.append(f"card has invalid trust: {card_id} -> {trust}")
        if source and source not in SOURCE_KINDS:
            issues.append(f"card has invalid source: {card_id} -> {source}")
        for anchor in front.get("anchors", []) or []:
            if anchor not in anchors:
                issues.append(f"card references unknown anchor: {card_id} -> {anchor}")
        if card_id not in creation_events:
            issues.append(f"card missing creation ledger event: {card_id}")
        if front.get("ledger_event") and front["ledger_event"] not in event_ids:
            issues.append(f"card references missing ledger event: {card_id} -> {front['ledger_event']}")
        if status == "confirmed":
            has_human_approval = any(
                event.get("object_id") == card_id
                and event.get("to_status") == "confirmed"
                and (event.get("actor_type") == "human" or bool(event.get("human_approval")))
                for event in events
            )
            if not has_human_approval:
                issues.append(f"confirmed card lacks human approval ledger evidence: {card_id}")
            if trust not in {"human-approved", "source-backed"}:
                issues.append(f"confirmed card has weak trust: {card_id} -> {trust}")
            if source == "llm_inference":
                issues.append(f"confirmed card cannot use llm_inference source: {card_id}")
        if status == "superseded" and front.get("superseded_by") == card_id:
            issues.append(f"card cannot supersede itself: {card_id}")
        validate_card_architecture_metadata(front, card_id, issues)
        if status_events.get(card_id):
            for event in status_events[card_id]:
                if event.get("op") != "update_status":
                    issues.append(f"status change ledger event must use update_status: {event.get('event_id')}")
                if event.get("to_status") == "superseded" and event.get("superseded_by") == card_id:
                    issues.append(f"ledger event self-supersedes card: {event.get('event_id')}")

    for recall_path in (path / "recalls").glob("*.json"):
        try:
            digest = json.loads(recall_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"invalid recall JSON: {recall_path.name}: {exc}")
            continue
        validate_recall_digest_shape(digest, recall_path.name, issues)
        if not isinstance(digest, dict):
            continue
        for address in digest.get("source_addresses", []) or []:
            if isinstance(address, str) and address.startswith("external:"):
                continue
            if isinstance(address, str) and "/card/" in address:
                card_id = address.rstrip("/").split("/")[-1]
                if not list((path / "cards").rglob(f"{card_id}.md")):
                    issues.append(f"recall source address does not resolve: {address}")
            elif isinstance(address, str) and "/ledger/event/" in address:
                event_id = address.rstrip("/").split("/")[-1]
                if event_id not in event_ids:
                    issues.append(f"recall source address does not resolve: {address}")
            else:
                issues.append(f"recall source address must resolve or be external: {address}")

    return issues


def validate_recall_digest_shape(digest: Any, name: str, issues: list[str]) -> None:
    if not isinstance(digest, dict):
        issues.append(f"recall digest must be a JSON object: {name}")
        return

    for key in RECALL_KEYS:
        if key not in digest:
            issues.append(f"recall digest missing key: {name} -> {key}")

    require_type(digest, name, issues, "query_or_task", str)
    require_type(digest, name, issues, "memory_intent", str)
    for key in (
        "anchors_used",
        "cards_read",
        "recalled_points",
        "warnings",
        "do_not_assume",
        "source_addresses",
        "open_questions",
        "lateral_recovery",
    ):
        require_type(digest, name, issues, key, list)

    memory_intent = digest.get("memory_intent")
    if isinstance(memory_intent, str) and memory_intent not in MEMORY_INTENTS:
        issues.append(f"recall digest has invalid memory_intent: {name} -> {memory_intent}")

    active_anchor_fields = digest.get("active_anchor_fields")
    if not isinstance(active_anchor_fields, list):
        issues.append(f"recall digest active_anchor_fields must be a list: {name}")
    else:
        for item in active_anchor_fields:
            if not isinstance(item, str):
                issues.append(f"recall digest active_anchor_fields must contain strings: {name} -> {item}")

    scale_path = digest.get("scale_path")
    if not isinstance(scale_path, list):
        issues.append(f"recall digest scale_path must be a list: {name}")
    else:
        for index, item in enumerate(scale_path):
            if not isinstance(item, dict):
                issues.append(f"recall digest scale_path item must be a mapping: {name} -> {index}")
                continue
            layer = item.get("layer")
            if not is_non_negative_int(layer):
                issues.append(f"recall digest scale_path layer must be a non-negative integer: {name} -> {index}")
            card = item.get("card")
            if not isinstance(card, str) or not card:
                issues.append(f"recall digest scale_path card must be a non-empty string: {name} -> {index}")
            anchor_fields = item.get("anchor_fields")
            if not isinstance(anchor_fields, list):
                issues.append(f"recall digest scale_path anchor_fields must be a list: {name} -> {index}")
            else:
                for anchor_field in anchor_fields:
                    if not isinstance(anchor_field, str):
                        issues.append(
                            f"recall digest scale_path anchor_fields must contain strings: {name} -> {index}"
                        )
            if "note" in item and not isinstance(item["note"], str):
                issues.append(f"recall digest scale_path note must be a string: {name} -> {index}")

    if not isinstance(digest.get("sufficient_scale_reached"), bool):
        issues.append(f"recall digest sufficient_scale_reached must be a boolean: {name}")


def require_type(digest: dict[str, Any], name: str, issues: list[str], key: str, expected_type: type) -> None:
    if key in digest and not isinstance(digest[key], expected_type):
        type_name = "string" if expected_type is str else "list"
        issues.append(f"recall digest {key} must be a {type_name}: {name}")


def architecture_metadata_issues(front: dict[str, Any], card_id: str = "<input>") -> list[str]:
    issues: list[str] = []
    validate_card_architecture_metadata(front, card_id, issues)
    return issues


def validate_card_architecture_metadata(
    front: dict[str, Any],
    card_id: str,
    issues: list[str],
) -> None:
    layer = front.get("layer")
    valid_layer = "layer" in front and is_non_negative_int(layer)
    if "layer" in front and not valid_layer:
        issues.append(f"card layer must be a non-negative integer: {card_id} -> {front['layer']}")

    if "hex" in front:
        hex_meta = front["hex"]
        if not isinstance(hex_meta, dict):
            issues.append(f"card hex must be a mapping: {card_id}")
        else:
            for key in hex_meta:
                if key not in HEX_KEYS:
                    issues.append(f"card hex has invalid key: {card_id} -> {key}")
            for coord in ("q", "r"):
                if coord not in hex_meta:
                    issues.append(f"card hex.{coord} is required when hex is present: {card_id}")
                elif not is_int(hex_meta[coord]):
                    issues.append(f"card hex.{coord} must be an integer: {card_id} -> {hex_meta[coord]}")
            if "rotation" in hex_meta:
                rotation = hex_meta["rotation"]
                if not is_number(rotation):
                    issues.append(f"card hex.rotation must be numeric: {card_id} -> {rotation}")
                elif not valid_layer:
                    issues.append(f"card hex.rotation requires a valid layer: {card_id}")
                elif not nearly_equal(float(rotation), layer_rotation_degrees(int(layer))):
                    issues.append(
                        f"card hex.rotation does not match layer rotation: {card_id} -> {rotation}"
                    )
            if "scale" in hex_meta:
                scale = hex_meta["scale"]
                if not is_number(scale) or float(scale) <= 0:
                    issues.append(f"card hex.scale must be a positive number: {card_id} -> {scale}")
                elif not valid_layer:
                    issues.append(f"card hex.scale requires a valid layer: {card_id}")
                elif not nearly_equal(float(scale), layer_scale(int(layer))):
                    issues.append(f"card hex.scale does not match layer scale: {card_id} -> {scale}")

    if "anchor_fields" in front:
        anchor_fields = front["anchor_fields"]
        if not isinstance(anchor_fields, dict):
            issues.append(f"card anchor_fields must be a mapping: {card_id}")
        else:
            for anchor_id, influence in anchor_fields.items():
                if not isinstance(anchor_id, str) or not anchor_id:
                    issues.append(f"card anchor_fields key must be a non-empty string: {card_id}")
                if not isinstance(influence, dict):
                    issues.append(f"card anchor_fields entry must be a mapping: {card_id} -> {anchor_id}")
                    continue
                if "weight" not in influence:
                    issues.append(f"card anchor_fields weight is required: {card_id} -> {anchor_id}")
                else:
                    weight = influence["weight"]
                    if not is_number(weight) or not 0 <= float(weight) <= 1:
                        issues.append(f"card anchor_fields weight out of range: {card_id} -> {anchor_id}={weight}")
                if "role" in influence and influence["role"] not in ANCHOR_FIELD_ROLES:
                    issues.append(f"card anchor_fields has invalid role: {card_id} -> {anchor_id}={influence['role']}")

    if "scale_links" in front:
        scale_links = front["scale_links"]
        if not isinstance(scale_links, dict):
            issues.append(f"card scale_links must be a mapping: {card_id}")
        else:
            for key, values in scale_links.items():
                if key not in SCALE_LINK_KEYS:
                    issues.append(f"card scale_links has invalid key: {card_id} -> {key}")
                if not isinstance(values, list):
                    issues.append(f"card scale_links value must be a list: {card_id} -> {key}")
                    continue
                for value in values:
                    if not isinstance(value, str) or not value:
                        issues.append(f"card scale_links value must be a card id or address: {card_id} -> {key}")


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_non_negative_int(value: Any) -> bool:
    return is_int(value) and value >= 0


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def nearly_equal(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= FLOAT_TOLERANCE
