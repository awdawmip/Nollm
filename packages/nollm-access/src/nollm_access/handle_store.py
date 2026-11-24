from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_core import AtomHandle


SCHEMA_VERSION = "nollm_access_bindings_v2"
PAGED_SCHEMA_VERSION = "nollm_access_bindings_pages_v1"
HANDLE_STATE_SCHEMA_VERSION = "nollm_access_handle_state_v1"


@dataclass(frozen=True)
class HandleBinding:
    handle: AtomHandle
    current_statement_id: str
    supporting_statement_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.handle) is not AtomHandle:
            raise TypeError("handle must be an exact AtomHandle")
        if type(self.current_statement_id) is not str or not self.current_statement_id:
            raise TypeError("current_statement_id must be a non-empty string")
        if type(self.supporting_statement_ids) is not tuple:
            raise TypeError("supporting_statement_ids must be a tuple")
        if any(type(value) is not str or not value for value in self.supporting_statement_ids):
            raise TypeError("supporting statement ids must be non-empty strings")
        if tuple(sorted(set(self.supporting_statement_ids))) != self.supporting_statement_ids:
            raise ValueError("supporting_statement_ids must be sorted and unique")
        if self.current_statement_id in self.supporting_statement_ids:
            raise ValueError("current statement cannot also be supporting")

    def to_mapping(self) -> dict[str, object]:
        return {"handle": self.handle.to_mapping(), "current_statement_id": self.current_statement_id, "supporting_statement_ids": list(self.supporting_statement_ids)}


def _canonical(document: dict[str, object]) -> bytes:
    return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


