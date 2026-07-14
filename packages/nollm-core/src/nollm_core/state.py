from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import RLock

from .atom import MemoryAtom
from .bridge import BridgeSpec
from .command import (
    BridgeAddCommand,
    BridgeRemoveCommand,
    CoreCommand,
    MoveCommand,
    PutCommand,
    RemoveCommand,
    ReplaceCommand,
)
from .geometry import GeometryAddress
from .handle import AtomHandle
from .kernel_registry import KernelRegistry
from .ports import CoreTraceEvent, TraceSink
from .storage import SCHEMA_VERSION, _FileCoreStateStore, canonical_state_bytes
from .surface import (
    CoverageDescentPage,
    SurfaceOrderInfo,
    SurfacePage,
    SurfacePlane,
    build_surface_orders,
    descent_page,
    order_info,
    surface_page,
)
from .workspace_owner import claim, release


class _CellStore:
    def __init__(self, cells: dict[GeometryAddress, dict[str, MemoryAtom]] | None = None) -> None:
        self._cells = cells if cells is not None else {}

    def atoms_at(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        atoms = self._cells.get(address, {})
        return tuple((AtomHandle(address, local_id), atoms[local_id]) for local_id in sorted(atoms))

    def occupied_cells(self) -> tuple[GeometryAddress, ...]:
        return tuple(sorted(self._cells, key=lambda cell: cell.stable_key()))

    def placement_count(self) -> int:
        return sum(len(atoms) for atoms in self._cells.values())

    def density_state(self, address: GeometryAddress) -> str:
        count = len(self.atoms_at(address))
        return "overloaded" if count >= 32 else "dense" if count >= 8 else "normal"


class CoreRuntime:
    """Deterministic geometry current state with atomic file persistence."""

    def __init__(self, workspace: Path, *, trace_sink: TraceSink | None = None) -> None:
        self._workspace = Path(workspace).resolve()
        self._state_path = self._workspace / "core" / "current_state.json"
        self._trace_sink = trace_sink
        self._lock = RLock()
        self._state = "OPEN"
        self._kernel_registry = KernelRegistry()
        self._owner_key = claim(self._state_path, self)
        self._store = _FileCoreStateStore(self._workspace, self._validate_state_bytes)
        try:
            if self._store.exists():
                self._cells, self._bridges = self._decode_state_bytes(self._store.read_bytes())
            else:
                self._cells = {}
                self._bridges = {}
                self._store.write_document(self._document(self._cells, self._bridges))
        except Exception:
            self._state = "CLOSED"
            release(self._owner_key, self)
            raise
        self._cell_store = _CellStore(self._cells)

    def close(self) -> None:
        with self._lock:
            if self._state == "CLOSED":
                return
            release(self._owner_key, self)
            self._state = "CLOSED"

    def __enter__(self) -> "CoreRuntime":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def state_path(self) -> Path:
        return self._state_path

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._state == "OPEN"

    @property
    def lifecycle_state(self) -> str:
        with self._lock:
            return self._state

    @property
    def kernel_registry(self) -> KernelRegistry:
        return self._kernel_registry

    @contextmanager
    def _operation(self):
        with self._lock:
            if self._state != "OPEN":
                raise RuntimeError("CoreRuntime is closed")
            yield

    def _emit_trace(self, event: CoreTraceEvent) -> None:
        if self._trace_sink is None:
            return
        try:
            self._trace_sink.emit(event)
        except Exception:
            return

    def put(self, atom: MemoryAtom, target_cell: GeometryAddress) -> AtomHandle:
        return self.apply_batch((PutCommand(atom, target_cell),))[0]

    def remove(self, handle: AtomHandle) -> MemoryAtom:
        return self.apply_batch((RemoveCommand(handle),))[0]

    def replace(self, handle: AtomHandle, new_payload_utf8: str) -> AtomHandle:
        return self.apply_batch((ReplaceCommand(handle, new_payload_utf8),))[0]

    def move(self, handle: AtomHandle, target_cell: GeometryAddress) -> AtomHandle:
        return self.apply_batch((MoveCommand(handle, target_cell),))[0]

    def bridge_add(self, spec: BridgeSpec) -> BridgeSpec:
        return self.apply_batch((BridgeAddCommand(spec),))[0]

    def bridge_remove(self, bridge_id: str) -> BridgeSpec:
        return self.apply_batch((BridgeRemoveCommand(bridge_id),))[0]

    def apply_batch(self, commands: tuple[CoreCommand, ...]) -> tuple[object, ...]:
        with self._operation():
            return self._apply_batch_locked(commands)

    def _apply_batch_locked(self, commands: tuple[CoreCommand, ...]) -> tuple[object, ...]:
        if type(commands) is not tuple or not commands:
            raise ValueError("batch must contain at least one command")
        cells = {address: dict(atoms) for address, atoms in self._cells.items()}
        bridges = dict(self._bridges)
        results: list[object] = []
        events: list[CoreTraceEvent] = []
        self._emit_trace(CoreTraceEvent("core.batch.begin", {"command_count": len(commands)}, "stable"))
        try:
            for command in commands:
                result, event = self._apply(command, cells, bridges)
                results.append(result)
                events.append(event)
            self._store.write_document(self._document(cells, bridges))
        except Exception:
            self._emit_trace(CoreTraceEvent("core.batch.rollback", {"command_count": len(commands)}, "stable"))
            raise
        self._cells = cells
        self._bridges = bridges
        self._cell_store = _CellStore(self._cells)
        for event in events:
            self._emit_trace(event)
        self._emit_trace(CoreTraceEvent("core.batch.commit", {"command_count": len(commands)}, "stable"))
        return tuple(results)

    def get(self, handle: AtomHandle) -> MemoryAtom:
        with self._operation():
            return self._require_handle(handle, self._cells)

    def contains(self, handle: AtomHandle) -> bool:
        with self._operation():
            try:
                self._require_handle(handle, self._cells)
            except KeyError:
                return False
            return True

    def atoms_at(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        with self._operation():
            return self._cell_store.atoms_at(address)

    def occupied_cells(self) -> tuple[GeometryAddress, ...]:
        with self._operation():
            return self._cell_store.occupied_cells()

    def bridges(self) -> tuple[BridgeSpec, ...]:
        with self._operation():
            return self._bridges_locked()

    def placement_count(self) -> int:
        with self._operation():
            return self._cell_store.placement_count()

    def density_state(self, address: GeometryAddress) -> str:
        with self._operation():
            return self._cell_store.density_state(address)

    def recall(self, request: object) -> object:
        with self._operation():
            from .recall import CoreRecallRequest, resolve_recall

            if type(request) is not CoreRecallRequest:
                raise TypeError("request must be CoreRecallRequest")
            return resolve_recall(self, request)

    def surface_orders(self, plane: SurfacePlane, max_order: int) -> tuple[SurfaceOrderInfo, ...]:
        with self._operation():
            orders = self._surface_orders_locked(plane, max_order)
            return tuple(order_info(plane, records, order) for order, records in enumerate(orders))

    def surface_page(
        self,
        plane: SurfacePlane,
        order: int,
        after: GeometryAddress | None,
        limit: int,
    ) -> SurfacePage:
        with self._operation():
            orders = self._surface_orders_locked(plane, order)
            return surface_page(plane, order, orders[order], after, limit)

    def surface_descend(
        self,
        plane: SurfacePlane,
        parent_order: int,
        parent_address: GeometryAddress,
        after: GeometryAddress | None,
        limit: int,
    ) -> CoverageDescentPage:
        with self._operation():
            orders = self._surface_orders_locked(plane, parent_order)
            return descent_page(plane, parent_order, parent_address, orders, after, limit)

    def export_state_bytes(self) -> bytes:
        with self._operation():
            payload = self._state_bytes_locked()
            self._emit_trace(CoreTraceEvent("core.state.export", {"size_bytes": len(payload)}, "stable"))
            return payload

    def import_state_bytes(self, payload: bytes) -> None:
        with self._operation():
            cells, bridges = self._decode_state_bytes(payload)
            self._store.write_bytes(payload)
            self._cells = cells
            self._bridges = bridges
            self._cell_store = _CellStore(self._cells)
            self._emit_trace(CoreTraceEvent("core.state.import", {"size_bytes": len(payload)}, "stable"))

    def _state_bytes_locked(self) -> bytes:
        return canonical_state_bytes(self._document(self._cells, self._bridges))

    def _surface_orders_locked(self, plane: SurfacePlane, max_order: int):
        if type(plane) is not SurfacePlane:
            raise TypeError("plane must be SurfacePlane")
        occupancy = {address: len(atoms) for address, atoms in self._cells.items()}
        endpoints = frozenset(
            cell
            for bridge in self._bridges.values()
            for anchor in (bridge.from_anchor, bridge.to_anchor)
            for cell in anchor.cells
        )
        return build_surface_orders(plane, max_order, occupancy, endpoints, self._kernel_registry)

    def _atoms_at_locked(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        return self._cell_store.atoms_at(address)

    def _bridges_locked(self) -> tuple[BridgeSpec, ...]:
        return tuple(self._bridges[key] for key in sorted(self._bridges))

    def _apply(
        self,
        command: CoreCommand,
        cells: dict[GeometryAddress, dict[str, MemoryAtom]],
        bridges: dict[str, BridgeSpec],
    ) -> tuple[object, CoreTraceEvent]:
        if type(command) is PutCommand:
            local_id = command.atom.atom_id
            values = cells.setdefault(command.target_cell, {})
            if local_id in values:
                raise FileExistsError("local atom already exists at target cell")
            values[local_id] = command.atom
            handle = AtomHandle(command.target_cell, local_id)
            return handle, self._handle_event("core.put", handle)
        if type(command) is RemoveCommand:
            atom = self._require_handle(command.handle, cells)
            del cells[command.handle.geometry_address][command.handle.local_atom_id]
            if not cells[command.handle.geometry_address]:
                del cells[command.handle.geometry_address]
            return atom, self._handle_event("core.remove", command.handle)
        if type(command) is ReplaceCommand:
            old = self._require_handle(command.handle, cells)
            cells[command.handle.geometry_address][command.handle.local_atom_id] = MemoryAtom(old.atom_id, command.new_payload_utf8)
            return command.handle, self._handle_event("core.replace", command.handle)
        if type(command) is MoveCommand:
            atom = self._require_handle(command.handle, cells)
            if command.target_cell == command.handle.geometry_address:
                return command.handle, self._handle_event("core.move", command.handle)
            target_values = cells.setdefault(command.target_cell, {})
            if command.handle.local_atom_id in target_values:
                raise FileExistsError("local atom already exists at target cell")
            del cells[command.handle.geometry_address][command.handle.local_atom_id]
            if not cells[command.handle.geometry_address]:
                del cells[command.handle.geometry_address]
            target_values[command.handle.local_atom_id] = atom
            handle = AtomHandle(command.target_cell, command.handle.local_atom_id)
            return handle, self._handle_event("core.move", handle)
        if type(command) is BridgeAddCommand:
            if command.spec.bridge_id in bridges:
                raise FileExistsError("bridge already exists")
            bridges[command.spec.bridge_id] = command.spec
            return command.spec, CoreTraceEvent("core.bridge.add", {"bridge_id": command.spec.bridge_id}, "stable")
        if type(command) is BridgeRemoveCommand:
            try:
                spec = bridges.pop(command.bridge_id)
            except KeyError as error:
                raise KeyError("bridge does not exist") from error
            return spec, CoreTraceEvent("core.bridge.remove", {"bridge_id": command.bridge_id}, "stable")
        raise TypeError("unsupported Core command")

    @staticmethod
    def _handle_event(name: str, handle: AtomHandle) -> CoreTraceEvent:
        return CoreTraceEvent(
            name,
            {
                "profile_id": handle.geometry_address.profile_id,
                "chart_id": handle.geometry_address.chart_id,
                "layer": handle.geometry_address.layer,
                "q": handle.geometry_address.q,
                "r": handle.geometry_address.r,
                "phase": handle.geometry_address.phase,
                "local_atom_id": handle.local_atom_id,
            },
            "stable",
        )

    @staticmethod
    def _require_handle(handle: AtomHandle, cells: dict[GeometryAddress, dict[str, MemoryAtom]]) -> MemoryAtom:
        if type(handle) is not AtomHandle:
            raise TypeError("mutation requires AtomHandle")
        try:
            return cells[handle.geometry_address][handle.local_atom_id]
        except KeyError as error:
            raise KeyError("AtomHandle does not exist") from error

    def _document(self, cells: dict[GeometryAddress, dict[str, MemoryAtom]], bridges: dict[str, BridgeSpec]) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "geometry_registry": self.kernel_registry.state_identity,
            "cells": [
                {
                    "address": address.to_mapping(),
                    "atoms": [
                        {"local_atom_id": local_id, "atom": atoms[local_id].to_mapping()}
                        for local_id in sorted(atoms)
                    ],
                }
                for address, atoms in sorted(cells.items(), key=lambda item: item[0].stable_key())
            ],
            "bridges": [bridges[key].to_mapping() for key in sorted(bridges)],
        }

    def _decode(self, document: dict[str, object]) -> tuple[dict[GeometryAddress, dict[str, MemoryAtom]], dict[str, BridgeSpec]]:
        if type(document) is not dict or frozenset(document) != frozenset({"schema_version", "geometry_registry", "cells", "bridges"}):
            raise ValueError("Core state fields are not canonical")
        if document["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported Core state schema")
        if document["geometry_registry"] != self.kernel_registry.state_identity:
            raise ValueError("Core state geometry registry mismatch")
        if type(document["cells"]) is not list or type(document["bridges"]) is not list:
            raise TypeError("Core cells and bridges must be arrays")
        cells: dict[GeometryAddress, dict[str, MemoryAtom]] = {}
        for cell in document["cells"]:
            if type(cell) is not dict or frozenset(cell) != frozenset({"address", "atoms"}) or type(cell["atoms"]) is not list:
                raise ValueError("invalid Core cell record")
            address = GeometryAddress.from_mapping(cell["address"])
            if address in cells:
                raise ValueError("duplicate cell address")
            atoms: dict[str, MemoryAtom] = {}
            for item in cell["atoms"]:
                if type(item) is not dict or frozenset(item) != frozenset({"local_atom_id", "atom"}) or type(item["local_atom_id"]) is not str:
                    raise ValueError("invalid Core atom record")
                local_id = item["local_atom_id"]
                if local_id in atoms:
                    raise ValueError("duplicate local atom id")
                atom = MemoryAtom.from_mapping(item["atom"])
                if atom.atom_id != local_id:
                    raise ValueError("local atom identity mismatch")
                atoms[local_id] = atom
            if not atoms:
                raise ValueError("empty cells are not canonical Core state")
            cells[address] = atoms
        bridges: dict[str, BridgeSpec] = {}
        for value in document["bridges"]:
            bridge = BridgeSpec.from_mapping(value)
            if bridge.bridge_id in bridges:
                raise ValueError("duplicate bridge id")
            bridges[bridge.bridge_id] = bridge
        return cells, bridges

    @staticmethod
    def _decode_document(payload: bytes) -> dict[str, object]:
        import json

        if type(payload) is not bytes:
            raise TypeError("Core state payload must be bytes")
        value = json.loads(payload.decode("utf-8"))
        if canonical_state_bytes(value) != payload:
            raise ValueError("snapshot bytes must be canonical Core state")
        return value

    def _decode_state_bytes(self, payload: bytes) -> tuple[dict[GeometryAddress, dict[str, MemoryAtom]], dict[str, BridgeSpec]]:
        document = self._decode_document(payload)
        cells, bridges = self._decode(document)
        if canonical_state_bytes(self._document(cells, bridges)) != payload:
            raise ValueError("Core state semantic order is not canonical")
        return cells, bridges

    def _validate_state_bytes(self, payload: bytes) -> None:
        self._decode_state_bytes(payload)
