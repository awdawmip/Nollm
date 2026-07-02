"""CI1 Capture Ingress stable error codes."""

from __future__ import annotations


CI1_INVALID_REQUEST = "CI1_INVALID_REQUEST"
CI1_INVALID_POLICY = "CI1_INVALID_POLICY"
CI1_REPLAYABLE_FORBIDDEN = "CI1_REPLAYABLE_FORBIDDEN"
CI1_VISIBILITY_SCOPE_FORBIDDEN = "CI1_VISIBILITY_SCOPE_FORBIDDEN"
CI1_CANDIDATE_FORBIDDEN = "CI1_CANDIDATE_FORBIDDEN"
CI1_CAPTURE_ID_CONFLICT = "CI1_CAPTURE_ID_CONFLICT"
CI1_COMMIT_FAILED = "CI1_COMMIT_FAILED"
CI1_NOT_FOUND = "CI1_NOT_FOUND"


class CaptureError(ValueError):
    def __init__(self, code: str, message_class: str, *, stage: str = "capture"):
        super().__init__(code)
        self.code = code
        self.message_class = message_class
        self.stage = stage


__all__ = [
    "CI1_CANDIDATE_FORBIDDEN",
    "CI1_CAPTURE_ID_CONFLICT",
    "CI1_COMMIT_FAILED",
    "CI1_INVALID_POLICY",
    "CI1_INVALID_REQUEST",
    "CI1_NOT_FOUND",
    "CI1_REPLAYABLE_FORBIDDEN",
    "CI1_VISIBILITY_SCOPE_FORBIDDEN",
    "CaptureError",
]
