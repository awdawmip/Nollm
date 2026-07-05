from __future__ import annotations

import ast
import json
from pathlib import Path

from nollm.dream_geometry.adapters import IntegrationShell
from nollm.dream_geometry.validation.dx1_synthetic_cycle_report import public_envelope_boundary_pass
from nollm.dream_geometry.validation.dx1_synthetic_cycle_fixture import build_dx1_cycle
from subprocess_harness import run_subprocess


ROOT = Path(__file__).resolve().parents[3]
DI1_SEALED_BASE = "76a4d1ba8b97043ea2c673ca64ab6f816be18a12"
DI1_SEALED_ADAPTER_DIR = "reference/python/nollm/dream_geometry/adapters"
DI1_SEALED_ADAPTER_FILES = (
    "reference/python/nollm/dream_geometry/adapters/__init__.py",
    "reference/python/nollm/dream_geometry/adapters/errors.py",
    "reference/python/nollm/dream_geometry/adapters/integration_shell.py",
    "reference/python/nollm/dream_geometry/adapters/public_recall_view.py",
    "reference/python/nollm/dream_geometry/adapters/types.py",
)
DX1_SEALED_IMPLEMENTATION_DIRS = (
    "reference/python/nollm/dream_geometry/geometry",
    "reference/python/nollm/dream_geometry/field",
    "reference/python/nollm/dream_geometry/evidence",
    "reference/python/nollm/dream_geometry/cortex",
    "reference/python/nollm/dream_geometry/recall",
)
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
    diff_output = _sealed_scope_diff(DX1_SEALED_IMPLEMENTATION_DIRS + _di1_sealed_adapter_paths())
    _assert_no_sealed_scope_diff(diff_output)


def test_dx1_c1_di1_adapter_base_tree_is_exact() -> None:
    assert _di1_sealed_adapter_paths() == DI1_SEALED_ADAPTER_FILES


def test_dx1_c1_snapshot_compaction_is_outside_di1_adapter_scope() -> None:
    sealed_paths = _di1_sealed_adapter_paths()
    assert all("/snapshot_compaction/" not in path for path in sealed_paths)
    diff_output = _sealed_scope_diff(sealed_paths)
    _assert_no_sealed_scope_diff(diff_output)


def test_dx1_c1_original_adapter_diff_output_is_rejected() -> None:
    for path in DI1_SEALED_ADAPTER_FILES:
        try:
            _assert_no_sealed_scope_diff(path)
        except AssertionError as exc:
            assert path in str(exc)
        else:
            raise AssertionError(f"scope witness accepted simulated DI1 adapter change: {path}")


def test_dx1_c1_adapters_init_change_would_fail_scope_witness() -> None:
    changed_path = "reference/python/nollm/dream_geometry/adapters/__init__.py"
    try:
        _assert_no_sealed_scope_diff(changed_path)
    except AssertionError as exc:
        assert changed_path in str(exc)
    else:
        raise AssertionError("scope witness accepted simulated DI1 adapters/__init__.py change")


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


def _di1_sealed_adapter_paths() -> tuple[str, ...]:
    inside = run_subprocess(["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT, timeout_seconds=10)
    assert inside.returncode == 0
    assert inside.stdout.strip() == "true"
    result = run_subprocess(
        ["git", "ls-tree", "-r", "--name-only", DI1_SEALED_BASE, "--", DI1_SEALED_ADAPTER_DIR],
        cwd=ROOT,
        timeout_seconds=10,
    )
    assert result.returncode == 0
    paths = tuple(sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()))
    assert paths == DI1_SEALED_ADAPTER_FILES
    assert all(path.endswith(".py") for path in paths)
    return paths


def _sealed_scope_diff(paths: tuple[str, ...]) -> str:
    result = run_subprocess(
        ["git", "diff", "--name-only", f"{DI1_SEALED_BASE}..HEAD", "--", *paths],
        cwd=ROOT,
        timeout_seconds=10,
    )
    assert result.returncode == 0
    return result.stdout.strip()


def _assert_no_sealed_scope_diff(diff_output: str) -> None:
    changed_paths = [line.strip().replace("\\", "/") for line in diff_output.splitlines() if line.strip()]
    assert changed_paths == [], "sealed implementation paths changed:\n" + "\n".join(changed_paths)
