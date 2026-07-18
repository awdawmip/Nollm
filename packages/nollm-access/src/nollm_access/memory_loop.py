from __future__ import annotations

from pathlib import Path
from time import perf_counter_ns
import hashlib
import json

from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, JunctionRequest, PhysicalFieldScope, RelationGroupJunctionRequest

from .handle_store import FileHandleStore
from .locality import AtlasNode, AtlasPath, LocalityAtlas, LocalityCandidateRef
from .placement_contract import AccessDecision, ProvisionalRevisionDecision, RevisionConfirmationResult
from .recall_lens import JunctionSemanticPlan
from .runtime import AccessRuntime
from .statement import MemoryStatement
from .statement_store import FileStatementStore
from .surface_navigation import AccessSurfaceNavigator
from .surface_selection import PLACEMENT_SURFACE_BUDGET
from .write_policy import ACTIVE_SEMANTIC_WRITE_POLICY


PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_surface_placement_v1"
BATCH_PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_batch_placement_v1"
DEFAULT_FIELD_SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)
_Q32_ONE = 1 << 32
_MIN_FRONTIER_RING = 4
_MIN_FRONTIER_DISTANCE_SQUARED_Q32 = 3 * _MIN_FRONTIER_RING * _MIN_FRONTIER_RING * _Q32_ONE
_MAX_FRONTIER_RADIUS = 1024


class RevisionTargetExcludedError(ValueError):
    pass


