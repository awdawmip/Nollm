from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .ids import today_iso
from .models import CARD_DIRS


def notebook_name(path: Path) -> str:
    anchors = read_yaml_file(path / "anchors.yaml")
    return str(anchors.get("notebook") or path.name)


def card_address(notebook: str, card_id: str) -> str:
    return f"nollm://{notebook}/card/{card_id}"


def ledger_address(notebook: str, event_id: str) -> str:
    return f"nollm://{notebook}/ledger/event/{event_id}"


def recall_address(notebook: str, recall_id: str) -> str:
    return f"nollm://{notebook}/recall/{recall_id}"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def init_notebook(path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for directory in CARD_DIRS.values():
        (path / "cards" / directory).mkdir(parents=True, exist_ok=True)
    (path / "ledger").mkdir(exist_ok=True)
    (path / "recalls").mkdir(exist_ok=True)

    anchors = {
        "notebook": name,
        "anchors": [
            {
                "id": f"project:{name}",
                "label": f"{name} project",
                "definition": "Project-level orientation anchor.",
                "scope": "Project-level memory.",
                "status": "confirmed",
                "aliases": [name],
                "neighbors": [],
                "max_aliases": 8,
                "max_neighbors": 12,
                "max_active_cards": 50,
                "created": today_iso(),
            }
        ],
    }
    aliases = {"notebook": name, "aliases": {name: {"anchor": f"project:{name}"}}}
    write_yaml_file(path / "anchors.yaml", anchors)
    write_yaml_file(path / "aliases.yaml", aliases)
    (path / "ledger" / "events.jsonl").touch(exist_ok=True)


def append_ledger(path: Path, event: dict[str, Any]) -> None:
    ledger = path / "ledger" / "events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def read_ledger(path: Path) -> list[dict[str, Any]]:
    ledger = path / "ledger" / "events.jsonl"
    if not ledger.exists():
        return []
    events = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def find_card_path(path: Path, card_id_or_address: str) -> Path:
    card_id = card_id_or_address.rstrip("/").split("/")[-1]
    matches = list((path / "cards").rglob(f"{card_id}.md"))
    if not matches:
        raise FileNotFoundError(f"card not found: {card_id_or_address}")
    if len(matches) > 1:
        raise ValueError(f"multiple cards found for: {card_id}")
    return matches[0]


def read_card(path: Path, card_id_or_address: str) -> tuple[dict[str, Any], str, Path]:
    card_path = find_card_path(path, card_id_or_address)
    text = card_path.read_text(encoding="utf-8")
    front, body = parse_front_matter(text)
    return front, body, card_path


def write_card_file(card_path: Path, front: dict[str, Any], body: str) -> None:
    card_path.parent.mkdir(parents=True, exist_ok=True)
    card_path.write_text(render_card(front, body), encoding="utf-8")


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    return parse_yaml(parts[1]), parts[2].lstrip("\n")


def render_card(front: dict[str, Any], body: str) -> str:
    return f"---\n{render_yaml(front)}---\n\n{body.strip()}\n"


def read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return parse_yaml(path.read_text(encoding="utf-8"))


def write_yaml_file(path: Path, data: dict[str, Any]) -> None:
    path.write_text(render_yaml(data), encoding="utf-8")


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "null":
        return None
    if value == "[]":
        return []
    if value.isdigit():
        return int(value)
    return value.strip("\"'")


def parse_yaml(text: str) -> dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    data: dict[str, Any] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("  "):
            index += 1
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        raw = raw.strip()
        if raw:
            data[key] = parse_scalar(raw)
            index += 1
            continue
        block, index = parse_block(lines, index + 1, 2)
        data[key] = block
    return data


def parse_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    prefix = " " * indent
    if not lines[index].startswith(prefix + "- "):
        result: dict[str, Any] = {}
        while index < len(lines) and lines[index].startswith(prefix):
            line = lines[index]
            key, _, raw = line[indent:].partition(":")
            key = key.strip()
            raw = raw.strip()
            if raw:
                result[key] = parse_scalar(raw)
                index += 1
            else:
                child, index = parse_block(lines, index + 1, indent + 2)
                result[key] = child
        return result, index

    result_list: list[Any] = []
    while index < len(lines) and lines[index].startswith(prefix + "- "):
        item = lines[index][indent + 2 :]
        if ": " not in item and not item.endswith(":"):
            result_list.append(parse_scalar(item))
            index += 1
            continue
        item_dict: dict[str, Any] = {}
        key, _, raw = item.partition(":")
        item_dict[key.strip()] = parse_scalar(raw)
        index += 1
        while index < len(lines) and lines[index].startswith(prefix + "  "):
            child_line = lines[index][indent + 2 :]
            child_key, _, child_raw = child_line.partition(":")
            child_key = child_key.strip()
            child_raw = child_raw.strip()
            if child_raw:
                item_dict[child_key] = parse_scalar(child_raw)
                index += 1
            else:
                child, index = parse_block(lines, index + 1, indent + 4)
                item_dict[child_key] = child
        result_list.append(item_dict)
    return result_list, index


def render_yaml(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        render_yaml_value(lines, key, value, 0)
    return "\n".join(lines) + "\n"


def render_yaml_value(lines: list[str], key: str, value: Any, indent: int) -> None:
    prefix = " " * indent
    if isinstance(value, list):
        lines.append(f"{prefix}{key}:")
        for item in value:
            if isinstance(item, dict):
                first = True
                for child_key, child_value in item.items():
                    if first:
                        if isinstance(child_value, list):
                            lines.append(f"{prefix}  - {child_key}:")
                            render_list(lines, child_value, indent + 4)
                        else:
                            lines.append(f"{prefix}  - {child_key}: {format_scalar(child_value)}")
                        first = False
                    else:
                        render_yaml_value(lines, child_key, child_value, indent + 4)
            else:
                lines.append(f"{prefix}  - {format_scalar(item)}")
    elif isinstance(value, dict):
        lines.append(f"{prefix}{key}:")
        for child_key, child_value in value.items():
            render_yaml_value(lines, child_key, child_value, indent + 2)
    else:
        lines.append(f"{prefix}{key}: {format_scalar(value)}")


def render_list(lines: list[str], value: list[Any], indent: int) -> None:
    prefix = " " * indent
    if not value:
        return
    for item in value:
        lines.append(f"{prefix}- {format_scalar(item)}")


def format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value == []:
        return "[]"
    return str(value)
