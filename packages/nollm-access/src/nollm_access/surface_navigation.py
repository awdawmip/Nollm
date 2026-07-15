from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path

from nollm_core import (
    AtomHandle,
    CoreRuntime,
    GeometryAddress,
    PhysicalFieldScope,
    RecallBudget,
    SurfaceAggregateAddress,
    SurfaceCellProjection,
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
    address: SurfaceAggregateAddress
    native_atom_count: int
    aggregate_atom_count: int
    physical_source_cell_count: int
    density_q16: int
    observation_area_ratio_q32: int
    has_deeper_locality: bool
    has_bridge_endpoint: bool
    statements: tuple[SurfaceStatementPreview, ...]
    truncated: bool
    remaining_count: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "order": self.order,
            "surface_address": self.address.to_mapping(),
            "native_atom_count": self.native_atom_count,
            "aggregate_atom_count": self.aggregate_atom_count,
            "physical_source_cell_count": self.physical_source_cell_count,
            "density_q16": self.density_q16,
            "observation_area_ratio_q32": self.observation_area_ratio_q32,
            "has_deeper_locality": self.has_deeper_locality,
            "has_bridge_endpoint": self.has_bridge_endpoint,
            "statements": [item.to_mapping() for item in self.statements],
            "truncated": self.truncated,
            "remaining_count": self.remaining_count,
        }


@dataclass(frozen=True)
class PhysicalEntryCandidateView:
    candidate_id: str
    address: GeometryAddress
    native_atom_count: int
    current_statement_preview: SurfaceStatementPreview | None
    truncated: bool
    membership_weight_q16: int
    source_surface_candidate_id: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "address": self.address.to_mapping(),
            "native_atom_count": self.native_atom_count,
            "current_statement_preview": self.current_statement_preview.to_mapping() if self.current_statement_preview else None,
            "truncated": self.truncated,
            "membership_weight_q16": self.membership_weight_q16,
            "source_surface_candidate_id": self.source_surface_candidate_id,
        }


@dataclass(frozen=True)
class _TraversalFrame:
    order: int
    parent_order: int | None
    parent_address: SurfaceAggregateAddress | None
    after: SurfaceAggregateAddress | None


@dataclass(frozen=True)
class SurfaceTraversalState:
    operation_id: str
    scope: PhysicalFieldScope
    budget: SurfaceBudgetProfile
    order: int
    parent_order: int | None = None
    parent_address: SurfaceAggregateAddress | None = None
    after: SurfaceAggregateAddress | None = None
    stack: tuple[_TraversalFrame, ...] = ()
    call_count: int = 0


@dataclass(frozen=True)
class SurfaceTraversalPage:
    state: SurfaceTraversalState
    selection: ActiveSurfaceSelection
    cells: tuple[SurfaceCellView, ...]
    has_more: bool
    next_after: SurfaceAggregateAddress | None

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
class PhysicalEntryPage:
    state: SurfaceTraversalState
    source_surface_candidate_id: str
    source_surface_address: SurfaceAggregateAddress
    candidates: tuple[PhysicalEntryCandidateView, ...]
    total_candidate_count: int
    has_more: bool
    next_after: GeometryAddress | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "source_surface_candidate_id": self.source_surface_candidate_id,
            "source_surface_address": self.source_surface_address.to_mapping(),
            "physical_entry_candidates": [candidate.to_mapping() for candidate in self.candidates],
            "total_candidate_count": self.total_candidate_count,
            "resolved_singleton": self.total_candidate_count == 1,
            "has_more": self.has_more,
            "next_after": self.next_after.to_mapping() if self.next_after else None,
            "call_count": self.state.call_count,
        }


@dataclass(frozen=True)
class PhysicalEntryResolution:
    entry_cell: GeometryAddress
    resolved_singleton: bool


