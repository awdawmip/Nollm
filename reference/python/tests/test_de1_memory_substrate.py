from __future__ import annotations

import json
from hashlib import sha256

import pytest

from nollm.dream_geometry.evidence import (
    DreamShard,
    InterpretationRecord,
    MemorySubstrateStore,
    OriginDescriptor,
    RevisionEdge,
    RevisionThread,
    TemporalContext,
    UsageStateTransition,
    canonical_json,
    open_store,
    payload_key,
)
from nollm.dream_geometry.protocol.contracts import (
    InterpretationAuthoringMode,
    InterpretationKind,
    OriginKind,
    RevisionRelation,
    UsageState,
)


def _origin(reference: str = "conversation:1") -> OriginDescriptor:
    return OriginDescriptor(OriginKind.user_utterance, reference, "turn:1", "user")


def _temporal(captured_at: str = "2026-06-29T08:00:00+08:00", expression: str | None = "today") -> TemporalContext:
    return TemporalContext(captured_at, expression, "2026-06-29T08:00:00+08:00", "zh-CN")


def _shard(shard_id: str = "shard:rain-1", content: str = "Kunming is rainy today.", *, captured_at: str = "2026-06-29T08:00:00+08:00") -> DreamShard:
    return DreamShard(shard_id, content, _origin(), _temporal(captured_at), ("basis:trace-seed", "context:weather"), UsageState.tentative)


def _interpretation(interpretation_id: str = "interpretation:city", subject: str = "shard:rain-1") -> InterpretationRecord:
    return InterpretationRecord(
        interpretation_id,
        subject,
        InterpretationKind.classification,
        "Kunming is a city.",
        InterpretationAuthoringMode.llm_proposed,
        ("basis:opaque-field-ref",),
        ("context:weather",),
        UsageState.tentative,
    )


