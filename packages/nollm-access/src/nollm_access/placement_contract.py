from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from nollm_core import AtomHandle, BridgeSpec, GeometryAddress

from .write_policy import ACTIVE_SEMANTIC_WRITE_POLICY


ACTIONS = frozenset({"reuse", "new", "move", "revision_current", "revision_keep_history", "stitch", "unstitch", "defer", "forget"})
DECIDED_BY = frozenset({"host", "llm", "human", "fixture"})
PLACEMENT_ACTION_SEMANTICS_VERSION = "nollm_access_semantic_placement_actions_v1"
REVISION_CONFIRMATION_SCHEMA_VERSION = "nollm_openclaw_revision_confirmation_v1"
REVISION_CONFIRMATION_OUTCOMES = frozenset({"confirm_revision", "reject_revision", "defer"})
REVISION_CONFIRMATION_RELATIONS = frozenset({
    "same_subject_same_slot_supersedes",
    "different_subject_or_non_superseding",
    "uncertain",
})
PLACEMENT_ACTION_SEMANTICS = (
    ("reuse", "The new Statement is materially the same current fact; reuse its exact current Handle without changing the current fact."),
    ("revision_current", "Destructive: only the same subject or referent, the same proposition slot, and a new value that explicitly supersedes the current value. The decision remains provisional until bounded real-LLM confirmation."),
    ("new_local", "Use for a distinct fact, a different subject with an analogous field, or an additive fact about the same subject when a supplied locality is suitable."),
    ("expand_surface", "Use for a distinct or additive fact when none of the supplied local candidates is suitable."),
    ("defer", "Use when subject identity, proposition identity, supersession, or placement remains uncertain."),
)


def placement_action_semantics_prompt() -> str:
    return "\n".join(f"{action}: {meaning}" for action, meaning in PLACEMENT_ACTION_SEMANTICS)


@dataclass(frozen=True)
class ProvisionalRevisionDecision:
    provisional_id: str
    statement_id: str
    current_statement_id: str
    candidate_id: str
    existing_handle: AtomHandle
    proposed_content_utf8: str
    current_content_utf8: str

    def __post_init__(self) -> None:
        strings = (
            self.provisional_id, self.statement_id, self.current_statement_id,
            self.candidate_id, self.proposed_content_utf8, self.current_content_utf8,
        )
        if any(type(value) is not str or not value for value in strings):
            raise TypeError("provisional revision strings must be non-empty")
        if type(self.existing_handle) is not AtomHandle:
            raise TypeError("existing_handle must be an exact AtomHandle")

    @classmethod
    def create(
        cls,
        statement_id: str,
        current_statement_id: str,
        candidate_id: str,
        existing_handle: AtomHandle,
        proposed_content_utf8: str,
        current_content_utf8: str,
    ) -> "ProvisionalRevisionDecision":
        identity = {
            "candidate_id": candidate_id,
            "current_content_utf8": current_content_utf8,
            "current_statement_id": current_statement_id,
            "existing_handle": existing_handle.to_mapping(),
            "proposed_content_utf8": proposed_content_utf8,
            "statement_id": statement_id,
        }
        wire = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return cls(
            f"revision:{sha256(wire).hexdigest()}", statement_id,
            current_statement_id, candidate_id, existing_handle,
            proposed_content_utf8, current_content_utf8,
        )

    @classmethod
    def from_mapping(cls, value: object) -> "ProvisionalRevisionDecision":
        expected = {
            "schema_version", "provisional_id", "statement_id", "current_statement_id",
            "candidate_id", "existing_handle", "proposed_content_utf8",
            "current_content_utf8",
        }
        if type(value) is not dict or set(value) != expected or value.get("schema_version") != REVISION_CONFIRMATION_SCHEMA_VERSION:
            raise ValueError("invalid provisional revision envelope")
        return cls(
            value["provisional_id"], value["statement_id"], value["current_statement_id"],
            value["candidate_id"], AtomHandle.from_mapping(value["existing_handle"]),
            value["proposed_content_utf8"], value["current_content_utf8"],
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": REVISION_CONFIRMATION_SCHEMA_VERSION,
            "provisional_id": self.provisional_id,
            "statement_id": self.statement_id,
            "current_statement_id": self.current_statement_id,
            "candidate_id": self.candidate_id,
            "existing_handle": self.existing_handle.to_mapping(),
            "proposed_content_utf8": self.proposed_content_utf8,
            "current_content_utf8": self.current_content_utf8,
        }


