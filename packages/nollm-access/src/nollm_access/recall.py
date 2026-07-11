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
        if type(self.request_id) is not str or not self.request_id or type(self.entry_cells) is not tuple or type(self.entry_handles) is not tuple or type(self.allowed_kernels) is not tuple or type(self.budget) is not RecallBudget:
            raise TypeError("Access Recall fields have invalid types")
        if any(type(cell) is not GeometryAddress for cell in self.entry_cells) or any(type(handle) is not AtomHandle for handle in self.entry_handles) or any(type(kernel) is not str for kernel in self.allowed_kernels): raise TypeError("Access Recall tuple members have invalid types")
        if tuple(sorted(self.entry_cells,key=lambda cell:cell.stable_key())) != self.entry_cells or len(set(self.entry_cells)) != len(self.entry_cells): raise ValueError("entry_cells must be canonical and unique")
        handle_key=lambda handle:(handle.geometry_address.stable_key(),handle.local_atom_id)
        if tuple(sorted(self.entry_handles,key=handle_key)) != self.entry_handles or len(set(self.entry_handles)) != len(self.entry_handles): raise ValueError("entry_handles must be canonical and unique")
        if tuple(sorted(self.allowed_kernels)) != self.allowed_kernels or len(set(self.allowed_kernels)) != len(self.allowed_kernels): raise ValueError("allowed_kernels must be canonical and unique")
        if any(kernel not in {"coverage_up","coverage_down","lateral","bridge"} for kernel in self.allowed_kernels): raise ValueError("unknown Recall kernel")
        projected=(*self.entry_cells,*(handle.geometry_address for handle in self.entry_handles))
        if len(set(projected)) != len(projected): raise ValueError("entry cell projections must be unique")
        if not self.entry_cells and not self.entry_handles:
            raise ValueError("explicit entry_cells or entry_handles are required")

    def to_core_request(self) -> CoreRecallRequest:
        cells = tuple(sorted((*self.entry_cells, *(handle.geometry_address for handle in self.entry_handles)), key=lambda item: item.stable_key()))
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
