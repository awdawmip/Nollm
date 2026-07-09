"""Raw GRF evidence shard records."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


ORIGIN_KINDS = frozenset(
    {
        "user_utterance",
        "assistant_output",
        "tool_result",
        "imported_text",
        "internal_reflection",
        "validation_fixture",
    }
)


@dataclass(frozen=True)
class EvidenceShardRecord:
    shard_id: str
    content: str
    created_at: str
    origin_kind: str
    source_window_refs: tuple[str, ...]
    trust_state: str
    usage_state: str
    content_sha256: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.shard_id, "shard_id")
        _require_text(self.content, "content")
        _require_text(self.created_at, "created_at")
        if self.origin_kind not in ORIGIN_KINDS:
            raise ValueError("unknown origin_kind")
        _require_refs(self.source_window_refs, "source_window_refs")
        _require_text(self.trust_state, "trust_state")
        _require_text(self.usage_state, "usage_state")
        expected = sha256(self.content.encode("utf-8")).hexdigest()
        if self.content_sha256 is None:
            object.__setattr__(self, "content_sha256", expected)
        elif self.content_sha256 != expected:
            raise ValueError("content_sha256 must match content")

    def to_mapping(self) -> dict[str, object]:
        return {
            "shard_id": self.shard_id,
            "content": self.content,
            "created_at": self.created_at,
            "origin_kind": self.origin_kind,
            "source_window_refs": tuple(sorted(self.source_window_refs)),
            "trust_state": self.trust_state,
            "usage_state": self.usage_state,
            "content_sha256": self.content_sha256,
            "no_truth_score": True,
            "no_importance_score": True,
            "no_semantic_edge": True,
        }


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_refs(values: tuple[str, ...], label: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, str) or value == "" for value in values):
        raise ValueError(f"{label} must be a tuple of non-empty text")
