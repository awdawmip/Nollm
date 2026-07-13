from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_core import AtomHandle


SCHEMA_VERSION = "nollm_access_bindings_v2"


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
    """Canonical one-handle/one-current physical binding registry."""

    def __init__(self, root: Path) -> None:
        self._workspace = Path(root).resolve()
        self._path = self._workspace / "access" / "bindings.json"

    @property
    def workspace(self) -> Path:
        return self._workspace

    @property
    def path(self) -> Path:
        return self._path

    def state_bytes(self) -> bytes:
        if not self.path.exists():
            return self._encode(())
        payload = self.path.read_bytes()
        self._decode(payload)
        return payload

    def import_state(self, payload: bytes) -> None:
        self._decode(payload)
        self._write_bytes(payload)

    def put(self, statement_id: str, handle: AtomHandle) -> None:
        bindings = list(self._load())
        self._require_unbound_statement(bindings, statement_id)
        for index, binding in enumerate(bindings):
            if binding.handle == handle:
                supports = tuple(sorted((*binding.supporting_statement_ids, statement_id)))
                bindings[index] = HandleBinding(handle, binding.current_statement_id, supports)
                self._write(tuple(bindings))
                return
        bindings.append(HandleBinding(handle, statement_id))
        self._write(tuple(bindings))

    def revise_current(self, old_handle: AtomHandle, statement_id: str, new_handle: AtomHandle) -> None:
        bindings = list(self._load())
        self._require_unbound_statement(bindings, statement_id)
        index = self._index_for_handle(bindings, old_handle)
        del bindings[index]
        if any(binding.handle == new_handle for binding in bindings):
            raise ValueError("new revision handle is already bound")
        bindings.append(HandleBinding(new_handle, statement_id))
        self._write(tuple(bindings))

    def move_handle(self, old_handle: AtomHandle, new_handle: AtomHandle) -> None:
        bindings = list(self._load())
        index = self._index_for_handle(bindings, old_handle)
        if old_handle == new_handle:
            return
        if any(binding.handle == new_handle for binding in bindings):
            raise ValueError("moved handle is already bound")
        binding = bindings[index]
        bindings[index] = HandleBinding(new_handle, binding.current_statement_id, binding.supporting_statement_ids)
        self._write(tuple(bindings))

    def get(self, statement_id: str) -> AtomHandle:
        matches = [binding.handle for binding in self._load() if statement_id == binding.current_statement_id or statement_id in binding.supporting_statement_ids]
        if len(matches) != 1:
            raise KeyError("statement has no saved Core handle")
        return matches[0]

    def binding_for_handle(self, handle: AtomHandle) -> HandleBinding:
        bindings = self._load()
        return bindings[self._index_for_handle(list(bindings), handle)]

    def remove_handle(self, handle: AtomHandle) -> None:
        bindings = list(self._load())
        del bindings[self._index_for_handle(bindings, handle)]
        self._write(tuple(bindings))

    def exists(self, statement_id: str) -> bool:
        try:
            self.get(statement_id)
        except KeyError:
            return False
        return True

    def statement_for_handle(self, handle: AtomHandle) -> str:
        return self.binding_for_handle(handle).current_statement_id

    def _load(self) -> tuple[HandleBinding, ...]:
        return self._decode(self.state_bytes())

    @staticmethod
    def _require_unbound_statement(bindings: list[HandleBinding], statement_id: str) -> None:
        if type(statement_id) is not str or not statement_id:
            raise ValueError("statement_id is required")
        if any(statement_id == binding.current_statement_id or statement_id in binding.supporting_statement_ids for binding in bindings):
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
        value = json.loads(payload.decode("utf-8"))
        if type(value) is not dict or frozenset(value) != frozenset({"schema_version", "bindings"}) or value["schema_version"] != SCHEMA_VERSION or type(value["bindings"]) is not list:
            raise ValueError("invalid HandleStore state")
        if _canonical(value) != payload:
            raise ValueError("HandleStore bytes must be canonical")
        bindings = []
        statements: set[str] = set()
        handles: set[AtomHandle] = set()
        for item in value["bindings"]:
            if type(item) is not dict or frozenset(item) != frozenset({"handle", "current_statement_id", "supporting_statement_ids"}) or type(item["current_statement_id"]) is not str or type(item["supporting_statement_ids"]) is not list:
                raise ValueError("invalid HandleBinding")
            if any(type(statement) is not str for statement in item["supporting_statement_ids"]):
                raise TypeError("supporting statement ids must be strings")
            binding = HandleBinding(AtomHandle.from_mapping(item["handle"]), item["current_statement_id"], tuple(item["supporting_statement_ids"]))
            ids = {binding.current_statement_id, *binding.supporting_statement_ids}
            if binding.handle in handles or statements.intersection(ids):
                raise ValueError("duplicate binding identity")
            handles.add(binding.handle)
            statements.update(ids)
            bindings.append(binding)
        canonical = FileHandleStore._encode(tuple(bindings))
        if canonical != payload:
            raise ValueError("HandleBinding order is not canonical")
        return tuple(bindings)

    def _write_bytes(self, payload: bytes) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.parent / f".{self.path.name}.{uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()


FileBindingStore = FileHandleStore
