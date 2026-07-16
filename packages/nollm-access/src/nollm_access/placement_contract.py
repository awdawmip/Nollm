from __future__ import annotations

from dataclasses import dataclass

from nollm_core import AtomHandle, BridgeSpec, GeometryAddress

from .write_policy import ACTIVE_SEMANTIC_WRITE_POLICY


ACTIONS = frozenset({"reuse", "new", "move", "revision_current", "revision_keep_history", "stitch", "unstitch", "defer", "forget"})
DECIDED_BY = frozenset({"host", "llm", "human", "fixture"})
PLACEMENT_ACTION_SEMANTICS_VERSION = "nollm_access_semantic_placement_actions_v1"
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
