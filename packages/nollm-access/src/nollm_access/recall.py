from __future__ import annotations

from dataclasses import dataclass

from nollm_core import AtomHandle, CoreRecallRequest, GeometryAddress, RecallBudget


@dataclass(frozen=True)
class AccessRecallRequest:
    request_id: str
    entry_cells: tuple[GeometryAddress, ...] = ()
    entry_handles: tuple[AtomHandle, ...] = ()
    allowed_kernels: tuple[str, ...] = ()
    budget: RecallBudget = RecallBudget(0, 1, 0, 0, 0, 16)

    def __post_init__(self) -> None:
        if not self.request_id or (not self.entry_cells and not self.entry_handles):
            raise ValueError("explicit entry_cells or entry_handles are required")

    def to_core_request(self) -> CoreRecallRequest:
        cells = tuple(sorted(set((*self.entry_cells, *(handle.geometry_address for handle in self.entry_handles)))))
        return CoreRecallRequest(self.request_id, cells, self.allowed_kernels, self.budget)


@dataclass(frozen=True)
class AccessRecallItem:
    handle: AtomHandle
    statement_id: str
    evidence_utf8: str | None
    score_q16: int
    fallback_error: str | None = None


@dataclass(frozen=True)
class AccessRecallResult:
    request_id: str
    items: tuple[AccessRecallItem, ...]
    budget_exhausted: bool
    path_is_not_truth_proof: bool = True
