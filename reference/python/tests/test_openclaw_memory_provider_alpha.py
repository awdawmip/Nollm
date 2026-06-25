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
    repo_dir = tmp_path / "repo"; repo_dir.mkdir(parents=True, exist_ok=True); path = repo_dir / "alpha-field.json"
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
            "schema": "nollm.provider.capture.v2",
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
        "schema": "nollm.provider.capture.v2",
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
            "schema": "nollm.provider.capture.v2",
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


# ---- F0-02 Additional Tests ----


def test_capture_idempotent_same_event(config: ProviderConfig, fixture_path: Path) -> None:
    """Same agent/session/run/messages twice produces same receipt_id."""
    field = AlphaField.load(str(fixture_path))
    payload = {
        "schema": "nollm.provider.capture.v2",
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


def test_capture_secret_in_string_content_not_persisted(
    config: ProviderConfig, fixture_path: Path, tmp_path: Path
) -> None:
    """Secrets in string content must not be persisted in receipt."""
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v2",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [
                {"role": "user", "content": "Authorization: Bearer TOP_SECRET_123"}
            ],
        },
        config,
    )
    assert result["ok"] is True
    receipt_path = Path(result["receipt"]["stored_at"])
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert "TOP_SECRET_123" not in receipt_text
    assert "Bearer" not in receipt_text


def test_capture_nested_secret_not_persisted(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """Nested secrets must not be persisted."""
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v2",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [
                {
                    "role": "user",
                    "content": "check this",
                    "nested": {"api_key": "NESTED_SECRET_456"},
                }
            ],
        },
        config,
    )
    assert result["ok"] is True
    receipt_path = Path(result["receipt"]["stored_at"])
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert "NESTED_SECRET_456" not in receipt_text


def test_capture_failure_stores_no_body(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """success=false stores no message body."""
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v2",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": False,
            "messages": [{"role": "user", "content": "should not be stored"}],
        },
        config,
    )
    assert result["ok"] is True
    receipt_path = Path(result["receipt"]["stored_at"])
    import json as _json
    receipt = _json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt.get("message_summaries", []) == []


def test_capture_invalid_success_type_rejected(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """Invalid success type must be rejected."""
    field = AlphaField.load(str(fixture_path))
    with pytest.raises(Exception):
        capture(
            field,
            {
                "schema": "nollm.provider.capture.v2",
                "agent_id": "main",
                "session_id": "s1",
                "run_id": "run1",
                "success": "not_a_bool",
                "messages": [{"role": "user", "content": "blue"}],
            },
            config,
        )


def test_capture_receipt_contains_no_legacy_path(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """Receipt must not contain legacy memory path."""
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v2",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [{"role": "user", "content": "blue"}],
        },
        config,
    )
    assert result["ok"] is True
    receipt_path = Path(result["receipt"]["stored_at"])
    receipt_text = receipt_path.read_text(encoding="utf-8")
    assert "MEMORY.md" not in receipt_text
    assert "DREAMS.md" not in receipt_text
    assert "memory/" not in receipt_text
    assert "request_id" not in receipt_text


def test_segment_aware_legacy_path_rejection(tmp_path: Path) -> None:
    """nollmDataRoot ending with 'memory' must be rejected."""
    from nollm.openclaw_memory_provider_alpha import ProviderConfig, NollmProviderError

    fixture_repo_dir = tmp_path / "repo"
    fixture_repo_dir.mkdir(parents=True, exist_ok=True)
    fixture_file = fixture_repo_dir / "alpha-field.json"
    fixture_file.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    with pytest.raises(NollmProviderError, match="legacy"):
        ProviderConfig.from_payload(
            {
                "pythonCommand": "python",
                "nollmRepoRoot": str(tmp_path / "repo"),
                "nollmDataRoot": str(tmp_path / "memory"),
                "alphaFixturePath": str(fixture_file),
            }
        )


