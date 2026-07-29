from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from time import time_ns

from nollm_core import (
    AtomHandle,
    CoreRuntime,
    GeometryAddress,
    JunctionRequest,
    PhysicalFieldScope,
    RelationGroupJunctionRequest,
)

from .cartography import ProgressiveAtlasPage, ProgressiveAtlasPolicy
from .handle_store import FileHandleStore
from .memory_loop import AccessMemoryLoop
from .placement_contract import (
    AccessDecision,
    ProvisionalRevisionDecision,
    RevisionConfirmationResult,
)
from .provenance import FileStatementProvenanceStore
from .runtime import AccessConsistencyError, AccessRuntime
from .statement import MemoryStatement
from .statement_store import FileStatementStore


FIELD_ENCOUNTER_SCHEMA_VERSION = "nollm_access_field_encounter_v1"
FIELD_ENCOUNTER_WIRE_VERSION = "nollm_openclaw_field_encounter_v1"
ENCOUNTER_WRITER_WIRE_VERSION = "nollm_encounter_writer_v1"
ENCOUNTER_ACTIONS = frozenset(
    {
        "surface",
        "open_region",
        "enter_locality",
        "expand_same_entry",
        "select_fact",
        "select_vacancy",
        "none",
        "defer",
        "cancel",
    }
)
SEMANTIC_RELATIONS = frozenset(
    {"same", "revision", "related_distinct", "unrelated", "uncertain"}
)
VACANCY_KINDS = frozenset(
    {
        "LOCAL_VACANCY",
        "BOUNDARY_VACANCY",
        "JUNCTION_VACANCY",
        "NEUTRAL_SEED_VACANCY",
    }
)
MUTATION_EFFECTS = frozenset({"reuse", "provisional_revision", "place"})


