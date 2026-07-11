from __future__ import annotations

from pathlib import Path
from threading import Condition, RLock, get_ident, local
from contextlib import contextmanager
from typing import Callable

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
        self._cells = {address: dict(atoms) for address, atoms in (cells or {}).items()}

    def get(self, handle: AtomHandle) -> MemoryAtom:
        try:
            return self._cells[handle.geometry_address][handle.local_atom_id]
        except KeyError as error:
            raise KeyError("AtomHandle does not exist") from error

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


class CoreClientLease:
    __slots__ = ("_runtime", "_token", "_generation", "_active", "client_kind")

    def __init__(self, runtime: "CoreRuntime", token: object, generation: object, client_kind: str) -> None:
        self._runtime = runtime
        self._token = token
        self._generation = generation
        self._active = True
        self.client_kind = client_kind

    def callback(self, callback: Callable[..., object], *args: object) -> object:
        return self._runtime._client_callback(self, callback, *args)

    def close(self) -> None:
        self._runtime.release_client_lease(self)


class CoreTransaction:
    __slots__ = ("_runtime", "_token", "_generation", "_owner_thread", "_active")

    def __init__(self, runtime: "CoreRuntime", token: object, generation: object) -> None:
        self._runtime = runtime
        self._token = token
        self._generation = generation
        self._owner_thread = get_ident()
        self._active = True

    def apply_batch(self, commands: tuple[CoreCommand, ...]) -> tuple[object, ...]:
        self._runtime._validate_transaction(self)
        return self._runtime._apply_batch_locked(commands)

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

    def get(self, handle: AtomHandle) -> MemoryAtom:
        self._runtime._validate_transaction(self)
        return self._runtime._require_handle(handle, self._runtime._cells)

    def contains(self, handle: AtomHandle) -> bool:
        try:
            self.get(handle)
        except KeyError:
            return False
        return True

    def recall(self, request: object) -> object:
        self._runtime._validate_transaction(self)
        return self._runtime._recall_locked(request)

    def state_bytes(self) -> bytes:
        self._runtime._validate_transaction(self)
        return self._runtime._state_bytes_locked()

    def import_state(self, payload: bytes) -> None:
        self._runtime._validate_transaction(self)
        self._runtime._import_state_locked(payload)

    def callback(self, callback: Callable[..., object], *args: object) -> object:
        self._runtime._validate_transaction(self)
        return self._runtime._run_callback(callback, *args)


