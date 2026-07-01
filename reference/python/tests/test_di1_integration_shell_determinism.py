from __future__ import annotations

import json
from dataclasses import replace

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.validation.di1_integration_fixture import build_di1_context


def canonical(mapping: dict) -> str:
    return json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def test_t_724_same_invocation_and_context_are_canonical_json_identical(tmp_path) -> None:
    _, _, _, invocation, context = build_di1_context(tmp_path)
    shell = IntegrationShell()
    first = shell.handle(invocation, context).to_mapping()
    second = shell.handle(invocation, context).to_mapping()
    assert canonical(first) == canonical(second)


def test_t_725_universe_tuple_permutation_keeps_public_mapping_aligned_with_dr1(tmp_path) -> None:
    _, _, universe, invocation, context = build_di1_context(tmp_path)
    permuted = replace(
        universe,
        proposal_records=tuple(reversed(universe.proposal_records)),
        traces=tuple(reversed(universe.traces)),
        covers=tuple(reversed(universe.covers)),
        coverage_up=tuple(reversed(universe.coverage_up)),
        coverage_down=tuple(reversed(universe.coverage_down)),
    )
    shell = IntegrationShell()
    first = shell.handle(invocation, context).to_mapping()
    second = shell.handle(invocation, replace(context, recall_universe=permuted)).to_mapping()
    primary = first["result"]["primary_evidence"][0]
    assert primary["origin"] == {
        "kind": "user_utterance",
        "reference_state": "present_redacted",
        "context_reference_state": "present_redacted",
        "role_state": "present_redacted",
    }
    assert primary["temporal_context"] == {
        "captured_at": "2026-06-30T08:00:00+08:00",
        "reference_instant": "2026-06-30T08:00:00+08:00",
        "source_time_expression_state": "present_redacted",
        "locale_hint_state": "present_redacted",
    }
    assert canonical(first) == canonical(second)


def test_t_727_adapter_source_has_no_request_cache_or_session_registry() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "reference" / "python" / "nollm" / "dream_geometry" / "adapters"
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in root.glob("*.py"))
    for token in ("last_result", "request_cache", "session_registry", "global_universe", "cache ="):
        assert token not in combined
