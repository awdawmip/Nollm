from __future__ import annotations

from nollm_core import AtomHandle, CoreRuntime, MemoryAtom

from .evidence_store import EvidenceStore
from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallItem, AccessRecallRequest, AccessRecallResult
from .statement import MemoryStatement
from .workspace_lock import acquire, release
from contextlib import contextmanager
from threading import local


class AccessRuntime:
    def __init__(self, core: CoreRuntime, evidence_store: EvidenceStore, handle_store: FileHandleStore) -> None:
        self.core = core
        self.evidence_store = evidence_store
        self.handle_store = handle_store
        access_root = handle_store.path.parent.parent
        if hasattr(evidence_store, "workspace") and evidence_store.workspace.resolve() != access_root.resolve():
            raise ValueError("Evidence and Binding workspace identity mismatch")
        self._transaction_lock, self._lease = acquire(access_root, core.state_path)
        self._closed = False
        self._local = local()
        try:
            with self._transaction_lock:
                with core.transaction_lease():
                    if not core.is_open:
                        raise RuntimeError("AccessRuntime requires an OPEN CoreRuntime")
        except RuntimeError as error:
            release(self._lease)
            raise RuntimeError("AccessRuntime requires an OPEN CoreRuntime") from error
        except Exception:
            release(self._lease)
            raise

    def close(self) -> None:
        with self._transaction_lock:
            if getattr(self._local, "operation_depth", 0):
                raise RuntimeError("cannot close during an active Access operation")
            if not self._closed:
                self._closed=True; release(self._lease)

    def __enter__(self) -> "AccessRuntime": return self
    def __exit__(self,*_args: object) -> None: self.close()

    def _require_open(self) -> None:
        if self._closed: raise RuntimeError("AccessRuntime is closed")

    @contextmanager
    def _operation(self):
        with self._transaction_lock:
            self._require_open()
            self._local.operation_depth = getattr(self._local, "operation_depth", 0) + 1
            try:
                yield
            finally:
                depth = self._local.operation_depth - 1
                if depth:
                    self._local.operation_depth = depth
                else:
                    del self._local.operation_depth

    def capture(self, statement: MemoryStatement) -> None:
        with self._operation():
            self.evidence_store.put_original(statement)

    def apply(self, decision: AccessDecision) -> object | None:
        with self._operation():
            return self._apply_locked(decision)

    def _apply_locked(self, decision: AccessDecision) -> object | None:
        if decision.action in {"new", "reuse", "revision_current", "revision_keep_history", "defer"} and not self.evidence_store.exists(decision.statement_id):
            raise FileNotFoundError("original Evidence is missing")
        if decision.action == "reuse":
            assert decision.existing_handle is not None
            self.evidence_store.get_original(decision.statement_id)
            with self.core.transaction_lease():
                if not self.core.contains(decision.existing_handle):
                    raise KeyError("explicit reuse handle no longer exists")
                self.handle_store.put(decision.statement_id, decision.existing_handle)
            return decision.existing_handle
        if decision.action == "new":
            assert decision.target_cell is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            return self._atomic(lambda: self.core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell), lambda handle: self.handle_store.put(statement.statement_id, handle))
        if decision.action == "revision_current":
            assert decision.existing_handle is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            return self._atomic(lambda: self.core.replace(decision.existing_handle, statement.content_utf8), lambda handle: self.handle_store.revise_current(decision.existing_handle, statement.statement_id, handle))
        if decision.action == "revision_keep_history":
            assert decision.target_cell is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            return self._atomic(lambda: self.core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell), lambda handle: self.handle_store.put(statement.statement_id, handle))
        if decision.action == "stitch":
            assert decision.bridge_spec is not None
            return self.core.bridge_add(decision.bridge_spec)
        if decision.action == "unstitch":
            assert decision.bridge_spec is not None
            return self.core.bridge_remove(decision.bridge_spec.bridge_id)
        if decision.action == "defer":
            return None
        if decision.action == "forget":
            assert decision.existing_handle is not None
            return self._atomic(lambda: self.core.remove(decision.existing_handle), lambda _atom: self.handle_store.remove_handle(decision.existing_handle))
        raise AssertionError("unreachable Access action")

    def recall(self, request: AccessRecallRequest) -> AccessRecallResult:
        with self._operation():
            return self._recall_locked(request)

    def _recall_locked(self, request: AccessRecallRequest) -> AccessRecallResult:
        result = self.core.recall(request.to_core_request())
        items = []
        for item in result.items:
            try:
                statement_id = self.handle_store.statement_for_handle(item.handle)
            except KeyError:
                items.append(AccessRecallItem(item.handle, "", None, item.score_q16, "binding_missing"))
                continue
            try:
                statement = self.evidence_store.get_original(statement_id)
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
            return self.handle_store.get(statement_id)

    def _atomic(self, core_action: object, binding_action: object) -> object:
        with self.core.transaction_lease():
            core_before = self.core.state_bytes(); binding_before = self.handle_store.state_bytes()
            try:
                result = core_action(); binding_action(result); return result
            except Exception as original:
                failures = []
                try: self.core.import_state(core_before)
                except Exception as error: failures.append(error)
                try: self.handle_store.import_state(binding_before)
                except Exception as error: failures.append(error)
                if failures: raise AccessConsistencyError("fatal consistency failure during Access rollback") from original
                raise


class AccessConsistencyError(RuntimeError):
    pass
