from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path

from nollm_core import (
    AtomHandle,
    CoreRuntime,
    GeometryAddress,
    RecallBudget,
    SurfaceCellProjection,
    SurfacePlane,
)

from .handle_store import FileHandleStore
from .recall import AccessRecallRequest
from .runtime import AccessRuntime
from .statement_store import FileStatementStore
from .surface_selection import ActiveSurfaceSelection, SurfaceBudgetProfile, select_active_surface


MAX_STATEMENTS_PER_CELL = 3
MAX_STATEMENT_CHARS = 256


@dataclass(frozen=True)
class SurfaceStatementPreview:
    statement_id: str
    content_utf8: str
    handle: AtomHandle

    def to_mapping(self) -> dict[str, object]:
        return {
            "statement_id": self.statement_id,
            "content_utf8": self.content_utf8,
            "handle": self.handle.to_mapping(),
        }


@dataclass(frozen=True)
class SurfaceCellView:
    candidate_id: str
    order: int
    address: GeometryAddress
    native_occupancy_count: int
    aggregate_occupancy_count: int
    occupied_member_count: int
    density_q16: int
    dispersion_q16: int
    boundary_mass_q16: int
    has_deeper_locality: bool
    has_bridge_endpoint: bool
    statements: tuple[SurfaceStatementPreview, ...]
    truncated: bool
    remaining_count: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "order": self.order,
            "geometry_address": self.address.to_mapping(),
            "native_occupancy_count": self.native_occupancy_count,
            "aggregate_occupancy_count": self.aggregate_occupancy_count,
            "occupied_member_count": self.occupied_member_count,
            "density_q16": self.density_q16,
            "dispersion_q16": self.dispersion_q16,
            "boundary_mass_q16": self.boundary_mass_q16,
            "has_deeper_locality": self.has_deeper_locality,
            "has_bridge_endpoint": self.has_bridge_endpoint,
            "statements": [item.to_mapping() for item in self.statements],
            "truncated": self.truncated,
            "remaining_count": self.remaining_count,
        }


@dataclass(frozen=True)
class _TraversalFrame:
    order: int
    parent_order: int | None
    parent_address: GeometryAddress | None
    after: GeometryAddress | None


@dataclass(frozen=True)
class SurfaceTraversalState:
    operation_id: str
    plane: SurfacePlane
    budget: SurfaceBudgetProfile
    order: int
    parent_order: int | None = None
    parent_address: GeometryAddress | None = None
    after: GeometryAddress | None = None
    stack: tuple[_TraversalFrame, ...] = ()
    call_count: int = 0


@dataclass(frozen=True)
class SurfaceTraversalPage:
    state: SurfaceTraversalState
    selection: ActiveSurfaceSelection
    cells: tuple[SurfaceCellView, ...]
    has_more: bool
    next_after: GeometryAddress | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "active_order": self.selection.info.order,
            "current_order": self.state.order,
            "overflow": self.selection.overflow,
            "order_statistics": {
                "occupied_cell_count": self.selection.info.occupied_cell_count,
                "estimated_pages": self.selection.estimated_pages,
                "projection_units": self.selection.projection_units,
            },
            "surface_cells": [cell.to_mapping() for cell in self.cells],
            "has_more": self.has_more,
            "next_after": self.next_after.to_mapping() if self.next_after else None,
            "call_count": self.state.call_count,
        }


@dataclass(frozen=True)
class SurfaceRecallResult:
    entry_cells: tuple[GeometryAddress, ...]
    items: tuple[dict[str, object], ...]
    per_entry: tuple[dict[str, object], ...]


