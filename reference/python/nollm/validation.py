from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .filesystem import read_card, read_ledger, read_yaml_file
from .models import CARD_TYPES, SOURCE_KINDS, STATUSES, TRUST_VALUES


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

    for card_path in (path / "cards").rglob("*.md"):
        front, _body, _ = read_card(path, card_path.stem)
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
                and event.get("actor_type") == "human"
                for event in events
            )
            if not has_human_approval:
                issues.append(f"confirmed card lacks human approval ledger evidence: {card_id}")
            if trust not in {"human-approved", "source-backed"}:
                issues.append(f"confirmed card has weak trust: {card_id} -> {trust}")
            if source == "llm_inference":
                issues.append(f"confirmed card cannot use llm_inference source: {card_id}")
        if status_events.get(card_id):
            for event in status_events[card_id]:
                if event.get("op") != "update_status":
                    issues.append(f"status change ledger event must use update_status: {event.get('event_id')}")

    for recall_path in (path / "recalls").glob("*.json"):
        try:
            digest = json.loads(recall_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"invalid recall JSON: {recall_path.name}: {exc}")
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