class _ConsistentReadToken:
    __slots__ = ("runtime", "generation", "owner_thread", "token", "active")

    def __init__(self, runtime: "CoreRuntime", generation: object) -> None:
        self.runtime = runtime
        self.generation = generation
        self.owner_thread = get_ident()
        self.token = object()
        self.active = True


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
        self._trace_sink = trace_sink or NullTraceSink()
        self._store = store or FileCoreStateStore(self.workspace)
        self._generation = object()
        self._lifecycle = Condition(RLock())
        self._state = "OPEN"
        self._active_operations = 0
        self._active_transactions = 0
        self._active_consistent_reads = 0
        self._client_leases: set[CoreClientLease] = set()
        self._state_lock = RLock()
        self._local = local()
        self._read_token: _ConsistentReadToken | None = None
        self._owner_key = claim(self._store.path, self)
        self._kernel_registry = kernel_registry or KernelRegistry()
        try:
            self._store_token = self._store.bind_semantic_validator(self._validate_state_bytes, self._run_callback)
            if self._store.exists():
                self._cells, self._bridges = self._decode_state_bytes(self._store.read_bytes())
            else:
                self._cells = {}
                self._bridges = {}
                self._store.write_document(self._document(self._cells, self._bridges), self._store_token)
        except Exception:
            self._state = "CLOSED"
            release(self._owner_key,self)
            raise
        self._cell_store = CellStore(self._cells)
        self._mutation_active = False

    def close(self) -> None:
        self._reject_lifecycle_reentry("close")
        with self._lifecycle:
            if self._state == "CLOSED":
                return
            if self._state == "CLOSING":
                while self._state != "CLOSED":
                    self._lifecycle.wait()
                return
            if self._client_leases:
                raise RuntimeError("cannot close CoreRuntime while client leases are active")
            self._state = "CLOSING"
            self._lifecycle.notify_all()
            while self._active_operations:
                self._lifecycle.wait()
            release(self._owner_key, self)
            self._state = "CLOSED"
            self._lifecycle.notify_all()

    def __enter__(self) -> "CoreRuntime": return self
    def __exit__(self,*_args: object) -> None: self.close()

    def _require_open(self) -> None:
        if self._state != "OPEN":
            raise RuntimeError(f"CoreRuntime is {self._state.lower()}")

    @property
    def state_path(self) -> Path:
        return self._store.path

    @property
    def is_open(self) -> bool:
        with self._lifecycle:
            return self._state == "OPEN"

    @property
    def lifecycle_state(self) -> str:
        with self._lifecycle:
            return self._state

    def acquire_client_lease(self, client_kind: str) -> CoreClientLease:
        if type(client_kind) is not str or not client_kind:
            raise ValueError("client_kind is required")
        self._reject_lifecycle_reentry("client lease")
        with self._lifecycle:
            self._require_open()
            lease = CoreClientLease(self, object(), self._generation, client_kind)
            self._client_leases.add(lease)
            return lease

    def release_client_lease(self, lease: CoreClientLease) -> None:
        self._reject_lifecycle_reentry("client lease release")
        with self._lifecycle:
            self._validate_client_lease_locked(lease)
            self._client_leases.remove(lease)
            lease._active = False
            self._lifecycle.notify_all()

    @contextmanager
    def transaction(self):
        self._enter_activity("transaction")
        try:
            self._state_lock.acquire()
            transaction = CoreTransaction(self, object(), self._generation)
            self._local.transaction = transaction
            try:
                yield transaction
            finally:
                transaction._active = False
                if getattr(self._local, "transaction", None) is transaction:
                    del self._local.transaction
                self._state_lock.release()
        finally:
            self._leave_activity("transaction")

    @contextmanager
    def transaction_lease(self):
        with self.transaction() as transaction:
            yield transaction

    @contextmanager
    def _operation(self, name: str):
        self._enter_activity("public", name)
        try:
            self._state_lock.acquire()
            try:
                yield
            finally:
                self._state_lock.release()
        finally:
            self._leave_activity("public")

    def _emit_trace(self, event: TraceEvent) -> None:
        self._run_callback(safe_emit, self._trace_sink, event)

    def _run_callback(self, callback: Callable[..., object], *args: object) -> object:
        self._local.callback_depth = getattr(self._local, "callback_depth", 0) + 1
        try:
            return callback(*args)
        finally:
            depth = self._local.callback_depth - 1
            if depth:
                self._local.callback_depth = depth
            else:
                del self._local.callback_depth

    def _client_callback(self, lease: CoreClientLease, callback: Callable[..., object], *args: object) -> object:
        with self._lifecycle:
            self._validate_client_lease_locked(lease)
            self._require_open()
            self._active_operations += 1
        try:
            return self._run_callback(callback, *args)
        finally:
            with self._lifecycle:
                self._active_operations -= 1
                self._lifecycle.notify_all()

    def _enter_activity(self, kind: str, name: str = "") -> None:
        self._reject_lifecycle_reentry(name or kind)
        with self._lifecycle:
            self._require_open()
            self._active_operations += 1
            if kind == "transaction":
                self._active_transactions += 1
                self._local.activity = "transaction"
            elif kind == "consistent":
                self._active_consistent_reads += 1
                self._local.activity = "consistent-read"
            else:
                self._local.activity = f"public:{name}"

    def _leave_activity(self, kind: str) -> None:
        with self._lifecycle:
            if kind == "transaction":
                self._active_transactions -= 1
            elif kind == "consistent":
                self._active_consistent_reads -= 1
            self._active_operations -= 1
            if hasattr(self._local, "activity"):
                del self._local.activity
            self._lifecycle.notify_all()

    def _reject_lifecycle_reentry(self, operation: str) -> None:
        if getattr(self._local, "callback_depth", 0):
            raise RuntimeError(f"Core callback cannot enter {operation}")
        if hasattr(self._local, "activity"):
            if operation == "close":
                raise RuntimeError("cannot close during an active Core operation")
            if self._local.activity == "consistent-read":
                raise RuntimeError("public Core operation is forbidden during consistent read")
            raise RuntimeError(f"reentrant public Core operation is forbidden during {self._local.activity}")

    def _validate_client_lease_locked(self, lease: CoreClientLease) -> None:
        if type(lease) is not CoreClientLease or lease._runtime is not self or lease._generation is not self._generation:
            raise ValueError("foreign Core client lease")
        if not lease._active or lease not in self._client_leases:
            raise ValueError("expired Core client lease")

    def _validate_transaction(self, transaction: CoreTransaction) -> None:
        if type(transaction) is not CoreTransaction or transaction._runtime is not self or transaction._generation is not self._generation:
            raise ValueError("foreign Core transaction capability")
        if not transaction._active or transaction._owner_thread != get_ident() or getattr(self._local, "transaction", None) is not transaction:
            raise ValueError("expired or wrong-thread Core transaction capability")
        if getattr(self._local, "callback_depth", 0):
            raise RuntimeError("Core callback cannot use transaction capability")

    def put(self, atom: MemoryAtom, target_cell: GeometryAddress) -> AtomHandle:
        with self._operation("put"):
            return self._apply_batch_locked((PutCommand(atom, target_cell),))[0]
    @property
    def kernel_registry(self) -> KernelRegistry:
        return self._kernel_registry


    def remove(self, handle: AtomHandle) -> MemoryAtom:
        with self._operation("remove"):
            return self._apply_batch_locked((RemoveCommand(handle),))[0]

    def replace(self, handle: AtomHandle, new_payload_utf8: str) -> AtomHandle:
        with self._operation("replace"):
            return self._apply_batch_locked((ReplaceCommand(handle, new_payload_utf8),))[0]

    def move(self, handle: AtomHandle, target_cell: GeometryAddress) -> AtomHandle:
        with self._operation("move"):
            return self._apply_batch_locked((MoveCommand(handle, target_cell),))[0]

    def bridge_add(self, spec: BridgeSpec) -> BridgeSpec:
        with self._operation("bridge_add"):
            return self._apply_batch_locked((BridgeAddCommand(spec),))[0]

    def bridge_remove(self, bridge_id: str) -> BridgeSpec:
        with self._operation("bridge_remove"):
            return self._apply_batch_locked((BridgeRemoveCommand(bridge_id),))[0]

    def apply_batch(self, commands: tuple[CoreCommand, ...]) -> tuple[object, ...]:
        with self._operation("apply_batch"):
            return self._apply_batch_locked(commands)

    def _apply_batch_locked(self, commands: tuple[CoreCommand, ...]) -> tuple[object, ...]:
        if not commands:
            raise ValueError("batch must contain at least one command")
        if self._read_token is not None:
            raise RuntimeError("mutation is forbidden during consistent read")
        if self._mutation_active:
            raise RuntimeError("reentrant Core mutation is forbidden")
        self._mutation_active = True
        cells = {address: dict(atoms) for address, atoms in self._cells.items()}
        bridges = dict(self._bridges)
        results: list[object] = []
        events: list[TraceEvent] = []
        self._emit_trace(TraceEvent("core.batch.begin", {"command_count": len(commands)}, "stable"))
        try:
            for command in commands:
                result, event = self._apply(command, cells, bridges)
                results.append(result)
                events.append(event)
            self._store.write_document(self._document(cells, bridges), self._store_token)
            self._cells = cells; self._bridges = bridges; self._cell_store = CellStore(self._cells)
            for event in events: self._emit_trace(event)
            self._emit_trace(TraceEvent("core.batch.commit", {"command_count": len(commands)}, "stable"))
            return tuple(results)
        except Exception:
            self._emit_trace(TraceEvent("core.batch.rollback", {"command_count": len(commands)}, "stable"))
            raise
        finally:
            self._mutation_active = False

    def get(self, handle: AtomHandle) -> MemoryAtom:
        with self._operation("get"):
            return self._require_handle(handle, self._cells)

    def contains(self, handle: AtomHandle) -> bool:
        with self._operation("contains"):
            try:
                self._require_handle(handle, self._cells)
            except KeyError:
                return False
            return True

    def atoms_at(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        with self._operation("atoms_at"):
            return self._cell_store.atoms_at(address)

    def occupied_cells(self) -> tuple[GeometryAddress, ...]:
        with self._operation("occupied_cells"):
            return self._cell_store.occupied_cells()

    def bridges(self) -> tuple[BridgeSpec, ...]:
        with self._operation("bridges"):
            return tuple(self._bridges[key] for key in sorted(self._bridges))

    def placement_count(self) -> int:
        with self._operation("placement_count"):
            return self._cell_store.placement_count()

    def density_state(self, address: GeometryAddress) -> str:
        with self._operation("density_state"):
            return self._cell_store.density_state(address)

    def recall(self, request: object) -> object:
        with self._operation("recall"):
            return self._recall_locked(request)

    def _recall_locked(self, request: object) -> object:
        from .recall import CoreRecallRequest, resolve_recall

        if not isinstance(request, CoreRecallRequest):
            raise TypeError("request must be CoreRecallRequest")
        return resolve_recall(self, request)

    def state_bytes(self) -> bytes:
        with self._operation("state_bytes"):
            return self._state_bytes_locked()

    def _state_bytes_locked(self) -> bytes:
        return canonical_state_bytes(self._document(self._cells, self._bridges))

    def begin_consistent_read(self) -> object:
        self._enter_activity("consistent")
        self._state_lock.acquire()
        try:
            if self._read_token is not None:
                raise RuntimeError("consistent read already active")
            token = _ConsistentReadToken(self, self._generation)
            self._read_token = token
            self._local.consistent_token = token
            self._emit_trace(TraceEvent("core.snapshot.freeze", {}, "stable"))
            return token
        except Exception:
            self._state_lock.release()
            self._leave_activity("consistent")
            raise

    def export_state(self, token: object) -> bytes:
        self._require_token(token)
        return self._state_bytes_locked()

    def import_state(self, payload: bytes) -> None:
        with self._operation("import_state"):
            self._import_state_locked(payload)

    def _import_state_locked(self, payload: bytes) -> None:
        if self._read_token is not None:
            raise RuntimeError("cannot restore during a consistent read")
        cells, bridges = self._decode_state_bytes(payload)
        self._store.write_bytes(payload, self._store_token)
        self._cells = cells
        self._bridges = bridges
        self._cell_store = CellStore(self._cells)

    def end_consistent_read(self, token: object) -> None:
        self._require_token(token)
        try:
            self._emit_trace(TraceEvent("core.snapshot.release", {}, "stable"))
        finally:
            assert isinstance(token, _ConsistentReadToken)
            token.active = False
            self._read_token = None
            if hasattr(self._local, "consistent_token"):
                del self._local.consistent_token
            self._state_lock.release()
            self._leave_activity("consistent")

    def _atoms_at_locked(self, address: GeometryAddress) -> tuple[tuple[AtomHandle, MemoryAtom], ...]:
        return self._cell_store.atoms_at(address)

    def _bridges_locked(self) -> tuple[BridgeSpec, ...]:
        return tuple(self._bridges[key] for key in sorted(self._bridges))

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
        if type(token) is not _ConsistentReadToken or token.runtime is not self or token.generation is not self._generation:
            raise ValueError("foreign consistent-read token")
        if token.owner_thread != get_ident():
            raise RuntimeError("consistent-read token belongs to another thread")
        if not token.active or token is not self._read_token or getattr(self._local, "consistent_token", None) is not token:
            raise ValueError("invalid consistent-read token")