class FileHandleStore:
    """Current bindings, optionally paged by their known physical addresses.

    Statement lookup remains an explicit physical inventory operation. No
    statement-to-geometry routing index is maintained.
    """

    def __init__(self, root: Path) -> None:
        self._workspace = Path(root).resolve()
        self._path = self._workspace / "access" / "bindings.json"

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def path(self) -> Path:
        return self._path

    @property
    def is_paged(self) -> bool:
        return self._read_document().get("schema_version") == PAGED_SCHEMA_VERSION

    @staticmethod
    def inspect_storage(workspace: Path) -> dict[str, object]:
        """Read only the layout entry, without reading any binding pages."""
        path = Path(workspace) / "access" / "bindings.json"
        try:
            document = json.loads(path.read_bytes())
        except FileNotFoundError:
            return {"layout": "single_file"}
        if not isinstance(document, dict) or document.get("schema_version") not in {SCHEMA_VERSION, PAGED_SCHEMA_VERSION}:
            raise ValueError("unknown bindings storage layout")
        if document["schema_version"] == SCHEMA_VERSION:
            return {"layout": "single_file"}
        width = document.get("partition_width")
        if type(width) is not int or width <= 0:
            raise ValueError("invalid bindings partition width")
        return {"layout": "paged", "partition_width": width}

    def enable_paged_storage(self, partition_width: int = 64) -> None:
        if type(partition_width) is not int or partition_width <= 0:
            raise ValueError("partition width must be positive")
        document = self._read_document()
        if document.get("schema_version") == PAGED_SCHEMA_VERSION:
            if document["partition_width"] != partition_width:
                raise ValueError("paged bindings already use a different partition width")
            return
        self._write_paged_view(self._decode_document(document), partition_width)

    def state_bytes(self) -> bytes:
        """Export the established logical v2 state, independent of page layout."""
        return self._encode(self._load())

    def import_state(self, payload: bytes) -> None:
        bindings = self._decode(payload)
        document = self._read_document()
        if document.get("schema_version") == PAGED_SCHEMA_VERSION:
            self._write_paged_view(bindings, document["partition_width"])
        else:
            self._write(bindings)

    def export_handle_state(self, handles: tuple[AtomHandle, ...]) -> bytes:
        handles = self._unique_handles(handles)
        return _canonical({"schema_version": HANDLE_STATE_SCHEMA_VERSION,
                           "handles": [handle.to_mapping() for handle in handles],
                           "bindings": [binding.to_mapping() for binding in self.bindings_for_handles(handles)]})

    def import_handle_state(self, payload: bytes) -> None:
        value = json.loads(payload.decode("utf-8"))
        if (not isinstance(value, dict) or set(value) != {"schema_version", "handles", "bindings"}
                or value["schema_version"] != HANDLE_STATE_SCHEMA_VERSION
                or not isinstance(value["handles"], list)):
            raise ValueError("invalid local HandleStore state")
        handles = self._unique_handles(tuple(AtomHandle.from_mapping(item) for item in value["handles"]))
        bindings = self._decode(_canonical({"schema_version": SCHEMA_VERSION, "bindings": value["bindings"]}))
        # These bindings belonged to this exact scope when the savepoint was
        # taken. The Access composition lock owns recovery of that operation.
        self.replace_handles(handles, bindings,
                             fresh_statement_ids=tuple(identity for binding in bindings
                                                       for identity in self._statement_ids(binding)))

    def replace_handles(self, handles: tuple[AtomHandle, ...], bindings: tuple[HandleBinding, ...], *,
                        fresh_statement_ids: tuple[str, ...] = ()) -> None:
        """Replace one explicit scope, preserving other handles in its pages.

        fresh_statement_ids is supplied by Access only for Statements absent
        before this capture; those cannot already have a legitimate binding.
        Other newly bound IDs retain the full uniqueness check.
        """
        handles = self._unique_handles(handles)
        document, pages = self._read_scope(handles)
        self._replace_scope(handles, tuple(bindings), document, pages, set(fresh_statement_ids))

    def put(self, statement_id: str, handle: AtomHandle, *, fresh_statement: bool = False) -> None:
        handles = (handle,)
        document, pages = self._read_scope(handles)
        old = next((binding for page in pages.values() for binding in page if binding.handle == handle), None)
        if old is not None:
            self._require_unbound_statement([old], statement_id)
            binding = HandleBinding(handle, old.current_statement_id,
                                    tuple(sorted((*old.supporting_statement_ids, statement_id))))
        else:
            binding = HandleBinding(handle, statement_id)
        self._replace_scope(handles, (binding,), document, pages,
                            {statement_id} if fresh_statement else set())

    def revise_current(self, old_handle: AtomHandle, statement_id: str, new_handle: AtomHandle, *,
                       fresh_statement: bool = False) -> None:
        handles = self._unique_handles((old_handle, new_handle))
        document, pages = self._read_scope(handles)
        selected = {binding.handle: binding for page in pages.values() for binding in page
                    if binding.handle in handles}
        if old_handle not in selected:
            raise KeyError("Core handle has no canonical binding")
        self._require_unbound_statement(list(selected.values()), statement_id)
        if old_handle != new_handle and new_handle in selected:
            raise ValueError("new revision handle is already bound")
        self._replace_scope(handles, (HandleBinding(new_handle, statement_id),), document, pages,
                            {statement_id} if fresh_statement else set())

    def move_handle(self, old_handle: AtomHandle, new_handle: AtomHandle) -> None:
        handles = self._unique_handles((old_handle, new_handle))
        document, pages = self._read_scope(handles)
        selected = {binding.handle: binding for page in pages.values() for binding in page
                    if binding.handle in handles}
        if old_handle not in selected:
            raise KeyError("Core handle has no canonical binding")
        if old_handle == new_handle:
            return
        if new_handle in selected:
            raise ValueError("moved handle is already bound")
        old = selected[old_handle]
        moved = HandleBinding(new_handle, old.current_statement_id, old.supporting_statement_ids)
        self._replace_scope(handles, (moved,), document, pages, set())

    def get(self, statement_id: str) -> AtomHandle:
        matches = [binding.handle for binding in self._load()
                   if statement_id in self._statement_ids(binding)]
        if len(matches) != 1:
            raise KeyError("statement has no saved Core handle")
        return matches[0]

    def binding_for_handle(self, handle: AtomHandle) -> HandleBinding:
        bindings = self.bindings_for_handles((handle,))
        if not bindings:
            raise KeyError("Core handle has no canonical binding")
        return bindings[0]

    def bindings_for_handles(self, handles: tuple[AtomHandle, ...]) -> tuple[HandleBinding, ...]:
        if type(handles) is not tuple or any(type(handle) is not AtomHandle for handle in handles):
            raise TypeError("handles must be an AtomHandle tuple")
        if not handles:
            return ()
        _document, pages = self._read_scope(handles)
        by_handle = {binding.handle: binding for page in pages.values() for binding in page}
        return tuple(by_handle[handle] for handle in handles if handle in by_handle)

    def bindings_for_atom_ids(self, atom_ids: tuple[str, ...]) -> tuple[HandleBinding, ...]:
        """Inventory physical candidates; a local atom ID is not globally unique."""
        if type(atom_ids) is not tuple or any(type(value) is not str or not value for value in atom_ids):
            raise TypeError("atom_ids must be a non-empty-string tuple")
        wanted = set(atom_ids)
        return tuple(binding for binding in self._load() if binding.handle.local_atom_id in wanted)

    def remove_handle(self, handle: AtomHandle) -> None:
        handles = (handle,)
        document, pages = self._read_scope(handles)
        if not any(binding.handle == handle for page in pages.values() for binding in page):
            raise KeyError("Core handle has no canonical binding")
        self._replace_scope(handles, (), document, pages, set())

    def exists(self, statement_id: str) -> bool:
        try:
            self.get(statement_id)
        except KeyError:
            return False
        return True

    def statement_for_handle(self, handle: AtomHandle) -> str:
        return self.binding_for_handle(handle).current_statement_id

    @staticmethod
    def _statement_ids(binding: HandleBinding) -> tuple[str, ...]:
        return (binding.current_statement_id, *binding.supporting_statement_ids)

    @staticmethod
    def _unique_handles(handles: tuple[AtomHandle, ...]) -> tuple[AtomHandle, ...]:
        if type(handles) is not tuple or any(type(handle) is not AtomHandle for handle in handles):
            raise TypeError("handles must be an AtomHandle tuple")
        return tuple(sorted(set(handles), key=lambda handle:
                            (handle.geometry_address.stable_key(), handle.local_atom_id)))

    def _read_document(self) -> dict[str, object]:
        try:
            payload = self.path.read_bytes()
        except FileNotFoundError:
            return {"schema_version": SCHEMA_VERSION, "bindings": []}
        value = json.loads(payload.decode("utf-8"))
        if isinstance(value, dict) and value.get("schema_version") == PAGED_SCHEMA_VERSION:
            if (set(value) != {"schema_version", "partition_width", "directory"}
                    or type(value["partition_width"]) is not int or value["partition_width"] <= 0
                    or not isinstance(value["directory"], str) or len(value["directory"]) != 32
                    or any(char not in "0123456789abcdef" for char in value["directory"])):
                raise ValueError("invalid paged HandleStore marker")
        elif (not isinstance(value, dict) or set(value) != {"schema_version", "bindings"}
              or value["schema_version"] != SCHEMA_VERSION or not isinstance(value["bindings"], list)):
            raise ValueError("invalid HandleStore state")
        return value

    def _page_root(self, document: dict[str, object]) -> Path:
        return self.path.parent / "binding_pages" / document["directory"]

    def _page_path(self, document: dict[str, object], handle: AtomHandle) -> Path:
        cell = handle.geometry_address
        q, r = cell.partition_id(document["partition_width"])
        # Reversible storage components, not source/topic/object routing keys.
        phase = "none" if cell.phase is None else "value-" + cell.phase.encode("utf-8").hex()
        return (self._page_root(document) / cell.profile_id.encode("utf-8").hex()
                / cell.chart_id.encode("utf-8").hex() / phase / str(cell.layer) / f"{q}_{r}.json")

    def _read_page(self, document: dict[str, object], path: Path) -> tuple[HandleBinding, ...]:
        try:
            bindings = self._decode(path.read_bytes())
        except FileNotFoundError:
            return ()
        if any(self._page_path(document, binding.handle) != path for binding in bindings):
            raise ValueError("binding is stored outside its physical page")
        return bindings

    def _read_scope(self, handles: tuple[AtomHandle, ...]):
        document = self._read_document()
        if document.get("schema_version") != PAGED_SCHEMA_VERSION:
            return document, {self.path: self._decode_document(document)}
        paths = {self._page_path(document, handle) for handle in handles}
        return document, {path: self._read_page(document, path) for path in sorted(paths)}

    def _all_bindings(self, document: dict[str, object], loaded=None) -> tuple[HandleBinding, ...]:
        if document.get("schema_version") != PAGED_SCHEMA_VERSION:
            return self._decode_document(document)
        loaded = loaded or {}
        bindings = []
        for path in sorted(self._page_root(document).rglob("*.json")):
            bindings.extend(loaded[path] if path in loaded else self._read_page(document, path))
        # Full inventory/export checks uniqueness across physical pages too.
        return self._validate_bindings(tuple(bindings))

    def _load(self) -> tuple[HandleBinding, ...]:
        return self._all_bindings(self._read_document())

    def _replace_scope(self, handles, bindings, document, pages, fresh_ids):
        selected = set(handles)
        bindings = self._validate_bindings(bindings)
        if any(binding.handle not in selected for binding in bindings):
            raise ValueError("replacement binding is outside the selected handle scope")
        if not handles:
            return
        old_ids = {identity for page in pages.values() for binding in page if binding.handle in selected
                   for identity in self._statement_ids(binding)}
        new_ids = {identity for binding in bindings for identity in self._statement_ids(binding)}
        unchecked = new_ids - old_ids - fresh_ids
        if unchecked:
            for binding in self._all_bindings(document, pages):
                if binding.handle not in selected and unchecked.intersection(self._statement_ids(binding)):
                    raise ValueError("statement is already bound")
        if document.get("schema_version") != PAGED_SCHEMA_VERSION:
            remaining = tuple(binding for binding in pages[self.path] if binding.handle not in selected)
            self._write((*remaining, *bindings))
            return
        replacements = {path: [binding for binding in page if binding.handle not in selected]
                        for path, page in pages.items()}
        for binding in bindings:
            replacements[self._page_path(document, binding.handle)].append(binding)
        for path, page in replacements.items():
            result = tuple(page)
            if self._encode(result) == self._encode(pages[path]):
                continue
            if result:
                self._write_page(path, self._encode(result))
            else:
                path.unlink(missing_ok=True)

    def _write_paged_view(self, bindings: tuple[HandleBinding, ...], width: int) -> None:
        document = {"schema_version": PAGED_SCHEMA_VERSION, "partition_width": width,
                    "directory": uuid4().hex}
        pages = {}
        for binding in bindings:
            pages.setdefault(self._page_path(document, binding.handle), []).append(binding)
        for path, values in pages.items():
            self._write_page(path, self._encode(tuple(values)))
        # A full import/migration becomes visible only after all its pages exist.
        # Previous views remain available if writing the new view is interrupted.
        self._write_bytes(_canonical(document))

    @staticmethod
    def _require_unbound_statement(bindings: list[HandleBinding], statement_id: str) -> None:
        if type(statement_id) is not str or not statement_id:
            raise ValueError("statement_id is required")
        if any(statement_id in FileHandleStore._statement_ids(binding) for binding in bindings):
            raise ValueError("statement is already bound")

    @staticmethod
    def _index_for_handle(bindings: list[HandleBinding], handle: AtomHandle) -> int:
        matches = [index for index, binding in enumerate(bindings) if binding.handle == handle]
        if len(matches) != 1:
            raise KeyError("Core handle has no canonical binding")
        return matches[0]

    def _write(self, bindings: tuple[HandleBinding, ...]) -> None:
        self._write_bytes(self._encode(bindings))

    @staticmethod
    def _encode(bindings: tuple[HandleBinding, ...]) -> bytes:
        ordered = sorted(bindings, key=lambda binding: (binding.handle.geometry_address.stable_key(), binding.handle.local_atom_id))
        return _canonical({"schema_version": SCHEMA_VERSION, "bindings": [binding.to_mapping() for binding in ordered]})

    @staticmethod
    def _decode(payload: bytes) -> tuple[HandleBinding, ...]:
        return FileHandleStore._decode_document(json.loads(payload.decode("utf-8")))

    @staticmethod
    def _decode_document(value: object) -> tuple[HandleBinding, ...]:
        if type(value) is not dict or frozenset(value) != frozenset({"schema_version", "bindings"}) or value["schema_version"] != SCHEMA_VERSION or type(value["bindings"]) is not list:
            raise ValueError("invalid HandleStore state")
        bindings = []
        for item in value["bindings"]:
            if type(item) is not dict or frozenset(item) != frozenset({"handle", "current_statement_id", "supporting_statement_ids"}) or type(item["supporting_statement_ids"]) is not list:
                raise ValueError("invalid HandleBinding")
            binding = HandleBinding(AtomHandle.from_mapping(item["handle"]), item["current_statement_id"], tuple(item["supporting_statement_ids"]))
            bindings.append(binding)
        return FileHandleStore._validate_bindings(tuple(bindings))

    @staticmethod
    def _validate_bindings(bindings: tuple[HandleBinding, ...]) -> tuple[HandleBinding, ...]:
        statements: set[str] = set()
        handles: set[AtomHandle] = set()
        for binding in bindings:
            ids = set(FileHandleStore._statement_ids(binding))
            if binding.handle in handles or statements.intersection(ids):
                raise ValueError("duplicate binding identity")
            handles.add(binding.handle)
            statements.update(ids)
        return bindings

    def _write_bytes(self, payload: bytes) -> None:
        self._write_page(self.path, payload)

    @staticmethod
    def _write_page(path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


FileBindingStore = FileHandleStore
