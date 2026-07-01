from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.validation.dx1_synthetic_cycle_report import public_envelope_boundary_pass
from nollm.dream_geometry.validation.dx1_synthetic_cycle_fixture import build_dx1_cycle


ROOT = Path(__file__).resolve().parents[3]
DI1_SEALED_BASE = "76a4d1ba8b97043ea2c673ca64ab6f816be18a12"
VALIDATION_FILE = ROOT / "reference" / "python" / "nollm" / "dream_geometry" / "validation" / "dx1_synthetic_cycle_fixture.py"
FORBIDDEN_PUBLIC = (
    r"C:\dx1-private",
    "/dx1-private",
    "synthetic-private-role",
    "trace:",
    "cover:",
    "cell",
    "chart",
    "kernel",
    "path_mass",
    "mass",
    "score",
    "gravity",
    "potential",
    "coverage",
)


def test_x012_s05_public_envelope_hides_provenance_and_internal_geometry(tmp_path) -> None:
    fixture = build_dx1_cycle(tmp_path)
    response = IntegrationShell().handle(fixture.invocation, fixture.integration_context).to_mapping()
    target = response["result"]["primary_evidence"][0]
    assert target["origin"] == {
        "kind": "user_utterance",
        "reference_state": "present_redacted",
        "context_reference_state": "present_redacted",
        "role_state": "present_redacted",
    }
    assert target["temporal_context"] == {
        "captured_at": "2026-06-30T08:00:00+08:00",
        "reference_instant": "2026-06-30T08:00:00+08:00",
        "source_time_expression_state": "present_redacted",
        "locale_hint_state": "present_redacted",
    }
    assert target["selection_basis"] == ["exact_structural_projection", "eligible_stable_cover", "final_multi_axis_evidence_gate"]
    rendered = json.dumps(_without_content(response), sort_keys=True).lower()
    for token in FORBIDDEN_PUBLIC:
        assert token.lower() not in rendered
    assert public_envelope_boundary_pass(response) is True


def test_s05_report_witness_checks_public_metadata_not_body_text(tmp_path) -> None:
    fixture = build_dx1_cycle(tmp_path)
    response = IntegrationShell().handle(fixture.invocation, fixture.integration_context).to_mapping()
    assert public_envelope_boundary_pass(response) is True

    leaked = json.loads(json.dumps(response))
    leaked["result"]["primary_evidence"][0]["selection_basis"].append("cover:synthetic-leak")
    assert public_envelope_boundary_pass(leaked) is False

    body_only = json.loads(json.dumps(response))
    body_only["result"]["primary_evidence"][0]["content"] = "Body text may contain cover: and chart tokens without becoming metadata."
    body_only["result"]["primary_evidence"][0]["interpretation_context"][0]["statement"] = "Statement text may contain gravity and mass tokens."
    assert public_envelope_boundary_pass(body_only) is True


def test_x015_scope_sealed_implementation_paths_are_unmodified() -> None:
    from subprocess_harness import run_subprocess

    inside = run_subprocess(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, timeout_seconds=10)
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        pytest.skip("DX1 scope witness requires a Git checkout")
    result = run_subprocess(
        [
            "git",
            "diff",
            "--name-only",
            f"{DI1_SEALED_BASE}..HEAD",
            "--",
            "reference/python/nollm/dream_geometry/geometry",
            "reference/python/nollm/dream_geometry/field",
            "reference/python/nollm/dream_geometry/evidence",
            "reference/python/nollm/dream_geometry/cortex",
            "reference/python/nollm/dream_geometry/recall",
            "reference/python/nollm/dream_geometry/adapters",
        ],
        cwd=ROOT,
        timeout_seconds=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_dx1_validation_does_not_construct_sealed_output_dataclasses_directly() -> None:
    source = VALIDATION_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {"CompiledGrowthProposal", "CompiledQueryProbe", "CompilationReceipt", "GrowthTrace", "CoarseCover", "GravitySnapshot", "CoverageDistribution", "RecallDigest"}
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if name in forbidden_calls:
                calls.append(name)
    assert calls == []
    for forbidden in ("openclaw", "requests", "urllib", "socket", "sqlite", "session", "cache"):
        assert forbidden not in source.lower()


def _without_content(value):
    if isinstance(value, dict):
        return {key: _without_content(item) for key, item in value.items() if key not in {"content", "statement"}}
    if isinstance(value, list):
        return [_without_content(item) for item in value]
    return value
