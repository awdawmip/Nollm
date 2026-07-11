from __future__ import annotations

from nollm_core import AtomHandle, CoreRuntime, MemoryAtom

from .evidence_store import EvidenceStore
from .handle_store import FileHandleStore
from .placement_contract import AccessDecision
from .recall import AccessRecallItem, AccessRecallRequest, AccessRecallResult
from .statement import MemoryStatement


class AccessRuntime:
    def __init__(self, core: CoreRuntime, evidence_store: EvidenceStore, handle_store: FileHandleStore) -> None:
        self.core = core
        self.evidence_store = evidence_store
        self.handle_store = handle_store

    def capture(self, statement: MemoryStatement) -> None:
        self.evidence_store.put_original(statement)

    def apply(self, decision: AccessDecision) -> object | None:
        if decision.action not in {"stitch", "unstitch"} and not self.evidence_store.exists(decision.statement_id):
            raise FileNotFoundError("original Evidence is missing")
        if decision.action == "reuse":
            assert decision.existing_handle is not None
            if not self.core.contains(decision.existing_handle):
                raise KeyError("explicit reuse handle no longer exists")
            self.handle_store.put(decision.statement_id, decision.existing_handle)
            return decision.existing_handle
        if decision.action == "new":
            assert decision.target_cell is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            handle = self.core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell)
            self.handle_store.put(statement.statement_id, handle)
            return handle
        if decision.action == "revision_current":
            assert decision.existing_handle is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            handle = self.core.replace(decision.existing_handle, statement.content_utf8)
            self.handle_store.remove_handle(decision.existing_handle)
            self.handle_store.put(statement.statement_id, handle)
            return handle
        if decision.action == "revision_keep_history":
            assert decision.target_cell is not None
            statement = self.evidence_store.get_original(decision.statement_id)
            handle = self.core.put(MemoryAtom(statement.statement_id, statement.content_utf8), decision.target_cell)
            self.handle_store.put(statement.statement_id, handle)
            return handle
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
            atom = self.core.remove(decision.existing_handle)
            self.handle_store.remove_handle(decision.existing_handle)
            return atom
        raise AssertionError("unreachable Access action")

    def recall(self, request: AccessRecallRequest) -> AccessRecallResult:
        result = self.core.recall(request.to_core_request())
        items = []
        for item in result.items:
            try:
                statement_id = self.handle_store.statement_for_handle(item.handle)
            except KeyError:
                statement_id = item.atom.atom_id
            try:
                statement = self.evidence_store.get_original(statement_id)
            except FileNotFoundError:
                items.append(AccessRecallItem(item.handle, statement_id, None, item.score_q16, "evidence_missing"))
            else:
                items.append(AccessRecallItem(item.handle, statement.statement_id, statement.content_utf8, item.score_q16))
        return AccessRecallResult(result.request_id, tuple(items), result.budget_exhausted)

    def saved_handle(self, statement_id: str) -> AtomHandle:
        return self.handle_store.get(statement_id)
