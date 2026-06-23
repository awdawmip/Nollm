from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from nollm.openclaw_memory_provider_alpha import (
    AlphaField,
    ProviderConfig,
    capture,
    prepare,
    run_from_stdin,
)


def _make_fixture(field_id: str = "alpha_test") -> dict[str, object]:
    fixture: dict[str, object] = {
        "schema": "nollm.alpha_field.v1",
        "field_id": field_id,
        "facts": [
            {
                "shard_id": "alpha-preference-blue",
                "claim": "The alpha user prefers blue labels in synthetic demonstrations.",
                "keywords": ["blue", "label", "preference"],
                "epistemic_state": "source_backed",
                "operational_state": "active",
                "source_refs": ["nollm://synthetic/fixture/alpha-field#fact-1"],
            },
            {
                "shard_id": "alpha-project-nollm",
                "claim": "The alpha user is working on a project named Nollm.",
                "keywords": ["project", "nollm"],
                "epistemic_state": "source_backed",
                "operational_state": "active",
                "source_refs": ["nollm://synthetic/fixture/alpha-field#fact-2"],
            },
        ],
    }
    canonical = {
        "schema": fixture["schema"],
        "field_id": fixture["field_id"],
        "facts": fixture["facts"],
    }
    canonical_json = json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    fixture["revision_id"] = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    return fixture


@pytest.fixture
def fixture_path(tmp_path: Path) -> Path:
    path = tmp_path / "alpha-field.json"
    path.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    return path


@pytest.fixture
def config(tmp_path: Path, fixture_path: Path) -> ProviderConfig:
    return ProviderConfig.from_payload(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": str(tmp_path / "repo"),
            "nollmDataRoot": str(tmp_path / "data"),
            "alphaFixturePath": str(fixture_path),
            "commandTimeoutMs": 15000,
            "maxFacts": 3,
            "maxCharacters": 1200,
            "captureMode": "receipt_only",
        }
    )


def test_fixture_schema_invalid(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
    with pytest.raises(Exception):
        AlphaField.load(str(path))


def test_revision_identity_deterministic(fixture_path: Path) -> None:
    field1 = AlphaField.load(str(fixture_path))
    field2 = AlphaField.load(str(fixture_path))
    assert field1.revision_id == field2.revision_id
    assert field1.compute_revision_id() == field1.revision_id


def test_relevant_turn_returns_fact(config: ProviderConfig, fixture_path: Path) -> None:
    field = AlphaField.load(str(fixture_path))
    result = prepare(
        field,
        {
            "schema": "nollm.provider.prepare.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "messages": [{"role": "user", "content": "What is the blue preference?"}],
            "budget": {"max_facts": 3, "max_characters": 1200},
        },
        config,
    )
    assert result["ok"] is True
    ctx = result["context"]
    assert ctx["freshness"] == "fresh"
    assert len(ctx["facts"]) >= 1
    assert any("blue" in fact["claim"].lower() for fact in ctx["facts"])


def test_irrelevant_turn_returns_none_and_explicit_absence(
    config: ProviderConfig, fixture_path: Path
) -> None:
    field = AlphaField.load(str(fixture_path))
    result = prepare(
        field,
        {
            "schema": "nollm.provider.prepare.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "messages": [{"role": "user", "content": "What is the weather?"}],
            "budget": {"max_facts": 3, "max_characters": 1200},
        },
        config,
    )
    assert result["ok"] is True
    ctx = result["context"]
    assert ctx["freshness"] == "none"
    assert ctx["facts"] == []
    assert any(
        "No matching active Nollm memory" in absence
        for absence in ctx["completeness"]["explicit_absences"]
    )


def test_budget_honored(config: ProviderConfig, fixture_path: Path) -> None:
    field = AlphaField.load(str(fixture_path))
    result = prepare(
        field,
        {
            "schema": "nollm.provider.prepare.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "messages": [{"role": "user", "content": "blue nollm project"}],
            "budget": {"max_facts": 1, "max_characters": 1200},
        },
        config,
    )
    assert result["ok"] is True
    assert len(result["context"]["facts"]) <= 1


def test_malformed_sidecar_stdin(config: ProviderConfig, monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    monkeypatch.setattr(sys, 'stdin', io.StringIO(''))
    result = run_from_stdin(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": str(config.nollm_repo_root),
            "nollmDataRoot": str(config.nollm_data_root),
            "alphaFixturePath": str(config.alpha_fixture_path),
        }
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_command"


def test_capture_receipt_under_data_root(
    config: ProviderConfig, fixture_path: Path
) -> None:
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [{"role": "user", "content": "blue"}],
        },
        config,
    )
    assert result["ok"] is True
    receipt = result["receipt"]
    assert receipt["state"] == "captured_pending_native_ingress"
    stored = Path(receipt["stored_at"])
    assert stored.is_relative_to(config.nollm_data_root)


