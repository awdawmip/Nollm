"""Canonical JSON helpers for file-first GRF records."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def canonical_dumps(obj: Any) -> bytes:
    _reject_float(obj)
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_loads(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


def sha256_canonical(obj: Any) -> str:
    return sha256(canonical_dumps(obj)).hexdigest()


def _reject_float(obj: Any) -> None:
    if isinstance(obj, float):
        raise TypeError("canonical GRF JSON rejects float values")
    if isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError("canonical GRF JSON requires text keys")
            _reject_float(value)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            _reject_float(value)