class AccessMemoryLoop:
    """Access-owned cursor-free Surface placement and recall composition."""

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
        self._closed = False

    @property
    def workspace(self) -> Path:
        return self._workspace

    def close(self) -> None:
        self._closed = True

    def __enter__(self) -> "AccessMemoryLoop":
        self._require_open()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def navigator(self) -> AccessSurfaceNavigator:
        self._require_open()
        return AccessSurfaceNavigator(self._workspace)

    def placement_candidates(
        self,
        selected_entry: object,
        request_id: str,
        scope: PhysicalFieldScope = DEFAULT_FIELD_SCOPE,
    ) -> list[dict[str, object]]:
        self._require_request(request_id)
        if type(scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        entry = None if selected_entry is None else self._cell(selected_entry)
        if entry is not None and not scope.contains(entry):
            raise ValueError("selected_entry must belong to the Physical FieldScope")
        with CoreRuntime(self._workspace) as core:
            occupied = tuple(cell for cell in core.occupied_cells() if scope.contains(cell))
            candidates: list[dict[str, object]] = []
            if entry is not None:
                candidates.append(self._candidate(core, "placement:existing:0", "existing_cell", entry))
                for index, address in enumerate(entry.lateral(1)):
                    candidates.append(self._candidate(core, f"placement:lateral:{index}", "lateral_ring_1", address))
            frontier = self._expand_surface_frontier(scope, occupied)
            candidates.append(self._candidate(core, "placement:expand:0", "expand_surface", frontier))
        if len(candidates) > 8 or len({item["candidate_id"] for item in candidates}) != len(candidates):
            raise AssertionError("placement candidates must be unique and bounded")
        return candidates

    def candidate_statement_context(self, candidates: object) -> list[dict[str, object]]:
        if type(candidates) is not list or len(candidates) > 8:
            raise TypeError("candidates must be a bounded list")
        return self._candidate_statement_context(candidates, 8)

    def _candidate_statement_context(
        self,
        candidates: object,
        max_candidates: int,
    ) -> list[dict[str, object]]:
        if type(candidates) is not list or len(candidates) > max_candidates:
            raise TypeError("candidates must be a bounded list")
        handle_store = FileHandleStore(self._workspace)
        statement_store = FileStatementStore(self._workspace)
        context = []
        for candidate in candidates:
            if type(candidate) is not dict or type(candidate.get("candidate_id")) is not str or type(candidate.get("existing_handles")) is not list:
                raise TypeError("candidate is invalid")
            statements = []
            for raw_handle in candidate["existing_handles"]:
                handle = AtomHandle.from_mapping(raw_handle)
                try:
                    binding = handle_store.binding_for_handle(handle)
                    statement = statement_store.get(binding.current_statement_id)
                except (KeyError, FileNotFoundError):
                    continue
                statements.append({
                    "statement_id": statement.statement_id,
                    "content_utf8": statement.content_utf8[:256],
                    "handle": handle.to_mapping(),
                })
            context.append({"candidate_id": candidate["candidate_id"], "statements": statements[:3]})
        return context

    def bounded_physical_entries(
        self,
        request_id: str,
        max_entries: int = 32,
        scope: PhysicalFieldScope = DEFAULT_FIELD_SCOPE,
    ) -> list[dict[str, object]]:
        """Project a finite geometry-ordered entry view without a semantic index."""
        self._require_request(request_id)
        if type(max_entries) is not int or not 1 <= max_entries <= 64:
            raise ValueError("max_entries must be between 1 and 64")
        if type(scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        with CoreRuntime(self._workspace) as core:
            cells = tuple(sorted(
                (cell for cell in core.occupied_cells() if scope.contains(cell)),
                key=lambda item: item.stable_key(),
            ))[:max_entries]
            candidates = [self._candidate(core, f"physical-entry:{index}", "existing_cell", cell) for index, cell in enumerate(cells)]
        contexts = self._candidate_statement_context(candidates, max_entries)
        statements = {item["candidate_id"]: item["statements"] for item in contexts}
        return [{
            "entry_id": item["candidate_id"],
            "entry_cell": item["geometry_address"],
            "occupancy_count": item["occupancy"]["count"],
            "statements": statements[item["candidate_id"]],
        } for item in candidates]

    def batch_placement_view(self, request_id: str, max_existing: int = 16, max_empty: int = 16) -> dict[str, object]:
        self._require_request(request_id)
        if type(max_existing) is not int or not 1 <= max_existing <= 32 or type(max_empty) is not int or not 1 <= max_empty <= 32:
            raise ValueError("batch placement view budgets are invalid")
        with CoreRuntime(self._workspace) as core:
            state_sha256 = hashlib.sha256(core.export_state_bytes()).hexdigest()
            occupied = tuple(sorted(
                (cell for cell in core.occupied_cells() if DEFAULT_FIELD_SCOPE.contains(cell)),
                key=lambda item: item.stable_key(),
            ))
            selected_occupied = occupied[:max_existing]
            candidates = [self._candidate(core, f"batch:existing:{index}", "existing_cell", cell) for index, cell in enumerate(selected_occupied)]
            occupied_keys = {cell.stable_key() for cell in occupied}
            empty: list[GeometryAddress] = []
            if not occupied:
                origin = GeometryAddress(DEFAULT_FIELD_SCOPE.profile_id, DEFAULT_FIELD_SCOPE.chart_id, DEFAULT_FIELD_SCOPE.reference_layer, 0, 0)
                empty.append(origin)
                empty.extend(sorted(origin.lateral(_MIN_FRONTIER_RING), key=lambda item: item.stable_key())[:max_empty - 1])
            else:
                for cell in selected_occupied:
                    for candidate in sorted(cell.lateral(1), key=lambda item: item.stable_key()):
                        if candidate.stable_key() in occupied_keys or candidate in empty:
                            continue
                        empty.append(candidate)
                        if len(empty) >= max_empty:
                            break
                    if len(empty) >= max_empty:
                        break
                frontier = self._expand_surface_frontier(DEFAULT_FIELD_SCOPE, occupied)
                if frontier not in empty:
                    empty.append(frontier)
            for index, cell in enumerate(empty[:max_empty]):
                relation = "expand_surface" if all(
                    self._physical_distance_squared_q32(cell, occupied_cell) >= _MIN_FRONTIER_DISTANCE_SQUARED_Q32
                    for occupied_cell in occupied
                ) else "lateral_ring_1"
                candidates.append(self._candidate(core, f"batch:empty:{index}", relation, cell))
        contexts = self._candidate_statement_context(candidates, max_existing + max_empty)
        statements = {item["candidate_id"]: item["statements"] for item in contexts}
        projected = [{**item, "statements": statements[item["candidate_id"]]} for item in candidates]
        fingerprint = hashlib.sha256(json.dumps(
            {"core_state_sha256": state_sha256, "candidates": projected},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")).hexdigest()
        return {"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "core_state_sha256": state_sha256, "view_fingerprint": fingerprint, "candidates": projected}

    def build_locality_atlas(
        self,
        request_id: str,
        candidate_limit: int = 512,
        scope: PhysicalFieldScope = DEFAULT_FIELD_SCOPE,
    ) -> LocalityAtlas:
        self._require_request(request_id)
        if type(candidate_limit) is not int or not 1 <= candidate_limit <= 512:
            raise ValueError("candidate_limit must be in [1,512]")
        if type(scope) is not PhysicalFieldScope:
            raise TypeError("scope must be PhysicalFieldScope")
        with CoreRuntime(self._workspace) as core:
            state_sha256 = hashlib.sha256(core.export_state_bytes()).hexdigest()
            occupied = tuple(sorted((cell for cell in core.occupied_cells() if scope.contains(cell)), key=lambda item: item.stable_key()))
            occupied_set = frozenset(occupied)
            candidates: list[LocalityCandidateRef] = []
            nodes: list[AtlasNode] = []
            paths: list[AtlasPath] = []
            selected_order: int | None = 0
            order_projection_counts: tuple[int, ...] = (0,)
            covered: frozenset[GeometryAddress] = frozenset()
            overflow = False
            if occupied:
                projection_counts = []
                selected_order = None
                for order in range(9):
                    info = core.surface_orders(scope, order)[-1]
                    projection_counts.append(info.occupied_cell_count)
                    if info.occupied_cell_count <= candidate_limit:
                        selected_order = order
                        break
                order_projection_counts = tuple(projection_counts)
                if selected_order is None:
                    overflow = True
                    projections = ()
                else:
                    projections = self._surface_projections(core, scope, selected_order)
                    if len(projections) != order_projection_counts[selected_order]:
                        raise RuntimeError("Surface order count changed during Atlas construction")
                covered = frozenset(
                    cell for projection in projections for cell in projection.source_cells if cell in occupied_set
                )
                for projection in projections:
                    source_cells = tuple(sorted(set(projection.source_cells) & occupied_set, key=lambda item: item.stable_key()))
                    if not source_cells:
                        raise RuntimeError("occupied Surface projection has no current source Cell")
                    cells = self._region_support(source_cells, 4)
                    support_overflow = self._support_coverage_radius(source_cells, cells) > 4
                    material = json.dumps({"state": state_sha256, "surface": projection.address.to_mapping()}, sort_keys=True, separators=(",", ":")).encode("ascii")
                    digest = hashlib.sha256(material).hexdigest()
                    candidate_id = f"locality:{digest}"
                    raw = [self._candidate(core, f"{candidate_id}:{cell_index}", "existing_cell", cell) for cell_index, cell in enumerate(cells)]
                    contexts = self._candidate_statement_context(raw, 4)
                    representatives = []
                    seen_statements = set()
                    for context in contexts:
                        for statement in context["statements"]:
                            if statement["statement_id"] not in seen_statements:
                                representatives.append(statement)
                                seen_statements.add(statement["statement_id"])
                    neighbor_counts = tuple(sum(neighbor in occupied_set for neighbor in cell.lateral(1)) for cell in cells)
                    candidates.append(LocalityCandidateRef(
                        candidate_id, cells, True, any(value < 6 for value in neighbor_counts),
                        max(6 - value for value in neighbor_counts), min(neighbor_counts), tuple(representatives[:3]),
                        len(source_cells), "geometry_center_farthest_v1", support_overflow,
                    ))
                    node_id = f"atlas-node:{digest}"
                    nodes.append(AtlasNode(
                        node_id, selected_order, projection.address.to_mapping(), (),
                        len(source_cells), projection.native_atom_count,
                        projection.truncated, tuple(representatives[:3]), len(source_cells), len(cells),
                        "geometry_center_farthest_v1", support_overflow,
                    ))
                    paths.append(AtlasPath(
                        f"atlas-path:{digest}", (node_id,), () if support_overflow else (candidate_id,),
                    ))
            else:
                frontier = core.junction_candidates(JunctionRequest(scope, (), (), 1, 1))[0]
                candidates.append(LocalityCandidateRef(frontier.candidate_id, (frontier.cell,), False, False, 6, 0, (), 0, "empty_field_frontier_v1", False))
                node_id = f"atlas-node:{frontier.candidate_id}"
                nodes.append(AtlasNode(node_id, 0, frontier.cell.to_mapping(), (), 0, 0, False, (), 0, 1, "empty_field_frontier_v1", False))
                paths.append(AtlasPath(f"atlas-path:{frontier.candidate_id}", (node_id,), (frontier.candidate_id,)))
            uncovered = occupied_set - covered
            certificate = {
                "occupied_field_cell_count": len(occupied),
                "covered_field_cell_count": len(covered),
                "uncovered_field_cell_count": len(uncovered),
                "selected_aggregation_order": selected_order,
                "region_count": len(nodes),
                "overflow": overflow,
                "order_projection_counts": list(order_projection_counts),
            }
        payload = {
            "field_scope": scope.to_mapping(),
            "core_state_sha256": state_sha256,
            "nodes": [item.to_mapping() for item in nodes],
            "paths": [item.to_mapping() for item in paths],
            "candidates": [item.to_mapping() for item in candidates],
            "coverage_certificate": certificate,
        }
        fingerprint = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return LocalityAtlas(
            request_id, scope, state_sha256, fingerprint, tuple(candidates), tuple(nodes), tuple(paths),
            certificate["occupied_field_cell_count"], certificate["covered_field_cell_count"],
            certificate["uncovered_field_cell_count"], certificate["selected_aggregation_order"],
            certificate["region_count"], certificate["overflow"], tuple(order_projection_counts),
        )

    @classmethod
    def _region_support(cls, source_cells: tuple[GeometryAddress, ...], limit: int) -> tuple[GeometryAddress, ...]:
        if len(source_cells) <= limit:
            return source_cells
        center = min(
            source_cells,
            key=lambda cell: (sum(cls._hex_distance(cell, other) for other in source_cells), cell.stable_key()),
        )
        selected = [center]
        while len(selected) < limit:
            selected.append(max(
                (cell for cell in source_cells if cell not in selected),
                key=lambda cell: (min(cls._hex_distance(cell, current) for current in selected), tuple(-value if type(value) is int else value for value in cell.stable_key())),
            ))
        return tuple(sorted(selected, key=lambda item: item.stable_key()))

    @classmethod
    def _support_coverage_radius(cls, source_cells: tuple[GeometryAddress, ...], support: tuple[GeometryAddress, ...]) -> int:
        return max(min(cls._hex_distance(cell, anchor) for anchor in support) for cell in source_cells)

    @staticmethod
    def _hex_distance(left: GeometryAddress, right: GeometryAddress) -> int:
        dq, dr = left.q - right.q, left.r - right.r
        return max(abs(dq), abs(dr), abs(dq + dr))

    @staticmethod
    def _surface_projections(core: CoreRuntime, scope: PhysicalFieldScope, order: int) -> tuple:
        projections = []
        after = None
        while True:
            page = core.surface_page(scope, order, after, 256)
            projections.extend(page.cells)
            if not page.has_more:
                return tuple(projections)
            after = page.next_after

    def apply_batch_placements(
        self,
        statements: object,
        decisions: object,
        request_id: str,
        view_fingerprint: str,
        max_existing: int = 16,
        max_empty: int = 16,
    ) -> dict[str, object]:
        self._require_request(request_id)
        if type(statements) is not list or not statements or type(decisions) is not list or len(decisions) != len(statements):
            raise TypeError("batch Statements and decisions must be equal non-empty lists")
        formed = [_statement if type(_statement) is MemoryStatement else MemoryStatement.from_mapping(_statement) for _statement in statements]
        if len({item.statement_id for item in formed}) != len(formed):
            raise ValueError("batch Statement identities must be unique")
        view = self.batch_placement_view(request_id + ":view", max_existing, max_empty)
        if type(view_fingerprint) is not str or view_fingerprint != view["view_fingerprint"]:
            raise ValueError("batch placement view changed before apply")
        candidates = {item["candidate_id"]: item for item in view["candidates"]}
        operations = []
        outcomes = []
        used_empty = set()
        for statement, raw in zip(formed, decisions, strict=True):
            if type(raw) is not dict or raw.get("statement_id") != statement.statement_id or type(raw.get("outcome")) is not str or type(raw.get("reason_text")) is not str:
                raise ValueError("batch decision does not bind its Statement")
            if raw["outcome"] == "defer":
                if set(raw) != {"statement_id", "outcome", "reason_text"}:
                    raise ValueError("deferred batch decision has invalid fields")
                outcomes.append({"statement_id": statement.statement_id, "outcome": "defer", "reason": raw["reason_text"]})
                continue
            if raw["outcome"] != "apply" or type(raw.get("action")) is not str or type(raw.get("candidate_id")) is not str:
                raise ValueError("batch decision has invalid outcome")
            try:
                candidate = candidates[raw["candidate_id"]]
            except KeyError as exc:
                raise ValueError("batch decision selected an unavailable candidate") from exc
            action = raw["action"]
            address = GeometryAddress.from_mapping(candidate["geometry_address"])
            if action in {"new_local", "expand_surface"}:
                if set(raw) != {"statement_id", "outcome", "action", "candidate_id", "reason_text"}:
                    raise ValueError("new batch placement has invalid fields")
                if action == "expand_surface" and candidate["relation_kind"] != "expand_surface":
                    raise ValueError("expand_surface requires a frontier candidate")
                if candidate["occupancy"]["count"] == 0 and candidate["candidate_id"] in used_empty:
                    raise ValueError("batch cannot place two new Statements into one empty candidate")
                if candidate["occupancy"]["count"] == 0:
                    used_empty.add(candidate["candidate_id"])
                decision = AccessDecision(f"batch:{request_id}:{statement.statement_id}", statement.statement_id, "new", address, None, None, raw["reason_text"], "llm")
            elif action == "reuse":
                if set(raw) != {"statement_id", "outcome", "action", "candidate_id", "existing_handle", "reason_text"}:
                    raise ValueError("reuse batch placement has invalid fields")
                handle = AtomHandle.from_mapping(raw["existing_handle"])
                if handle.to_mapping() not in candidate["existing_handles"]:
                    raise ValueError("reuse Handle is not supplied by the selected candidate")
                decision = AccessDecision(f"batch:{request_id}:{statement.statement_id}", statement.statement_id, "reuse", None, handle, None, raw["reason_text"], "llm")
            elif action == "revision_current":
                raise ValueError("batch revision_current requires the separate bounded confirmation path")
            else:
                raise ValueError("unsupported batch placement action")
            operations.append((statement, decision))
            outcomes.append({"statement_id": statement.statement_id, "outcome": "pending_apply", "action": action})
        verified_by_statement = {}
        statement_store = FileStatementStore(self._workspace)
        for statement, decision in operations:
            existed_before = statement_store.exists(statement.statement_id)
            if existed_before:
                try:
                    with self._runtime() as access:
                        existing_handle = access.saved_handle(statement.statement_id)
                    durable = self._durable_readback(statement, existing_handle)
                except KeyError:
                    pass
                else:
                    verified_by_statement[statement.statement_id] = {
                        "statement_id": statement.statement_id,
                        "outcome": "applied",
                        "action": "replay_existing",
                        "durable_commit": durable,
                    }
                    continue
            try:
                with self._runtime() as access:
                    access.capture(statement)
                    result = access.apply(decision)
                durable = self._durable_readback(statement, result)
            except Exception as error:
                if not existed_before and statement_store.exists(statement.statement_id):
                    statement_store.discard_new(statement)
                verified_by_statement[statement.statement_id] = {
                    "statement_id": statement.statement_id,
                    "outcome": "error",
                    "error": str(error),
                }
            else:
                verified_by_statement[statement.statement_id] = {
                    "statement_id": statement.statement_id,
                    "outcome": "applied",
                    "action": next(item["action"] for item in outcomes if item["statement_id"] == statement.statement_id),
                    "durable_commit": durable,
                }
        verified = [
            verified_by_statement.get(outcome["statement_id"], outcome)
            for outcome in outcomes
        ]
        return {"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "view_fingerprint": view_fingerprint, "outcomes": verified}

    def apply_junction_plans(
        self,
        plans: tuple[JunctionSemanticPlan, ...],
        atlas: LocalityAtlas,
        request_id: str,
        revision_confirmations: object = None,
    ) -> dict[str, object]:
        """Apply validated semantic plans while keeping exact Cell selection in Core."""
        self._require_request(request_id)
        if type(plans) is not tuple or not plans or any(type(item) is not JunctionSemanticPlan for item in plans):
            raise TypeError("plans must be a non-empty JunctionSemanticPlan tuple")
        if type(atlas) is not LocalityAtlas:
            raise TypeError("atlas must be LocalityAtlas")
        if atlas.overflow or atlas.uncovered_field_cell_count != 0:
            raise ValueError("Locality Atlas is not active and field-complete")
        if revision_confirmations is None:
            confirmations: dict[str, object] = {}
        elif type(revision_confirmations) is dict and all(type(key) is str for key in revision_confirmations):
            confirmations = revision_confirmations
        else:
            raise TypeError("revision_confirmations must be a Statement-keyed mapping")

        confirmed_revision_replay = all(
            plan.action == "revision_current" and plan.statement.statement_id in confirmations
            for plan in plans
        )
        if not confirmed_revision_replay:
            reopened = self.build_locality_atlas(request_id + ":reopen", len(atlas.candidates), atlas.scope)
            if reopened.core_state_sha256 != atlas.core_state_sha256 or reopened.atlas_fingerprint != atlas.atlas_fingerprint:
                raise ValueError("Locality Atlas changed before Junction apply")
        prepared: list[tuple[JunctionSemanticPlan, AccessDecision | None, dict[str, object] | None]] = []
        for plan in plans:
            if plan.atlas_fingerprint != atlas.atlas_fingerprint:
                raise ValueError("semantic plan does not bind the current Locality Atlas")
            if plan.action == "defer":
                prepared.append((plan, None, None))
                continue
            if plan.action in {"new_local", "expand_surface"}:
                prepared.append((plan, None, {"relation_groups": plan.relation_groups}))
                continue
            handle = plan.existing_handle
            assert handle is not None
            if not any(handle.geometry_address in group for group in plan.relation_groups):
                raise ValueError("existing Handle is not supplied by a resolved Lens relation group")
            action = "reuse" if plan.action == "reuse" else "revision_current"
            decision = AccessDecision(
                f"junction:{request_id}:{plan.statement.statement_id}", plan.statement.statement_id,
                action, None, handle, None, plan.reason_text, "llm",
            )
            prepared.append((plan, decision, None))

        outcomes = []
        for plan, decision, placement in prepared:
            if decision is None and placement is not None and "relation_groups" in placement:
                with CoreRuntime(self._workspace) as core:
                    if placement["relation_groups"]:
                        candidates = core.relation_group_junction_candidates(RelationGroupJunctionRequest(
                            atlas.scope, placement["relation_groups"], 4, 2, 8,
                        ))
                    else:
                        candidates = core.junction_candidates(JunctionRequest(atlas.scope, (), (), 1, 1))
                if not candidates:
                    outcomes.append({
                        "statement_id": plan.statement.statement_id,
                        "source_capture_ids": list(plan.source_capture_ids),
                        "outcome": "defer",
                        "reason": "lens_geometry_unrealized",
                    })
                    continue
                if hasattr(candidates[0], "all_groups_realized") and not candidates[0].all_groups_realized:
                    raise RuntimeError("Core exposed an unrealized relation-group Junction")
                decision = AccessDecision(
                    f"junction:{request_id}:{plan.statement.statement_id}", plan.statement.statement_id,
                    "new", candidates[0].cell, None, None, plan.reason_text, "llm",
                )
                placement = {"junction": candidates[0].to_mapping()}
            if decision is None:
                outcomes.append({
                    "statement_id": plan.statement.statement_id,
                    "source_capture_ids": list(plan.source_capture_ids),
                    "outcome": "defer",
                    "reason": plan.reason_text if placement is None else placement["reason"],
                })
                continue
            confirmation_value = confirmations.get(plan.statement.statement_id)
            if decision.action == "revision_current" and confirmation_value is None:
                provisional = self._provisional_revision(plan.statement, decision, self._relation_group_locator(plan.relation_groups))
                outcomes.append({
                    "statement_id": plan.statement.statement_id,
                    "source_capture_ids": list(plan.source_capture_ids),
                    "outcome": "revision_confirmation_required",
                    "provisional_revision": provisional.to_mapping(),
                })
                continue
            if decision.action == "revision_current":
                confirmation = RevisionConfirmationResult.from_mapping(confirmation_value)
                provisional = self._provisional_revision(plan.statement, decision, self._relation_group_locator(plan.relation_groups))
                if confirmation.provisional_id != provisional.provisional_id or not confirmation.confirmed:
                    outcomes.append({
                        "statement_id": plan.statement.statement_id,
                        "source_capture_ids": list(plan.source_capture_ids),
                        "outcome": "defer",
                        "reason": "revision was not confirmed",
                    })
                    continue
            statement_store = FileStatementStore(self._workspace)
            existed_before = statement_store.exists(plan.statement.statement_id)
            if existed_before:
                try:
                    with self._runtime() as access:
                        existing_handle = access.saved_handle(plan.statement.statement_id)
                    durable = self._durable_readback(plan.statement, existing_handle)
                except KeyError:
                    pass
                else:
                    outcomes.append({
                        "statement_id": plan.statement.statement_id,
                        "source_capture_ids": list(plan.source_capture_ids),
                        "outcome": "applied",
                        "action": "replay_existing",
                        "durable_commit": durable,
                    })
                    continue
            try:
                with self._runtime() as access:
                    access.capture(plan.statement)
                    handle = access.apply(decision)
                durable = self._durable_readback(plan.statement, handle)
            except Exception as error:
                if not existed_before and statement_store.exists(plan.statement.statement_id):
                    statement_store.discard_new(plan.statement)
                outcomes.append({
                    "statement_id": plan.statement.statement_id,
                    "source_capture_ids": list(plan.source_capture_ids),
                    "outcome": "error",
                    "error": str(error),
                })
            else:
                outcomes.append({
                    "statement_id": plan.statement.statement_id,
                    "source_capture_ids": list(plan.source_capture_ids),
                    "outcome": "applied",
                    "action": plan.action,
                    "durable_commit": durable,
                    **({} if placement is None else placement),
                })
        return {
            "schema_version": "nollm_access_junction_apply_v2",
            "atlas_fingerprint": atlas.atlas_fingerprint,
            "outcomes": outcomes,
        }

    @staticmethod
    def _relation_group_locator(groups: tuple[tuple[GeometryAddress, ...], ...]) -> dict[str, object]:
        mapping = [[cell.to_mapping() for cell in group] for group in groups]
        payload = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode("ascii")
        return {"candidate_id": f"relation-groups:{hashlib.sha256(payload).hexdigest()}", "relation_groups": mapping}

    def local_context(self, entry_cells: object, request_id: str) -> list[dict[str, object]]:
        self._require_request(request_id)
        if type(entry_cells) is not list or len(entry_cells) != 1:
            raise TypeError("entry_cells must contain exactly one entry")
        cells = tuple(sorted((self._cell(item) for item in entry_cells), key=lambda item: item.stable_key()))
        result = self.navigator().recall_entry(request_id, cells[0])
        return list(result.items)

    def apply_placement(
        self,
        statement: MemoryStatement,
        placement: object,
        request_id: str,
        selected_entry: object = None,
        scope: PhysicalFieldScope = DEFAULT_FIELD_SCOPE,
        revision_confirmation: object = None,
        excluded_revision_targets: object = None,
    ) -> dict[str, object]:
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        self._require_request(request_id)
        decision_started = perf_counter_ns()
        candidates = self.placement_candidates(selected_entry, request_id + ":candidates", scope)
        decision, public_action, selected = self._decision(placement, statement, request_id, candidates)
        decision_validation_us = (perf_counter_ns() - decision_started) // 1_000
        empty_timing = {
            "decision_validation_us": decision_validation_us,
            "decision_validation_ms": decision_validation_us // 1_000,
            "statement_persist_us": 0,
            "statement_persist_ms": 0,
            "core_apply_us": 0,
            "placement_apply_ms": 0,
            "handle_bind_us": 0,
            "handle_bind_ms": 0,
            "durable_readback_us": 0,
        }
        if decision is None:
            return {"outcome": "defer", "statement_id": statement.statement_id, "core_write_count": 0, "revision_confirmation_count": 0, "durable_commit": None, "operation_timing": empty_timing}
        confirmation_count = 0
        if decision.action == "revision_current":
            provisional = self._provisional_revision(statement, decision, selected)
            excluded = self._excluded_revision_target_keys(excluded_revision_targets)
            if self._handle_key(provisional.existing_handle.to_mapping()) in excluded:
                raise RevisionTargetExcludedError("revision target was rejected earlier in this operation")
            if revision_confirmation is None:
                return {
                    "outcome": "revision_confirmation_required",
                    "statement_id": statement.statement_id,
                    "provisional_revision": provisional.to_mapping(),
                    "core_write_count": 0,
                    "revision_confirmation_count": 0,
                    "durable_commit": None,
                    "operation_timing": empty_timing,
                }
            confirmation = RevisionConfirmationResult.from_mapping(revision_confirmation)
            confirmation_count = 1
            if confirmation.provisional_id != provisional.provisional_id:
                raise ValueError("revision confirmation does not bind the provisional decision")
            if not confirmation.confirmed:
                return {
                    "outcome": "revision_rejected",
                    "statement_id": statement.statement_id,
                    "provisional_revision": provisional.to_mapping(),
                    "revision_confirmation": confirmation.to_mapping(),
                    "core_write_count": 0,
                    "revision_confirmation_count": 1,
                    "durable_commit": None,
                    "operation_timing": empty_timing,
                }
        statement_store = FileStatementStore(self._workspace)
        existed_before = statement_store.exists(statement.statement_id)
        with self._runtime() as access:
            persist_started = perf_counter_ns()
            access.capture(statement)
            statement_persist_us = (perf_counter_ns() - persist_started) // 1_000
            try:
                apply_started = perf_counter_ns()
                result = access.apply(decision)
                core_apply_us = (perf_counter_ns() - apply_started) // 1_000
            except Exception:
                if not existed_before:
                    statement_store.discard_new(statement)
                raise
            bind_started = perf_counter_ns()
            if type(result) is AtomHandle:
                binding = access.handle_store.binding_for_handle(result)
                statement_is_bound = (
                    binding.current_statement_id == statement.statement_id
                    or (
                        public_action == "reuse"
                        and statement.statement_id in binding.supporting_statement_ids
                    )
                )
                if not statement_is_bound:
                    raise RuntimeError("placement HandleBinding verification failed")
            handle_bind_us = (perf_counter_ns() - bind_started) // 1_000
        durable_started = perf_counter_ns()
        durable_commit = self._durable_readback(statement, result)
        durable_readback_us = (perf_counter_ns() - durable_started) // 1_000
        return {
            "outcome": "applied",
            "statement_id": statement.statement_id,
            "action": public_action,
            "candidate_id": selected["candidate_id"] if selected is not None else None,
            "handle": result.to_mapping() if type(result) is AtomHandle else None,
            "durable_commit": durable_commit,
            "core_write_count": 1 if public_action in {"new_local", "expand_surface", "revision_current"} else 0,
            "revision_confirmation_count": confirmation_count,
            "operation_timing": {
                "decision_validation_us": decision_validation_us,
                "decision_validation_ms": decision_validation_us // 1_000,
                "statement_persist_us": statement_persist_us,
                "statement_persist_ms": statement_persist_us // 1_000,
                "core_apply_us": core_apply_us,
                "placement_apply_ms": core_apply_us // 1_000,
                "handle_bind_us": handle_bind_us,
                "handle_bind_ms": handle_bind_us // 1_000,
                "durable_readback_us": durable_readback_us,
            },
        }

    def _durable_readback(self, statement: MemoryStatement, result: object) -> dict[str, object]:
        if type(result) is not AtomHandle:
            raise RuntimeError("applied placement did not return an AtomHandle")
        statement_store = FileStatementStore(self._workspace)
        persisted = statement_store.get(statement.statement_id)
        if persisted != statement:
            raise RuntimeError("durable Statement readback mismatch")
        binding = FileHandleStore(self._workspace).binding_for_handle(result)
        statement_is_bound = (
            binding.current_statement_id == statement.statement_id
            or statement.statement_id in binding.supporting_statement_ids
        )
        if not statement_is_bound:
            raise RuntimeError("durable HandleBinding readback mismatch")
        current = statement_store.get(binding.current_statement_id)
        with CoreRuntime(self._workspace) as core:
            atom = core.get(result)
        if atom.payload_utf8 != current.content_utf8:
            raise RuntimeError("durable Core Atom readback mismatch")
        return {
            "verified": True,
            "reopen_verified": True,
            "statement_id": statement.statement_id,
            "current_statement_id": binding.current_statement_id,
            "atom_id": atom.atom_id,
            "handle": result.to_mapping(),
        }

    def _provisional_revision(
        self,
        statement: MemoryStatement,
        decision: AccessDecision,
        selected: dict[str, object] | None,
    ) -> ProvisionalRevisionDecision:
        if decision.existing_handle is None or selected is None:
            raise AssertionError("revision decision must bind one existing Handle")
        handle_store = FileHandleStore(self._workspace)
        statement_store = FileStatementStore(self._workspace)
        binding = handle_store.binding_for_handle(decision.existing_handle)
        current = statement_store.get(binding.current_statement_id)
        return ProvisionalRevisionDecision.create(
            statement.statement_id,
            current.statement_id,
            selected["candidate_id"],
            decision.existing_handle,
            statement.content_utf8,
            current.content_utf8,
        )

    @classmethod
    def _excluded_revision_target_keys(cls, value: object) -> frozenset[tuple[object, ...]]:
        if value is None:
            return frozenset()
        if type(value) is not list or len(value) > 1:
            raise TypeError("excluded_revision_targets must be a list with at most one Handle")
        try:
            return frozenset(cls._handle_key(AtomHandle.from_mapping(item).to_mapping()) for item in value)
        except (KeyError, TypeError, ValueError) as exc:
            raise TypeError("excluded revision target is invalid") from exc

    def binding(self, statement_id: str) -> dict[str, object]:
        if type(statement_id) is not str or not statement_id:
            raise ValueError("statement_id is required")
        with self._runtime() as access:
            handle = access.saved_handle(statement_id)
            return access.handle_store.binding_for_handle(handle).to_mapping()

    def verify_admitted_statements(self, statement_ids: object) -> dict[str, object]:
        self._require_open()
        if type(statement_ids) is not list or not statement_ids:
            raise TypeError("statement_ids must be a non-empty string list")
        if any(type(statement_id) is not str or not statement_id for statement_id in statement_ids):
            raise TypeError("statement_ids must be a non-empty string list")
        if len(statement_ids) != len(set(statement_ids)):
            raise ValueError("statement_ids must be unique")
        statements = FileStatementStore(self._workspace)
        handles = FileHandleStore(self._workspace)
        verified = []
        with CoreRuntime(self._workspace) as core:
            for statement_id in statement_ids:
                statement = statements.get(statement_id)
                handle = handles.get(statement_id)
                binding = handles.binding_for_handle(handle)
                current = statements.get(binding.current_statement_id)
                atom = core.get(handle)
                if atom.payload_utf8 != current.content_utf8:
                    raise RuntimeError(f"durable Core Atom readback mismatch: {statement_id}")
                verified.append(statement.statement_id)
        return {"status": "verified", "statement_ids": verified, "reopen_verified": True}

    def _decision(
        self,
        raw: object,
        statement: MemoryStatement,
        request_id: str,
        candidates: list[dict[str, object]],
    ) -> tuple[AccessDecision | None, str, dict[str, object] | None]:
        if type(raw) is not dict or raw.get("schema_version") != PLACEMENT_SCHEMA_VERSION or type(raw.get("outcome")) is not str:
            raise ValueError("invalid placement envelope")
        if raw["outcome"] == "defer":
            if set(raw) != {"schema_version", "outcome", "reason_text"} or type(raw["reason_text"]) is not str:
                raise ValueError("invalid deferred placement")
            return None, "defer", None
        if raw["outcome"] != "apply" or set(raw) != {"schema_version", "outcome", "decision"} or type(raw["decision"]) is not dict:
            raise ValueError("invalid placement outcome")
        value = raw["decision"]
        if value.get("statement_id") != statement.statement_id or type(value.get("action")) is not str or type(value.get("candidate_id")) is not str or type(value.get("reason_text")) is not str:
            raise ValueError("decision does not bind the formed statement and candidate")
        by_id = {item["candidate_id"]: item for item in candidates}
        try:
            selected = by_id[value["candidate_id"]]
        except KeyError as exc:
            raise ValueError("decision selected an unavailable candidate") from exc
        action = value["action"]
        if action in {"new_local", "expand_surface"}:
            if set(value) != {"statement_id", "action", "candidate_id", "reason_text"}:
                raise ValueError("new placement contains unrelated fields")
            if action == "expand_surface" and selected["relation_kind"] != "expand_surface":
                raise ValueError("expand_surface requires the frontier candidate")
            if action == "new_local" and selected["relation_kind"] not in {"existing_cell", "lateral_ring_1"}:
                raise ValueError("new_local requires a selected locality")
            occupancy = selected.get("occupancy")
            if type(occupancy) is not dict or type(occupancy.get("count")) is not int:
                raise ValueError("candidate occupancy is invalid")
            if selected["relation_kind"] != "existing_cell" and occupancy["count"] != 0:
                raise ValueError("new placement selected an occupied candidate")
            target = GeometryAddress.from_mapping(selected["geometry_address"])
            return AccessDecision(
                f"placement:{request_id}:{statement.statement_id}",
                statement.statement_id,
                "new",
                target,
                None,
                None,
                value["reason_text"],
                "llm",
            ), action, selected
        if action not in {"reuse", "revision_current"} or set(value) != {"statement_id", "action", "candidate_id", "existing_handle", "reason_text"}:
            raise ValueError("unknown or malformed candidate placement action")
        handle = AtomHandle.from_mapping(value["existing_handle"])
        available_handles = {
            self._handle_key(item)
            for item in selected["existing_handles"]
            if type(item) is dict
        }
        if self._handle_key(handle.to_mapping()) not in available_handles:
            raise ValueError("existing handle is not available in the selected candidate")
        return AccessDecision(
            f"placement:{request_id}:{statement.statement_id}",
            statement.statement_id,
            action,
            None,
            handle,
            None,
            value["reason_text"],
            "llm",
        ), action, selected

    @staticmethod
    def _candidate(
        core: CoreRuntime,
        candidate_id: str,
        relation_kind: str,
        address: GeometryAddress,
    ) -> dict[str, object]:
        ACTIVE_SEMANTIC_WRITE_POLICY.validate(address)
        handles = [handle.to_mapping() for handle, _atom in core.atoms_at(address)]
        return {
            "candidate_id": candidate_id,
            "relation_kind": relation_kind,
            "geometry_address": address.to_mapping(),
            "occupancy": {"count": len(handles), "band": core.occupancy_band(address)},
            "existing_handles": handles,
        }

    @staticmethod
    def _expand_surface_frontier(
        scope: PhysicalFieldScope,
        occupied: tuple[GeometryAddress, ...],
    ) -> GeometryAddress:
        origin = GeometryAddress(scope.profile_id, scope.chart_id, scope.reference_layer, 0, 0)
        if not occupied:
            return origin
        for ring in range(1, _MAX_FRONTIER_RADIUS + 1):
            for candidate in sorted(origin.lateral(ring), key=lambda item: item.stable_key()):
                if all(
                    AccessMemoryLoop._physical_distance_squared_q32(candidate, cell)
                    >= _MIN_FRONTIER_DISTANCE_SQUARED_Q32
                    for cell in occupied
                ):
                    return candidate
        raise RuntimeError("no bounded Surface frontier is available")

    @staticmethod
    def _physical_distance_squared_q32(left: GeometryAddress, right: GeometryAddress) -> int:
        if (
            left.profile_id != "default_dream_v1"
            or right.profile_id != "default_dream_v1"
            or left.chart_id != right.chart_id
            or left.layer != 0
            or right.layer != 0
        ):
            raise ValueError("frontier distance requires one default_dream_v1 layer 0 physical plane")
        dq, dr = left.q - right.q, left.r - right.r
        # Pointy-top axial centers: distance^2 = 3 * (dq^2 + dq*dr + dr^2) * s0^2.
        return 3 * (dq * dq + dq * dr + dr * dr) * _Q32_ONE

    @staticmethod
    def _handle_key(value: dict[str, object]) -> tuple[object, ...]:
        address = value["geometry_address"]
        if type(address) is not dict:
            raise TypeError("handle geometry address must be an object")
        return (
            address.get("profile_id"),
            address.get("chart_id"),
            address.get("layer"),
            address.get("q"),
            address.get("r"),
            address.get("phase"),
            value.get("local_atom_id"),
        )

    @staticmethod
    def _cell(value: object) -> GeometryAddress:
        if type(value) is GeometryAddress:
            return value
        return GeometryAddress.from_mapping(value)

    @staticmethod
    def _require_request(request_id: str) -> None:
        if type(request_id) is not str or not request_id:
            raise ValueError("request_id is required")

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("AccessMemoryLoop is closed")

    def _runtime(self):
        self._require_open()
        core = CoreRuntime(self._workspace)
        try:
            access = AccessRuntime(core, FileStatementStore(self._workspace), FileHandleStore(self._workspace))
        except Exception:
            core.close()
            raise

        class _RuntimeContext:
            def __enter__(self_inner) -> AccessRuntime:
                return access

            def __exit__(self_inner, *_args: object) -> None:
                access.close()
                core.close()

        return _RuntimeContext()
