from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

from scripts import install_openclaw_nollm_companion as installer


ROOT = Path(__file__).resolve().parents[3]


def test_build_config_patch_preserves_existing_maps_and_disables_write_by_default(tmp_path: Path) -> None:
    config = {
        "plugins": {
            "entries": {
                "memory-core": {"enabled": True},
                "other": {"config": {"keep": True}},
            },
            "allow": ["memory-core"],
            "deny": ["blocked-plugin"],
        },
        "tools": {"allow": ["memory_search"], "alsoAllow": ["web_search"], "deny": ["dangerous_tool"]},
    }

    patch = installer.build_config_patch(
        config_before=config,
        repo_root=ROOT,
        workspace_root=tmp_path,
        enable_write_candidate=False,
    )

    assert patch["plugins"]["entries"]["nollm-memory-companion"]["enabled"] is True
    assert patch["plugins"]["entries"]["nollm-memory-companion"]["config"]["nollmRepoRoot"] == str(ROOT)
    assert patch["plugins"]["entries"]["nollm-memory-companion"]["config"]["pythonCommand"] == sys.executable
    assert "memory-core" not in patch["plugins"]["entries"]
    assert "allow" not in patch["plugins"]
    assert "deny" not in patch["plugins"]
    assert patch["tools"]["allow"] == [
        "memory_search",
        "nollm_field_overview",
        "nollm_open_well",
        "nollm_surface",
        "nollm_focus",
        "nollm_drift",
        "nollm_read",
        "nollm_recall_trace",
        "nollm_memory_status",
    ]
    assert patch["tools"]["alsoAllow"] == [
        "web_search",
        "nollm_field_overview",
        "nollm_open_well",
        "nollm_surface",
        "nollm_focus",
        "nollm_drift",
        "nollm_read",
        "nollm_recall_trace",
        "nollm_memory_status",
    ]
    assert "nollm_memory_write_candidate" not in patch["tools"]["allow"]
    assert "nollm_memory_commit_candidate" not in patch["tools"]["allow"]
    assert "nollm_memory_write_candidate" not in patch["tools"]["alsoAllow"]
    assert "nollm_memory_commit_candidate" not in patch["tools"]["alsoAllow"]


def test_build_config_patch_write_candidate_flag_is_noop(tmp_path: Path) -> None:
    patch = installer.build_config_patch(
        config_before={"tools": {"allow": []}},
        repo_root=ROOT,
        workspace_root=tmp_path,
        enable_write_candidate=True,
    )

    assert "nollm_memory_write_candidate" not in patch["tools"]["allow"]
    assert "nollm_memory_commit_candidate" not in patch["tools"]["allow"]
    assert "nollm_memory_write_candidate" not in patch["tools"]["alsoAllow"]
    assert "nollm_memory_commit_candidate" not in patch["tools"]["alsoAllow"]


def test_redact_removes_secret_like_values() -> None:
    report = {
        "token": "abc",
        "nested": {"api_key": "secret", "safe": "value"},
        "items": [{"password": "pw"}],
    }

    assert installer.redact(report) == {
        "token": "<redacted>",
        "nested": {"api_key": "<redacted>", "safe": "value"},
        "items": [{"password": "<redacted>"}],
    }


