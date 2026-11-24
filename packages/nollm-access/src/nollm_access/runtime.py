from __future__ import annotations

from contextlib import contextmanager
from base64 import b64decode, b64encode
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from threading import RLock

from nollm_core import AtomHandle, CoreRuntime

from .content_budget import ContentBudgetPolicy, validate_content_projection
from .statement_store import StatementStore, _atomic_write
from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallItem, AccessRecallRequest, AccessRecallResult
from .reorganization import project_reorganization, reorganization_handles
from .statement import MemoryStatement
from .workspace_lock import composition_lock


class AccessRuntime:
    """Trusted local coordinator for Evidence, Handle binding, and Core."""

    def __init__(self, core: CoreRuntime, evidence_store: StatementStore, handle_store: FileHandleStore,
                 *, content_budget: ContentBudgetPolicy | None = None) -> None:
        self._core = core
        self._evidence_store = evidence_store
        self._handle_store = handle_store
        access_root = handle_store.path.parent.parent.resolve()
        if hasattr(evidence_store, "workspace") and evidence_store.workspace.resolve() != access_root:
            raise ValueError("Evidence and Binding workspace identity mismatch")
        if not core.is_open:
            raise RuntimeError("AccessRuntime requires an open CoreRuntime")
        self._canonical_access_root = access_root
        self._content_budget = content_budget if content_budget is not None else ContentBudgetPolicy.load(access_root)
        self._canonical_core_state_path = core.state_path.resolve()
        self._composition_lock = composition_lock(access_root, core.state_path)
        self._lifecycle_lock = RLock()
        self._state = "OPEN"
        self._last_commit_state = "pre_commit"
        self._reorganization_path = access_root / "access" / "reorganization.pending.json"
        with self._composition_lock, self._core.operation_lease():
            if self._reorganization_path.exists():
                self._recover_reorganization()
                if content_budget is None:
                    self._content_budget = ContentBudgetPolicy.load(access_root)

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
    def content_budget(self) -> ContentBudgetPolicy | None:
        return self._content_budget

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
    def reorganization_scope(self):
        """Hold Access coordination locks across Host planning and public calls.

        Individual operations acquire their own Core lease, so adapters may
        invoke public Access and Core APIs while this scope is held.
        """
        with self._lifecycle_lock:
            if self._state != "OPEN":
                raise RuntimeError(f"AccessRuntime is {self._state.lower()}")
            with self._composition_lock:
                if not self._core.is_open:
                    raise RuntimeError("AccessRuntime Core is closed")
                yield

    @contextmanager
    def _operation(self):
        with self.reorganization_scope():
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

    def reorganize(
        self,
        decisions: tuple[AccessDecision, ...],
        *,
        statements: tuple[MemoryStatement, ...] = (),
        content_budget: ContentBudgetPolicy | None = None,
        configuration_files: dict[Path, bytes] | None = None,
    ) -> tuple[object, ...]:
        """Apply explicit Host changes as one final-layout operation.

        Configuration paths are field-relative internal inputs; the calling Host
        adapter validates which settings it permits. Captured Statements remain
        readable after a later commit failure. On interruption, the next Access
        open restores the affected cells, bindings and settings before use.
        """
        if not isinstance(decisions, tuple) or not isinstance(statements, tuple):
            raise TypeError("reorganization decisions and statements must be tuples")
        handles = reorganization_handles(decisions)
        configuration = {}
        for relative, payload in (configuration_files or {}).items():
            relative = Path(relative)
            if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
                raise ValueError("configuration path must be relative to this field")
            if relative == Path("access/content_budget.json"):
                raise ValueError("use content_budget for the content budget configuration")
            if relative == Path("access/reorganization.pending.json"):
                raise ValueError("configuration cannot replace its reorganization recovery record")
            if not isinstance(payload, bytes):
                raise TypeError("configuration values must be bytes")
            configuration[relative] = payload
        if content_budget is not None:
            configuration[Path("access/content_budget.json")] = (
                json.dumps(content_budget.to_mapping(), ensure_ascii=False, indent=2) + "\n"
            ).encode("utf-8")
        if not decisions and not configuration:
            raise ValueError("reorganization requires a decision or configuration change")

        with self._operation():
            return self._reorganize_locked(decisions, statements, content_budget, configuration, handles)

    def _reorganize_locked(
        self, decisions, statements, content_budget, configuration, handles,
        *, fresh_statement_ids=frozenset(),
    ) -> tuple[object, ...]:
        self._set_commit_state("pre_commit")
        supplied = {}
        fresh = set(fresh_statement_ids)
        for statement in statements:
            if not isinstance(statement, MemoryStatement):
                raise TypeError("reorganization statements must be MemoryStatement values")
            identity = statement.statement_id
            if identity in supplied and supplied[identity] != statement:
                raise ValueError("conflicting supplied Statement versions")
            if self._evidence_store.exists(identity):
                if self._get_statement(identity) != statement:
                    raise FileExistsError("statement already exists with different content")
            else:
                fresh.add(identity)
            supplied[identity] = statement
        needed = {decision.statement_id for decision in decisions if decision.action in {
            "new", "revision_keep_history", "revision_current", "reuse",
        }}
        available = dict(supplied)
        for identity in needed - available.keys():
            available[identity] = self._get_statement(identity)

        addresses = tuple(sorted({handle.geometry_address for handle in handles},
                                 key=lambda cell: cell.stable_key()))
        before_cells = {
            cell: {handle.local_atom_id: atom for handle, atom in self._core.atoms_at(cell)}
            for cell in addresses
        }
        bindings = self._handle_store.bindings_for_handles(handles)
        unavailable = set()
        # New immutable IDs cannot already have a valid binding. Historical
        # IDs require a physical lookup to preserve one binding per ID.
        for identity in needed - fresh:
            try:
                existing = self._handle_store.get(identity)
            except KeyError:
                continue
            if existing not in handles:
                unavailable.add(identity)
        plan = project_reorganization(decisions, available, before_cells, bindings,
                                      frozenset(unavailable))
        next_budget = content_budget if content_budget is not None else self._content_budget
        validate_content_projection(self._core, next_budget, before_cells, plan.final_cells,
                                    check_all_layers=content_budget is not None)

        # Capture follows successful preflight and remains independent of
        # later placement: rollback never deletes accepted Evidence.
        for statement in supplied.values():
            if hasattr(self._evidence_store, "put"):
                self._evidence_store.put(statement)
            else:
                self._evidence_store.put_original(statement)
        bindings_changed = plan.final_bindings != bindings
        if not plan.commands and not bindings_changed and not configuration:
            self._set_commit_state("committed")
            return plan.results
        before_policy = self._content_budget
        record = {
            "schema_version": "nollm_access_reorganization_undo_v1",
            "core_before": self._core.export_cell_state(addresses).decode("utf-8") if plan.commands else None,
            "bindings_before": self._handle_store.export_handle_state(handles).decode("utf-8") if bindings_changed else None,
            "configuration_before": {},
        }
        for relative in configuration:
            path = self._canonical_access_root / relative
            record["configuration_before"][relative.as_posix()] = (
                b64encode(path.read_bytes()).decode("ascii") if path.exists() else None
            )
        _atomic_write(self._reorganization_path,
                      (json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
        try:
            self._set_commit_state("commit_state_unknown")
            core_results = self._core.apply_batch(plan.commands) if plan.commands else ()
            if bindings_changed:
                self._handle_store.replace_handles(handles, plan.final_bindings,
                                                   fresh_statement_ids=tuple(sorted(fresh)))
            for relative, payload in configuration.items():
                _atomic_write(self._canonical_access_root / relative, payload)
            self._reorganization_path.unlink()
        except Exception as original:
            failures = self._restore_reorganization(record)
            if failures:
                self._mark_failed("commit_state_unknown")
                raise AccessConsistencyError(original, failures) from original
            self._content_budget = before_policy
            self._set_commit_state("rolled_back_failure")
            raise
        except BaseException:
            self._mark_failed("commit_state_unknown")
            raise
        self._content_budget = next_budget
        self._set_commit_state("committed")
        return tuple(core_results[index] if index is not None else result
                     for index, result in zip(plan.command_indexes, plan.results))

    def _restore_reorganization(self, record: dict[str, object]) -> tuple["AccessRollbackFailure", ...]:
        failures = []
        for name, payload, restore in (
            ("core", record["core_before"], self._core.import_cell_state),
            ("binding", record["bindings_before"], self._handle_store.import_handle_state),
        ):
            if payload is not None:
                try:
                    restore(payload.encode("utf-8"))
                except Exception as error:
                    failures.append(AccessRollbackFailure.from_error(name, error))
        for relative, payload in record["configuration_before"].items():
            try:
                path = self._canonical_access_root / relative
                if payload is None:
                    path.unlink(missing_ok=True)
                else:
                    _atomic_write(path, b64decode(payload))
            except Exception as error:
                failures.append(AccessRollbackFailure.from_error(relative, error))
        if not failures:
            try:
                self._reorganization_path.unlink(missing_ok=True)
            except Exception as error:
                failures.append(AccessRollbackFailure.from_error("reorganization_record", error))
        return tuple(failures)

    def _recover_reorganization(self) -> None:
        record = json.loads(self._reorganization_path.read_text(encoding="utf-8"))
        if record.get("schema_version") != "nollm_access_reorganization_undo_v1":
            raise ValueError("unsupported Access reorganization recovery record")
        failures = self._restore_reorganization(record)
        if failures:
            self._mark_failed("commit_state_unknown")
            raise AccessConsistencyError(RuntimeError("interrupted Access reorganization"), failures)

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
                result = self._apply_locked(
                    decision, fresh_statement_ids=frozenset((statement.statement_id,))
                    if not existed_before else frozenset(),
                )
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

    def _apply_locked(self, decision: AccessDecision, *, fresh_statement_ids=frozenset()) -> object | None:
        self._set_commit_state("pre_commit")
        if decision.action in {"new", "reuse", "revision_current", "revision_keep_history", "move", "forget"}:
            handles = reorganization_handles((decision,))
            return self._reorganize_locked(
                (decision,), (), None, {}, handles, fresh_statement_ids=fresh_statement_ids,
            )[0]
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
            if not self._evidence_store.exists(decision.statement_id):
                raise FileNotFoundError("original Evidence is missing")
            return None
        raise AssertionError("unreachable Access action")

    def recall(self, request: AccessRecallRequest) -> AccessRecallResult:
        with self._operation():
            result = self._core.recall(request.to_core_request())
            if not result.items:
                return AccessRecallResult(result.request_id, (), result.budget_exhausted)
            bindings = self._handle_store.bindings_for_handles(tuple(item.handle for item in result.items))
            current = {binding.handle: binding.current_statement_id for binding in bindings}
            items = []
            for item in result.items:
                statement_id = current.get(item.handle)
                if statement_id is None:
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
                        items.append(AccessRecallItem(item.handle, statement.statement_id, statement.content_utf8,
                                                      item.score_q16, path=item.path, statement=statement))
            return AccessRecallResult(result.request_id, tuple(items), result.budget_exhausted)

    def saved_handle(self, statement_id: str) -> AtomHandle:
        with self._operation():
            return self._handle_store.get(statement_id)

    def _get_statement(self, statement_id: str) -> MemoryStatement:
        if hasattr(self._evidence_store, "get"):
            return self._evidence_store.get(statement_id)
        return self._evidence_store.get_original(statement_id)

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