def test_repeated_capture_idempotent(config: ProviderConfig, fixture_path: Path) -> None:
    field = AlphaField.load(str(fixture_path))
    payload = {
        "schema": "nollm.provider.capture.v1",
        "request_id": "r1",
        "agent_id": "main",
        "session_id": "s1",
        "run_id": "run1",
        "success": True,
        "messages": [{"role": "user", "content": "blue"}],
    }
    result1 = capture(field, payload, config)
    result2 = capture(field, payload, config)
    assert result1["ok"] is True
    assert result2["ok"] is True
    assert result1["receipt"]["receipt_id"] == result2["receipt"]["receipt_id"]


def test_capture_failure_does_not_create_success_receipt(
    config: ProviderConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    import io
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"command": "capture", "schema": "wrong.schema"})),
    )
    result = run_from_stdin(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": str(config.nollm_repo_root),
            "nollmDataRoot": str(config.nollm_data_root),
            "alphaFixturePath": str(config.alpha_fixture_path),
        }
    )
    assert result["ok"] is False


def test_no_legacy_file_read_write(
    config: ProviderConfig, fixture_path: Path, tmp_path: Path
) -> None:
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    (legacy_dir / "MEMORY.md").write_text(
        "LEGACY_SENTINEL_DO_NOT_READ", encoding="utf-8"
    )
    (legacy_dir / "DREAMS.md").write_text(
        "LEGACY_SENTINEL_DO_NOT_READ", encoding="utf-8"
    )
    memory_dir = legacy_dir / "memory"
    memory_dir.mkdir()
    (memory_dir / "2026-06-23.md").write_text(
        "LEGACY_SENTINEL_DO_NOT_READ", encoding="utf-8"
    )
    field = AlphaField.load(str(fixture_path))
    prepare(
        field,
        {
            "schema": "nollm.provider.prepare.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "messages": [{"role": "user", "content": "blue"}],
            "budget": {"max_facts": 3, "max_characters": 1200},
        },
        config,
    )
    capture(
        field,
        {
            "schema": "nollm.provider.capture.v1",
            "request_id": "r1",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [{"role": "user", "content": "blue"}],
        },
        config,
    )
    assert (
        legacy_dir / "MEMORY.md"
    ).read_text(encoding="utf-8") == "LEGACY_SENTINEL_DO_NOT_READ"
    assert (
        legacy_dir / "DREAMS.md"
    ).read_text(encoding="utf-8") == "LEGACY_SENTINEL_DO_NOT_READ"
    assert (
        memory_dir / "2026-06-23.md"
    ).read_text(encoding="utf-8") == "LEGACY_SENTINEL_DO_NOT_READ"


def test_no_side_effect_before_invalid_config_preflight(tmp_path: Path) -> None:
    data_root = tmp_path / "data"
    data_root.mkdir()
    result = run_from_stdin(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": "relative/path",
            "nollmDataRoot": str(data_root),
            "alphaFixturePath": "/absolute/but/missing.json",
        }
    )
    assert result["ok"] is False
    assert list(data_root.iterdir()) == []



def test_script_invocation_with_empty_stdin() -> None:
    import subprocess
    repo_root = Path(__file__).resolve().parents[3]
    sidecar_script = repo_root / "reference" / "python" / "scripts" / "run_openclaw_nollm_provider.py"
    config_json = json.dumps(
        {
            "pythonCommand": sys.executable,
            "nollmRepoRoot": str(repo_root),
            "nollmDataRoot": str(repo_root / "out" / "nollm-alpha-test-data"),
            "alphaFixturePath": str(
                repo_root / "integrations" / "openclaw" / "nollm-memory-provider" / "fixtures" / "alpha-field.json"
            ),
        }
    )
    proc = subprocess.run(
        [sys.executable, str(sidecar_script), "--config-json", config_json],
        input="",
        capture_output=True,
        text=True,
        timeout=10,
    )
    result = json.loads(proc.stdout)
    assert result["ok"] is False
    assert result["error"]["code"] == "invalid_command"
