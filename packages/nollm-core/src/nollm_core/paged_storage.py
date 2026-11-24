"""Geometry-addressed Core pages and a local undo journal.

Only explicit migration selects this storage layout. The logical snapshot stays
the Core v1 document. Page metadata contains physical occupancy and byte counts;
relations continue to be calculated from geometry.
"""
from __future__ import annotations

from base64 import urlsafe_b64encode
from collections import OrderedDict
from collections.abc import Mapping, MutableMapping
import json
import os
from pathlib import Path

from .atom import MemoryAtom
from .geometry import GeometryAddress
from .storage import SCHEMA_VERSION, _atomic_write, canonical_state_bytes


PAGED_SCHEMA_VERSION = "nollm_core_paged_state_v1"
PAGE_SCHEMA_VERSION = "nollm_core_page_v1"
METADATA_SCHEMA_VERSION = "nollm_core_page_occupancy_v1"
CELL_STATE_SCHEMA_VERSION = "nollm_core_cell_state_v1"


def _component(value: str) -> str:
    return urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _sync_directory(path: Path) -> None:
    # Windows does not expose directory fsync through os.open. File replacement
    # and the recoverable journal remain the persistence mechanism there.
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class _ChangedFiles:
    """One owned Core writer; undo an interrupted multi-file replacement."""

    def __init__(self, workspace: Path) -> None:
        self.root = Path(workspace).resolve() / "core"
        self.journal = self.root / "paged_write.pending.json"

    def recover(self) -> None:
        try:
            value = json.loads(self.journal.read_bytes())
        except FileNotFoundError:
            return
        if not isinstance(value, dict) or set(value) != {"schema_version", "before"} or value["schema_version"] != "nollm_core_page_undo_v1" or not isinstance(value["before"], dict):
            raise ValueError("invalid Core page recovery record")
        self._restore(value["before"])
        self.journal.unlink()
        _sync_directory(self.root)

    def _target(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts or path == Path(self.journal.name):
            raise ValueError("invalid Core page recovery path")
        return self.root / path

    def _restore(self, before: dict[str, str | None]) -> None:
        for relative, text in before.items():
            if not isinstance(relative, str) or (text is not None and not isinstance(text, str)):
                raise ValueError("invalid Core page recovery bytes")
            path = self._target(relative)
            if text is None:
                path.unlink(missing_ok=True)
            else:
                _atomic_write(path, text.encode("utf-8"))
            if path.parent.exists():
                _sync_directory(path.parent)

    def apply(self, changes: dict[Path, bytes | None]) -> None:
        if not changes:
            return
        before = {}
        for path in changes:
            relative = str(path.relative_to(self.root))
            self._target(relative)
            try:
                before[relative] = path.read_text(encoding="utf-8")
            except FileNotFoundError:
                before[relative] = None
        record = {"schema_version": "nollm_core_page_undo_v1", "before": before}
        _atomic_write(self.journal, canonical_state_bytes(record))
        _sync_directory(self.root)
        try:
            for path, payload in changes.items():
                if payload is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write(path, payload)
                if path.parent.exists():
                    _sync_directory(path.parent)
            self.journal.unlink()
            _sync_directory(self.root)
        except BaseException:
            # If restoring itself fails, keep the journal for the next opener.
            # Cleanup can fail after unlink; reinstate recovery before undoing.
            if not self.journal.exists():
                _atomic_write(self.journal, canonical_state_bytes(record))
            self._restore(before)
            self.journal.unlink()
            _sync_directory(self.root)
            raise


class _CellChanges(MutableMapping):
    """Copy only cells touched by a command; preserve the accepted base."""

    def __init__(self, base: Mapping) -> None:
        self.base = base
        self.changed: dict[GeometryAddress, dict[str, MemoryAtom]] = {}
        self.deleted: set[GeometryAddress] = set()

    def __getitem__(self, address):
        if address in self.deleted:
            raise KeyError(address)
        if address not in self.changed:
            self.changed[address] = dict(self.base[address])
        return self.changed[address]

    def __setitem__(self, address, atoms):
        self.changed[address] = atoms
        self.deleted.discard(address)

    def __delitem__(self, address):
        self[address]
        self.changed.pop(address, None)
        self.deleted.add(address)

    def __iter__(self):
        return iter((set(self.base) | set(self.changed)) - self.deleted)

    def __len__(self):
        return sum(1 for _ in self)


class _PagedCells(Mapping):
    def __init__(self, store: "_PagedCoreStateStore", decode) -> None:
        self.store = store
        self.decode = decode
        self._pages = OrderedDict()

    def page(self, path: Path):
        if path in self._pages:
            self._pages.move_to_end(path)
            return self._pages[path]
        try:
            value = json.loads(path.read_bytes())
        except FileNotFoundError:
            cells = {}
        else:
            if not isinstance(value, dict) or set(value) != {"schema_version", "cells"} or value["schema_version"] != PAGE_SCHEMA_VERSION:
                raise ValueError("invalid Core page")
            document = {"schema_version": SCHEMA_VERSION, "geometry_registry": self.store.geometry_registry,
                        "cells": value["cells"], "bridges": []}
            cells, _ = self.decode(document)
            if any(self.store.page_path(cell) != path for cell in cells):
                raise ValueError("Core page contains a different geometric partition")
        self._pages[path] = cells
        if len(self._pages) > 64:
            self._pages.popitem(last=False)
        return cells

    def __getitem__(self, address):
        return self.page(self.store.page_path(address))[address]

    def __iter__(self):
        return (address for address, _, _ in self.occupancy())

    def __len__(self):
        return sum(1 for _ in self)

    def occupancy(self, scope=None):
        for path in self.store.page_paths(scope):
            metadata = self.store.metadata_path(path)
            try:
                value = json.loads(metadata.read_bytes())
            except FileNotFoundError:
                # Occupancy is rebuildable; losing it must not hide the body.
                records = self.store.occupancy_records(self.page(path))
            else:
                if not isinstance(value, dict) or set(value) != {"schema_version", "cells"} or value["schema_version"] != METADATA_SCHEMA_VERSION or not isinstance(value["cells"], list):
                    raise ValueError("invalid Core page occupancy")
                records = value["cells"]
            seen = set()
            for item in records:
                if not isinstance(item, dict) or set(item) != {"address", "atoms", "utf8_bytes"}:
                    raise ValueError("invalid Core occupancy cell")
                address = GeometryAddress.from_mapping(item["address"])
                count, size = item["atoms"], item["utf8_bytes"]
                if address in seen or self.store.page_path(address) != path or type(count) is not int or count <= 0 or type(size) is not int or size < 0:
                    raise ValueError("invalid Core occupancy counts")
                seen.add(address)
                if scope is None or scope.contains(address):
                    yield address, count, size


class _PagedCoreStateStore:
    def __init__(self, workspace: Path, marker: dict[str, object]) -> None:
        expected = {"schema_version", "geometry_registry", "partition_width"}
        if not isinstance(marker, dict) or set(marker) != expected or marker["schema_version"] != PAGED_SCHEMA_VERSION or type(marker["partition_width"]) is not int or marker["partition_width"] <= 0:
            raise ValueError("invalid paged Core state marker")
        self.workspace = Path(workspace).resolve()
        self.root = self.workspace / "core"
        self.path = self.root / "current_state.json"
        self.pages_root = self.root / "pages"
        self.bridges_path = self.root / "bridges.json"
        self.geometry_registry = marker["geometry_registry"]
        self.width = marker["partition_width"]
        self.transaction = _ChangedFiles(self.workspace)

    def page_path(self, address: GeometryAddress) -> Path:
        q, r = address.partition_id(self.width)
        phase = "none" if address.phase is None else "value_" + _component(address.phase)
        return self.pages_root / _component(address.profile_id) / _component(address.chart_id) / str(address.layer) / phase / f"{q}_{r}.json"

    @staticmethod
    def metadata_path(path: Path) -> Path:
        return path.with_suffix(".meta.json")

    def page_paths(self, scope=None):
        if scope is None:
            paths = self.pages_root.glob("*/*/*/*/*.json")
        else:
            base = self.pages_root / _component(scope.profile_id) / _component(scope.chart_id)
            paths = (path for layer in scope.physical_layers for path in (base / str(layer)).glob("*/*.json"))
        return tuple(sorted(path for path in paths if not path.name.endswith(".meta.json")))

    @staticmethod
    def cell_records(cells):
        return [{"address": address.to_mapping(), "atoms": [
                    {"local_atom_id": key, "atom": atoms[key].to_mapping()} for key in sorted(atoms)]}
                for address, atoms in sorted(cells.items(), key=lambda pair: pair[0].stable_key()) if atoms]

    @staticmethod
    def occupancy_records(cells):
        return [{"address": address.to_mapping(), "atoms": len(atoms),
                 "utf8_bytes": sum(len(atom.payload_utf8.encode("utf-8")) for atom in atoms.values())}
                for address, atoms in sorted(cells.items(), key=lambda pair: pair[0].stable_key()) if atoms]

    def _page_updates(self, path, cells):
        if not cells:
            return {path: None, self.metadata_path(path): None}
        return {path: canonical_state_bytes({"schema_version": PAGE_SCHEMA_VERSION, "cells": self.cell_records(cells)}),
                self.metadata_path(path): canonical_state_bytes({"schema_version": METADATA_SCHEMA_VERSION, "cells": self.occupancy_records(cells)})}

    def write_changes(self, base: _PagedCells, changes: _CellChanges, bridges=None):
        addresses = set(changes.changed) | changes.deleted
        pages = {self.page_path(address) for address in addresses}
        updates = {}
        for path in sorted(pages):
            cells = dict(base.page(path))
            for address in addresses:
                if self.page_path(address) != path:
                    continue
                if address in changes.deleted:
                    cells.pop(address, None)
                else:
                    cells[address] = changes.changed[address]
            updates.update(self._page_updates(path, cells))
        if bridges is not None:
            updates[self.bridges_path] = canonical_state_bytes({"bridges": [bridges[key].to_mapping() for key in sorted(bridges)]})
        self.transaction.apply(updates)
        for path in pages:
            base._pages.pop(path, None)

    def replace_all(self, cells, bridges, *, marker=None):
        pages = {}
        for address, atoms in cells.items():
            pages.setdefault(self.page_path(address), {})[address] = atoms
        updates = {}
        for path in self.page_paths():
            if path not in pages:
                updates.update(self._page_updates(path, {}))
        for path, contents in pages.items():
            updates.update(self._page_updates(path, contents))
        updates[self.bridges_path] = canonical_state_bytes({"bridges": [bridges[key].to_mapping() for key in sorted(bridges)]})
        if marker is not None:
            updates[self.path] = canonical_state_bytes(marker)
        self.transaction.apply(updates)

    def read_bridges(self, decode):
        value = json.loads(self.bridges_path.read_bytes())
        if not isinstance(value, dict) or set(value) != {"bridges"}:
            raise ValueError("invalid Core bridges file")
        _, bridges = decode({"schema_version": SCHEMA_VERSION, "geometry_registry": self.geometry_registry,
                             "cells": [], "bridges": value["bridges"]})
        return bridges
