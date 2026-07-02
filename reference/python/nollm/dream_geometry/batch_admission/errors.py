"""BA1 Batch Admission Coordinator errors."""

from __future__ import annotations

from dataclasses import dataclass


BA1_INVALID_REQUEST = "BA1_INVALID_REQUEST"
BA1_WINDOW_NOT_READY = "BA1_WINDOW_NOT_READY"
BA1_DUPLICATE_MEMBER = "BA1_DUPLICATE_MEMBER"
BA1_DUPLICATE_CANDIDATE = "BA1_DUPLICATE_CANDIDATE"
BA1_DUPLICATE_SHARD = "BA1_DUPLICATE_SHARD"
BA1_DUPLICATE_ADMISSION = "BA1_DUPLICATE_ADMISSION"
BA1_DECISION_NOT_PROMOTE = "BA1_DECISION_NOT_PROMOTE"
BA1_DECISION_NEXT_ACTION_INVALID = "BA1_DECISION_NEXT_ACTION_INVALID"
BA1_DECISION_MEMBER_MISMATCH = "BA1_DECISION_MEMBER_MISMATCH"
BA1_CANDIDATE_UNAVAILABLE = "BA1_CANDIDATE_UNAVAILABLE"
BA1_CANDIDATE_NOT_ELIGIBLE = "BA1_CANDIDATE_NOT_ELIGIBLE"
BA1_EVIDENCE_UNAVAILABLE = "BA1_EVIDENCE_UNAVAILABLE"
BA1_REQUEST_SHARD_MISMATCH = "BA1_REQUEST_SHARD_MISMATCH"
BA1_WINDOW_MEMBER_SET_MISMATCH = "BA1_WINDOW_MEMBER_SET_MISMATCH"
BA1_GEOMETRY_PROFILE_MISMATCH = "BA1_GEOMETRY_PROFILE_MISMATCH"
BA1_MEMBER_PREFLIGHT_REJECTED = "BA1_MEMBER_PREFLIGHT_REJECTED"


@dataclass(frozen=True)
class BA1Rejection(ValueError):
    reason_codes: tuple[str, ...]
    detail: str
    stage: str = "preflight"

    def __str__(self) -> str:
        return f"{self.stage}:{','.join(self.reason_codes)}: {self.detail}"


@dataclass(frozen=True)
class BA1CommitInterrupted(RuntimeError):
    window_id: str
    completed_member_receipts: tuple[object, ...]
    failed_member_id: str
    cause: Exception

    def __str__(self) -> str:
        return f"commit:{self.window_id}:{self.failed_member_id}: {self.cause}"


def reject(code: str, detail: str, *, stage: str = "preflight") -> None:
    raise BA1Rejection((code,), detail, stage)


__all__ = [name for name in globals() if name.startswith("BA1_")] + ["BA1CommitInterrupted", "BA1Rejection", "reject"]
