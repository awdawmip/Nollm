from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import RLock

from nollm_core import AtomHandle, CoreRuntime, MemoryAtom

from .statement_store import StatementStore
from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallItem, AccessRecallRequest, AccessRecallResult
from .statement import MemoryStatement
from .workspace_lock import composition_lock


class AccessRuntime:
    """Trusted local coordinator for Evidence, Handle binding, and Core."""

    def __init__(self, core: CoreRuntime, evidence_store: StatementStore, handle_store: FileHandleStore) -> None:
        self._core = core
        self._evidence_store = evidence_store
        self._handle_store = handle_store
        access_root = handle_store.path.parent.parent.resolve()
        if hasattr(evidence_store, "workspace") and evidence_store.workspace.resolve() != access_root:
            raise ValueError("Evidence and Binding workspace identity mismatch")
        if not core.is_open:
            raise RuntimeError("AccessRuntime requires an open CoreRuntime")
        self._canonical_access_root = access_root
        self._canonical_core_state_path = core.state_path.resolve()
        self._composition_lock = composition_lock(access_root, core.state_path)
        self._lifecycle_lock = RLock()
        self._state = "OPEN"

    @property
    def core(self) -> CoreRuntime:
        return self._core

    @property
    def statement_store(self) -> StatementStore:
        return self._evidence_store

    @property
    def evidence_store(self) -> StatementStore:
        return self.statement_store

    @property
    def handle_store(self) -> FileHandleStore:
        return self._handle_store

    @property
    def canonical_access_root(self) -> Path:
        return self._canonical_access_root

    @property
    def canonical_core_state_path(self) -> Path:
        return self._canonical_core_state_path

    @property
    def lifecycle_state(self) -> str:
        with self._lifecycle_lock:
            return self._state

    def close(self) -> None:
        with self._lifecycle_lock:
            self._state = "CLOSED"

    def __enter__(self) -> "AccessRuntime":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    @contextmanager
    def _operation(self):
        with self._lifecycle_lock:
            if self._state != "OPEN":
                raise RuntimeError("AccessRuntime is closed")
        with self._composition_lock:
            if not self._core.is_open:
                raise RuntimeError("AccessRuntime Core is closed")
            yield

    def capture(self, statement: MemoryStatement) -> None:
        self.put_statement(statement)

    def stage_statement(self, statement: MemoryStatement) -> None:
        self.put_statement(statement)

    def put_statement(self, statement: MemoryStatement) -> None:
        with self._operation():
            if hasattr(self._evidence_store, "put"):
                self._evidence_store.put(statement)
            else:
                self._evidence_store.put_original(statement)

    def apply(self, decision: AccessDecision) -> object | None:
        with self._operation():
            return self._apply_locked(decision)

    def _apply_locked(self, decision: AccessDecision) -> object | None:
        if decision.action in {"new", "reuse", "revision_current", "revision_keep_history", "defer"} and not self._evidence_store.exists(decision.statement_id):
            raise FileNotFoundError("original Evidence is missing")
        if decision.action == "reuse":
            assert decision.existing_handle is not None
            self._get_statement(decision.statement_id)
            if not self._core.contains(decision.existing_handle):
                raise KeyError("explicit reuse handle no longer exists")
            try:
                existing = self._handle_store.binding_for_handle(decision.existing_handle)
            except KeyError:
                existing = None
            if existing is not None and existing.current_statement_id == decision.statement_id:
                return decision.existing_handle
            self._handle_store.put(decision.statement_id, decision.existing_handle)
            return decision.existing_handle
        if decision.action == "new":
            assert decision.target_cell is not None
            statement = self._get_statement(decision.statement_id)
            return self._atomic(
                lambda: self._core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell),
                lambda handle: self._handle_store.put(statement.statement_id, handle),
            )
        if decision.action == "move":
            assert decision.existing_handle is not None and decision.target_cell is not None
            self._get_statement(decision.statement_id)
            return self._atomic(
                lambda: self._core.move(decision.existing_handle, decision.target_cell),
                lambda handle: self._handle_store.move_handle(decision.existing_handle, handle),
            )
        if decision.action == "revision_current":
            assert decision.existing_handle is not None
            statement = self._get_statement(decision.statement_id)
            return self._atomic(
                lambda: self._core.replace(decision.existing_handle, statement.content_utf8),
                lambda handle: self._handle_store.revise_current(decision.existing_handle, statement.statement_id, handle),
            )
        if decision.action == "revision_keep_history":
            assert decision.target_cell is not None
            statement = self._get_statement(decision.statement_id)
            return self._atomic(
                lambda: self._core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell),
                lambda handle: self._handle_store.put(statement.statement_id, handle),
            )
        if decision.action == "stitch":
            assert decision.bridge_spec is not None
            return self._core.bridge_add(decision.bridge_spec)
        if decision.action == "unstitch":
            assert decision.bridge_spec is not None
            return self._core.bridge_remove(decision.bridge_spec.bridge_id)
        if decision.action == "defer":
            return None
        if decision.action == "forget":
            assert decision.existing_handle is not None
            return self._atomic(
                lambda: self._core.remove(decision.existing_handle),
                lambda _atom: self._handle_store.remove_handle(decision.existing_handle),
            )
        raise AssertionError("unreachable Access action")

    def recall(self, request: AccessRecallRequest) -> AccessRecallResult:
        with self._operation():
            result = self._core.recall(request.to_core_request())
            items = []
            for item in result.items:
                try:
                    statement_id = self._handle_store.statement_for_handle(item.handle)
                except KeyError:
                    items.append(AccessRecallItem(item.handle, "", None, item.score_q16, "binding_missing"))
                    continue
                try:
                    statement = self._get_statement(statement_id)
                except FileNotFoundError:
                    items.append(AccessRecallItem(item.handle, statement_id, None, item.score_q16, "evidence_missing"))
                else:
                    if statement.content_utf8 != item.atom.payload_utf8:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, None, item.score_q16, "evidence_payload_mismatch"))
                    else:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, statement.content_utf8, item.score_q16))
            return AccessRecallResult(result.request_id, tuple(items), result.budget_exhausted)

    def saved_handle(self, statement_id: str) -> AtomHandle:
        with self._operation():
            return self._handle_store.get(statement_id)

    def _get_statement(self, statement_id: str) -> MemoryStatement:
        if hasattr(self._evidence_store, "get"):
            return self._evidence_store.get(statement_id)
        return self._evidence_store.get_original(statement_id)

    def _atomic(self, core_action: object, binding_action: object) -> object:
        core_before = self._core.export_state_bytes()
        binding_before = self._handle_store.state_bytes()
        try:
            result = core_action()
            binding_action(result)
            return result
        except Exception as original:
            failures = []
            try:
                self._core.import_state_bytes(core_before)
            except Exception as error:
                failures.append(error)
            try:
                self._handle_store.import_state(binding_before)
            except Exception as error:
                failures.append(error)
            if failures:
                raise AccessConsistencyError("fatal consistency failure during trusted Access rollback") from original
            raise


class AccessConsistencyError(RuntimeError):
    pass
