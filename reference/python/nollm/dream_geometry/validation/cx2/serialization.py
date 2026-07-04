"""Canonical CX2 serialization helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json


def canonical_json(value: object) -> str:
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def canonical_markdown(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def _normalize(value: object) -> object:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


__all__ = ["canonical_json", "canonical_markdown"]
