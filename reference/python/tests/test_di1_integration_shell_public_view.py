from __future__ import annotations

import json
from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell, RecallInvocation
from nollm.dream_geometry.evidence import DreamShard, OriginDescriptor, TemporalContext, open_store
from nollm.dream_geometry.protocol.contracts import OriginKind, UsageState
from nollm.dream_geometry.recall import EvidenceQualification, RecallDigest, RecallDigestStatus, RecallPolicy, RecallResultItem
from nollm.dream_geometry.validation.di1_integration_fixture import build_di1_context
from nollm.dream_geometry.validation.dr1_fixture import query_probe


FORBIDDEN_PUBLIC_TOKENS = (
    "gravity",
    "score",
    "mass",
    "cell",
    "chart",
    "cover",
    "trace",
    "kernel",
    "path",
    "filesystem",
)
PRIVATE_PROVENANCE_TOKENS = (
    r"C:\private\MEMORY.md",
    "/srv/private/conversation.json",
    "owner-private-label",
    "/private/time-note.txt",
    r"C:\private\locale.txt",
)


def test_t_712_primary_content_matches_dream_shard_verbatim(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    item = IntegrationShell().handle(invocation, context).to_mapping()["result"]["primary_evidence"][0]
    assert item["content"] == "Kunming had rain on 2026-06-29."
    assert item["tier"] == "primary"


def test_p_801_origin_free_text_provenance_is_redacted(tmp_path, monkeypatch) -> None:
    store, invocation, digest = _private_provenance_digest(tmp_path)
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: digest)
    _, _, _, _, context = build_di1_context(tmp_path / "context")
    mapping = IntegrationShell().handle(invocation, replace(context, evidence_store=store)).to_mapping()
    item = mapping["result"]["primary_evidence"][0]
    assert item["content"] == "Synthetic public provenance closure shard."
    assert item["tier"] == "primary"
    assert item["origin"] == {
        "kind": "user_utterance",
        "reference_state": "present_redacted",
        "context_reference_state": "present_redacted",
        "role_state": "present_redacted",
    }
    rendered = json.dumps(_without_content(mapping), sort_keys=True)
    for token in PRIVATE_PROVENANCE_TOKENS[:3]:
        assert token not in rendered


def test_p_802_temporal_free_text_is_redacted_but_rfc3339_instants_remain(tmp_path, monkeypatch) -> None:
    store, invocation, digest = _private_provenance_digest(tmp_path)
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: digest)
    _, _, _, _, context = build_di1_context(tmp_path / "context")
    temporal = IntegrationShell().handle(invocation, replace(context, evidence_store=store)).to_mapping()["result"]["primary_evidence"][0]["temporal_context"]
    assert temporal == {
        "captured_at": "2026-07-01T10:00:00+08:00",
        "reference_instant": "2026-07-01T09:59:00+08:00",
        "source_time_expression_state": "present_redacted",
        "locale_hint_state": "present_redacted",
    }


def test_p_803_absent_provenance_metadata_uses_stable_absent_schema(tmp_path, monkeypatch) -> None:
    store = open_store(tmp_path / "absent-store")
    shard = DreamShard(
        "shard:absent-provenance",
        "Synthetic absent provenance shard.",
        OriginDescriptor(OriginKind.user_utterance, None, None, None),
        TemporalContext(None, None, None, None),
        (),
        UsageState.active,
    )
    store.put_dream_shard(shard)
    qualification = EvidenceQualification(shard.shard_id, "active", "primary_active", True, ("DR1_EVIDENCE_ACTIVE",))
    item = RecallResultItem(shard.shard_id, "cover:hidden", (), ("axis:a", "axis:b"), 0.0, qualification, (), ())
    digest = RecallDigest("digest:absent", "probe:rain", RecallDigestStatus.resolved, True, (item,), (item,), (), (), (), (), 0.0, False, {})
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: digest)
    _, _, _, invocation, context = build_di1_context(tmp_path / "context")
    result = IntegrationShell().handle(invocation, replace(context, evidence_store=store)).to_mapping()["result"]["primary_evidence"][0]
    assert result["origin"] == {
        "kind": "user_utterance",
        "reference_state": "absent",
        "context_reference_state": "absent",
        "role_state": "absent",
    }
    assert result["temporal_context"] == {
        "captured_at": None,
        "reference_instant": None,
        "source_time_expression_state": "absent",
        "locale_hint_state": "absent",
    }


