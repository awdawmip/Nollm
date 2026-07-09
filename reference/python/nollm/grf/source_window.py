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

    def to_mapping(self) -> dict[str, object]:
        return {
            "window_id": self.window_id,
            "kind": self.kind,
            "refs": tuple(sorted(self.refs)),
            "opened_at": self.opened_at,
            "closed_at": self.closed_at,
            "policy_ref": self.policy_ref,
        }


def _require_text(value: str, label: str) -> None:
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label} must be non-empty text")


def _require_refs(values: tuple[str, ...], label: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, str) or value == "" for value in values):
        raise ValueError(f"{label} must be a tuple of non-empty text")