def _canonical_sha(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _required_text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be non-empty text")
    return value


def _text_tuple(value: object, name: str, limit: int) -> tuple[str, ...]:
    if (
        type(value) is not tuple
        or len(value) > limit
        or any(type(item) is not str or not item for item in value)
    ):
        raise TypeError(f"{name} must be a bounded non-empty-text tuple")
    return value


@dataclass(frozen=True)
class PendingProposition:
    proposition_id: str
    content_utf8: str
    evidence_refs: tuple[str, ...]
    origin_kinds: tuple[str, ...]
    derived_from_statement_ids: tuple[str, ...]
    formation_version: str

    def __post_init__(self) -> None:
        _required_text(self.proposition_id, "proposition_id")
        _required_text(self.content_utf8, "content_utf8")
        _text_tuple(self.evidence_refs, "evidence_refs", 64)
        if not self.evidence_refs:
            raise ValueError("pending proposition requires Evidence refs")
        _text_tuple(self.origin_kinds, "origin_kinds", 16)
        if not self.origin_kinds:
            raise ValueError("pending proposition requires origin kinds")
        _text_tuple(
            self.derived_from_statement_ids, "derived_from_statement_ids", 32
        )
        _required_text(self.formation_version, "formation_version")

    @property
    def identity(self) -> str:
        return _canonical_sha(self.to_mapping())

    def to_mapping(self) -> dict[str, object]:
        return {
            "proposition_id": self.proposition_id,
            "content_utf8": self.content_utf8,
            "evidence_refs": list(self.evidence_refs),
            "origin_kinds": list(self.origin_kinds),
            "derived_from_statement_ids": list(
                self.derived_from_statement_ids
            ),
            "formation_version": self.formation_version,
        }


@dataclass(frozen=True)
class FieldEncounterRequest:
    operation_id: str
    scope_id: str
    workspace_id: str
    stimulus_material: tuple[str, ...]
    optional_pending_proposition: PendingProposition | None
    field_scope: PhysicalFieldScope
    surface_policy: ProgressiveAtlasPolicy
    locality_max_results: int
    locality_max_chars: int
    vacancy_budget: int
    expected_state_identity: str
    created_at_ms: int
    ttl_ms: int

    def __post_init__(self) -> None:
        for name in ("operation_id", "scope_id", "workspace_id"):
            _required_text(getattr(self, name), name)
        material = _text_tuple(self.stimulus_material, "stimulus_material", 32)
        if not material:
            raise ValueError("stimulus material is required")
        if sum(len(item) for item in material) > 32000:
            raise ValueError("stimulus material exceeds operation budget")
        if self.optional_pending_proposition is not None and type(
            self.optional_pending_proposition
        ) is not PendingProposition:
            raise TypeError("optional_pending_proposition is invalid")
        if type(self.field_scope) is not PhysicalFieldScope:
            raise TypeError("field_scope must be PhysicalFieldScope")
        if type(self.surface_policy) is not ProgressiveAtlasPolicy:
            raise TypeError("surface_policy must be ProgressiveAtlasPolicy")
        if (
            type(self.locality_max_results) is not int
            or not 1 <= self.locality_max_results <= 16
            or type(self.locality_max_chars) is not int
            or not 1 <= self.locality_max_chars <= 12000
            or type(self.vacancy_budget) is not int
            or not 1 <= self.vacancy_budget <= 16
        ):
            raise ValueError("Field Encounter budgets are invalid")
        if (
            type(self.expected_state_identity) is not str
            or len(self.expected_state_identity) != 64
        ):
            raise ValueError("expected_state_identity must be SHA-256 text")
        if type(self.created_at_ms) is not int or self.created_at_ms < 0:
            raise ValueError("created_at_ms must be non-negative")
        if type(self.ttl_ms) is not int or not 1 <= self.ttl_ms <= 900000:
            raise ValueError("ttl_ms must be in [1,900000]")

    @property
    def expires_at_ms(self) -> int:
        return self.created_at_ms + self.ttl_ms


@dataclass(frozen=True)
class EncounterFactCard:
    fact_id: str
    statement_id: str
    content_utf8: str
    handle: AtomHandle
    geometry_path: tuple[str, ...]
    revision_eligible: bool
    provenance_sha256: str | None
    state_identity: str

    def __post_init__(self) -> None:
        for name in ("fact_id", "statement_id", "content_utf8"):
            _required_text(getattr(self, name), name)
        if type(self.handle) is not AtomHandle:
            raise TypeError("fact handle must be an exact AtomHandle")
        _text_tuple(self.geometry_path, "geometry_path", 64)
        if type(self.revision_eligible) is not bool:
            raise TypeError("revision_eligible must be bool")
        if self.provenance_sha256 is not None and (
            type(self.provenance_sha256) is not str
            or len(self.provenance_sha256) != 64
        ):
            raise ValueError("provenance_sha256 must be null or SHA-256 text")
        if type(self.state_identity) is not str or len(self.state_identity) != 64:
            raise ValueError("fact state identity must be SHA-256 text")

    def to_mapping(self) -> dict[str, object]:
        return {
            "fact_id": self.fact_id,
            "statement_id": self.statement_id,
            "content_utf8": self.content_utf8,
            "handle": self.handle.to_mapping(),
            "geometry_path": list(self.geometry_path),
            "revision_eligible": self.revision_eligible,
            "provenance_sha256": self.provenance_sha256,
            "state_identity": self.state_identity,
        }


@dataclass(frozen=True)
class EncounterVacancyCard:
    vacancy_id: str
    vacancy_kind: str
    address: GeometryAddress
    state_identity: str
    capacity: int
    boundary: bool
    relation_groups: tuple[tuple[GeometryAddress, ...], ...]
    free_face_count: int
    expires_at_ms: int

    def __post_init__(self) -> None:
        _required_text(self.vacancy_id, "vacancy_id")
        if self.vacancy_kind not in VACANCY_KINDS:
            raise ValueError("unknown vacancy kind")
        if type(self.address) is not GeometryAddress:
            raise TypeError("vacancy address must be GeometryAddress")
        if type(self.state_identity) is not str or len(self.state_identity) != 64:
            raise ValueError("vacancy state identity must be SHA-256 text")
        if type(self.capacity) is not int or self.capacity < 1:
            raise ValueError("vacancy capacity must be positive")
        if type(self.boundary) is not bool:
            raise TypeError("vacancy boundary must be bool")
        if type(self.relation_groups) is not tuple:
            raise TypeError("relation_groups must be a tuple")
        for group in self.relation_groups:
            if (
                type(group) is not tuple
                or not group
                or any(type(cell) is not GeometryAddress for cell in group)
            ):
                raise TypeError("vacancy relation group is invalid")
        if type(self.free_face_count) is not int or not 0 <= self.free_face_count <= 6:
            raise ValueError("free_face_count must be in [0,6]")
        if type(self.expires_at_ms) is not int or self.expires_at_ms < 0:
            raise ValueError("expires_at_ms must be non-negative")

    def to_mapping(self) -> dict[str, object]:
        return {
            "vacancy_id": self.vacancy_id,
            "vacancy_kind": self.vacancy_kind,
            "address": self.address.to_mapping(),
            "state_identity": self.state_identity,
            "capacity": self.capacity,
            "boundary": self.boundary,
            "relation_groups": [
                [cell.to_mapping() for cell in group]
                for group in self.relation_groups
            ],
            "free_face_count": self.free_face_count,
            "expires_at_ms": self.expires_at_ms,
        }


@dataclass(frozen=True)
class FieldEncounterPage:
    operation_id: str
    root_identity: str
    page_fingerprint: str
    entry_id: str
    entry_cell: GeometryAddress
    facts: tuple[EncounterFactCard, ...]
    vacancies: tuple[EncounterVacancyCard, ...]
    state_identity: str
    legal_actions: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema_version": FIELD_ENCOUNTER_SCHEMA_VERSION,
            "operation_id": self.operation_id,
            "root_identity": self.root_identity,
            "page_fingerprint": self.page_fingerprint,
            "entry_id": self.entry_id,
            "entry_cell": self.entry_cell.to_mapping(),
            "facts": [item.to_mapping() for item in self.facts],
            "vacancies": [item.to_mapping() for item in self.vacancies],
            "state_identity": self.state_identity,
            "legal_actions": list(self.legal_actions),
        }


