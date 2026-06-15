from __future__ import annotations

from dataclasses import dataclass, field
from string import punctuation, whitespace
from typing import Mapping

ALLOWED_SHARD_STATUSES = frozenset({"draft", "candidate", "rejected", "archived"})
ALLOWED_SHARD_SOURCES = frozenset(
    {
        "user_utterance",
        "assistant_utterance",
        "llm_work_residue",
        "project_note",
        "imported_text",
    }
)


@dataclass(frozen=True)
class DreamShard:
    shard_id: str
    text: str
    source: str = "llm_work_residue"
    status: str = "candidate"
    anchors_hint: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = normalize_shard_text(self.text)
        object.__setattr__(self, "text", normalized)
        object.__setattr__(self, "anchors_hint", tuple(self.anchors_hint))
        object.__setattr__(self, "metadata", dict(self.metadata))
        validate_dream_shard(self)


def normalize_shard_text(text: str) -> str:
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    return " ".join(text.strip().split())


def is_independently_meaningful(text: str) -> bool:
    normalized = normalize_shard_text(text)
    if len(normalized) < 8:
        return False
    return any(char not in punctuation and char not in whitespace for char in normalized)


def validate_dream_shard(shard: DreamShard) -> None:
    _require_non_empty_string(shard.shard_id, "shard_id")
    if not is_independently_meaningful(shard.text):
        raise ValueError("text must be an independently meaningful utterance")
    if shard.status not in ALLOWED_SHARD_STATUSES:
        raise ValueError(f"unsupported dream shard status: {shard.status}")
    if shard.source not in ALLOWED_SHARD_SOURCES:
        raise ValueError(f"unsupported dream shard source: {shard.source}")
    if not isinstance(shard.anchors_hint, tuple):
        raise ValueError("anchors_hint must be a tuple")
    for anchor in shard.anchors_hint:
        _require_non_empty_string(anchor, "anchor hint")
    if not isinstance(shard.metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    for key, value in shard.metadata.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError("metadata must contain only string keys and string values")


def shard_to_record(shard: DreamShard) -> dict[str, object]:
    validate_dream_shard(shard)
    return {
        "shard_id": shard.shard_id,
        "text": shard.text,
        "source": shard.source,
        "status": shard.status,
        "anchors_hint": list(shard.anchors_hint),
        "metadata": dict(shard.metadata),
    }


def shard_from_record(record: Mapping[str, object]) -> DreamShard:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    anchors = record.get("anchors_hint", ())
    metadata = record.get("metadata", {})
    if not isinstance(anchors, (list, tuple)):
        raise ValueError("anchors_hint must be a list or tuple")
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping")
    return DreamShard(
        shard_id=_record_string(record, "shard_id"),
        text=_record_string(record, "text"),
        source=_record_string(record, "source", "llm_work_residue"),
        status=_record_string(record, "status", "candidate"),
        anchors_hint=tuple(anchors),
        metadata=metadata,
    )


def _record_string(record: Mapping[str, object], key: str, default: str | None = None) -> str:
    value = record.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_non_empty_string(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


__all__ = [
    "ALLOWED_SHARD_STATUSES",
    "ALLOWED_SHARD_SOURCES",
    "DreamShard",
    "normalize_shard_text",
    "is_independently_meaningful",
    "validate_dream_shard",
    "shard_to_record",
    "shard_from_record",
]
