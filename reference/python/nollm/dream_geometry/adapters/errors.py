"""Stable DI1 Integration Shell public error codes."""

from __future__ import annotations

from enum import Enum


class DI1ErrorCode(Enum):
    invalid_invocation = "DI1_INVALID_INVOCATION"
    operation_unsupported = "DI1_OPERATION_UNSUPPORTED"
    invalid_read_context = "DI1_INVALID_READ_CONTEXT"
    recall_rejected = "DI1_RECALL_REJECTED"
    evidence_unavailable = "DI1_EVIDENCE_UNAVAILABLE"
    context_record_unavailable = "DI1_CONTEXT_RECORD_UNAVAILABLE"
    internal_error = "DI1_INTERNAL_ERROR"


ERROR_MESSAGES = {
    DI1ErrorCode.invalid_invocation: "Invocation must be a supported typed DI1 request.",
    DI1ErrorCode.operation_unsupported: "Operation is not supported by the DI1 integration shell.",
    DI1ErrorCode.invalid_read_context: "Recall requires a host-provided typed read context.",
    DI1ErrorCode.recall_rejected: "Recall was rejected by the sealed recall resolver.",
    DI1ErrorCode.evidence_unavailable: "Selected DreamShard evidence is unavailable.",
    DI1ErrorCode.context_record_unavailable: "Selected context record is unavailable or inconsistent.",
    DI1ErrorCode.internal_error: "Integration shell failed without exposing internal details.",
}


__all__ = ["DI1ErrorCode", "ERROR_MESSAGES"]
