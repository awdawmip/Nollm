"""HAG1 canonical JSON serialization helpers."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any


def canonical_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def fingerprint(payload: object) -> str:
    return "sha256:" + sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def ok_envelope(request_id: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "action": "admit",
        "request_id": request_id,
        "result": result,
        "warnings": [],
    }


def error_envelope(request_id: str | None, code: str, message: str = "request was rejected") -> dict[str, Any]:
    return {
        "ok": False,
        "action": "admit",
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


__all__ = ["canonical_json", "error_envelope", "fingerprint", "ok_envelope"]