@dataclass(frozen=True)
class SurfaceRecallResult:
    entry_cell: GeometryAddress
    items: tuple[dict[str, object], ...]
    budget_exhausted: bool


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
        scope: PhysicalFieldScope,
        budget: SurfaceBudgetProfile,
    ) -> SurfaceTraversalPage:
        if type(operation_id) is not str or not operation_id:
            raise ValueError("operation_id is required")
        with CoreRuntime(self._workspace) as core:
            selection = select_active_surface(core.surface_orders(scope, budget.hard_max_order), budget)
        state = SurfaceTraversalState(operation_id, scope, budget, selection.info.order)
        return self.page(state)

    @staticmethod
    def state_to_mapping(state: SurfaceTraversalState) -> dict[str, object]:
        AccessSurfaceNavigator._require_state(state)
        return {
            "operation_id": state.operation_id,
            "scope": state.scope.to_mapping(),
            "budget": {
                name: getattr(state.budget, name)
                for name in SurfaceBudgetProfile.__dataclass_fields__
            },
            "order": state.order,
            "parent_order": state.parent_order,
            "parent_address": state.parent_address.to_mapping() if state.parent_address else None,
            "after": state.after.to_mapping() if state.after else None,
            "stack": [
                {
                    "order": frame.order,
                    "parent_order": frame.parent_order,
                    "parent_address": frame.parent_address.to_mapping() if frame.parent_address else None,
                    "after": frame.after.to_mapping() if frame.after else None,
                }
                for frame in state.stack
            ],
            "call_count": state.call_count,
        }

    @staticmethod
    def state_from_mapping(value: object) -> SurfaceTraversalState:
        required = {"operation_id", "scope", "budget", "order", "parent_order", "parent_address", "after", "stack", "call_count"}
        if type(value) is not dict or set(value) != required:
            raise ValueError("invalid Surface traversal state")
        scope_value = value["scope"]
        budget_value = value["budget"]
        if type(scope_value) is not dict:
            raise ValueError("invalid Surface traversal scope")
        if type(budget_value) is not dict or set(budget_value) != set(SurfaceBudgetProfile.__dataclass_fields__):
            raise ValueError("invalid Surface traversal budget")
        if type(value["stack"]) is not list:
            raise ValueError("invalid Surface traversal stack")
        scope = PhysicalFieldScope.from_mapping(scope_value)
        budget = SurfaceBudgetProfile(**budget_value)

        def address(item: object) -> SurfaceAggregateAddress | None:
            return None if item is None else SurfaceAggregateAddress.from_mapping(item)

        frames = []
        for item in value["stack"]:
            if type(item) is not dict or set(item) != {"order", "parent_order", "parent_address", "after"}:
                raise ValueError("invalid Surface traversal frame")
            frames.append(_TraversalFrame(item["order"], item["parent_order"], address(item["parent_address"]), address(item["after"])))
        state = SurfaceTraversalState(
            value["operation_id"],
            scope,
            budget,
            value["order"],
            value["parent_order"],
            address(value["parent_address"]),
            address(value["after"]),
            tuple(frames),
            value["call_count"],
        )
        AccessSurfaceNavigator._require_state(state)
        return state

    def page(self, state: SurfaceTraversalState) -> SurfaceTraversalPage:
        self._require_state(state)
        if state.call_count >= state.budget.max_calls:
            raise RuntimeError("Surface traversal call limit reached")
        with CoreRuntime(self._workspace) as core:
            selection = select_active_surface(core.surface_orders(state.scope, state.budget.hard_max_order), state.budget)
            if state.parent_address is None:
                raw_page = core.surface_page(state.scope, state.order, state.after, state.budget.page_size)
                projections = raw_page.cells
            else:
                raw_page = core.surface_descend(
                    state.scope,
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

    def open_physical_entries(self, page: SurfaceTraversalPage, candidate_id: str) -> PhysicalEntryPage:
        selected = self._shown(page, candidate_id)
        if page.state.order != 0:
            raise ValueError("physical entries require an Order 0 Surface cell")
        return self._physical_entry_page(page.state, selected.candidate_id, selected.address, None)

    def continue_physical_entries(self, page: PhysicalEntryPage) -> PhysicalEntryPage:
        if type(page) is not PhysicalEntryPage:
            raise TypeError("page must be PhysicalEntryPage")
        if not page.has_more or page.next_after is None:
            raise ValueError("current physical-entry page has no continuation")
        return self._physical_entry_page(
            page.state,
            page.source_surface_candidate_id,
            page.source_surface_address,
            page.next_after,
        )

    def reopen_physical_entries(
        self,
        state: SurfaceTraversalState,
        source_surface_candidate_id: str,
        source_surface_address: SurfaceAggregateAddress,
        after: GeometryAddress | None,
    ) -> PhysicalEntryPage:
        return self._physical_entry_page(state, source_surface_candidate_id, source_surface_address, after)

    def select_entry(self, page: PhysicalEntryPage, candidate_id: str) -> PhysicalEntryResolution:
        if type(page) is not PhysicalEntryPage:
            raise TypeError("select_entry requires a PhysicalEntryPage")
        if type(candidate_id) is not str or not candidate_id:
            raise ValueError("candidate_id is required")
        matches = tuple(candidate for candidate in page.candidates if candidate.candidate_id == candidate_id)
        if len(matches) != 1:
            raise ValueError("decision selected an unavailable physical-entry candidate")
        return PhysicalEntryResolution(matches[0].address, page.total_candidate_count == 1)

    def _physical_entry_page(
        self,
        state: SurfaceTraversalState,
        source_surface_candidate_id: str,
        source_surface_address: SurfaceAggregateAddress,
        after: GeometryAddress | None,
    ) -> PhysicalEntryPage:
        self._require_state(state)
        if state.order != 0 or source_surface_address.aggregation_order != 0:
            raise ValueError("physical entries require an Order 0 Surface cell")
        if type(source_surface_candidate_id) is not str or not source_surface_candidate_id:
            raise ValueError("source_surface_candidate_id is required")
        if after is not None and type(after) is not GeometryAddress:
            raise TypeError("physical-entry after must be GeometryAddress")
        if state.call_count >= state.budget.max_calls:
            raise RuntimeError("Surface traversal call limit reached")
        with CoreRuntime(self._workspace) as core:
            projection = self._projection_at(core, state.scope, source_surface_address)
            if not projection.source_memberships:
                raise ValueError("Order 0 Surface projection has no physical memberships")
            all_candidates = tuple(
                self._physical_candidate(core, state, source_surface_candidate_id, address, weight)
                for address, weight in projection.source_memberships
            )
        selected = all_candidates if after is None else tuple(
            candidate for candidate in all_candidates if candidate.address.stable_key() > after.stable_key()
        )
        candidates = selected[:state.budget.page_size]
        has_more = len(selected) > state.budget.page_size
        return PhysicalEntryPage(
            replace(state, call_count=state.call_count + 1),
            source_surface_candidate_id,
            source_surface_address,
            candidates,
            len(all_candidates),
            has_more,
            candidates[-1].address if has_more and candidates else None,
        )

    @staticmethod
    def _projection_at(core: CoreRuntime, scope: PhysicalFieldScope, address: SurfaceAggregateAddress) -> SurfaceCellProjection:
        after = None
        while True:
            page = core.surface_page(scope, 0, after, 256)
            match = next((projection for projection in page.cells if projection.address == address), None)
            if match is not None:
                return match
            if not page.has_more or page.next_after is None:
                raise ValueError("source Surface candidate is no longer available")
            after = page.next_after

    def _physical_candidate(
        self,
        core: CoreRuntime,
        state: SurfaceTraversalState,
        source_surface_candidate_id: str,
        address: GeometryAddress,
        membership_weight_q16: int,
    ) -> PhysicalEntryCandidateView:
        handles = tuple(handle for handle, _atom in core.atoms_at(address))
        previews = self._previews(handles)
        material = f"{state.operation_id}\0{source_surface_candidate_id}\0{address.stable_key()}"
        candidate_id = "physical-entry:" + sha256(material.encode("utf-8")).hexdigest()[:20]
        return PhysicalEntryCandidateView(
            candidate_id,
            address,
            len(handles),
            previews[0] if previews else None,
            len(previews) > 1,
            membership_weight_q16,
            source_surface_candidate_id,
        )

    def recall_entry(self, request_id: str, entry_cell: GeometryAddress) -> SurfaceRecallResult:
        if type(request_id) is not str or not request_id:
            raise ValueError("request_id is required")
        if type(entry_cell) is not GeometryAddress:
            raise TypeError("entry_cell must be GeometryAddress")
        recall_budget = RecallBudget(4, 64, 2, 1, 1, 16)
        with self._runtime() as access:
            result = access.recall(AccessRecallRequest(request_id, (entry_cell,), (), ("bridge", "coverage_down", "coverage_up", "lateral"), recall_budget))
        by_statement: dict[str, dict[str, object]] = {}
        for raw in result.items:
            if raw.evidence_utf8 is None:
                continue
            item = self._recall_item(raw)
            previous = by_statement.get(item["statement_id"])
            if previous is None or item["score_q16"] > previous["score_q16"]:
                by_statement[item["statement_id"]] = item
        items = tuple(sorted(by_statement.values(), key=lambda item: (-item["score_q16"], item["statement_id"])))
        return SurfaceRecallResult(entry_cell, items, result.budget_exhausted)

    def _view(
        self,
        core: CoreRuntime,
        state: SurfaceTraversalState,
        projection: SurfaceCellProjection,
        index: int,
    ) -> SurfaceCellView:
        entry_cells = projection.source_cells
        handles = tuple(
            handle
            for address in entry_cells
            for handle, _atom in core.atoms_at(address)
        )
        previews = self._previews(handles)
        shown = tuple(previews[:MAX_STATEMENTS_PER_CELL])
        remaining = max(0, len(previews) - len(shown))
        candidate_id = self._candidate_id(state, projection.address, index)
        return SurfaceCellView(
            candidate_id,
            projection.order,
            projection.address,
            projection.native_atom_count,
            projection.aggregate_atom_count,
            projection.physical_source_cell_count,
            projection.density_q16,
            projection.grid.observation_area_ratio_q32,
            projection.has_deeper_locality,
            projection.has_bridge_endpoint,
            shown,
            remaining > 0,
            remaining,
        )

    def _previews(self, handles: tuple[AtomHandle, ...]) -> tuple[SurfaceStatementPreview, ...]:
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
        return tuple(previews)

    @staticmethod
    def _candidate_id(state: SurfaceTraversalState, address: SurfaceAggregateAddress, index: int) -> str:
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
        if type(state.operation_id) is not str or not state.operation_id:
            raise ValueError("Surface traversal operation_id is required")
        if type(state.scope) is not PhysicalFieldScope or type(state.budget) is not SurfaceBudgetProfile:
            raise TypeError("Surface traversal scope and budget are invalid")
        if type(state.order) is not int or not 0 <= state.order <= state.budget.hard_max_order:
            raise ValueError("Surface traversal order is invalid")
        if type(state.call_count) is not int or state.call_count < 0:
            raise ValueError("Surface traversal call_count is invalid")

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
            "path": list(item.path),
            "path_is_not_truth_proof": True,
        }
