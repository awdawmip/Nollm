"""GRF1-E local mini validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class ValidationItem:
    item_id: str
    text: str
    group: str
    source_window: str


def load_jsonl(path: Path) -> tuple[ValidationItem, ...]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        items.append(ValidationItem(payload["id"], payload["text"], payload["group"], payload["source_window"]))
    return tuple(items)


def token_set(text: str) -> frozenset[str]:
    return frozenset(part.lower().strip(".,:/;-_") for part in text.split() if part.strip(".,:/;-_"))


def lexical_pairs(items: tuple[ValidationItem, ...]) -> set[tuple[str, str]]:
    pairs = set()
    for left in items:
        for right in items:
            if left.item_id >= right.item_id:
                continue
            if token_set(left.text) & token_set(right.text):
                pairs.add((left.item_id, right.item_id))
    return pairs


def vector_like_pairs(items: tuple[ValidationItem, ...]) -> set[tuple[str, str]]:
    pairs = set()
    for left in items:
        for right in items:
            if left.item_id >= right.item_id:
                continue
            common = token_set(left.text) & token_set(right.text)
            if len(common) >= 2:
                pairs.add((left.item_id, right.item_id))
    return pairs


def explicit_graph_pairs(items: tuple[ValidationItem, ...]) -> set[tuple[str, str]]:
    pairs = set()
    by_group: dict[str, list[str]] = {}
    for item in items:
        by_group.setdefault(item.group, []).append(item.item_id)
    for ids in by_group.values():
        ordered = sorted(ids)
        for idx, left in enumerate(ordered):
            for right in ordered[idx + 1 :]:
                pairs.add((left, right))
    return pairs


def score_pairs(predicted: set[tuple[str, str]], expected: set[tuple[str, str]], false_pairs: set[tuple[str, str]]) -> dict[str, object]:
    correct = len(predicted & expected)
    false_hits = len(predicted & false_pairs)
    missed = len(expected - predicted)
    return {
        "recall_correctness": _ratio(correct, len(expected)),
        "source_faithfulness": _ratio(correct, max(1, len(predicted))),
        "false_stitch_rate": _ratio(false_hits, max(1, len(predicted))),
        "missed_stitch_rate": _ratio(missed, len(expected)),
    }


def relation_storage_size(pairs: set[tuple[str, str]]) -> int:
    return len(pairs)


def _ratio(numer: int, denom: int) -> str:
    if denom == 0:
        return "0/0"
    return f"{numer}/{denom}"
