from __future__ import annotations

from pathlib import Path

from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, RecallBudget

from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallRequest
from .runtime import AccessRuntime
from .statement import MemoryStatement
from .statement_store import FileStatementStore


_CLUSTER_RECALL_BUDGET = RecallBudget(1, 12, 0, 1, 0, 16)
_CLUSTER_RECALL_KERNELS = ("lateral",)
_CLUSTER_SPACING = 8
_MIN_CLUSTER_DISTANCE = 4
_MAX_CLUSTER_ANCHORS = 4
_MAX_ENTRY_CELLS = 8
_MAX_CLUSTER_SLOTS = 1024


class AccessMemoryLoop:
    """Access-owned bounded geometry placement and recall orchestration."""

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

    def cursor_cells(self, raw_cells: object, *, limit: int = _MAX_ENTRY_CELLS) -> list[dict[str, object]]:
        if type(raw_cells) is not list or type(limit) is not int or limit < 1:
            raise TypeError("cursor cells must be a list and limit must be positive")
        cells = tuple(GeometryAddress.from_mapping(item) for item in raw_cells)
        if len(cells) > limit or len(set(cells)) != len(cells):
            raise ValueError("cursor cells must be unique and bounded")
        return [cell.to_mapping() for cell in cells]

    def placement_candidates(
        self,
        cluster_anchors: object,
        entry_cells: object,
        request_id: str,
    ) -> list[dict[str, object]]:
        """Return finite addresses derived only from cursor geometry and Core state."""
        self._require_request(request_id)
        anchors = self._cells(cluster_anchors, _MAX_CLUSTER_ANCHORS)
        self._cells(entry_cells, _MAX_ENTRY_CELLS)
        with CoreRuntime(self._workspace) as core:
            occupied = core.occupied_cells()
            local_anchor = anchors[-1] if anchors else None
            candidates: list[dict[str, object]] = []
            if local_anchor is not None:
                candidates.append(self._candidate(core, "existing_cell:0", "existing_cell", local_anchor, local_anchor))
                for index, address in enumerate(local_anchor.lateral(1)):
                    candidates.append(self._candidate(core, f"lateral_ring_1:{index}", "lateral_ring_1", address, local_anchor))
            new_anchor = self._allocate_cluster_anchor(occupied, local_anchor)
            candidates.append(self._candidate(core, "new_cluster:0", "new_cluster", new_anchor, new_anchor))
        if len(candidates) > 8 or len({item["candidate_id"] for item in candidates}) != len(candidates):
            raise AssertionError("placement candidates must be unique and bounded")
        return candidates

    def candidate_statement_context(self, candidates: object) -> list[dict[str, object]]:
        """Attach bounded statement summaries after geometry selection is complete."""
        if type(candidates) is not list or len(candidates) > 8:
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
                    statement_id = handle_store.statement_for_handle(handle)
                    statement = statement_store.get(statement_id)
                except (KeyError, FileNotFoundError):
                    continue
                statements.append({
                    "statement_id": statement.statement_id,
                    "content_utf8": statement.content_utf8,
                    "handle": handle.to_mapping(),
                })
            context.append({"candidate_id": candidate["candidate_id"], "statements": statements})
        return context

    def per_anchor_context(self, cluster_anchors: object, request_id: str) -> list[dict[str, object]]:
        self._require_request(request_id)
        anchors = self._cells(cluster_anchors, _MAX_CLUSTER_ANCHORS)
        if not anchors:
            return []
        results = []
        with self._runtime() as access:
            for index, anchor in enumerate(anchors):
                recalled = access.recall(AccessRecallRequest(
                    f"{request_id}:anchor:{index}",
                    (anchor,),
                    (),
                    _CLUSTER_RECALL_KERNELS,
                    _CLUSTER_RECALL_BUDGET,
                ))
                results.append({
                    "anchor": anchor.to_mapping(),
                    "statements": [self._recall_item(item) for item in recalled.items if item.evidence_utf8 is not None],
                    "budget_exhausted": recalled.budget_exhausted,
                })
        return results

    def local_context(self, cursor_cells: object, request_id: str) -> list[dict[str, object]]:
        """Compatibility-sized public view over independent per-entry recalls."""
        groups = self.per_anchor_context(cursor_cells, request_id)
        selected: dict[str, dict[str, object]] = {}
        for group in groups:
            for item in group["statements"]:
                selected.setdefault(item["statement_id"], item)
        return list(selected.values())

    def apply_placement(
        self,
        statement: MemoryStatement,
        placement: object,
        request_id: str,
        cluster_anchors: object = None,
        entry_cells: object = None,
    ) -> dict[str, object]:
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        self._require_request(request_id)
        anchors = [] if cluster_anchors is None else cluster_anchors
        entries = [] if entry_cells is None else entry_cells
        candidates = self.placement_candidates(anchors, entries, request_id + ":candidates")
        decision, public_action, selected = self._decision(placement, statement, request_id, candidates)
        if decision is None:
            return {"outcome": "defer", "statement_id": statement.statement_id, "core_write_count": 0}
        statement_store = FileStatementStore(self._workspace)
        existed_before = statement_store.exists(statement.statement_id)
        with self._runtime() as access:
            access.capture(statement)
            try:
                result = access.apply(decision)
            except Exception:
                if not existed_before:
                    statement_store.discard_new(statement)
                raise
        return {
            "outcome": "applied",
            "statement_id": statement.statement_id,
            "action": public_action,
            "candidate_id": selected["candidate_id"] if selected is not None else None,
            "cluster_anchor": selected["cluster_anchor"] if selected is not None else None,
            "handle": result.to_mapping() if type(result) is AtomHandle else None,
            "core_write_count": 1 if public_action in {"new_local", "new_cluster", "revision_current"} else 0,
        }

    def binding(self, statement_id: str) -> dict[str, object]:
        if type(statement_id) is not str or not statement_id:
            raise ValueError("statement_id is required")
        with self._runtime() as access:
            handle = access.saved_handle(statement_id)
            return access.handle_store.binding_for_handle(handle).to_mapping()

    def _decision(
        self,
        raw: object,
        statement: MemoryStatement,
        request_id: str,
        candidates: list[dict[str, object]],
    ) -> tuple[AccessDecision | None, str, dict[str, object] | None]:
        if type(raw) is not dict or raw.get("schema_version") != "nollm_openclaw_placement_v2" or type(raw.get("outcome")) is not str:
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
        if action in {"new_local", "new_cluster"}:
            if set(value) != {"statement_id", "action", "candidate_id", "reason_text"}:
                raise ValueError("new placement contains unrelated fields")
            if (action == "new_cluster") != (selected["relation_kind"] == "new_cluster"):
                raise ValueError("placement action does not match candidate relation")
            if action == "new_local" and selected["relation_kind"] not in {"existing_cell", "lateral_ring_1"}:
                raise ValueError("local placement requires a local candidate")
            occupancy = selected.get("occupancy")
            if type(occupancy) is not dict or type(occupancy.get("count")) is not int:
                raise ValueError("candidate occupancy is invalid")
            if selected["relation_kind"] != "existing_cell" and occupancy["count"] != 0:
                raise ValueError("new placement selected an occupied candidate")
            target = GeometryAddress.from_mapping(selected["geometry_address"])
            decision = AccessDecision(
                f"placement:{request_id}:{statement.statement_id}", statement.statement_id,
                "new", target, None, None, value["reason_text"], "llm",
            )
            return decision, action, selected
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
        decision = AccessDecision(
            f"placement:{request_id}:{statement.statement_id}", statement.statement_id,
            action, None, handle, None, value["reason_text"], "llm",
        )
        return decision, action, selected

    def _candidate(
        self,
        core: CoreRuntime,
        candidate_id: str,
        relation_kind: str,
        address: GeometryAddress,
        cluster_anchor: GeometryAddress,
    ) -> dict[str, object]:
        handles = [handle.to_mapping() for handle, _atom in core.atoms_at(address)]
        return {
            "candidate_id": candidate_id,
            "relation_kind": relation_kind,
            "geometry_address": address.to_mapping(),
            "cluster_anchor": cluster_anchor.to_mapping(),
            "occupancy": {"count": len(handles), "density_state": core.density_state(address)},
            "existing_handles": handles,
        }

    @staticmethod
    def _allocate_cluster_anchor(
        occupied: tuple[GeometryAddress, ...],
        local_anchor: GeometryAddress | None,
    ) -> GeometryAddress:
        profile_id = local_anchor.profile_id if local_anchor is not None else "eisenstein_exact_v1"
        chart_id = local_anchor.chart_id if local_anchor is not None else "default"
        layer = local_anchor.layer if local_anchor is not None else 0
        phase = local_anchor.phase if local_anchor is not None else None
        same_plane = tuple(cell for cell in occupied if (cell.profile_id, cell.chart_id, cell.layer, cell.phase) == (profile_id, chart_id, layer, phase))
        for index in range(_MAX_CLUSTER_SLOTS):
            candidate = GeometryAddress(profile_id, chart_id, layer, index * _CLUSTER_SPACING, 0, phase)
            if all(AccessMemoryLoop._distance(candidate, cell) >= _MIN_CLUSTER_DISTANCE for cell in same_plane):
                return candidate
        raise RuntimeError("no bounded new_cluster anchor is available")

    @staticmethod
    def _distance(left: GeometryAddress, right: GeometryAddress) -> int:
        dq, dr = left.q - right.q, left.r - right.r
        return max(abs(dq), abs(dr), abs(dq + dr))

    @staticmethod
    def _handle_key(value: dict[str, object]) -> tuple[object, ...]:
        address = value["geometry_address"]
        if type(address) is not dict:
            raise TypeError("handle geometry address must be an object")
        return (
            address.get("profile_id"), address.get("chart_id"), address.get("layer"),
            address.get("q"), address.get("r"), address.get("phase"), value.get("local_atom_id"),
        )

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

    def _cells(self, raw_cells: object, limit: int) -> tuple[GeometryAddress, ...]:
        mapped = self.cursor_cells(raw_cells, limit=limit)
        return tuple(GeometryAddress.from_mapping(item) for item in mapped)

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
