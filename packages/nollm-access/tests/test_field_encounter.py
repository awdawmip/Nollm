from dataclasses import fields

import pytest

from nollm_access import (
    AccessDecision,
    AccessMemoryLoop,
    AccessRuntime,
    EncounterCommitRequest,
    FieldEncounterEngine,
    FieldEncounterRequest,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    PendingProposition,
    ProgressiveAtlasPolicy,
    RevisionConfirmationResult,
)
from nollm_access.memory_loop import DEFAULT_FIELD_SCOPE
from nollm_core import CoreRuntime, GeometryAddress


NOW = 1_800_000_000_000
POLICY = ProgressiveAtlasPolicy(32, 65536, 4, 8, 4)


def cell(q: int, r: int = 0) -> GeometryAddress:
    return GeometryAddress("default_dream_v1", "default", 0, q, r)


def seed(workspace, statement_id: str, content: str, address: GeometryAddress):
    core = CoreRuntime(workspace)
    access = AccessRuntime(
        core, FileStatementStore(workspace), FileHandleStore(workspace)
    )
    statement = MemoryStatement(statement_id, content, context_refs=("capture:seed",))
    access.capture(statement)
    handle = access.apply(
        AccessDecision(
            "seed:" + statement_id,
            statement_id,
            "new",
            target_cell=address,
            reason_text="fixture seed",
            decided_by="fixture",
        )
    )
    access.close()
    core.close()
    return handle


def core_bytes(workspace) -> bytes:
    with CoreRuntime(workspace) as core:
        return core.export_state_bytes()


def pending(statement_id: str = "new", content: str = "new fact"):
    return PendingProposition(
        statement_id,
        content,
        ("capture:new",),
        ("user",),
        (),
        "fixture-formation-v1",
    )


def request(workspace, operation_id: str, proposition=None, material=("stimulus",)):
    with AccessMemoryLoop(workspace) as loop:
        state = loop.core_state_sha256()
    return FieldEncounterRequest(
        operation_id,
        "scope:test",
        "workspace:test",
        material,
        proposition,
        DEFAULT_FIELD_SCOPE,
        POLICY,
        16,
        12000,
        8,
        state,
        NOW,
        60000,
    )


def enter(engine: FieldEncounterEngine, operation):
    page = operation.current_page
    region = next(item for item in page.regions if item.support_entries)
    entry = region.support_entries[0]
    return engine.enter_locality(
        operation.request.operation_id, region.region_id, entry["entry_id"]
    )


def commit_request(engine, operation_id: str, statement: MemoryStatement, confirmation=None):
    operation = engine.get(operation_id)
    result = operation.result
    proposition = operation.request.optional_pending_proposition
    assert result is not None and proposition is not None
    return EncounterCommitRequest(
        operation_id,
        result.state_identity,
        engine.result_identity(result),
        proposition.identity,
        statement,
        confirmation,
    )


def test_request_has_no_read_write_or_mode_fields(tmp_path):
    names = {field.name for field in fields(FieldEncounterRequest)}
    assert names.isdisjoint({"intent", "mode", "operation_type", "read", "write"})
    with pytest.raises(TypeError):
        FieldEncounterRequest(**{**request(tmp_path, "bad").__dict__, "mode": "read"})


def test_root_identity_and_structure_are_operation_neutral(tmp_path):
    seed(tmp_path, "existing", "existing fact", cell(0))
    query_engine = FieldEncounterEngine(tmp_path)
    write_engine = FieldEncounterEngine(tmp_path)
    mixed_engine = FieldEncounterEngine(tmp_path)
    query = query_engine.begin(request(tmp_path, "query", None, ("question",)))
    write = write_engine.begin(request(tmp_path, "write", pending(), ("fact",)))
    mixed = mixed_engine.begin(
        request(tmp_path, "mixed", pending("mixed-new"), ("question", "fact"))
    )
    assert query.root_identity == write.root_identity == mixed.root_identity
    assert [item.to_mapping() for item in query.root_page.regions] == [
        item.to_mapping() for item in write.root_page.regions
    ] == [item.to_mapping() for item in mixed.root_page.regions]


def test_query_fact_recalls_and_query_vacancy_returns_none_without_write(tmp_path):
    seed(tmp_path, "existing", "release is Wednesday", cell(0))
    before = core_bytes(tmp_path)
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "query"))
    locality = enter(engine, operation)
    fact = next(item for item in locality.facts if item.statement_id == "existing")
    recalled = engine.resolve("query", "select_fact", fact.fact_id, "same")
    assert recalled.effect.effect_kind == "recall"
    assert recalled.recalled_statement_ids == ("existing",)
    assert core_bytes(tmp_path) == before

    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "none-query"))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind != "NEUTRAL_SEED_VACANCY")
    none = engine.resolve("none-query", "select_vacancy", vacancy.vacancy_id)
    assert none.effect.effect_kind == "none"
    assert core_bytes(tmp_path) == before


