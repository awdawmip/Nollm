"""HAG1 stable public errors."""

from __future__ import annotations


class HAGError(Exception):
    """Gateway failure with a stable public reason code."""

    def __init__(self, code: str, message: str = "request was rejected") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


HAG_INVALID_REQUEST = "HAG_INVALID_REQUEST"
HAG_WORKSPACE_NOT_OWNED = "HAG_WORKSPACE_NOT_OWNED"
HAG_ADMISSION_REJECTED = "HAG_ADMISSION_REJECTED"
HAG_ADMISSION_INTERRUPTED = "HAG_ADMISSION_INTERRUPTED"
HAG_REOPEN_MISMATCH = "HAG_REOPEN_MISMATCH"
HAG_INTERNAL_ERROR = "HAG_INTERNAL_ERROR"


__all__ = [
    "HAGError",
    "HAG_ADMISSION_INTERRUPTED",
    "HAG_ADMISSION_REJECTED",
    "HAG_INTERNAL_ERROR",
    "HAG_INVALID_REQUEST",
    "HAG_REOPEN_MISMATCH",
    "HAG_WORKSPACE_NOT_OWNED",
]