def test_de1_t301_interpretation_does_not_mutate_shard(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    before = store.get_dream_shard(shard.shard_id)
    interpretation = _interpretation(subject=shard.shard_id)
    store.put_interpretation(interpretation)
    after = store.get_dream_shard(shard.shard_id)
    assert after == before
    assert store.get_interpretation(interpretation.interpretation_id).statement == "Kunming is a city."
    assert store.get_usage_state(interpretation.interpretation_id) is UsageState.tentative


def test_de1_t302_t311_same_text_different_occurrences_coexist(tmp_path) -> None:
    store = open_store(tmp_path)
    first = _shard("shard:rain-1", "Kunming is rainy today.", captured_at="2026-06-29T08:00:00+08:00")
    second = _shard("shard:rain-2", "Kunming is rainy today.", captured_at="2026-06-30T08:00:00+08:00")
    store.put_dream_shard(first)
    store.put_dream_shard(second)
    assert store.get_dream_shard(first.shard_id).temporal_context.captured_at != store.get_dream_shard(second.shard_id).temporal_context.captured_at
    assert len(store.read_ledger()) == 2


def test_de1_t303_llm_proposed_interpretation_remains_separate(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    interpretation = _interpretation(subject=shard.shard_id)
    store.put_dream_shard(shard)
    store.put_interpretation(interpretation)
    assert store.get_interpretation(interpretation.interpretation_id).authoring_mode is InterpretationAuthoringMode.llm_proposed
    assert store.get_usage_state(interpretation.interpretation_id) is UsageState.tentative
    with pytest.raises(ValueError, match="record missing"):
        store.get_dream_shard(interpretation.interpretation_id)


def test_de1_t304_revision_and_state_do_not_mutate_original(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    newer = _shard("shard:rain-2", "The prior weather note was only for that day.")
    store.put_dream_shard(shard)
    store.put_dream_shard(newer)
    thread = RevisionThread("revision:weather", (shard.shard_id, newer.shard_id), (RevisionEdge(newer.shard_id, shard.shard_id, RevisionRelation.supersedes, ("basis:correction",)),), ())
    store.put_revision_thread(thread)
    store.record_usage_transition(UsageStateTransition("state:rain-1-retired", shard.shard_id, UsageState.tentative, UsageState.retired, ("revision:weather",), "2026-06-30T08:00:00+08:00"))
    assert store.get_dream_shard(shard.shard_id) == shard
    assert store.get_usage_state(shard.shard_id) is UsageState.retired


def test_de1_t305_record_type_mismatch_in_shard_path_rejected(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    bad_payload = json.loads(canonical_json(_interpretation("interpretation:bad", shard.shard_id)))
    shard_path = next((tmp_path / "shards").glob("*.json"))
    shard_path.write_text(json.dumps(bad_payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="record type mismatch"):
        MemorySubstrateStore(tmp_path)


def test_de1_t310_t313_temporal_expression_is_preserved() -> None:
    temporal = TemporalContext("2026-06-29T08:00:00+08:00", "今天", "2026-06-29T08:00:00+08:00", "zh-CN")
    assert temporal.source_time_expression == "今天"
    assert temporal.reference_instant == "2026-06-29T08:00:00+08:00"
    assert TemporalContext("2026-06-29T08:00:00+08:00", "today", "2026-06-29T00:00:00Z", "en-US").locale_hint == "en-US"


def test_de1_t312_invalid_rfc3339_rejected() -> None:
    with pytest.raises(ValueError, match="RFC3339"):
        TemporalContext("2026-06-29", "today", None, None)


def test_de1_t320_t321_revision_cycles_only_for_replacement_relations() -> None:
    with pytest.raises(ValueError, match="cycle"):
        RevisionThread(
            "revision:cycle",
            ("shard:a", "shard:b"),
            (
                RevisionEdge("shard:a", "shard:b", RevisionRelation.supersedes, ()),
                RevisionEdge("shard:b", "shard:a", RevisionRelation.supersedes, ()),
            ),
            (),
        )
    thread = RevisionThread(
        "revision:coexists",
        ("shard:a", "shard:b"),
        (
            RevisionEdge("shard:a", "shard:b", RevisionRelation.coexists, ()),
            RevisionEdge("shard:b", "shard:a", RevisionRelation.conflicts, ()),
        ),
        (),
    )
    assert len(thread.edges) == 2


def test_de1_t322_revision_thread_does_not_change_state(tmp_path) -> None:
    store = open_store(tmp_path)
    first = _shard("shard:a")
    second = _shard("shard:b")
    store.put_dream_shard(first)
    store.put_dream_shard(second)
    store.put_revision_thread(RevisionThread("revision:clarifies", ("shard:a", "shard:b"), (RevisionEdge("shard:b", "shard:a", RevisionRelation.clarifies, ()),), ()))
    assert store.get_usage_state("shard:a") is UsageState.tentative
    assert store.get_usage_state("shard:b") is UsageState.tentative


def test_de1_t323_t325_usage_state_history_and_recovery(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    transitions = (
        UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.active, ("reason:1",), "2026-06-29T09:00:00+08:00"),
        UsageStateTransition("state:retired", shard.shard_id, UsageState.active, UsageState.retired, ("reason:2",), "2026-06-29T10:00:00+08:00"),
        UsageStateTransition("state:active-again", shard.shard_id, UsageState.retired, UsageState.active, ("reason:3",), "2026-06-29T11:00:00+08:00"),
        UsageStateTransition("state:rejected", shard.shard_id, UsageState.active, UsageState.rejected, ("reason:4",), "2026-06-29T12:00:00+08:00"),
        UsageStateTransition("state:tentative-again", shard.shard_id, UsageState.rejected, UsageState.tentative, ("reason:5",), "2026-06-29T13:00:00+08:00"),
    )
    for transition in transitions:
        store.record_usage_transition(transition)
    reopened = open_store(tmp_path)
    assert reopened.get_usage_state(shard.shard_id) is UsageState.tentative
    assert [event.ordinal for event in reopened.read_ledger()] == list(range(1 + len(transitions)))


def test_de1_t324_expected_from_mismatch_rejected_without_event(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    before = store.read_ledger()
    with pytest.raises(ValueError, match="expected_from_state"):
        store.record_usage_transition(UsageStateTransition("state:bad", shard.shard_id, UsageState.active, UsageState.retired, (), "2026-06-29T09:00:00+08:00"))
    assert store.read_ledger() == before


def test_de1_t330_t331_t332_idempotency_and_conflict(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    first = store.put_dream_shard(shard)
    retry = store.put_dream_shard(shard)
    assert first.created and first.ledger_event_id is not None
    assert retry.idempotent and retry.ledger_event_id is None
    assert len(store.read_ledger()) == 1
    with pytest.raises(ValueError, match="different payload"):
        store.put_dream_shard(_shard(content="Different content."))
    assert store.get_dream_shard(shard.shard_id) == shard
    assert len(store.read_ledger()) == 1


def test_de1_t333_reopen_roundtrip(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    interpretation = _interpretation(subject=shard.shard_id)
    store.put_dream_shard(shard)
    store.put_interpretation(interpretation)
    store.record_usage_transition(UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00"))
    reopened = open_store(tmp_path)
    assert reopened.get_dream_shard(shard.shard_id) == shard
    assert reopened.get_interpretation(interpretation.interpretation_id) == interpretation
    assert reopened.get_usage_state(shard.shard_id) is UsageState.active


def test_de1_t334_t335_inconsistent_files_fail_on_open(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    ledger_path = tmp_path / "ledger" / "events.jsonl"
    event = json.loads(ledger_path.read_text(encoding="utf-8").splitlines()[0])
    event["record_id"] = "shard:missing"
    ledger_path.write_text(json.dumps(event, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="record missing"):
        MemorySubstrateStore(tmp_path)

    format_root = tmp_path / "bad-format"
    bad = open_store(format_root)
    assert bad.root == format_root
    (format_root / "format.json").write_text('{"format_version":"de0","store_kind":"memory_substrate"}', encoding="utf-8")
    with pytest.raises(ValueError, match="format"):
        MemorySubstrateStore(format_root)


def test_de1_t336_path_escape_id_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="path-safe"):
        _shard("shard:../escape")
    assert not (tmp_path.parent / "escape.json").exists()


def test_de1_t343_opaque_field_refs_are_preserved(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    interpretation = _interpretation(subject=shard.shard_id)
    store.put_dream_shard(shard)
    store.put_interpretation(interpretation)
    assert store.get_interpretation(interpretation.interpretation_id).basis_refs == ("basis:opaque-field-ref",)


def test_de1_1_t350_t351_transition_retry_is_idempotent(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    transition = UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00")
    store.put_dream_shard(shard)
    first = store.record_usage_transition(transition)
    retry = store.record_usage_transition(transition)
    assert first.created is True
    assert retry.idempotent is True
    assert retry.ledger_event_id is None
    assert len(store.read_ledger()) == 2
    assert store.get_usage_state(shard.shard_id) is UsageState.active


def test_de1_1_t352_transition_retry_after_reopen_is_idempotent(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    transition = UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00")
    store.put_dream_shard(shard)
    store.record_usage_transition(transition)
    reopened = open_store(tmp_path)
    retry = reopened.record_usage_transition(transition)
    assert retry.idempotent is True
    assert len(reopened.read_ledger()) == 2


def test_de1_1_t353_transition_same_id_different_payload_rejected(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    transition = UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00")
    store.put_dream_shard(shard)
    store.record_usage_transition(transition)
    before = (store.read_ledger(), store.get_usage_state(shard.shard_id))
    changed = UsageStateTransition("state:active", shard.shard_id, UsageState.tentative, UsageState.retired, (), "2026-06-29T09:00:00+08:00")
    with pytest.raises(ValueError, match="different payload"):
        store.record_usage_transition(changed)
    assert (store.read_ledger(), store.get_usage_state(shard.shard_id)) == before


def test_de1_1_t354_orphan_shard_object_rejected_on_open(tmp_path) -> None:
    store = open_store(tmp_path)
    store.put_dream_shard(_shard())
    orphan = _shard("shard:orphan")
    _write_manual_record(tmp_path, "shards", orphan.shard_id, json.loads(canonical_json(orphan)))
    with pytest.raises(ValueError, match="missing ledger event"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t355_orphan_transition_object_rejected_on_open(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    transition = UsageStateTransition("state:orphan", shard.shard_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00")
    _write_manual_record(tmp_path, "state_transitions", transition.transition_id, json.loads(canonical_json(transition)))
    with pytest.raises(ValueError, match="missing ledger event"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t357_duplicate_ledger_event_rejected_on_open(tmp_path) -> None:
    store = open_store(tmp_path)
    store.put_dream_shard(_shard())
    ledger_path = tmp_path / "ledger" / "events.jsonl"
    line = ledger_path.read_text(encoding="utf-8").splitlines()[0]
    duplicate = json.loads(line)
    duplicate["event_id"] = "ledger:duplicate"
    duplicate["ordinal"] = 1
    ledger_path.write_text(line + "\n" + json.dumps(duplicate, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate ledger event"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t358_filename_payload_id_mismatch_rejected(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    payload = json.loads(canonical_json(shard))
    payload["shard_id"] = "shard:mismatched"
    path = next((tmp_path / "shards").glob("*.json"))
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    with pytest.raises(ValueError, match="filename"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t359_duplicate_record_id_in_same_bucket_rejected(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard()
    store.put_dream_shard(shard)
    duplicate_path = tmp_path / "shards" / "manual-duplicate.json"
    duplicate_path.write_text(canonical_json(shard), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate record_id"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t360_t361_cross_type_record_id_conflict_rejected(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard("record:shared")
    store.put_dream_shard(shard)
    with pytest.raises(ValueError, match="record_id conflict"):
        store.put_interpretation(_interpretation("record:shared", shard.shard_id))

    reverse = open_store(tmp_path / "reverse")
    base = _shard("shard:base")
    reverse.put_dream_shard(base)
    reverse.put_interpretation(_interpretation("record:shared", base.shard_id))
    with pytest.raises(ValueError, match="record_id conflict"):
        reverse.put_dream_shard(_shard("record:shared"))


def test_de1_1_t362_cross_bucket_same_id_rejected_on_open(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard("record:shared")
    store.put_dream_shard(shard)
    interpretation = _interpretation("record:shared", shard.shard_id)
    _write_manual_record(tmp_path, "interpretations", interpretation.interpretation_id, json.loads(canonical_json(interpretation)))
    with pytest.raises(ValueError, match="duplicate record_id"):
        MemorySubstrateStore(tmp_path)


def test_de1_1_t363_revision_and_usage_targets_work_with_unique_ids(tmp_path) -> None:
    store = open_store(tmp_path)
    shard = _shard("shard:unique")
    interpretation = _interpretation("interpretation:unique", shard.shard_id)
    store.put_dream_shard(shard)
    store.put_interpretation(interpretation)
    store.put_revision_thread(
        RevisionThread(
            "revision:unique",
            (shard.shard_id, interpretation.interpretation_id),
            (RevisionEdge(interpretation.interpretation_id, shard.shard_id, RevisionRelation.clarifies, ()),),
            (),
        )
    )
    store.record_usage_transition(UsageStateTransition("state:unique-active", interpretation.interpretation_id, UsageState.tentative, UsageState.active, (), "2026-06-29T09:00:00+08:00"))
    assert open_store(tmp_path).get_usage_state(interpretation.interpretation_id) is UsageState.active


def _write_manual_record(root, bucket: str, record_id: str, payload: dict) -> None:
    path = root / bucket / (sha256(record_id.encode("utf-8")).hexdigest() + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")
