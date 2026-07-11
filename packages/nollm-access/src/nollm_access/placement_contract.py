from __future__ import annotations

from dataclasses import dataclass

from nollm_core import AtomHandle, BridgeSpec, GeometryAddress


ACTIONS = frozenset({"reuse", "new", "revision_current", "revision_keep_history", "stitch", "unstitch", "defer", "forget"})
DECIDED_BY = frozenset({"host", "llm", "human", "fixture"})


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
        if not self.decision_id or not self.statement_id or not self.reason_text:
            raise ValueError("decision_id, statement_id, and reason_text are required")
        if self.action not in ACTIONS:
            raise ValueError("unknown Access action")
        if self.decided_by not in DECIDED_BY:
            raise ValueError("unknown decision source")
        if self.action in {"new", "revision_keep_history"} and self.target_cell is None:
            raise ValueError("explicit target_cell is required")
        if self.action in {"reuse", "revision_current", "forget"} and self.existing_handle is None:
            raise ValueError("explicit existing_handle is required")
        if self.action == "stitch" and self.bridge_spec is None:
            raise ValueError("explicit bridge_spec is required")
        if self.action == "unstitch" and (self.bridge_spec is None or not self.bridge_spec.bridge_id):
            raise ValueError("bridge_spec identifying the bridge is required")
