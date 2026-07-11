from __future__ import annotations

from nollm_core import AtomHandle, CoreRuntime, MemoryAtom

from .evidence_store import EvidenceStore
from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallItem, AccessRecallRequest, AccessRecallResult
from .statement import MemoryStatement
from .workspace_lock import acquire, release
from contextlib import contextmanager
from threading import Condition, RLock, local


class AccessRuntime:
    def __init__(self, core: CoreRuntime, evidence_store: EvidenceStore, handle_store: FileHandleStore) -> None:
        self.core = core
        self.evidence_store = evidence_store
        self.handle_store = handle_store
        access_root = handle_store.path.parent.parent
        if hasattr(evidence_store, "workspace") and evidence_store.workspace.resolve() != access_root.resolve():
            raise ValueError("Evidence and Binding workspace identity mismatch")
        self._transaction_lock, self._lease = acquire(access_root, core.state_path)
        self._lifecycle = Condition(RLock())
        self._state = "OPENING"
        self._active_operations = 0
        self._local = local()
        self._core_lease = None
        try:
            with self._transaction_lock:
                self._core_lease = core.acquire_client_lease("nollm-access")
                self._state = "OPEN"
        except RuntimeError as error:
            if self._core_lease is not None:
                self._core_lease.close()
            release(self._lease)
            raise RuntimeError("AccessRuntime requires an OPEN CoreRuntime") from error
        except Exception:
            if self._core_lease is not None:
                self._core_lease.close()
            release(self._lease)
            raise

    def close(self) -> None:
        self._reject_reentry("close")
        with self._lifecycle:
            if self._state == "CLOSED":
                return
            if self._state == "CLOSING":
                while self._state != "CLOSED":
                    self._lifecycle.wait()
                return
            self._state = "CLOSING"
            self._lifecycle.notify_all()
            while self._active_operations:
                self._lifecycle.wait()
        with self._transaction_lock:
            assert self._core_lease is not None
            self._core_lease.close()
            release(self._lease)
        with self._lifecycle:
            self._state = "CLOSED"
            self._lifecycle.notify_all()

    def __enter__(self) -> "AccessRuntime": return self
    def __exit__(self,*_args: object) -> None: self.close()

    def _require_open(self) -> None:
        if self._state != "OPEN":
            raise RuntimeError(f"AccessRuntime is {self._state.lower()}")

    @property
    def lifecycle_state(self) -> str:
        with self._lifecycle:
            return self._state

    @contextmanager
    def _operation(self, name: str):
        self._enter_operation(name)
        try:
            with self._transaction_lock:
                yield
        finally:
            self._leave_operation()

    def _enter_operation(self, name: str) -> None:
        self._reject_reentry(name)
        with self._lifecycle:
            self._require_open()
            self._active_operations += 1
            self._local.activity = name

    def _leave_operation(self) -> None:
        with self._lifecycle:
            self._active_operations -= 1
            if hasattr(self._local, "activity"):
                del self._local.activity
            self._lifecycle.notify_all()

    def _reject_reentry(self, name: str) -> None:
        if getattr(self._local, "callback_depth", 0) or hasattr(self._local, "activity"):
            raise RuntimeError(f"cannot enter Access {name} during an active Access operation or callback")

    def _callback(self, guard: object, callback: object, *args: object) -> object:
        self._local.callback_depth = getattr(self._local, "callback_depth", 0) + 1
        try:
            return guard.callback(callback, *args)
        finally:
            depth = self._local.callback_depth - 1
            if depth:
                self._local.callback_depth = depth
            else:
                del self._local.callback_depth

    def capture(self, statement: MemoryStatement) -> None:
        with self._operation("capture"):
            self._callback(self._core_lease, self.evidence_store.put_original, statement)

    def apply(self, decision: AccessDecision) -> object | None:
        with self._operation("apply"):
            return self._apply_locked(decision)

    def _apply_locked(self, decision: AccessDecision) -> object | None:
        if decision.action in {"new", "reuse", "revision_current", "revision_keep_history", "defer"} and not self._callback(self._core_lease, self.evidence_store.exists, decision.statement_id):
            raise FileNotFoundError("original Evidence is missing")
        if decision.action == "reuse":
            assert decision.existing_handle is not None
            self._callback(self._core_lease, self.evidence_store.get_original, decision.statement_id)
            with self.core.transaction() as transaction:
                if not transaction.contains(decision.existing_handle):
                    raise KeyError("explicit reuse handle no longer exists")
                self._callback(transaction, self.handle_store.put, decision.statement_id, decision.existing_handle)
            return decision.existing_handle
        if decision.action == "new":
            assert decision.target_cell is not None
            statement = self._callback(self._core_lease, self.evidence_store.get_original, decision.statement_id)
            return self._atomic(lambda tx: tx.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell), lambda tx, handle: self._callback(tx, self.handle_store.put, statement.statement_id, handle))
        if decision.action == "revision_current":
            assert decision.existing_handle is not None
            statement = self._callback(self._core_lease, self.evidence_store.get_original, decision.statement_id)
            return self._atomic(lambda tx: tx.replace(decision.existing_handle, statement.content_utf8), lambda tx, handle: self._callback(tx, self.handle_store.revise_current, decision.existing_handle, statement.statement_id, handle))
        if decision.action == "revision_keep_history":
            assert decision.target_cell is not None
            statement = self._callback(self._core_lease, self.evidence_store.get_original, decision.statement_id)
            return self._atomic(lambda tx: tx.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell), lambda tx, handle: self._callback(tx, self.handle_store.put, statement.statement_id, handle))
        if decision.action == "stitch":
            assert decision.bridge_spec is not None
            with self.core.transaction() as transaction:
                return transaction.bridge_add(decision.bridge_spec)
        if decision.action == "unstitch":
            assert decision.bridge_spec is not None
            with self.core.transaction() as transaction:
                return transaction.bridge_remove(decision.bridge_spec.bridge_id)
        if decision.action == "defer":
            return None
        if decision.action == "forget":
            assert decision.existing_handle is not None
            return self._atomic(lambda tx: tx.remove(decision.existing_handle), lambda tx, _atom: self._callback(tx, self.handle_store.remove_handle, decision.existing_handle))
        raise AssertionError("unreachable Access action")

    def recall(self, request: AccessRecallRequest) -> AccessRecallResult:
        with self._operation("recall"):
            return self._recall_locked(request)

    def _recall_locked(self, request: AccessRecallRequest) -> AccessRecallResult:
        with self.core.transaction() as transaction:
            result = transaction.recall(request.to_core_request())
            items = []
            for item in result.items:
                try:
                    statement_id = self._callback(transaction, self.handle_store.statement_for_handle, item.handle)
                except KeyError:
                    items.append(AccessRecallItem(item.handle, "", None, item.score_q16, "binding_missing"))
                    continue
                try:
                    statement = self._callback(transaction, self.evidence_store.get_original, statement_id)
                except FileNotFoundError:
                    items.append(AccessRecallItem(item.handle, statement_id, None, item.score_q16, "evidence_missing"))
                else:
                    if statement.content_utf8 != item.atom.payload_utf8:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, None, item.score_q16, "evidence_payload_mismatch"))
                    else:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, statement.content_utf8, item.score_q16))
        return AccessRecallResult(result.request_id, tuple(items), result.budget_exhausted)

    def saved_handle(self, statement_id: str) -> AtomHandle:
        with self._operation("saved_handle"):
            return self._callback(self._core_lease, self.handle_store.get, statement_id)

    def _atomic(self, core_action: object, binding_action: object) -> object:
        with self.core.transaction() as transaction:
            core_before = transaction.state_bytes()
            binding_before = self._callback(transaction, self.handle_store.state_bytes)
            try:
                result = core_action(transaction)
                binding_action(transaction, result)
                return result
            except Exception as original:
                failures = []
                try: transaction.import_state(core_before)
                except Exception as error: failures.append(error)
                try: self._callback(transaction, self.handle_store.import_state, binding_before)
                except Exception as error: failures.append(error)
                if failures: raise AccessConsistencyError("fatal consistency failure during Access rollback") from original
                raise


class AccessConsistencyError(RuntimeError):
    pass
