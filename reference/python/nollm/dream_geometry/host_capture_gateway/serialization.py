"""HCG1 canonical JSON serialization helpers."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def ok_envelope(operation: str, request_id: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "operation": operation,
        "request_id": request_id,
        "result": result,
    }


def error_envelope(operation: str, request_id: str | None, code: str, message: str = "request rejected") -> dict[str, Any]:
    return {
        "ok": False,
        "operation": operation,
        "request_id": request_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


__all__ = ["canonical_json", "error_envelope", "ok_envelope"]