def test_same_fact_reuses_without_core_write(tmp_path):
    original_handle = seed(tmp_path, "existing", "same durable fact", cell(0))
    proposition = pending("support", "same durable fact")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "reuse", proposition))
    locality = enter(engine, operation)
    fact = next(item for item in locality.facts if item.statement_id == "existing")
    result = engine.resolve("reuse", "select_fact", fact.fact_id, "same")
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    committed = engine.commit(commit_request(engine, "reuse", statement), NOW + 1)
    assert result.effect.effect_kind == "reuse"
    assert committed.commit_state == "committed_and_verified"
    assert committed.core_write_count == 0
    assert committed.handle == original_handle


def test_revision_is_zero_write_until_exact_confirmation(tmp_path):
    seed(tmp_path, "old", "meeting is Tuesday", cell(0))
    proposition = pending("revised", "meeting is Wednesday")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "revision", proposition))
    locality = enter(engine, operation)
    fact = next(item for item in locality.facts if item.statement_id == "old")
    before = core_bytes(tmp_path)
    result = engine.resolve("revision", "select_fact", fact.fact_id, "revision")
    assert result.effect.effect_kind == "provisional_revision"
    assert not FileStatementStore(tmp_path).exists("revised")
    assert core_bytes(tmp_path) == before
    provisional = result.effect.provisional_revision
    assert provisional is not None
    confirmation = RevisionConfirmationResult(
        provisional.provisional_id,
        "confirm_revision",
        "same_subject_same_slot_supersedes",
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    committed = engine.commit(
        commit_request(engine, "revision", statement, confirmation), NOW + 1
    )
    assert committed.commit_state == "committed_and_verified"
    assert committed.core_write_count == 1


def test_rejected_revision_is_structured_zero_write(tmp_path):
    seed(tmp_path, "old", "meeting is Tuesday", cell(0))
    proposition = pending("rejected", "meeting is Wednesday")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "revision-rejected", proposition))
    locality = enter(engine, operation)
    fact = next(item for item in locality.facts if item.statement_id == "old")
    result = engine.resolve(
        "revision-rejected", "select_fact", fact.fact_id, "revision"
    )
    provisional = result.effect.provisional_revision
    assert provisional is not None
    rejected = RevisionConfirmationResult(
        provisional.provisional_id,
        "reject_revision",
        "different_subject_or_non_superseding",
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    before = core_bytes(tmp_path)
    committed = engine.commit(
        commit_request(engine, "revision-rejected", statement, rejected), NOW + 1
    )
    assert committed.commit_state == "not_committed"
    assert committed.error_type == "revision_not_confirmed"
    assert core_bytes(tmp_path) == before
    assert not FileStatementStore(tmp_path).exists("rejected")


@pytest.mark.parametrize(
    ("relation", "kind"),
    [("related_distinct", "LOCAL_VACANCY"), ("unrelated", "NEUTRAL_SEED_VACANCY")],
)
def test_pending_proposition_places_only_through_visible_vacancy(tmp_path, relation, kind):
    seed(tmp_path, "existing", "existing locality", cell(0))
    proposition = pending("placed:" + relation, "distinct proposition " + relation)
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "place:" + relation, proposition))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == kind)
    result = engine.resolve(
        operation.request.operation_id,
        "select_vacancy",
        vacancy.vacancy_id,
        relation,
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    committed = engine.commit(
        commit_request(engine, operation.request.operation_id, statement), NOW + 1
    )
    assert result.effect.effect_kind == "place"
    assert committed.commit_state == "committed_and_verified"
    assert committed.handle.geometry_address == vacancy.address


def test_mixed_result_reuses_one_traversal_for_recall_and_placement(tmp_path):
    seed(tmp_path, "old-place", "the venue is room 4", cell(0))
    proposition = pending("new-time", "the meeting is Wednesday")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "mixed", proposition))
    locality = enter(engine, operation)
    fact = next(item for item in locality.facts if item.statement_id == "old-place")
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == "LOCAL_VACANCY")
    result = engine.resolve(
        "mixed",
        "select_vacancy",
        vacancy.vacancy_id,
        "related_distinct",
        (fact.fact_id,),
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    committed = engine.commit(commit_request(engine, "mixed", statement), NOW + 1)
    assert result.recalled_statement_ids == ("old-place",)
    assert result.effect.effect_kind == "place"
    assert len(engine.get("mixed").page_path) == 1
    assert committed.commit_state == "committed_and_verified"


def test_stale_and_expired_operations_are_zero_write(tmp_path):
    seed(tmp_path, "existing", "existing", cell(0))
    proposition = pending("stale-candidate", "stale candidate")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "stale", proposition))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == "LOCAL_VACANCY")
    engine.resolve("stale", "select_vacancy", vacancy.vacancy_id, "related_distinct")
    seed(tmp_path, "racer", "concurrent write", cell(5))
    after_racer = core_bytes(tmp_path)
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    stale = engine.commit(commit_request(engine, "stale", statement), NOW + 1)
    assert stale.commit_state == "stale_zero_write"
    assert not FileStatementStore(tmp_path).exists(proposition.proposition_id)
    assert core_bytes(tmp_path) == after_racer

    expiring = pending("expired-candidate", "expired")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "expired", expiring))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == "LOCAL_VACANCY")
    engine.resolve("expired", "select_vacancy", vacancy.vacancy_id, "related_distinct")
    expired_statement = MemoryStatement(
        expiring.proposition_id,
        expiring.content_utf8,
        context_refs=expiring.evidence_refs,
    )
    expired = engine.commit(
        commit_request(engine, "expired", expired_statement), NOW + 60001
    )
    assert expired.commit_state == "stale_zero_write"
    assert not FileStatementStore(tmp_path).exists(expiring.proposition_id)


