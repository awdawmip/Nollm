from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from .statement import MemoryStatement


DREAM_OUTCOMES = frozenset({"emit", "defer"})
DREAM_ACTORS = frozenset({"llm", "human", "fixture"})
DREAM_SCHEMA_VERSION = "nollm_access_dream_formation_v1"


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    content_utf8: str

    def __post_init__(self) -> None:
        if type(self.role) is not str or not self.role or type(self.content_utf8) is not str or not self.content_utf8:
            raise TypeError("role and content_utf8 must be non-empty strings")

    def to_mapping(self) -> dict[str, object]:
        return {"role": self.role, "content_utf8": self.content_utf8}

    @classmethod
    def from_mapping(cls, value: object) -> "ConversationTurn":
        if type(value) is not dict or set(value) != {"role", "content_utf8"}:
            raise ValueError("ConversationTurn mapping must have exact fields")
        return cls(value["role"], value["content_utf8"])


@dataclass(frozen=True)
class ConversationMaterial:
    material_id: str
    turns: tuple[ConversationTurn, ...]

    def __post_init__(self) -> None:
        if type(self.material_id) is not str or not self.material_id:
            raise TypeError("material_id must be a non-empty string")
        if type(self.turns) is not tuple or not self.turns or any(type(item) is not ConversationTurn for item in self.turns):
            raise TypeError("turns must be a non-empty tuple of ConversationTurn")

    def to_mapping(self) -> dict[str, object]:
        return {"material_id": self.material_id, "turns": [item.to_mapping() for item in self.turns]}

    @classmethod
    def from_mapping(cls, value: object) -> "ConversationMaterial":
        if type(value) is not dict or set(value) != {"material_id", "turns"} or type(value["turns"]) is not list:
            raise ValueError("ConversationMaterial mapping must have exact fields")
        return cls(value["material_id"], tuple(ConversationTurn.from_mapping(item) for item in value["turns"]))


@dataclass(frozen=True)
class DreamFormationRequest:
    request_id: str
    material: ConversationMaterial
    max_statements: int = 8
    max_statement_chars: int = 4096
    max_total_chars: int = 8192
    schema_version: str = DREAM_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not self.request_id or type(self.material) is not ConversationMaterial:
            raise TypeError("request_id and material are required")
        for name, value in (("max_statements", self.max_statements), ("max_statement_chars", self.max_statement_chars), ("max_total_chars", self.max_total_chars)):
            if type(value) is not int or value < 1:
                raise TypeError(f"{name} must be a positive integer")
        if self.schema_version != DREAM_SCHEMA_VERSION:
            raise ValueError("unsupported Dream Formation schema")


@dataclass(frozen=True)
class DreamMemoryDraft:
    draft_id: str
    content_utf8: str
    stability_hint: str | None = None
    uncertainty_hint: str | None = None
    scope_hint: str | None = None

    def __post_init__(self) -> None:
        if type(self.draft_id) is not str or not self.draft_id or type(self.content_utf8) is not str or not self.content_utf8:
            raise TypeError("draft_id and content_utf8 must be non-empty strings")
        for value in (self.stability_hint, self.uncertainty_hint, self.scope_hint):
            if value is not None and (type(value) is not str or not value):
                raise TypeError("draft hints must be null or non-empty strings")

    def to_mapping(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id, "content_utf8": self.content_utf8,
            "scope_hint": self.scope_hint, "stability_hint": self.stability_hint,
            "uncertainty_hint": self.uncertainty_hint,
        }

    @classmethod
    def from_mapping(cls, value: object) -> "DreamMemoryDraft":
        keys = {"draft_id", "content_utf8", "scope_hint", "stability_hint", "uncertainty_hint"}
        if type(value) is not dict or set(value) != keys:
            raise ValueError("DreamMemoryDraft mapping must have exact fields")
        return cls(value["draft_id"], value["content_utf8"], value["stability_hint"], value["uncertainty_hint"], value["scope_hint"])


@dataclass(frozen=True)
class DreamFormationResult:
    result_id: str
    request_id: str
    outcome: str
    drafts: tuple[DreamMemoryDraft, ...]
    defer_reason: str | None
    decided_by: str
    schema_version: str = DREAM_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.result_id) is not str or not self.result_id or type(self.request_id) is not str or not self.request_id:
            raise TypeError("result_id and request_id must be non-empty strings")
        if self.outcome not in DREAM_OUTCOMES or self.decided_by not in DREAM_ACTORS or self.schema_version != DREAM_SCHEMA_VERSION:
            raise ValueError("invalid Dream Formation result enum or schema")
        if type(self.drafts) is not tuple or any(type(item) is not DreamMemoryDraft for item in self.drafts):
            raise TypeError("drafts must be a tuple of DreamMemoryDraft")
        ids = tuple(item.draft_id for item in self.drafts)
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise ValueError("drafts must be canonical and unique by draft_id")
        if self.outcome == "emit" and (not self.drafts or self.defer_reason is not None):
            raise ValueError("emit requires drafts and no defer_reason")
        if self.outcome == "defer" and (self.drafts or type(self.defer_reason) is not str or not self.defer_reason):
            raise ValueError("defer requires no drafts and a reason")


def form_dream_statements(request: DreamFormationRequest, result: DreamFormationResult) -> tuple[MemoryStatement, ...]:
    if type(request) is not DreamFormationRequest or type(result) is not DreamFormationResult:
        raise TypeError("exact Dream Formation request and result types are required")
    if result.request_id != request.request_id:
        raise ValueError("Dream Formation request identity mismatch")
    if result.outcome == "defer":
        return ()
    if len(result.drafts) > request.max_statements:
        raise ValueError("Dream Formation statement count exceeds budget")
    if any(len(item.content_utf8) > request.max_statement_chars for item in result.drafts):
        raise ValueError("Dream Formation statement exceeds character budget")
    if sum(len(item.content_utf8) for item in result.drafts) > request.max_total_chars:
        raise ValueError("Dream Formation total characters exceed budget")
    return tuple(MemoryStatement(_statement_id(result.result_id, item), item.content_utf8) for item in result.drafts)


def _statement_id(result_id: str, draft: DreamMemoryDraft) -> str:
    payload = f"{DREAM_SCHEMA_VERSION}\0{result_id}\0{draft.draft_id}\0{draft.content_utf8}".encode("utf-8")
    return f"dream:{sha256(payload).hexdigest()}"
