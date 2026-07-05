"""Canonical HX1 serialization."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def canonical_json(value: object) -> str:
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"


def stable_fingerprint(value: object) -> str:
    return "sha256:" + sha256(canonical_json(value).encode("utf-8")).hexdigest()


def receipt_to_mapping(receipt: object) -> dict[str, Any]:
    return json.loads(canonical_json(receipt))


def _normalize(value: object) -> object:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return "<path>"
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        return format(value, ".17g")
    return str(value)


__all__ = ["canonical_json", "receipt_to_mapping", "stable_fingerprint"]
