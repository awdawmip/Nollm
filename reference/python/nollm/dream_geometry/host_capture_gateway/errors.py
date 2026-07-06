"""HCG1 stable error values."""

from __future__ import annotations


class HCGError(Exception):
    """Gateway failure with a stable public reason code."""

    def __init__(self, code: str, message: str = "request rejected") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


HCG_INVALID_JSON = "HCG_INVALID_JSON"
HCG_INVALID_REQUEST = "HCG_INVALID_REQUEST"
HCG_UNSUPPORTED_CAPTURE_MODE = "HCG_UNSUPPORTED_CAPTURE_MODE"
HCG_UNSUPPORTED_READ_SELECTOR = "HCG_UNSUPPORTED_READ_SELECTOR"
HCG_WORKSPACE_NOT_OWNED = "HCG_WORKSPACE_NOT_OWNED"
HCG_CAPTURE_REJECTED = "HCG_CAPTURE_REJECTED"
HCG_REOPEN_MISMATCH = "HCG_REOPEN_MISMATCH"
HCG_READ_REJECTED = "HCG_READ_REJECTED"
HCG_INTERNAL_ERROR = "HCG_INTERNAL_ERROR"


__all__ = [
    "HCGError",
    "HCG_CAPTURE_REJECTED",
    "HCG_INTERNAL_ERROR",
    "HCG_INVALID_JSON",
    "HCG_INVALID_REQUEST",
    "HCG_READ_REJECTED",
    "HCG_REOPEN_MISMATCH",
    "HCG_UNSUPPORTED_CAPTURE_MODE",
    "HCG_UNSUPPORTED_READ_SELECTOR",
    "HCG_WORKSPACE_NOT_OWNED",
]