class AccessSurfaceNavigator:
    """Rebuildable Access projection over Core Surface APIs."""

    def __init__(self, workspace: str | Path) -> None:
        if type(workspace) is str:
            if not workspace:
                raise ValueError("workspace is required")
            root = Path(workspace)
        elif isinstance(workspace, Path):
            root = workspace
        else:
            raise TypeError("workspace must be a string or Path")
        self._workspace = root.resolve()

    def begin(
        self,
        operation_id: str,
        plane: SurfacePlane,
        budget: SurfaceBudgetProfile,
    ) -> SurfaceTraversalPage:
        if type(operation_id) is not str or not operation_id:
            raise ValueError("operation_id is required")
        with CoreRuntime(self._workspace) as core:
            selection = select_active_surface(core.surface_orders(plane, budget.hard_max_order), budget)
        state = SurfaceTraversalState(operation_id, plane, budget, selection.info.order)
        return self.page(state)

    def page(self, state: SurfaceTraversalState) -> SurfaceTraversalPage:
        self._require_state(state)
        if state.call_count >= state.budget.max_calls:
            raise RuntimeError("Surface traversal call limit reached")
        with CoreRuntime(self._workspace) as core:
            selection = select_active_surface(core.surface_orders(state.plane, state.budget.hard_max_order), state.budget)
            if state.parent_address is None:
                raw_page = core.surface_page(state.plane, state.order, state.after, state.budget.page_size)
                projections = raw_page.cells
            else:
                raw_page = core.surface_descend(
                    state.plane,
                    state.parent_order,
                    state.parent_address,
                    state.after,
                    state.budget.page_size,
                )
                projections = tuple(cell.projection for cell in raw_page.cells)
            views = tuple(
                self._view(core, state, projection, index)
                for index, projection in enumerate(projections)
            )
        return SurfaceTraversalPage(
            replace(state, call_count=state.call_count + 1),
            selection,
            views,
            raw_page.has_more,
            raw_page.next_after,
        )

    def continue_page(self, page: SurfaceTraversalPage) -> SurfaceTraversalPage:
        if not page.has_more or page.next_after is None:
            raise ValueError("current Surface page has no continuation")
        return self.page(replace(page.state, after=page.next_after))

    def open_surface_cell(self, page: SurfaceTraversalPage, candidate_id: str) -> SurfaceTraversalPage:
        selected = self._shown(page, candidate_id)
        if page.state.order == 0 or not selected.has_deeper_locality:
            raise ValueError("candidate has no deeper Surface locality")
        frame = _TraversalFrame(page.state.order, page.state.parent_order, page.state.parent_address, page.state.after)
        state = replace(
            page.state,
            order=page.state.order - 1,
            parent_order=page.state.order,
            parent_address=selected.address,
            after=None,
            stack=(*page.state.stack, frame),
        )
        self._require_depth(state)
        return self.page(state)

    def request_coarser_surface(self, page: SurfaceTraversalPage) -> SurfaceTraversalPage:
        order = page.state.order + 1
        if order > page.state.budget.hard_max_order:
            raise ValueError("no coarser Surface order is available")
        return self.page(replace(page.state, order=order, parent_order=None, parent_address=None, after=None, stack=()))

    def return_to_parent(self, page: SurfaceTraversalPage) -> SurfaceTraversalPage:
        if not page.state.stack:
            raise ValueError("Surface traversal has no parent")
        frame = page.state.stack[-1]
        return self.page(replace(
            page.state,
            order=frame.order,
            parent_order=frame.parent_order,
            parent_address=frame.parent_address,
            after=frame.after,
            stack=page.state.stack[:-1],
        ))

    def select_entry(self, page: SurfaceTraversalPage, candidate_id: str) -> GeometryAddress:
        selected = self._shown(page, candidate_id)
        if page.state.order != 0:
            raise ValueError("Recall entry selection requires Order 0")
        return selected.address

    def recall_entries(
        self,
        request_id: str,
        entry_cells: tuple[GeometryAddress, ...],
        limit: int,
    ) -> SurfaceRecallResult:
        if type(request_id) is not str or not request_id:
            raise ValueError("request_id is required")
        if type(entry_cells) is not tuple or not entry_cells or any(type(cell) is not GeometryAddress for cell in entry_cells):
            raise TypeError("entry_cells must be a non-empty GeometryAddress tuple")
        canonical = tuple(sorted(set(entry_cells), key=lambda cell: cell.stable_key()))
        if canonical != entry_cells or type(limit) is not int or limit < 1 or len(entry_cells) > limit:
            raise ValueError("entry_cells must be canonical, unique, and within the selection limit")
        merged: dict[str, dict[str, object]] = {}
        per_entry = []
        recall_budget = RecallBudget(1, 12, 0, 1, 0, 16)
        with self._runtime() as access:
            for index, entry in enumerate(entry_cells):
                result = access.recall(AccessRecallRequest(
                    f"{request_id}:entry:{index}",
                    (entry,),
                    (),
                    ("lateral",),
                    recall_budget,
                ))
                items = tuple(self._recall_item(item) for item in result.items if item.evidence_utf8 is not None)
                per_entry.append({"entry_cell": entry.to_mapping(), "items": items, "budget_exhausted": result.budget_exhausted})
                for item in items:
                    previous = merged.get(item["statement_id"])
                    if previous is None or item["score_q16"] > previous["score_q16"]:
                        merged[item["statement_id"]] = item
        items = tuple(sorted(merged.values(), key=lambda item: (-item["score_q16"], item["statement_id"])))
        return SurfaceRecallResult(entry_cells, items, tuple(per_entry))

    def _view(
        self,
        core: CoreRuntime,
        state: SurfaceTraversalState,
        projection: SurfaceCellProjection,
        index: int,
    ) -> SurfaceCellView:
        entry_cells = self._order_zero_members(core, state.plane, projection)
        handles = tuple(
            handle
            for address in entry_cells
            for handle, _atom in core.atoms_at(address)
        )
        previews = []
        handle_store = FileHandleStore(self._workspace)
        statement_store = FileStatementStore(self._workspace)
        for handle in sorted(handles, key=lambda item: (item.geometry_address.stable_key(), item.local_atom_id)):
            try:
                binding = handle_store.binding_for_handle(handle)
                statement = statement_store.get(binding.current_statement_id)
            except (KeyError, FileNotFoundError):
                continue
            previews.append(SurfaceStatementPreview(
                statement.statement_id,
                statement.content_utf8[:MAX_STATEMENT_CHARS],
                handle,
            ))
        shown = tuple(previews[:MAX_STATEMENTS_PER_CELL])
        remaining = max(0, len(previews) - len(shown))
        candidate_id = self._candidate_id(state, projection.address, index)
        return SurfaceCellView(
            candidate_id,
            projection.order,
            projection.address,
            projection.native_occupancy_count,
            projection.aggregate_occupancy_count,
            projection.occupied_member_count,
            projection.density_q16,
            projection.dispersion_q16,
            projection.boundary_mass_q16,
            projection.has_deeper_locality,
            projection.has_bridge_endpoint,
            shown,
            remaining > 0,
            remaining,
        )

    def _order_zero_members(
        self,
        core: CoreRuntime,
        plane: SurfacePlane,
        projection: SurfaceCellProjection,
    ) -> tuple[GeometryAddress, ...]:
        current = (projection.address,)
        for parent_order in range(projection.order, 0, -1):
            lower = []
            for parent in current:
                after = None
                while True:
                    page = core.surface_descend(plane, parent_order, parent, after, 256)
                    lower.extend(cell.projection.address for cell in page.cells)
                    if not page.has_more:
                        break
                    after = page.next_after
            current = tuple(sorted(set(lower), key=lambda item: item.stable_key()))
        return current

    @staticmethod
    def _candidate_id(state: SurfaceTraversalState, address: GeometryAddress, index: int) -> str:
        material = f"{state.operation_id}\0{state.call_count}\0{state.order}\0{index}\0{address.stable_key()}"
        return "surface:" + sha256(material.encode("utf-8")).hexdigest()[:20]

    @staticmethod
    def _shown(page: SurfaceTraversalPage, candidate_id: str) -> SurfaceCellView:
        if type(candidate_id) is not str or not candidate_id:
            raise ValueError("candidate_id is required")
        matches = tuple(cell for cell in page.cells if cell.candidate_id == candidate_id)
        if len(matches) != 1:
            raise ValueError("decision selected an unavailable Surface candidate")
        return matches[0]

    @staticmethod
    def _require_state(state: SurfaceTraversalState) -> None:
        if type(state) is not SurfaceTraversalState:
            raise TypeError("state must be SurfaceTraversalState")

    @staticmethod
    def _require_depth(state: SurfaceTraversalState) -> None:
        if len(state.stack) > state.budget.max_descent_depth:
            raise RuntimeError("Surface traversal descent limit reached")

    def _runtime(self):
        core = CoreRuntime(self._workspace)
        try:
            access = AccessRuntime(core, FileStatementStore(self._workspace), FileHandleStore(self._workspace))
        except Exception:
            core.close()
            raise

        class _Context:
            def __enter__(self_inner) -> AccessRuntime:
                return access

            def __exit__(self_inner, *_args: object) -> None:
                access.close()
                core.close()

        return _Context()

    @staticmethod
    def _recall_item(item: object) -> dict[str, object]:
        return {
            "statement_id": item.statement_id,
            "content_utf8": item.evidence_utf8,
            "handle": item.handle.to_mapping(),
            "address": item.handle.geometry_address.to_mapping(),
            "score_q16": item.score_q16,
            "fallback_error": item.fallback_error,
        }
