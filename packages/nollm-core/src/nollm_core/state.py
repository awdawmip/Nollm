from __future__ import annotations

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
from .ports import ConsistentStatePort, NullTraceSink, TraceEvent, TraceSink, safe_emit
from .storage import FileCoreStateStore, SCHEMA_VERSION, canonical_state_bytes
from .workspace_owner import claim, release


class CellStore:
    """Geometry-addressed local occupancy with no identity or source route."""

    def __init__(self, cells: dict[GeometryAddress, dict[str, MemoryAtom]] | None = None) -> None:
        self._cells = cells or {}

    def get(self, handle: AtomHandle) -> MemoryAtom:
        try:
            return self._cells[handle.geometry_address][handle.local_atom_id]
        except KeyError as error:
            raise KeyError("AtomHandle does not exist") from error

    def atoms_at(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        atoms = self._cells.get(address, {})
        return tuple((AtomHandle(address, local_id), atoms[local_id]) for local_id in sorted(atoms))

    def occupied_cells(self) -> tuple[GeometryAddress, ...]:
        self._require_open()
        return tuple(sorted(self._cells, key=lambda cell: cell.stable_key()))

    def placement_count(self) -> int:
        return sum(len(atoms) for atoms in self._cells.values())

    def density_state(self, address: GeometryAddress) -> str:
        count = len(self.atoms_at(address))
        return "overloaded" if count >= 32 else "dense" if count >= 8 else "normal"


class CoreRuntime(ConsistentStatePort):
    def __init__(
        self,
        workspace: Path,
        *,
        trace_sink: TraceSink | None = None,
        store: FileCoreStateStore | None = None,
        kernel_registry: KernelRegistry | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.trace_sink = trace_sink or NullTraceSink()
        self.store = store or FileCoreStateStore(self.workspace)
        self._closed = False
        self._owner_key = claim(self.store.path, self)
        self._kernel_registry = kernel_registry or KernelRegistry()
        self._lock = RLock()
        self._read_token: object | None = None
        try:
            self.store.bind_semantic_validator(self._validate_state_bytes)
            if self.store.exists():
                self._cells, self._bridges = self._decode_state_bytes(self.store.read_bytes())
            else:
                self._cells = {}
                self._bridges = {}
                self.store.write_document(self._document(self._cells, self._bridges))
        except Exception:
            release(self._owner_key,self)
            raise
        self.cells = CellStore(self._cells)

    def close(self) -> None:
        if self._closed: return
        if self._read_token is not None: raise RuntimeError("cannot close during consistent read")
        self._closed=True; release(self._owner_key,self)

    def __enter__(self) -> "CoreRuntime": return self
    def __exit__(self,*_args: object) -> None: self.close()

    def _require_open(self) -> None:
        if self._closed: raise RuntimeError("CoreRuntime is closed")

    def put(self, atom: MemoryAtom, target_cell: GeometryAddress) -> AtomHandle:
        self._require_open()
        return self.apply_batch((PutCommand(atom, target_cell),))[0]
    @property
    def kernel_registry(self) -> KernelRegistry:
        return self._kernel_registry


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
        self._require_open()
        if not commands:
            raise ValueError("batch must contain at least one command")
        with self._lock:
            cells = {address: dict(atoms) for address, atoms in self._cells.items()}
            bridges = dict(self._bridges)
            results: list[object] = []
            events: list[TraceEvent] = []
            safe_emit(self.trace_sink, TraceEvent("core.batch.begin", {"command_count": len(commands)}, "stable"))
            try:
                for command in commands:
                    result, event = self._apply(command, cells, bridges)
                    results.append(result)
                    events.append(event)
                self.store.write_document(self._document(cells, bridges))
            except Exception:
                safe_emit(self.trace_sink, TraceEvent("core.batch.rollback", {"command_count": len(commands)}, "stable"))
                raise
            self._cells = cells
            self._bridges = bridges
            self.cells = CellStore(self._cells)
            for event in events:
                safe_emit(self.trace_sink, event)
            safe_emit(self.trace_sink, TraceEvent("core.batch.commit", {"command_count": len(commands)}, "stable"))
            return tuple(results)

    def get(self, handle: AtomHandle) -> MemoryAtom:
        self._require_open()
        with self._lock:
            return self._require_handle(handle, self._cells)

    def contains(self, handle: AtomHandle) -> bool:
        try:
            self.get(handle)
        except KeyError:
            return False
        return True

    def atoms_at(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        self._require_open()
        with self._lock:
            return self.cells.atoms_at(address)

    def occupied_cells(self) -> tuple[GeometryAddress, ...]:
        with self._lock:
            return self.cells.occupied_cells()

    def bridges(self) -> tuple[BridgeSpec, ...]:
        self._require_open()
        with self._lock:
            return tuple(self._bridges[key] for key in sorted(self._bridges))

    def placement_count(self) -> int:
        self._require_open()
        with self._lock:
            return self.cells.placement_count()

    def density_state(self, address: GeometryAddress) -> str:
        self._require_open()
        with self._lock:
            return self.cells.density_state(address)

    def recall(self, request: object) -> object:
        from .recall import CoreRecallRequest, resolve_recall

        if not isinstance(request, CoreRecallRequest):
            raise TypeError("request must be CoreRecallRequest")
        self._require_open()
        with self._lock:
            return resolve_recall(self, request, self.trace_sink)

    def state_bytes(self) -> bytes:
        self._require_open()
        with self._lock:
            return canonical_state_bytes(self._document(self._cells, self._bridges))

    def begin_consistent_read(self) -> object:
        self._require_open()
        self._lock.acquire()
        if self._read_token is not None:
            self._lock.release()
            raise RuntimeError("consistent read already active")
        token = object()
        self._read_token = token
        safe_emit(self.trace_sink, TraceEvent("core.snapshot.freeze", {}, "stable"))
        return token

    def export_state(self, token: object) -> bytes:
        self._require_token(token)
        return self.state_bytes()

    def import_state(self, payload: bytes) -> None:
        self._require_open()
        with self._lock:
            if self._read_token is not None:
                raise RuntimeError("cannot restore during a consistent read")
            cells, bridges = self._decode_state_bytes(payload)
            self.store.write_bytes(payload)
            self._cells = cells
            self._bridges = bridges
            self.cells = CellStore(self._cells)

    def end_consistent_read(self, token: object) -> None:
        self._require_token(token)
        self._read_token = None
        safe_emit(self.trace_sink, TraceEvent("core.snapshot.release", {}, "stable"))
        self._lock.release()

    def _apply(
        self,
        command: CoreCommand,
        cells: dict[GeometryAddress, dict[str, MemoryAtom]],
        bridges: dict[str, BridgeSpec],
    ) -> tuple[object, TraceEvent]:
        if isinstance(command, PutCommand):
            local_id = command.atom.atom_id
            values = cells.setdefault(command.target_cell, {})
            if local_id in values:
                raise FileExistsError("local atom already exists at target cell")
            values[local_id] = command.atom
            handle = AtomHandle(command.target_cell, local_id)
            return handle, TraceEvent("core.put", {"handle": handle.to_mapping()}, "stable")
        if isinstance(command, RemoveCommand):
            atom = self._require_handle(command.handle, cells)
            del cells[command.handle.geometry_address][command.handle.local_atom_id]
            if not cells[command.handle.geometry_address]:
                del cells[command.handle.geometry_address]
            return atom, TraceEvent("core.remove", {"handle": command.handle.to_mapping()}, "stable")
        if isinstance(command, ReplaceCommand):
            if not command.new_payload_utf8:
                raise ValueError("new_payload_utf8 is required")
            old = self._require_handle(command.handle, cells)
            cells[command.handle.geometry_address][command.handle.local_atom_id] = MemoryAtom(old.atom_id, command.new_payload_utf8)
            return command.handle, TraceEvent("core.replace", {"handle": command.handle.to_mapping()}, "stable")
        if isinstance(command, MoveCommand):
            atom = self._require_handle(command.handle, cells)
            if command.target_cell == command.handle.geometry_address:
                return command.handle, TraceEvent("core.move", {"from": command.handle.to_mapping(), "to": command.handle.to_mapping()}, "stable")
            target_values = cells.setdefault(command.target_cell, {})
            if command.handle.local_atom_id in target_values:
                raise FileExistsError("local atom already exists at target cell")
            del cells[command.handle.geometry_address][command.handle.local_atom_id]
            if not cells[command.handle.geometry_address]:
                del cells[command.handle.geometry_address]
            target_values[command.handle.local_atom_id] = atom
            handle = AtomHandle(command.target_cell, command.handle.local_atom_id)
            return handle, TraceEvent("core.move", {"from": command.handle.to_mapping(), "to": handle.to_mapping()}, "stable")
        if isinstance(command, BridgeAddCommand):
            if command.spec.bridge_id in bridges:
                raise FileExistsError("bridge already exists")
            bridges[command.spec.bridge_id] = command.spec
            return command.spec, TraceEvent("core.bridge.add", {"bridge_id": command.spec.bridge_id}, "stable")
        if isinstance(command, BridgeRemoveCommand):
            try:
                spec = bridges.pop(command.bridge_id)
            except KeyError as error:
                raise KeyError("bridge does not exist") from error
            return spec, TraceEvent("core.bridge.remove", {"bridge_id": command.bridge_id}, "stable")
        raise TypeError("unsupported Core command")

    @staticmethod
    def _require_handle(handle: AtomHandle, cells: dict[GeometryAddress, dict[str, MemoryAtom]]) -> MemoryAtom:
        if not isinstance(handle, AtomHandle):
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
            if atoms:
                cells[address] = atoms
            else:
                raise ValueError("empty cells are not canonical Core state")
        bridges = {}
        for value in document["bridges"]:
            bridge = BridgeSpec.from_mapping(value)
            if bridge.bridge_id in bridges:
                raise ValueError("duplicate bridge id")
            bridges[bridge.bridge_id] = bridge
        return cells, bridges

    @staticmethod
    def _decode_document(payload: bytes) -> dict[str, object]:
        import json

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

    def _require_token(self, token: object) -> None:
        if token is not self._read_token:
            raise ValueError("invalid consistent-read token")
