from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
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
        self._last_commit_state = "pre_commit"

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

    @property
    def last_commit_state(self) -> str:
        with self._lifecycle_lock:
            return self._last_commit_state

    def close(self) -> None:
        with self._lifecycle_lock:
            if self._state != "FAILED":
                self._state = "CLOSED"

    def __enter__(self) -> "AccessRuntime":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    @contextmanager
    def _operation(self):
        with self._lifecycle_lock:
            if self._state != "OPEN":
                raise RuntimeError(f"AccessRuntime is {self._state.lower()}")
            with self._composition_lock:
                if not self._core.is_open:
                    raise RuntimeError("AccessRuntime Core is closed")
                with self._core.operation_lease():
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

    def apply_if_state(
        self,
        expected_core_state_sha256: str,
        statement: MemoryStatement,
        decision: AccessDecision,
    ) -> "ConditionalAccessApplyResult":
        if (
            type(expected_core_state_sha256) is not str
            or len(expected_core_state_sha256) != 64
        ):
            raise ValueError("expected_core_state_sha256 must be SHA-256 text")
        if type(statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        if type(decision) is not AccessDecision:
            raise TypeError("decision must be AccessDecision")
        if decision.statement_id != statement.statement_id:
            raise ValueError("decision does not bind the conditional Statement")
        with self._operation():
            current = sha256(self._core.export_state_bytes()).hexdigest()
            if current != expected_core_state_sha256:
                return ConditionalAccessApplyResult(
                    "stale_zero_write", None, False, current
                )
            existed_before = self._evidence_store.exists(statement.statement_id)
            try:
                if hasattr(self._evidence_store, "put"):
                    self._evidence_store.put(statement)
                else:
                    self._evidence_store.put_original(statement)
                result = self._apply_locked(decision)
            except Exception:
                if not existed_before and hasattr(self._evidence_store, "discard_new"):
                    self._evidence_store.discard_new(statement)
                raise
            except BaseException:
                if (
                    not existed_before
                    and self._last_commit_state == "pre_commit"
                    and hasattr(self._evidence_store, "discard_new")
                ):
                    self._evidence_store.discard_new(statement)
                raise
            return ConditionalAccessApplyResult(
                "committed", result, not existed_before, current
            )

    def _apply_locked(self, decision: AccessDecision) -> object | None:
        self._set_commit_state("pre_commit")
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
                self._set_commit_state("committed")
                return decision.existing_handle
            self._handle_store.put(decision.statement_id, decision.existing_handle)
            self._set_commit_state("committed")
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
            result = self._core.bridge_add(decision.bridge_spec)
            self._set_commit_state("committed")
            return result
        if decision.action == "unstitch":
            assert decision.bridge_spec is not None
            result = self._core.bridge_remove(decision.bridge_spec.bridge_id)
            self._set_commit_state("committed")
            return result
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
                    items.append(AccessRecallItem(item.handle, "", None, item.score_q16, "binding_missing", item.path))
                    continue
                try:
                    statement = self._get_statement(statement_id)
                except FileNotFoundError:
                    items.append(AccessRecallItem(item.handle, statement_id, None, item.score_q16, "evidence_missing", item.path))
                except (ValueError, UnicodeError):
                    items.append(AccessRecallItem(item.handle, statement_id, None, item.score_q16, "evidence_corrupt", item.path))
                else:
                    if statement.content_utf8 != item.atom.payload_utf8:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, None, item.score_q16, "evidence_payload_mismatch", item.path))
                    else:
                        items.append(AccessRecallItem(item.handle, statement.statement_id, statement.content_utf8, item.score_q16, path=item.path))
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
            self._set_commit_state("commit_state_unknown")
            binding_action(result)
            self._set_commit_state("committed")
            return result
        except Exception as original:
            failures: list[AccessRollbackFailure] = []
            try:
                self._core.import_state_bytes(core_before)
            except Exception as error:
                failures.append(AccessRollbackFailure.from_error("core", error))
            try:
                self._handle_store.import_state(binding_before)
            except Exception as error:
                failures.append(AccessRollbackFailure.from_error("binding", error))
            if failures:
                self._mark_failed("commit_state_unknown")
                raise AccessConsistencyError(original, tuple(failures)) from original
            self._set_commit_state("rolled_back_failure")
            raise
        except BaseException:
            # Exception subclasses receive rollback. Process-control BaseException
            # subclasses are conservatively indeterminate and poison this runtime.
            self._mark_failed("commit_state_unknown")
            raise

    def _set_commit_state(self, state: str) -> None:
        with self._lifecycle_lock:
            self._last_commit_state = state

    def _mark_failed(self, commit_state: str) -> None:
        with self._lifecycle_lock:
            self._last_commit_state = commit_state
            self._state = "FAILED"


class AccessConsistencyError(RuntimeError):
    def __init__(self, original_error: Exception, rollback_failures: tuple["AccessRollbackFailure", ...]) -> None:
        super().__init__("fatal consistency failure during trusted Access rollback")
        self.original_error = original_error
        self.rollback_failures = rollback_failures
        self.commit_state = "commit_state_unknown"


@dataclass(frozen=True)
class ConditionalAccessApplyResult:
    commit_state: str
    result: object | None
    statement_created: bool
    observed_core_state_sha256: str

    def __post_init__(self) -> None:
        if self.commit_state not in {"stale_zero_write", "committed"}:
            raise ValueError("unknown conditional Access commit state")
        if type(self.statement_created) is not bool:
            raise TypeError("statement_created must be bool")
        if (
            type(self.observed_core_state_sha256) is not str
            or len(self.observed_core_state_sha256) != 64
        ):
            raise ValueError("observed Core state must be SHA-256 text")
        if self.commit_state == "stale_zero_write" and (
            self.result is not None or self.statement_created
        ):
            raise ValueError("stale conditional commit must be zero-write")


@dataclass(frozen=True)
class AccessRollbackFailure:
    component: str
    error_type: str
    message: str

    @classmethod
    def from_error(cls, component: str, error: Exception) -> "AccessRollbackFailure":
        return cls(component, type(error).__name__, str(error))

    def to_mapping(self) -> dict[str, str]:
        return {"component": self.component, "error_type": self.error_type, "message": self.message}
