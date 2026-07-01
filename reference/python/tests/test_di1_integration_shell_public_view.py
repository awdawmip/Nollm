from __future__ import annotations

import json
from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell, RecallInvocation
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


def test_t_712_primary_content_matches_dream_shard_verbatim(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    item = IntegrationShell().handle(invocation, context).to_mapping()["result"]["primary_evidence"][0]
    assert item["content"] == "Kunming had rain on 2026-06-29."
    assert item["tier"] == "primary"


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
