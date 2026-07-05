"""HX1 structured execution errors."""

from __future__ import annotations


class HX1ExecutionError(ValueError):
    """Stable host execution failure."""

    def __init__(self, reason_code: str, message: str, *, failed_stage: str | None = None) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.failed_stage = failed_stage


def error_to_mapping(error: HX1ExecutionError) -> dict[str, object]:
    return {
        "ok": False,
        "kind": "nollm_hx1_host_execution_error",
        "reason_code": error.reason_code,
        "failed_stage": error.failed_stage,
        "message": _sanitize(str(error)),
    }


def stable_message(exc: Exception) -> str:
    reason = getattr(exc, "reason_code", None) or getattr(exc, "code", None)
    if reason:
        return f"lower layer rejected input: {reason}"
    return "lower layer rejected input"


def _sanitize(message: str) -> str:
    forbidden = ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\")
    if any(token in message for token in forbidden):
        return "HX1 structured failure"
    return message


__all__ = ["HX1ExecutionError", "error_to_mapping", "stable_message"]
