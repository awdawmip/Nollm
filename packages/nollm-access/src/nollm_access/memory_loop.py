from __future__ import annotations

from pathlib import Path

from nollm_core import AtomHandle, CoreRuntime, GeometryAddress, SurfacePlane

from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .runtime import AccessRuntime
from .statement import MemoryStatement
from .statement_store import FileStatementStore
from .surface_navigation import AccessSurfaceNavigator


PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_surface_placement_v1"
DEFAULT_SURFACE_PLANE = SurfacePlane("eisenstein_exact_v1", "default", None, 0)
_MIN_FRONTIER_DISTANCE = 4
_MAX_FRONTIER_RADIUS = 1024


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
        plane: SurfacePlane = DEFAULT_SURFACE_PLANE,
    ) -> list[dict[str, object]]:
        self._require_request(request_id)
        if type(plane) is not SurfacePlane:
            raise TypeError("plane must be SurfacePlane")
        entry = None if selected_entry is None else self._cell(selected_entry)
        if entry is not None and not plane.contains(entry):
            raise ValueError("selected_entry must belong to the Surface Plane")
        with CoreRuntime(self._workspace) as core:
            occupied = tuple(cell for cell in core.occupied_cells() if plane.contains(cell))
            candidates: list[dict[str, object]] = []
            if entry is not None:
                candidates.append(self._candidate(core, "placement:existing:0", "existing_cell", entry))
                for index, address in enumerate(entry.lateral(1)):
                    candidates.append(self._candidate(core, f"placement:lateral:{index}", "lateral_ring_1", address))
            frontier = self._expand_surface_frontier(plane, occupied)
            candidates.append(self._candidate(core, "placement:expand:0", "expand_surface", frontier))
        if len(candidates) > 8 or len({item["candidate_id"] for item in candidates}) != len(candidates):
            raise AssertionError("placement candidates must be unique and bounded")
        return candidates

    def candidate_statement_context(self, candidates: object) -> list[dict[str, object]]:
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

    def local_context(self, entry_cells: object, request_id: str) -> list[dict[str, object]]:
        self._require_request(request_id)
        if type(entry_cells) is not list:
            raise TypeError("entry_cells must be a list")
        cells = tuple(sorted((self._cell(item) for item in entry_cells), key=lambda item: item.stable_key()))
        if not cells:
            return []
        result = self.navigator().recall_entries(request_id, cells, 3)
        return list(result.items)

    def apply_placement(
        self,
        statement: MemoryStatement,
        placement: object,
        request_id: str,
        selected_entry: object = None,
        plane: SurfacePlane = DEFAULT_SURFACE_PLANE,
    ) -> dict[str, object]:
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        self._require_request(request_id)
        candidates = self.placement_candidates(selected_entry, request_id + ":candidates", plane)
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
            "handle": result.to_mapping() if type(result) is AtomHandle else None,
            "core_write_count": 1 if public_action in {"new_local", "expand_surface", "revision_current"} else 0,
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
        handles = [handle.to_mapping() for handle, _atom in core.atoms_at(address)]
        return {
            "candidate_id": candidate_id,
            "relation_kind": relation_kind,
            "geometry_address": address.to_mapping(),
            "occupancy": {"count": len(handles), "density_state": core.density_state(address)},
            "existing_handles": handles,
        }

    @staticmethod
    def _expand_surface_frontier(
        plane: SurfacePlane,
        occupied: tuple[GeometryAddress, ...],
    ) -> GeometryAddress:
        origin = GeometryAddress(plane.profile_id, plane.chart_id, plane.base_layer, 0, 0, plane.phase)
        if not occupied:
            return origin
        for ring in range(1, _MAX_FRONTIER_RADIUS + 1):
            for candidate in sorted(origin.lateral(ring), key=lambda item: item.stable_key()):
                if all(AccessMemoryLoop._distance(candidate, cell) >= _MIN_FRONTIER_DISTANCE for cell in occupied):
                    return candidate
        raise RuntimeError("no bounded Surface frontier is available")

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