def test_t_713_selection_basis_is_fixed_discrete_allowlist(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    basis = IntegrationShell().handle(invocation, context).to_mapping()["result"]["primary_evidence"][0]["selection_basis"]
    assert basis == ["exact_structural_projection", "eligible_stable_cover", "final_multi_axis_evidence_gate"]
    assert not any(char.isdigit() for entry in basis for char in entry)


def test_t_714_715_interpretation_and_revision_are_context_only(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    item = IntegrationShell().handle(invocation, context).to_mapping()["result"]["primary_evidence"][0]
    assert item["interpretation_context"][0]["subject_shard_id"] == item["shard_id"]
    assert item["interpretation_context"][0]["tier"] == "contextual"
    assert item["interpretation_context"][0]["statement"] != item["content"]
    revision = item["revision_context"][0]
    assert revision["record_kind"] == "revision_thread"
    assert "true" not in revision
    assert "false" not in revision
    assert "current" not in revision


def test_t_716_missing_selected_dream_shard_is_stable_error(tmp_path, monkeypatch) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    qualification = EvidenceQualification("shard:missing", "active", "primary_active", True, ("DR1_EVIDENCE_ACTIVE",))
    item = RecallResultItem("shard:missing", "cover:hidden", (), (), 0.0, qualification, (), ())
    digest = RecallDigest("digest:test", "probe:rain", RecallDigestStatus.resolved, True, (item,), (item,), (), (), (), (), 0.0, False, {})
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: digest)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_EVIDENCE_UNAVAILABLE"


def test_t_717_missing_context_record_is_stable_error(tmp_path, monkeypatch) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    digest = IntegrationShell().handle(invocation, context).result
    assert digest is not None
    from nollm.dream_geometry.recall import resolve_recall

    real = resolve_recall(query_probe(), context.recall_universe, context.evidence_store, runtime_time=context.runtime_time, policy=RecallPolicy())
    item = replace(real.primary_evidence[0], context_record_ids=("interpretation:missing",))
    fake = replace(real, items=(item,), primary_evidence=(item,))
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: fake)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    assert mapping["ok"] is False
    assert mapping["error"]["code"] == "DI1_CONTEXT_RECORD_UNAVAILABLE"


def test_t_718_public_envelope_omits_internal_terms_outside_original_content(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    rendered = json.dumps(_without_content(mapping), sort_keys=True).lower()
    for token in FORBIDDEN_PUBLIC_TOKENS:
        assert token not in rendered


def test_p_805_private_provenance_tokens_never_escape_metadata(tmp_path, monkeypatch) -> None:
    store, invocation, digest = _private_provenance_digest(tmp_path)
    monkeypatch.setattr("nollm.dream_geometry.adapters.integration_shell.recall_facade.resolve_recall", lambda *args, **kwargs: digest)
    _, _, _, _, context = build_di1_context(tmp_path / "context")
    mapping = IntegrationShell().handle(invocation, replace(context, evidence_store=store)).to_mapping()
    rendered = json.dumps(_without_content(mapping), sort_keys=True).lower()
    for token in PRIVATE_PROVENANCE_TOKENS:
        assert token.lower() not in rendered
    for token in FORBIDDEN_PUBLIC_TOKENS + ("route", "store root"):
        assert token not in rendered


def test_t_719_no_primary_evidence_does_not_promote_context(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    no_primary_policy = RecallPolicy(include_tentative_primary=False, include_retired_context=True)
    context = replace(context, recall_policy=no_primary_policy)
    mapping = IntegrationShell().handle(invocation, context).to_mapping()
    assert mapping["ok"] is True
    if not mapping["result"]["primary_evidence"]:
        assert all(item["tier"] == "contextual" for item in mapping["result"]["contextual_evidence"])


def _without_content(value):
    if isinstance(value, dict):
        return {key: _without_content(item) for key, item in value.items() if key not in {"content", "statement", "selection_basis"}}
    if isinstance(value, list):
        return [_without_content(item) for item in value]
    return value


def _private_provenance_digest(tmp_path):
    store = open_store(tmp_path / "private-store")
    shard = DreamShard(
        "shard:private-provenance",
        "Synthetic public provenance closure shard.",
        OriginDescriptor(OriginKind.user_utterance, r"C:\private\MEMORY.md", "/srv/private/conversation.json", "owner-private-label"),
        TemporalContext("2026-07-01T10:00:00+08:00", "/private/time-note.txt", "2026-07-01T09:59:00+08:00", r"C:\private\locale.txt"),
        (),
        UsageState.active,
    )
    store.put_dream_shard(shard)
    qualification = EvidenceQualification(shard.shard_id, "active", "primary_active", True, ("DR1_EVIDENCE_ACTIVE",))
    item = RecallResultItem(shard.shard_id, "cover:hidden", (), ("axis:a", "axis:b"), 0.0, qualification, (), ())
    digest = RecallDigest("digest:private-provenance", "probe:rain", RecallDigestStatus.resolved, True, (item,), (item,), (), (), (), (), 0.0, False, {})
    return store, RecallInvocation("req-private-provenance", "recall", query_probe()), digest