@dataclass(frozen=True)
class EncounterEffect:
    effect_kind: str
    pending_proposition_identity: str | None
    selected_fact_id: str | None = None
    selected_vacancy_id: str | None = None
    provisional_revision: ProvisionalRevisionDecision | None = None
    retryable: bool = False

    @property
    def commit_eligible(self) -> bool:
        return self.effect_kind in MUTATION_EFFECTS


@dataclass(frozen=True)
class FieldEncounterResult:
    operation_id: str
    terminal_kind: str
    semantic_relation: str | None
    recalled_statement_ids: tuple[str, ...]
    state_identity: str
    path_digest: str
    effect: EncounterEffect

    def __post_init__(self) -> None:
        if self.terminal_kind not in {"fact", "vacancy", "ambiguous", "exhausted"}:
            raise ValueError("unknown Encounter terminal kind")
        if self.semantic_relation is not None and self.semantic_relation not in SEMANTIC_RELATIONS:
            raise ValueError("unknown Encounter semantic relation")
        _text_tuple(
            self.recalled_statement_ids, "recalled_statement_ids", 16
        )
        if len(self.recalled_statement_ids) != len(set(self.recalled_statement_ids)):
            raise ValueError("recalled Statement identities must be unique")


@dataclass(frozen=True)
class EncounterCommitRequest:
    operation_id: str
    expected_core_state_identity: str
    terminal_result_identity: str
    pending_proposition_identity: str
    statement: MemoryStatement
    revision_confirmation: RevisionConfirmationResult | None = None

    def __post_init__(self) -> None:
        _required_text(self.operation_id, "operation_id")
        for name in (
            "expected_core_state_identity",
            "terminal_result_identity",
            "pending_proposition_identity",
        ):
            value = getattr(self, name)
            if type(value) is not str or len(value) != 64:
                raise ValueError(f"{name} must be SHA-256 text")
        if type(self.statement) is not MemoryStatement:
            raise TypeError("statement must be MemoryStatement")
        if self.revision_confirmation is not None and type(
            self.revision_confirmation
        ) is not RevisionConfirmationResult:
            raise TypeError("revision_confirmation is invalid")