def test_source_memory_hashes_ignore_sidecar_outputs(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    (workspace / "memory").mkdir(parents=True)
    (workspace / ".nollm-memory").mkdir()
    (workspace / "MEMORY.md").write_text("durable\n", encoding="utf-8")
    (workspace / "DREAMS.md").write_text("dream\n", encoding="utf-8")
    (workspace / "memory/day.md").write_text("daily\n", encoding="utf-8")
    (workspace / ".nollm-memory/generated.json").write_text("ignore\n", encoding="utf-8")

    hashes = installer.hash_source_memory_files(workspace)

    assert sorted(hashes) == ["DREAMS.md", "MEMORY.md", "memory/day.md"]
    assert all(len(value) == 64 for value in hashes.values())


def test_installed_matching_plugin_skips_link(monkeypatch, tmp_path: Path) -> None:
    report = installer.build_initial_report(arg_namespace(apply=True))
    calls: list[list[str]] = []

    monkeypatch.setattr(
        installer,
        "inspect_installed_plugin_state",
        lambda _openclaw, _cwd, _root: {"present": True, "source_matches": True, "enabled": True},
    )
    monkeypatch.setattr(installer, "run_checked", lambda command, **kwargs: calls.append(command))

    installer.install_plugin("openclaw", tmp_path, tmp_path, report)

    assert calls == []
    assert report["plugin_installation"]["method"] == "already_linked"
    assert report["plugin_installation"]["source_matches"] is True
    assert report["integration_evidence"]["plugin_link_state"] == "already_linked"


def test_absent_plugin_installs_once_and_polls(monkeypatch, tmp_path: Path) -> None:
    report = installer.build_initial_report(arg_namespace(apply=True))
    calls: list[list[str]] = []
    poll_calls: list[str] = []

    monkeypatch.setattr(
        installer,
        "inspect_installed_plugin_state",
        lambda _openclaw, _cwd, _root: {"present": False, "source_matches": False, "enabled": False},
    )
    monkeypatch.setattr(installer, "run_checked", lambda command, **kwargs: calls.append(command))
    monkeypatch.setattr(installer, "poll_runtime_tools", lambda *_args: poll_calls.append("poll"))

    installer.install_plugin("openclaw", tmp_path, tmp_path, report)

    assert calls == [["openclaw", "plugins", "install", "--link", str(tmp_path)]]
    assert poll_calls == ["poll"]
    assert report["plugin_installation"]["attempted"] is True
    assert report["integration_evidence"]["plugin_link_state"] == "linked_now"


def test_poll_runtime_tools_timeout_is_bounded(monkeypatch, tmp_path: Path) -> None:
    report = installer.build_initial_report(arg_namespace(apply=True))
    monotonic_values = iter([0, 1, 2, 3])

    monkeypatch.setattr(installer, "READINESS_DEADLINE_SECONDS", 2)
    monkeypatch.setattr(installer, "READINESS_POLL_INTERVAL_SECONDS", 0)
    monkeypatch.setattr(installer.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(installer.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        installer,
        "inspect_installed_plugin_state",
        lambda _openclaw, _cwd, _root: {"present": False, "source_matches": False, "enabled": False},
    )

    installer.poll_runtime_tools("openclaw", tmp_path, tmp_path, report, "post_link_readiness")

    assert report["post_link_readiness"]["ok"] is False
    assert report["post_link_readiness"]["timeout_reason"]
    assert report["errors"][0]["code"] == "post_link_readiness_timeout"


def test_apply_config_patch_failure_has_structured_error(monkeypatch, tmp_path: Path) -> None:
    def fake_run_checked(_command, **_kwargs):
        raise installer.InstallerError("config_patch_failed", "patch failed safely")

    monkeypatch.setattr(installer, "run_checked", fake_run_checked)

    try:
        installer.apply_config_patch("openclaw", tmp_path, {"plugins": {"entries": {}}})
    except installer.InstallerError as exc:
        assert exc.code == "config_patch_failed"
    else:  # pragma: no cover
        raise AssertionError("expected InstallerError")


def test_run_capture_timeout_returns_bounded_result(monkeypatch, tmp_path: Path) -> None:
    killed: list[int] = []

    class FakeProcess:
        pid = 12345
        returncode = None

        def communicate(self, timeout=None):
            if timeout == 1:
                raise subprocess.TimeoutExpired(["fake"], timeout)
            self.returncode = -9
            return "", ""

    monkeypatch.setattr(installer.subprocess, "Popen", lambda *_args, **_kwargs: FakeProcess())
    monkeypatch.setattr(installer, "terminate_process_tree", lambda pid: killed.append(pid))

    result = installer.run_capture(["fake"], cwd=tmp_path, check=False, timeout=1)

    assert result.returncode == 124
    assert "timed out" in result.stderr
    assert killed == [12345]


def test_installer_dry_run_with_fake_openclaw_does_not_mutate_config_or_memory(tmp_path: Path, monkeypatch) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    memory_file = workspace / "MEMORY.md"
    memory_file.write_text("# Memory\n\nDo not mutate.\n", encoding="utf-8")
    config_path = tmp_path / "openclaw.json"
    config_before = {
        "agents": {"defaults": {"workspace": str(workspace)}},
        "plugins": {"entries": {"memory-core": {"enabled": True}}},
        "tools": {"allow": ["memory_search"]},
    }
    config_path.write_text(json.dumps(config_before), encoding="utf-8")
    log_path = tmp_path / "openclaw_calls.jsonl"
    openclaw = write_fake_openclaw(tmp_path, config_path, workspace, log_path)
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(
        installer,
        "ensure_plugin_package_ready",
        lambda _openclaw_bin, _plugin_root, report: report.update({"plugin_build_validation": {"attempted": True, "ok": True}}),
    )

    rc = installer.main(
        [
            "--dry-run",
            "--openclaw-bin",
            str(openclaw),
            "--workspace",
            str(workspace),
            "--config-path",
            str(config_path),
            "--repo-root",
            str(ROOT),
            "--plugin-root",
            str(ROOT / "integrations/openclaw/nollm-memory-companion"),
            "--report-path",
            str(report_path),
        ]
    )

    assert rc == 0
    assert json.loads(config_path.read_text(encoding="utf-8")) == config_before
    assert memory_file.read_text(encoding="utf-8") == "# Memory\n\nDo not mutate.\n"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["mode"] == "dry_run"
    assert report["ok"] is True
    assert report["write_candidate_visible"] is False
    assert report["integration_evidence"]["source_memory_unchanged"] is True
    assert "MEMORY.md" in report["integration_evidence"]["source_memory_hashes_before"]
    calls = [json.loads(line)["args"] for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert ["config", "patch"] in [call[:2] for call in calls]
    assert ["plugins", "install"] not in [call[:2] for call in calls]


def test_evidence_report_redacts_secret_like_values() -> None:
    evidence = installer.redact(
        {
            "integration_evidence": {"runtime_tool_names": ["nollm_memory_status"]},
            "config": {"token": "secret", "password": "pw"},
        }
    )

    assert evidence["integration_evidence"]["runtime_tool_names"] == ["nollm_memory_status"]
    assert evidence["config"]["token"] == "<redacted>"
    assert evidence["config"]["password"] == "<redacted>"


def arg_namespace(*, apply: bool) -> object:
    return type("Args", (), {"apply": apply})()


def write_fake_openclaw(tmp_path: Path, config_path: Path, workspace: Path, log_path: Path) -> Path:
    script = tmp_path / ("openclaw_fake.py")
    script.write_text(
        f"""
from __future__ import annotations
import json
from pathlib import Path
import sys

CONFIG = Path({str(config_path)!r})
WORKSPACE = Path({str(workspace)!r})
LOG = Path({str(log_path)!r})
args = sys.argv[1:]
with LOG.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"args": args}}) + "\\n")
if args == ["--version"]:
    print("OpenClaw 2026.6.8 fake")
elif args == ["config", "file"]:
    print(CONFIG)
elif args == ["config", "get", "agents.defaults.workspace", "--json"]:
    print(json.dumps(str(WORKSPACE)))
elif args[:3] == ["config", "patch", "--file"]:
    sys.exit(0)
elif args == ["plugins", "build", "--entry", "./dist/index.js", "--check"]:
    sys.exit(0)
elif args == ["plugins", "validate", "--entry", "./dist/index.js"]:
    sys.exit(0)
elif args == ["config", "validate"]:
    sys.exit(0)
elif args[:2] == ["plugins", "install"]:
    sys.exit(0)
elif args[:3] == ["plugins", "inspect", "nollm-memory-companion"]:
    print(json.dumps({{"plugin": {{"toolNames": ["nollm_field_overview", "nollm_open_well", "nollm_surface", "nollm_focus", "nollm_drift", "nollm_read", "nollm_recall_trace", "nollm_memory_status"]}}, "tools": []}}))
else:
    print("unexpected args", args, file=sys.stderr)
    sys.exit(2)
""",
        encoding="utf-8",
    )
    cmd = tmp_path / ("openclaw_fake.cmd" if sys.platform.startswith("win") else "openclaw_fake")
    if sys.platform.startswith("win"):
        cmd.write_text(f"@echo off\n\"{sys.executable}\" \"{script}\" %*\n", encoding="utf-8")
    else:
        cmd.write_text(f"#!/bin/sh\nexec {sys.executable!r} {str(script)!r} \"$@\"\n", encoding="utf-8")
        cmd.chmod(0o755)
    return cmd