def test_segment_aware_legacy_path_rejection_memory_md(tmp_path: Path) -> None:
    """nollmDataRoot with MEMORY.md segment must be rejected."""
    from nollm.openclaw_memory_provider_alpha import ProviderConfig, NollmProviderError

    fixture_repo_dir = tmp_path / "repo"
    fixture_repo_dir.mkdir(parents=True, exist_ok=True)
    fixture_file = fixture_repo_dir / "alpha-field.json"
    fixture_file.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    with pytest.raises(NollmProviderError, match="legacy"):
        ProviderConfig.from_payload(
            {
                "pythonCommand": "python",
                "nollmRepoRoot": str(tmp_path / "repo"),
                "nollmDataRoot": str(tmp_path / "MEMORY.md"),
                "alphaFixturePath": str(fixture_file),
            }
        )


def test_nollm_memory_alpha_accepted(tmp_path: Path) -> None:
    """nollm-memory-alpha should be accepted as data root."""
    from nollm.openclaw_memory_provider_alpha import ProviderConfig

    fixture_repo_dir = tmp_path / "repo"
    fixture_repo_dir.mkdir(parents=True, exist_ok=True)
    fixture_file = fixture_repo_dir / "alpha-field.json"
    fixture_file.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    config = ProviderConfig.from_payload(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": str(tmp_path / "repo"),
            "nollmDataRoot": str(tmp_path / "nollm-memory-alpha"),
            "alphaFixturePath": str(fixture_file),
        }
    )
    assert config.nollm_data_root == tmp_path / "nollm-memory-alpha"


# ---- F0-04 Additional Tests ----