def test_vacancy_projection_is_insertion_order_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    seed(first, "a", "alpha", cell(0))
    seed(first, "b", "beta", cell(1))
    seed(second, "b", "beta", cell(1))
    seed(second, "a", "alpha", cell(0))

    def projected(workspace):
        engine = FieldEncounterEngine(workspace)
        locality = enter(engine, engine.begin(request(workspace, "deterministic")))
        return [
            (item.vacancy_kind, item.address.stable_key(), item.free_face_count)
            for item in locality.vacancies
        ]

    assert projected(first) == projected(second)


def test_junction_vacancies_are_realized_geometry_candidates(tmp_path):
    seed(tmp_path, "left", "left relation", cell(0))
    seed(tmp_path, "right", "right relation", cell(1))
    engine = FieldEncounterEngine(tmp_path)
    locality = enter(engine, engine.begin(request(tmp_path, "junction")))
    junctions = [
        item for item in locality.vacancies if item.vacancy_kind == "JUNCTION_VACANCY"
    ]
    assert junctions
    assert all(len(item.relation_groups) >= 2 for item in junctions)


def test_binding_failure_rolls_back_conditional_statement_and_core(tmp_path, monkeypatch):
    seed(tmp_path, "existing", "existing", cell(0))
    proposition = pending("binding-failure", "candidate")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "binding-failure", proposition))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == "LOCAL_VACANCY")
    engine.resolve(
        "binding-failure", "select_vacancy", vacancy.vacancy_id, "related_distinct"
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )
    before = core_bytes(tmp_path)
    original = FileHandleStore._write_bytes
    failed = False

    def fail_once(store, payload):
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("fixture binding failure")
        return original(store, payload)

    monkeypatch.setattr(FileHandleStore, "_write_bytes", fail_once)
    committed = engine.commit(
        commit_request(engine, "binding-failure", statement), NOW + 1
    )
    assert committed.commit_state == "retryable_conflict"
    assert committed.error_type == "OSError"
    assert core_bytes(tmp_path) == before
    assert not FileStatementStore(tmp_path).exists("binding-failure")


def test_readback_failure_is_explicitly_indeterminate(tmp_path, monkeypatch):
    seed(tmp_path, "existing", "existing", cell(0))
    proposition = pending("readback-unknown", "candidate")
    engine = FieldEncounterEngine(tmp_path)
    operation = engine.begin(request(tmp_path, "readback-unknown", proposition))
    locality = enter(engine, operation)
    vacancy = next(item for item in locality.vacancies if item.vacancy_kind == "LOCAL_VACANCY")
    engine.resolve(
        "readback-unknown", "select_vacancy", vacancy.vacancy_id, "related_distinct"
    )
    statement = MemoryStatement(
        proposition.proposition_id,
        proposition.content_utf8,
        context_refs=proposition.evidence_refs,
    )

    def fail_readback(*_args, **_kwargs):
        raise OSError("fixture readback failure")

    monkeypatch.setattr(
        AccessMemoryLoop, "verify_admitted_statements", fail_readback
    )
    committed = engine.commit(
        commit_request(engine, "readback-unknown", statement), NOW + 1
    )
    assert committed.commit_state == "committed_readback_unknown"
    assert committed.error_type == "OSError"
    assert FileStatementStore(tmp_path).exists("readback-unknown")