@dataclass(frozen=True)
class EncounterCommitResult:
    commit_state: str
    operation_id: str
    statement_id: str
    handle: AtomHandle | None
    core_write_count: int
    reopen_verified: bool
    error_type: str | None = None

    def __post_init__(self) -> None:
        if self.commit_state not in {
            "not_committed",
            "committed_and_verified",
            "committed_readback_unknown",
            "stale_zero_write",
            "retryable_conflict",
        }:
            raise ValueError("unknown Encounter commit state")
        if type(self.core_write_count) is not int or self.core_write_count < 0:
            raise ValueError("core_write_count must be non-negative")
        if type(self.reopen_verified) is not bool:
            raise TypeError("reopen_verified must be bool")


@dataclass(frozen=True)
class FieldEncounterOperation:
    request: FieldEncounterRequest
    root_page: ProgressiveAtlasPage
    current_page: ProgressiveAtlasPage
    page_path: tuple[str, ...]
    locality: FieldEncounterPage | None = None
    result: FieldEncounterResult | None = None
    committed: bool = False

    @property
    def root_identity(self) -> str:
        return self.root_page.atlas_fingerprint


class FieldEncounterEngine:
    """Finite in-process Field Encounter coordinator over public geometry state."""

    def __init__(self, workspace: str | Path) -> None:
        if type(workspace) is str:
            root = Path(_required_text(workspace, "workspace"))
        elif isinstance(workspace, Path):
            root = workspace
        else:
            raise TypeError("workspace must be a string or Path")
        self._workspace = root.resolve()
        self._operations: dict[str, FieldEncounterOperation] = {}

    def begin(self, request: FieldEncounterRequest) -> FieldEncounterOperation:
        if type(request) is not FieldEncounterRequest:
            raise TypeError("request must be FieldEncounterRequest")
        if request.operation_id in self._operations:
            raise ValueError("Field Encounter operation identity is not reusable")
        with AccessMemoryLoop(self._workspace) as loop:
            observed = loop.core_state_sha256()
            if observed != request.expected_state_identity:
                raise ValueError("Field Encounter expected state is stale")
            page = loop.build_progressive_atlas(
                request.operation_id, request.surface_policy, request.field_scope
            )
        operation = FieldEncounterOperation(
            request, page, page, (page.page_fingerprint,)
        )
        self._operations[request.operation_id] = operation
        return operation

    def get(self, operation_id: str) -> FieldEncounterOperation:
        _required_text(operation_id, "operation_id")
        try:
            return self._operations[operation_id]
        except KeyError as exc:
            raise KeyError("unknown Field Encounter operation") from exc

    def open_region(
        self, operation_id: str, region_id: str
    ) -> FieldEncounterOperation:
        operation = self._active(operation_id)
        if operation.locality is not None:
            raise ValueError("Field Encounter already entered one Locality")
        with AccessMemoryLoop(self._workspace) as loop:
            page = loop.open_progressive_region(
                operation.current_page, region_id, operation_id + ":region"
            )
        updated = replace(
            operation,
            current_page=page,
            page_path=(*operation.page_path, page.page_fingerprint),
        )
        self._operations[operation_id] = updated
        return updated

    def enter_locality(
        self, operation_id: str, region_id: str, entry_id: str
    ) -> FieldEncounterPage:
        operation = self._active(operation_id)
        page = operation.current_page
        region = next(
            (item for item in page.regions if item.region_id == region_id), None
        )
        if region is None:
            raise ValueError("region is not visible on the current Encounter page")
        entries = [
            item for item in region.support_entries if item["entry_id"] == entry_id
        ]
        if len(entries) != 1:
            raise ValueError("entry is not uniquely visible in the selected region")
        entry = GeometryAddress.from_mapping(entries[0]["entry_cell"])
        state = page.core_state_sha256
        facts = self._facts(operation, entry, state)
        vacancies = self._vacancies(operation, entry, facts, state)
        payload = {
            "root": operation.root_identity,
            "path": [*operation.page_path, region_id, entry_id],
            "facts": [item.to_mapping() for item in facts],
            "vacancies": [item.to_mapping() for item in vacancies],
        }
        locality = FieldEncounterPage(
            operation_id,
            operation.root_identity,
            _canonical_sha(payload),
            entry_id,
            entry,
            facts,
            vacancies,
            state,
            (
                "expand_same_entry",
                "select_fact",
                "select_vacancy",
                "none",
                "defer",
                "cancel",
            ),
        )
        self._operations[operation_id] = replace(operation, locality=locality)
        return locality

    def resolve(
        self,
        operation_id: str,
        action: str,
        candidate_id: str | None = None,
        semantic_relation: str | None = None,
        recalled_fact_ids: tuple[str, ...] = (),
    ) -> FieldEncounterResult:
        operation = self._active(operation_id)
        locality = operation.locality
        if locality is None:
            raise ValueError("Field Encounter has not entered a Locality")
        if action not in {"select_fact", "select_vacancy", "none", "defer"}:
            raise ValueError("action is not an Encounter terminal action")
        if semantic_relation is not None and semantic_relation not in SEMANTIC_RELATIONS:
            raise ValueError("unknown semantic relation")
        by_fact = {item.fact_id: item for item in locality.facts}
        recalled = []
        for fact_id in _text_tuple(recalled_fact_ids, "recalled_fact_ids", 16):
            try:
                statement_id = by_fact[fact_id].statement_id
            except KeyError as exc:
                raise ValueError("recalled fact was not visible") from exc
            if statement_id not in recalled:
                recalled.append(statement_id)
        pending = operation.request.optional_pending_proposition
        selected_fact = None
        selected_vacancy = None
        if action == "select_fact":
            if type(candidate_id) is not str or candidate_id not in by_fact:
                raise ValueError("selected fact was not visible")
            selected_fact = by_fact[candidate_id]
            if selected_fact.statement_id not in recalled:
                recalled.append(selected_fact.statement_id)
        elif action == "select_vacancy":
            by_vacancy = {item.vacancy_id: item for item in locality.vacancies}
            if type(candidate_id) is not str or candidate_id not in by_vacancy:
                raise ValueError("selected vacancy was not visible")
            selected_vacancy = by_vacancy[candidate_id]
        elif candidate_id is not None:
            raise ValueError("NONE and defer cannot select a candidate")
        terminal, effect = self._effect(
            operation,
            action,
            semantic_relation,
            selected_fact,
            selected_vacancy,
        )
        if pending is None and effect.commit_eligible:
            raise AssertionError("query-only Encounter cannot produce mutation")
        path_digest = _canonical_sha(
            {
                "root": operation.root_identity,
                "pages": operation.page_path,
                "locality": locality.page_fingerprint,
            }
        )
        result = FieldEncounterResult(
            operation_id,
            terminal,
            semantic_relation,
            tuple(recalled),
            locality.state_identity,
            path_digest,
            effect,
        )
        self._operations[operation_id] = replace(operation, result=result)
        return result

    def commit(
        self, request: EncounterCommitRequest, now_ms: int | None = None
    ) -> EncounterCommitResult:
        if type(request) is not EncounterCommitRequest:
            raise TypeError("request must be EncounterCommitRequest")
        operation = self.get(request.operation_id)
        result = operation.result
        pending = operation.request.optional_pending_proposition
        if result is None or pending is None or not result.effect.commit_eligible:
            return EncounterCommitResult(
                "not_committed", request.operation_id, request.statement.statement_id,
                None, 0, False
            )
        if operation.committed:
            return EncounterCommitResult(
                "retryable_conflict", request.operation_id,
                request.statement.statement_id, None, 0, False,
                "operation_already_committed",
            )
        observed_now = time_ns() // 1_000_000 if now_ms is None else now_ms
        if type(observed_now) is not int or observed_now < 0:
            raise ValueError("now_ms must be non-negative")
        if observed_now > operation.request.expires_at_ms:
            return EncounterCommitResult(
                "stale_zero_write", request.operation_id,
                request.statement.statement_id, None, 0, False,
                "operation_expired",
            )
        result_identity = self.result_identity(result)
        if (
            request.expected_core_state_identity != result.state_identity
            or request.terminal_result_identity != result_identity
            or request.pending_proposition_identity != pending.identity
            or request.statement.statement_id != pending.proposition_id
            or request.statement.content_utf8 != pending.content_utf8
            or request.statement.context_refs != pending.evidence_refs
        ):
            raise ValueError("Encounter commit request does not bind the terminal")
        if result.effect.effect_kind == "provisional_revision":
            provisional = result.effect.provisional_revision
            confirmation = request.revision_confirmation
            if (
                provisional is None
                or confirmation is None
                or confirmation.provisional_id != provisional.provisional_id
                or not confirmation.confirmed
            ):
                return EncounterCommitResult(
                    "not_committed",
                    request.operation_id,
                    request.statement.statement_id,
                    None,
                    0,
                    False,
                    "revision_not_confirmed",
                )
        decision = self._commit_decision(operation, request)
        core = CoreRuntime(self._workspace)
        access = AccessRuntime(
            core, FileStatementStore(self._workspace), FileHandleStore(self._workspace)
        )
        try:
            conditional = access.apply_if_state(
                request.expected_core_state_identity, request.statement, decision
            )
            if conditional.commit_state == "stale_zero_write":
                return EncounterCommitResult(
                    "stale_zero_write", request.operation_id,
                    request.statement.statement_id, None, 0, False
                )
            handle = conditional.result
        except AccessConsistencyError as error:
            return EncounterCommitResult(
                "committed_readback_unknown", request.operation_id,
                request.statement.statement_id, None, 0, False,
                type(error).__name__,
            )
        except Exception as error:
            return EncounterCommitResult(
                "retryable_conflict", request.operation_id,
                request.statement.statement_id, None, 0, False,
                type(error).__name__,
            )
        finally:
            access.close()
            core.close()
        self._operations[request.operation_id] = replace(operation, committed=True)
        try:
            with AccessMemoryLoop(self._workspace) as loop:
                loop.verify_admitted_statements([request.statement.statement_id])
        except Exception as error:
            return EncounterCommitResult(
                "committed_readback_unknown", request.operation_id,
                request.statement.statement_id,
                handle if type(handle) is AtomHandle else None,
                0 if result.effect.effect_kind == "reuse" else 1,
                False,
                type(error).__name__,
            )
        return EncounterCommitResult(
            "committed_and_verified", request.operation_id,
            request.statement.statement_id,
            handle if type(handle) is AtomHandle else None,
            0 if result.effect.effect_kind == "reuse" else 1,
            True,
        )

    @staticmethod
    def result_identity(result: FieldEncounterResult) -> str:
        if type(result) is not FieldEncounterResult:
            raise TypeError("result must be FieldEncounterResult")
        return _canonical_sha(
            {
                "operation_id": result.operation_id,
                "terminal_kind": result.terminal_kind,
                "semantic_relation": result.semantic_relation,
                "recalled_statement_ids": result.recalled_statement_ids,
                "state_identity": result.state_identity,
                "path_digest": result.path_digest,
                "effect_kind": result.effect.effect_kind,
                "pending": result.effect.pending_proposition_identity,
                "fact": result.effect.selected_fact_id,
                "vacancy": result.effect.selected_vacancy_id,
                "provisional": (
                    result.effect.provisional_revision.provisional_id
                    if result.effect.provisional_revision
                    else None
                ),
            }
        )

    def cancel(self, operation_id: str) -> None:
        self._operations.pop(operation_id, None)

    def _active(self, operation_id: str) -> FieldEncounterOperation:
        operation = self.get(operation_id)
        if operation.result is not None:
            raise ValueError("Field Encounter operation is already terminal")
        return operation

    def _facts(
        self,
        operation: FieldEncounterOperation,
        entry: GeometryAddress,
        state: str,
    ) -> tuple[EncounterFactCard, ...]:
        with AccessMemoryLoop(self._workspace) as loop:
            recalled = loop.navigator().recall_entry(
                operation.request.operation_id + ":facts", entry
            )
        provenance = FileStatementProvenanceStore(self._workspace)
        facts = []
        remaining_chars = operation.request.locality_max_chars
        for item in recalled.items[: operation.request.locality_max_results]:
            content = item["content_utf8"][:remaining_chars]
            if not content:
                break
            handle = AtomHandle.from_mapping(item["handle"])
            digest = None
            if provenance.exists(item["statement_id"]):
                digest = provenance.get(item["statement_id"]).digest()
            fact_id = "encounter-fact:" + _canonical_sha(
                {
                    "operation": operation.request.operation_id,
                    "statement": item["statement_id"],
                    "handle": item["handle"],
                }
            )
            path = tuple(str(part) for part in item["path"])
            facts.append(
                EncounterFactCard(
                    fact_id,
                    item["statement_id"],
                    content,
                    handle,
                    path,
                    True,
                    digest,
                    state,
                )
            )
            remaining_chars -= len(content)
        return tuple(facts)

    def _vacancies(
        self,
        operation: FieldEncounterOperation,
        entry: GeometryAddress,
        facts: tuple[EncounterFactCard, ...],
        state: str,
    ) -> tuple[EncounterVacancyCard, ...]:
        request = operation.request
        cards: list[EncounterVacancyCard] = []
        seen: set[tuple[object, ...]] = set()
        with CoreRuntime(self._workspace) as core:
            observed = sha256(core.export_state_bytes()).hexdigest()
            if observed != state:
                raise ValueError("Core state changed before vacancy projection")
            local = core.junction_candidates(
                JunctionRequest(
                    request.field_scope,
                    (entry,),
                    (),
                    4,
                    min(8, request.vacancy_budget),
                )
            )
            local_limit = max(1, request.vacancy_budget - 2)
            for candidate in local[:local_limit]:
                kind = (
                    "LOCAL_VACANCY"
                    if candidate.primary_max_distance == 1
                    else "BOUNDARY_VACANCY"
                )
                self._append_vacancy(
                    cards, seen, operation, kind, candidate.cell, state,
                    ((entry,),), candidate.free_face_count, candidate.boundary
                )
            addresses = tuple(
                sorted(
                    {fact.handle.geometry_address for fact in facts},
                    key=lambda cell: cell.stable_key(),
                )
            )
            if len(addresses) >= 2 and len(cards) < request.vacancy_budget:
                groups = tuple((cell,) for cell in addresses[:4])
                junctions = core.relation_group_junction_candidates(
                    RelationGroupJunctionRequest(
                        request.field_scope,
                        groups,
                        4,
                        2,
                        1,
                    )
                )
                for candidate in junctions:
                    if not candidate.all_groups_realized:
                        raise RuntimeError("Core exposed unrealized Junction vacancy")
                    self._append_vacancy(
                        cards, seen, operation, "JUNCTION_VACANCY",
                        candidate.cell, state, groups, candidate.free_face_count,
                        candidate.boundary,
                    )
            neutral = core.junction_candidates(
                JunctionRequest(
                    request.field_scope,
                    (),
                    (),
                    8,
                    min(8, request.vacancy_budget),
                )
            )
            for candidate in neutral:
                if candidate.free_face_count != 6:
                    continue
                self._append_vacancy(
                    cards, seen, operation, "NEUTRAL_SEED_VACANCY",
                    candidate.cell, state, (), candidate.free_face_count, False
                )
                break
        return tuple(cards[: request.vacancy_budget])

    @staticmethod
    def _append_vacancy(
        cards: list[EncounterVacancyCard],
        seen: set[tuple[object, ...]],
        operation: FieldEncounterOperation,
        kind: str,
        address: GeometryAddress,
        state: str,
        groups: tuple[tuple[GeometryAddress, ...], ...],
        free_faces: int,
        boundary: bool,
    ) -> None:
        key = (kind, *address.stable_key())
        if key in seen or len(cards) >= operation.request.vacancy_budget:
            return
        seen.add(key)
        vacancy_id = "encounter-vacancy:" + _canonical_sha(
            {
                "operation": operation.request.operation_id,
                "state": state,
                "kind": kind,
                "address": address.to_mapping(),
                "groups": [
                    [cell.to_mapping() for cell in group] for group in groups
                ],
            }
        )
        cards.append(
            EncounterVacancyCard(
                vacancy_id,
                kind,
                address,
                state,
                1,
                boundary,
                groups,
                free_faces,
                operation.request.expires_at_ms,
            )
        )

    @staticmethod
    def _effect(
        operation: FieldEncounterOperation,
        action: str,
        relation: str | None,
        fact: EncounterFactCard | None,
        vacancy: EncounterVacancyCard | None,
    ) -> tuple[str, EncounterEffect]:
        pending = operation.request.optional_pending_proposition
        pending_id = pending.identity if pending else None
        if action == "defer" or relation == "uncertain":
            return "ambiguous", EncounterEffect("defer", pending_id, retryable=True)
        if action == "none":
            kind = "retryable_exhausted" if pending else "none"
            return "exhausted", EncounterEffect(kind, pending_id, retryable=bool(pending))
        if action == "select_fact":
            assert fact is not None
            if relation is None:
                raise ValueError("fact selection requires a semantic relation")
            if pending is None:
                if relation not in {"same", "revision", "related_distinct"}:
                    raise ValueError("query-only fact relation is invalid")
                return "fact", EncounterEffect("recall", None, fact.fact_id)
            if relation == "same":
                return "fact", EncounterEffect("reuse", pending_id, fact.fact_id)
            if relation == "revision":
                provisional = ProvisionalRevisionDecision.create(
                    pending.proposition_id,
                    fact.statement_id,
                    fact.fact_id,
                    fact.handle,
                    pending.content_utf8,
                    fact.content_utf8,
                )
                return "fact", EncounterEffect(
                    "provisional_revision", pending_id, fact.fact_id,
                    provisional_revision=provisional,
                )
            raise ValueError(
                "pending related or unrelated material must select a vacancy"
            )
        assert vacancy is not None
        if pending is None:
            if relation is not None:
                raise ValueError("query-only vacancy does not accept a relation")
            return "vacancy", EncounterEffect(
                "none", None, selected_vacancy_id=vacancy.vacancy_id
            )
        if relation == "related_distinct" and vacancy.vacancy_kind == "NEUTRAL_SEED_VACANCY":
            raise ValueError("related material cannot select a neutral seed")
        if relation == "unrelated" and vacancy.vacancy_kind != "NEUTRAL_SEED_VACANCY":
            raise ValueError("unrelated material requires a neutral seed")
        if relation not in {"related_distinct", "unrelated"}:
            raise ValueError("vacancy selection requires related_distinct or unrelated")
        return "vacancy", EncounterEffect(
            "place", pending_id, selected_vacancy_id=vacancy.vacancy_id
        )

    @staticmethod
    def _commit_decision(
        operation: FieldEncounterOperation, request: EncounterCommitRequest
    ) -> AccessDecision:
        result = operation.result
        locality = operation.locality
        assert result is not None and locality is not None
        effect = result.effect
        if effect.effect_kind in {"reuse", "provisional_revision"}:
            fact = next(
                item for item in locality.facts if item.fact_id == effect.selected_fact_id
            )
            if effect.effect_kind == "provisional_revision":
                provisional = effect.provisional_revision
                confirmation = request.revision_confirmation
                if provisional is None or confirmation is None:
                    raise ValueError("revision requires explicit confirmation")
                if (
                    confirmation.provisional_id != provisional.provisional_id
                    or not confirmation.confirmed
                ):
                    raise ValueError("revision confirmation does not bind terminal")
                action = "revision_current"
            else:
                if request.revision_confirmation is not None:
                    raise ValueError("reuse cannot include revision confirmation")
                action = "reuse"
            return AccessDecision(
                "encounter:" + request.terminal_result_identity,
                request.statement.statement_id,
                action,
                existing_handle=fact.handle,
                reason_text="LLM selected a visible Field Encounter fact",
                decided_by="llm",
            )
        vacancy = next(
            item
            for item in locality.vacancies
            if item.vacancy_id == effect.selected_vacancy_id
        )
        if request.revision_confirmation is not None:
            raise ValueError("placement cannot include revision confirmation")
        return AccessDecision(
            "encounter:" + request.terminal_result_identity,
            request.statement.statement_id,
            "new",
            target_cell=vacancy.address,
            reason_text="LLM selected a visible legal Field Encounter vacancy",
            decided_by="llm",
        )