def test_capture_rejects_non_list_messages(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D4: messages must be a list."""
    field = AlphaField.load(str(fixture_path))
    with pytest.raises(Exception):
        capture(
            field,
            {
                "schema": "nollm.provider.capture.v2",
                "agent_id": "main",
                "session_id": "s1",
                "run_id": "run1",
                "success": True,
                "messages": "not-a-list",
            },
            config,
        )


def test_capture_rejects_missing_agent(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D4: agent_id must be a non-empty string."""
    field = AlphaField.load(str(fixture_path))
    with pytest.raises(Exception):
        capture(
            field,
            {
                "schema": "nollm.provider.capture.v2",
                "session_id": "s1",
                "run_id": "run1",
                "success": True,
                "messages": [],
            },
            config,
        )


def test_capture_rejects_missing_success(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D4: success must be a boolean (no silent default)."""
    field = AlphaField.load(str(fixture_path))
    with pytest.raises(Exception):
        capture(
            field,
            {
                "schema": "nollm.provider.capture.v2",
                "agent_id": "main",
                "session_id": "s1",
                "run_id": "run1",
                "messages": [],
            },
            config,
        )


def test_capture_success_differs_receipt_differs(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D4: success change produces distinct receipt_id."""
    field = AlphaField.load(str(fixture_path))
    payload_true = {
        "schema": "nollm.provider.capture.v2",
        "agent_id": "main",
        "session_id": "s1",
        "run_id": "run1",
        "success": True,
        "messages": [{"role": "user", "content": "blue"}],
    }
    payload_false = {**payload_true, "success": False}
    result_true = capture(field, payload_true, config)
    result_false = capture(field, payload_false, config)
    assert result_true["receipt"]["receipt_id"] != result_false["receipt"]["receipt_id"]


def test_capture_canonical_hash_includes_full_identity(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D4: canonical event hash is computed by Python and includes identity."""
    field = AlphaField.load(str(fixture_path))
    result = capture(
        field,
        {
            "schema": "nollm.provider.capture.v2",
            "agent_id": "main",
            "session_id": "s1",
            "run_id": "run1",
            "success": True,
            "messages": [{"role": "user", "content": "blue"}],
        },
        config,
    )
    assert result["ok"] is True
    receipt = json.loads(Path(result["receipt"]["stored_at"]).read_text(encoding="utf-8"))
    assert receipt["schema"] == "nollm.capture_receipt.v2"
    assert "canonical_event_hash" in receipt
    assert "request_id" not in receipt


def test_capture_corrupt_existing_receipt_quarantined(
    config: ProviderConfig, fixture_path: Path, tmp_path: Path
) -> None:
    """D5: corrupt existing receipt is quarantined, not overwritten."""
    field = AlphaField.load(str(fixture_path))
    payload = {
        "schema": "nollm.provider.capture.v2",
        "agent_id": "main",
        "session_id": "s1",
        "run_id": "run1",
        "success": True,
        "messages": [{"role": "user", "content": "blue"}],
    }
    result1 = capture(field, payload, config)
    receipt_path = Path(result1["receipt"]["stored_at"])
    # Corrupt the receipt
    receipt_path.write_text("not valid json", encoding="utf-8")
    with pytest.raises(Exception):
        capture(field, payload, config)
    quarantine_dir = receipt_path.parent / "quarantine"
    assert any(quarantine_dir.glob("*.json"))


def test_symlinked_fixture_escaping_repo_root_rejected(tmp_path: Path) -> None:
    """D7: Python config follows symlinks and rejects escape."""
    from nollm.openclaw_memory_provider_alpha import ProviderConfig, NollmProviderError

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir(parents=True, exist_ok=True)
    fixture_file = repo_dir / "alpha-field.json"
    fixture_file.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    outside_fixture = outside_dir / "alpha-field.json"
    outside_fixture.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    link_dir = repo_dir / "external-link"
    import os
    os.symlink(str(outside_dir), str(link_dir), target_is_directory=True)
    with pytest.raises(NollmProviderError, match="alphaFixturePath must be under nollmRepoRoot"):
        ProviderConfig.from_payload(
            {
                "pythonCommand": "python",
                "nollmRepoRoot": str(repo_dir),
                "nollmDataRoot": str(tmp_path / "data"),
                "alphaFixturePath": str(link_dir / "alpha-field.json"),
            }
        )


def test_symlinked_fixture_inside_repo_root_accepted(tmp_path: Path) -> None:
    """D7: Python config accepts symlinks that stay inside repo root."""
    from nollm.openclaw_memory_provider_alpha import ProviderConfig

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(parents=True, exist_ok=True)
    fixtures_dir = repo_dir / "fixtures2"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    fixture_file = fixtures_dir / "alpha-field.json"
    fixture_file.write_text(json.dumps(_make_fixture()), encoding="utf-8")
    link_dir = repo_dir / "external-link-in"
    import os
    os.symlink(str(fixtures_dir), str(link_dir), target_is_directory=True)
    config = ProviderConfig.from_payload(
        {
            "pythonCommand": "python",
            "nollmRepoRoot": str(repo_dir),
            "nollmDataRoot": str(tmp_path / "data"),
            "alphaFixturePath": str(link_dir / "alpha-field.json"),
        }
    )
    assert config.alpha_fixture_path.resolve() == (link_dir / "alpha-field.json").resolve()


def test_concurrent_duplicate_capture_publishes_once(
    config: ProviderConfig, fixture_path: Path
) -> None:
    """D5: concurrent duplicate events produce exactly one receipt publish."""
    import threading

    field = AlphaField.load(str(fixture_path))
    payload = {
        "schema": "nollm.provider.capture.v2",
        "agent_id": "main",
        "session_id": "s1",
        "run_id": "run1",
        "success": True,
        "messages": [{"role": "user", "content": "blue"}],
    }
    results: list[dict[str, object]] = []
    lock = threading.Lock()

    def call() -> None:
        result = capture(field, payload, config)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r["ok"] for r in results), "all concurrent calls must succeed"
    receipt_ids = {r["receipt"]["receipt_id"] for r in results}
    assert len(receipt_ids) == 1, "all calls must observe the same canonical receipt id"
    assert sum(1 for r in results if r.get("reused")) >= 7, "all but at most one call must reuse"

    receipt_dir = config.nollm_data_root / "functional-alpha" / "capture-receipts"
    receipt_files = [f for f in receipt_dir.glob("*.json") if f.parent == receipt_dir]
    assert len(receipt_files) == 1, "exactly one receipt file must exist"