@dataclass(frozen=True)
class RevisionConfirmationResult:
    provisional_id: str
    outcome: str
    relation: str

    def __post_init__(self) -> None:
        if type(self.provisional_id) is not str or not self.provisional_id:
            raise TypeError("confirmation provisional_id is required")
        if self.outcome not in REVISION_CONFIRMATION_OUTCOMES:
            raise ValueError("unknown revision confirmation outcome")
        if self.relation not in REVISION_CONFIRMATION_RELATIONS:
            raise ValueError("unknown revision confirmation relation")
        expected_relation = {
            "confirm_revision": "same_subject_same_slot_supersedes",
            "reject_revision": "different_subject_or_non_superseding",
            "defer": "uncertain",
        }[self.outcome]
        if self.relation != expected_relation:
            raise ValueError("revision confirmation outcome and relation disagree")

    @property
    def confirmed(self) -> bool:
        return self.outcome == "confirm_revision"

    @classmethod
    def from_mapping(cls, value: object) -> "RevisionConfirmationResult":
        expected = {"schema_version", "provisional_id", "outcome", "relation"}
        if type(value) is not dict or set(value) != expected or value.get("schema_version") != REVISION_CONFIRMATION_SCHEMA_VERSION:
            raise ValueError("invalid revision confirmation envelope")
        return cls(value["provisional_id"], value["outcome"], value["relation"])

    @classmethod
    def from_wire_mapping(cls, value: object, provisional_id: str) -> "RevisionConfirmationResult":
        expected = {"schema_version", "outcome", "relation"}
        if type(value) is not dict or set(value) != expected or value.get("schema_version") != REVISION_CONFIRMATION_SCHEMA_VERSION:
            raise ValueError("invalid revision confirmation wire envelope")
        return cls(provisional_id, value["outcome"], value["relation"])

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": REVISION_CONFIRMATION_SCHEMA_VERSION,
            "provisional_id": self.provisional_id,
            "outcome": self.outcome,
            "relation": self.relation,
        }


@dataclass(frozen=True)
class AccessDecision:
    decision_id: str
    statement_id: str
    action: str
    target_cell: GeometryAddress | None = None
    existing_handle: AtomHandle | None = None
    bridge_spec: BridgeSpec | None = None
    reason_text: str = ""
    decided_by: str = "host"

    def __post_init__(self) -> None:
        if any(type(value) is not str or not value for value in (self.decision_id,self.statement_id,self.action,self.reason_text,self.decided_by)):
            raise ValueError("decision_id, statement_id, and reason_text are required")
        if self.target_cell is not None and type(self.target_cell) is not GeometryAddress: raise TypeError("target_cell must be GeometryAddress")
        if self.existing_handle is not None and type(self.existing_handle) is not AtomHandle: raise TypeError("existing_handle must be AtomHandle")
        if self.bridge_spec is not None and type(self.bridge_spec) is not BridgeSpec: raise TypeError("bridge_spec must be BridgeSpec")
        if self.action not in ACTIONS:
            raise ValueError("unknown Access action")
        if self.decided_by not in DECIDED_BY:
            raise ValueError("unknown decision source")
        if self.action in {"new", "revision_keep_history"} and self.target_cell is None:
            raise ValueError("explicit target_cell is required")
        if self.action in {"reuse", "move", "revision_current", "forget"} and self.existing_handle is None:
            raise ValueError("explicit existing_handle is required")
        if self.action == "move" and self.target_cell is None:
            raise ValueError("explicit target_cell is required")
        if self.action == "stitch" and self.bridge_spec is None:
            raise ValueError("explicit bridge_spec is required")
        if self.action == "unstitch" and (self.bridge_spec is None or not self.bridge_spec.bridge_id):
            raise ValueError("bridge_spec identifying the bridge is required")
        allowed = {
            "new": (self.target_cell is not None, self.existing_handle is None, self.bridge_spec is None),
            "revision_keep_history": (self.target_cell is not None, self.existing_handle is None, self.bridge_spec is None),
            "move": (self.target_cell is not None, self.existing_handle is not None, self.bridge_spec is None),
            "reuse": (self.target_cell is None, self.existing_handle is not None, self.bridge_spec is None),
            "revision_current": (self.target_cell is None, self.existing_handle is not None, self.bridge_spec is None),
            "forget": (self.target_cell is None, self.existing_handle is not None, self.bridge_spec is None),
            "stitch": (self.target_cell is None, self.existing_handle is None, self.bridge_spec is not None),
            "unstitch": (self.target_cell is None, self.existing_handle is None, self.bridge_spec is not None),
            "defer": (self.target_cell is None, self.existing_handle is None, self.bridge_spec is None),
        }[self.action]
        if not all(allowed):
            raise ValueError("AccessDecision contains conflicting or unrelated fields")
        if self.target_cell is not None:
            ACTIVE_SEMANTIC_WRITE_POLICY.validate(self.target_cell)
        if self.action == "revision_current" and self.existing_handle is not None:
            ACTIVE_SEMANTIC_WRITE_POLICY.validate(self.existing_handle.geometry_address)
