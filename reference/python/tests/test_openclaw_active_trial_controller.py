from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from reference.python.scripts.run_openclaw_nollm_active_trial import DEFAULT_TRIAL_ID_PREFIX, TargetBinding, _diagnose, _plan, _redact_text, _tool_catalog_safe


def _fake_openclaw(tmp_path: Path, text: str) -> Path:
    script = tmp_path / ("openclaw.cmd" if os.name == "nt" else "openclaw")
    if os.name == "nt":
        script.write_text(text, encoding="utf-8")
    else:
        script.write_text("#!/bin/sh\n" + text, encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _binding(tmp_path: Path, openclaw: Path) -> TargetBinding:
    config = tmp_path / "openclaw.json"
    workspace = tmp_path / "workspace"
    repo = tmp_path / "repo"
    provider = repo / "integrations" / "openclaw" / "nollm-memory-provider"
    provider.mkdir(parents=True)
    (provider / "package.json").write_text("{}", encoding="utf-8")
    workspace.mkdir()
    config.write_text(json.dumps({"plugins": {"entries": {}, "slots": {}}, "agents": {"list": []}}), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    return TargetBinding(openclaw, config, None, workspace, repo, Path(sys.executable).resolve(), out, "main", "w2-03r-test")


def test_target_binding_requires_absolute_openclaw(tmp_path: Path) -> None:
    ns = type("Args", (), {
        "openclaw_bin": "openclaw",
        "config": str(tmp_path / "missing.json"),
        "profile": None,
        "workspace": str(tmp_path),
        "repo_root": str(tmp_path),
        "python_executable": sys.executable,
        "out": str(tmp_path / "out"),
        "target_agent_id": "main",
        "trial_id": "test",
    })()
    try:
        TargetBinding.from_args(ns)
    except ValueError as exc:
        assert "openclaw_bin" in str(exc) or "absolute" in str(exc)
    else:
        raise AssertionError("relative openclaw path accepted")


def test_target_binding_checks_raw_path_before_resolve(tmp_path: Path, monkeypatch) -> None:
    openclaw = _fake_openclaw(tmp_path, "@echo off\necho fake\n" if os.name == "nt" else "echo fake\n")
    config = tmp_path / "openclaw.json"
    workspace = tmp_path / "workspace"
    repo = tmp_path / "repo"
    out = tmp_path / "out"
    for path in (workspace, repo, out):
        path.mkdir()
    config.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    ns = type("Args", (), {
        "openclaw_bin": str(openclaw.resolve()),
        "config": "openclaw.json",
        "profile": None,
        "workspace": str(workspace.resolve()),
        "repo_root": str(repo.resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
        "out": str(out.resolve()),
        "target_agent_id": "main",
        "trial_id": "test",
    })()
    try:
        TargetBinding.from_args(ns)
    except ValueError as exc:
        assert "config" in str(exc) and "absolute" in str(exc)
    else:
        raise AssertionError("relative config accepted after cwd resolve")


def test_target_binding_defaults_to_w2_04_trial_id(tmp_path: Path) -> None:
    if os.name == "nt":
        openclaw = _fake_openclaw(tmp_path, "@echo off\necho fake\n")
    else:
        openclaw = _fake_openclaw(tmp_path, "echo fake\n")
    config = tmp_path / "openclaw.json"
    workspace = tmp_path / "workspace"
    repo = tmp_path / "repo"
    out = tmp_path / "out"
    for path in (workspace, repo, out):
        path.mkdir()
    config.write_text("{}", encoding="utf-8")
    ns = type("Args", (), {
        "openclaw_bin": str(openclaw.resolve()),
        "config": str(config.resolve()),
        "profile": None,
        "workspace": str(workspace.resolve()),
        "repo_root": str(repo.resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
        "out": str(out.resolve()),
        "target_agent_id": "main",
        "trial_id": None,
    })()
    binding = TargetBinding.from_args(ns)
    assert binding.trial_id.startswith(f"{DEFAULT_TRIAL_ID_PREFIX}-")


def test_plan_blocks_when_real_turn_route_unavailable(tmp_path: Path) -> None:
    if os.name == "nt":
        openclaw = _fake_openclaw(tmp_path, "@echo off\nif \"%1\"==\"--version\" echo OpenClaw fake\nif \"%1\"==\"config\" echo validate\nif \"%1\"==\"plugins\" echo list\nif \"%1\"==\"gateway\" echo restart\nif \"%1\"==\"agent\" echo no-json-here\n")
    else:
        openclaw = _fake_openclaw(tmp_path, "case \"$1\" in --version) echo OpenClaw fake;; config) echo validate;; plugins) echo list;; gateway) echo restart;; agent) echo no-json-here;; esac\n")
    plan = _plan(_binding(tmp_path, openclaw.resolve()))
    assert plan["ok"] is False
    assert plan["routes"]["real_turn"] == "unavailable"


def test_plan_blocks_json5_like_config_before_mutation(tmp_path: Path) -> None:
    if os.name == "nt":
        openclaw = _fake_openclaw(tmp_path, "@echo off\nif \"%1\"==\"--version\" echo OpenClaw fake\nif \"%1\"==\"config\" echo validate\nif \"%1\"==\"plugins\" echo list\nif \"%1\"==\"gateway\" echo restart\nif \"%1\"==\"agent\" echo --message --json\n")
    else:
        openclaw = _fake_openclaw(tmp_path, "case \"$1\" in --version) echo OpenClaw fake;; config) echo validate;; plugins) echo list;; gateway) echo restart;; agent) echo --message --json;; esac\n")
    binding = _binding(tmp_path, openclaw.resolve())
    binding.config.write_text("{ // json5 style comment\n  plugins: {}\n}\n", encoding="utf-8")
    plan = _plan(binding)
    assert plan["ok"] is False
    assert plan["config_format"]["patch_route"] == "blocked_before_mutation"


def test_redaction_removes_home_and_tokens() -> None:
    text = str(Path.home()) + " Bearer abc sk-test password=secret "
    redacted = _redact_text(text)
    assert str(Path.home()) not in redacted
    assert "abc" not in redacted
    assert "secret" not in redacted


def test_diagnose_writes_private_and_share_capsules(tmp_path: Path) -> None:
    if os.name == "nt":
        openclaw = _fake_openclaw(tmp_path, "@echo off\necho OpenClaw fake\n")
    else:
        openclaw = _fake_openclaw(tmp_path, "echo OpenClaw fake\n")
    binding = _binding(tmp_path, openclaw.resolve())
    result = _diagnose(binding)
    assert result["ok"] is True
    assert Path(result["private_capsule"]).exists()
    assert Path(result["sanitized_share_capsule"]).exists()
    assert (Path(result["private_capsule"]) / "manifest.json").exists()


def test_tool_catalog_missing_is_failure() -> None:
    safe, names, status = _tool_catalog_safe({"parsed_safe_result": {"result": {"meta": {}}}})
    assert safe is False
    assert names == []
    assert status != "observed"


def test_tool_catalog_with_file_or_exec_is_failure() -> None:
    turn = {
        "parsed_safe_result": {
            "result": {
                "meta": {
                    "systemPromptReport": {
                        "tools": {"entries": [{"name": "session_status"}, {"name": "exec"}, {"name": "file_fetch"}]}
                    }
                }
            }
        }
    }
    safe, names, status = _tool_catalog_safe(turn)
    assert safe is False
    assert "exec" in names and "file_fetch" in names
    assert status == "observed"
