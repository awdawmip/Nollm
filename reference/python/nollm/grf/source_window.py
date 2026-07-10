"""Explicit source window records for GRF evidence capture."""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_WINDOW_KINDS = frozenset({"session", "file", "tool_output", "task", "import_batch", "validation_fixture"})


@dataclass(frozen=True)
class SourceWindowRecord:
    window_id: str
    kind: str
    refs: tuple[str, ...]
    opened_at: str
    closed_at: str | None = None
    policy_ref: str | None = None
    source_id: str | None = None
    source_path: str | None = None
    source_type: str | None = None
    encoding: str | None = None
    newline_style: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    ordinal: int | None = None
    exact_content: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.window_id, "window_id")
        if self.kind not in SOURCE_WINDOW_KINDS:
            raise ValueError("unknown source window kind")
        _require_refs(self.refs, "refs")
        _require_text(self.opened_at, "opened_at")
        if self.closed_at is not None:
            _require_text(self.closed_at, "closed_at")
        if self.policy_ref is not None:
            _require_text(self.policy_ref, "policy_ref")
        optional_text = (self.source_id, self.source_path, self.source_type, self.encoding, self.newline_style, self.exact_content)
        if any(value is not None and (not isinstance(value, str) or value == "") for value in optional_text):
            raise ValueError("source metadata text must be non-empty when provided")
        offsets = (self.start_offset, self.end_offset, self.ordinal)
        if any(value is not None and (type(value) is not int or value < 0) for value in offsets):
            raise ValueError("source offsets must be non-negative integers")
        if self.start_offset is not None and self.end_offset is not None and self.end_offset <= self.start_offset:
            raise ValueError("source window end_offset must exceed start_offset")

    def to_mapping(self) -> dict[str, object]:
        return {
            "window_id": self.window_id,
            "kind": self.kind,
            "refs": tuple(sorted(self.refs)),
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "policy_ref": self.policy_ref,
            "source_id": self.source_id,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "encoding": self.encoding,
            "newline_style": self.newline_style,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "ordinal": self.ordinal,
            "exact_content": self.exact_content,
        }


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_refs(values: tuple[str, ...], label: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, str) or value == "" for value in values):
        raise ValueError(f"{label} must be a tuple of non-empty text")
