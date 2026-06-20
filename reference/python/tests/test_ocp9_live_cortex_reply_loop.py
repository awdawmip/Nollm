from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path

from nollm.dream_cortex_recall import nollm_field_overview, publish_dreamer_delta, source_snapshot
from nollm.openclaw_active_memory_config import (
    OCP9_CORTEX_PROMPT_APPEND,
    OCP9_CORTEX_TOOLS,
    OCP9_LEGACY_NOLLM_TOOLS,
    OCP9_PRIMARY_AGENT_ID,
    OCP9_PROHIBITED_TOOLS,
    build_ocp9_live_cortex_reply_loop_patch,
)
from subprocess_harness import run_subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "examples/openclaw_dream_cortex_fixture"
SCRIPTS = REPO_ROOT / "reference/python/scripts"


def test_ocp9_patch_configures_blind_primary_and_bounded_cortex(tmp_path: Path) -> None:
    source_workspace = tmp_path / "source"
    blind_workspace = tmp_path / "blind"
    sidecar_out = source_workspace / ".nollm-cortex"
    source_workspace.mkdir()
    blind_workspace.mkdir()

    patch = build_ocp9_live_cortex_reply_loop_patch(
        config_before={"agents": {"list": [{"id": "main", "model": "ollama/qwen2.5:7b"}]}},
        repo_root=REPO_ROOT,
        source_workspace_root=source_workspace,
        blind_workspace_root=blind_workspace,
        sidecar_out_dir=sidecar_out,
        model="ollama/qwen2.5:7b",
        transcript_dir=str(sidecar_out / "transcripts"),
    )
    agents = {item["id"]: item for item in patch["agents"]["list"]}
    primary = agents[OCP9_PRIMARY_AGENT_ID]
    cortex = agents["ocp9-nollm-cortex"]
    active = patch["plugins"]["entries"]["active-memory"]["config"]
    companion = patch["plugins"]["entries"]["nollm-memory-companion"]["config"]
    global_tools = patch["tools"]

    assert primary["workspace"] == str(blind_workspace)
    assert primary["contextInjection"] == "never"
    assert primary["bootstrapMaxChars"] == 1
    assert primary["bootstrapTotalMaxChars"] == 1
    assert primary["memorySearch"] == {"provider": "none", "fallback": "none"}
    assert primary["tools"]["alsoAllow"] == OCP9_CORTEX_TOOLS
    assert set(OCP9_PROHIBITED_TOOLS).issubset(set(primary["tools"]["deny"]))
    assert not (set(OCP9_CORTEX_TOOLS) & set(primary["tools"]["deny"]))
    assert cortex["tools"]["alsoAllow"] == OCP9_CORTEX_TOOLS
    assert set(OCP9_PROHIBITED_TOOLS).issubset(set(cortex["tools"]["deny"]))
    assert set(OCP9_CORTEX_TOOLS).issubset(set(global_tools["alsoAllow"]))
    assert not (set(global_tools["alsoAllow"]) & set(OCP9_LEGACY_NOLLM_TOOLS))
    assert active["agents"] == [OCP9_PRIMARY_AGENT_ID]
    assert active["toolsAllow"] == OCP9_CORTEX_TOOLS
    assert active["transcriptDir"] == str(sidecar_out / "transcripts")
    assert companion["workspaceRoot"] == str(source_workspace)
    assert companion["sidecarOutDir"] == str(sidecar_out)
    assert "promptAppend" not in primary
    assert "promptAppend" not in cortex


def test_ocp9_active_tool_surface_excludes_legacy_search_and_raw_tools() -> None:
    forbidden = set(OCP9_LEGACY_NOLLM_TOOLS) | {"memory_search", "memory_get", "read", "exec", "write", "edit"}

    assert not (set(OCP9_CORTEX_TOOLS) & forbidden)
    assert "nollm_memory_status" in OCP9_CORTEX_TOOLS
    assert "nollm_read" in OCP9_CORTEX_TOOLS
    assert "nollm_memory_search" not in OCP9_CORTEX_TOOLS
    assert "nollm_memory_get" not in OCP9_CORTEX_TOOLS
    assert "nollm_memory_recall" not in OCP9_CORTEX_TOOLS


def test_ocp9_prompt_requires_entry_decision_digest_owner_and_stale_handling() -> None:
    prompt = OCP9_CORTEX_PROMPT_APPEND

    assert "explicitly choose the entry" in prompt
    assert "You, the Cortex, write the compact Recall Digest or NONE" in prompt
    assert "Core only executes deterministic geometry" in prompt
    assert "field_stale" in prompt
    assert "refresh required" in prompt
    assert "status is only a stale gate" in prompt
    assert "target_scale bridge and target_scale fine" in prompt
    assert "every named entity" in prompt
    assert "update, status, blockers, roadmap" in prompt
    assert "no current recall for that fact" in prompt
    assert "After nollm_recall_trace" in prompt
    assert "under 600 characters" in prompt
    assert "memory_search" in prompt and "Do not call" in prompt
    assert "drift_class is orientation only" in prompt


def test_ocp9_configure_dry_run_apply_and_idempotency(tmp_path: Path) -> None:
    config_path = tmp_path / "openclaw.json"
    source_workspace = tmp_path / "source"
    blind_workspace = tmp_path / "blind"
    source_workspace.mkdir()
    blind_workspace.mkdir()
    config_before = {
        "agents": {
            "list": [{"id": "main", "model": "ollama/qwen2.5:7b"}],
            "defaults": {"model": {"primary": "ollama/qwen2.5:7b"}},
        },
        "plugins": {"entries": {}},
    }
    config_path.write_text(json.dumps(config_before), encoding="utf-8")
    fake = write_fake_openclaw(tmp_path, config_path)
    script = SCRIPTS / "run_openclaw_nollm_cortex.py"

    dry = run_subprocess(
        [
            sys.executable,
            str(script),
            "configure",
            "--openclaw-bin",
            str(fake),
            "--workspace",
            str(source_workspace),
            "--config-path",
            str(config_path),
            "--blind-workspace",
            str(blind_workspace),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        timeout_seconds=30,
    )
    assert dry.returncode == 0, dry.stderr
    assert json.loads(config_path.read_text(encoding="utf-8")) == config_before
    dry_report = json.loads(dry.stdout)
    assert dry_report["schema_observed"] is True
    assert dry_report["active_memory_observed"] is True
    assert dry_report["nollm_companion_tools"] == OCP9_CORTEX_TOOLS

    first = run_subprocess(
        [
            sys.executable,
            str(script),
            "configure",
            "--openclaw-bin",
            str(fake),
            "--workspace",
            str(source_workspace),
            "--config-path",
            str(config_path),
            "--blind-workspace",
            str(blind_workspace),
            "--apply",
        ],
        cwd=REPO_ROOT,
        timeout_seconds=30,
    )
    second = run_subprocess(
        [
            sys.executable,
            str(script),
            "configure",
            "--openclaw-bin",
            str(fake),
            "--workspace",
            str(source_workspace),
            "--config-path",
            str(config_path),
            "--blind-workspace",
            str(blind_workspace),
            "--apply",
        ],
        cwd=REPO_ROOT,
        timeout_seconds=30,
    )
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    report = json.loads(second.stdout)
    assert report["status"] == "configured"
    assert all(report["safety"].values())

    config_after = json.loads(config_path.read_text(encoding="utf-8"))
    ids = [agent["id"] for agent in config_after["agents"]["list"]]
    assert ids.count("ocp9-nollm-primary-blind") == 1
    assert ids.count("ocp9-nollm-cortex") == 1
    active = config_after["plugins"]["entries"]["active-memory"]["config"]
    primary = next(agent for agent in config_after["agents"]["list"] if agent["id"] == "ocp9-nollm-primary-blind")
    assert active["toolsAllow"] == OCP9_CORTEX_TOOLS
    assert not (set(active["toolsAllow"]) & {"memory_search", "memory_get", "nollm_memory_search", "nollm_memory_get"})
    assert primary["workspace"] == str(blind_workspace)
    assert primary["tools"]["alsoAllow"] == OCP9_CORTEX_TOOLS
    assert not (set(config_after["tools"]["alsoAllow"]) & {"nollm_memory_search", "nollm_memory_get", "nollm_memory_recall"})


def test_ocp9_stale_field_is_visible_without_auto_refresh(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE, workspace)
    out = tmp_path / "out"
    publish_dreamer_delta(workspace, out, make_delta(workspace))
    before = nollm_field_overview(out, workspace=workspace)

    (workspace / "MEMORY.md").write_text(
        (workspace / "MEMORY.md").read_text(encoding="utf-8") + "\n- OCP9 stale field check changed the source plane.\n",
        encoding="utf-8",
    )
    after = nollm_field_overview(out, workspace=workspace)

    assert before["field_stale"] is False
    assert after["field_stale"] is True
    assert after["source_snapshot_hash"] != source_snapshot(workspace)["source_snapshot_hash"]


def make_delta(workspace: Path) -> dict[str, object]:
    delta = json.loads((FIXTURE / "dreamer_output.json").read_text(encoding="utf-8"))
    delta = copy.deepcopy(delta)
    snapshot = source_snapshot(workspace)
    hashes = {item["source_path"]: item["sha256"] for item in snapshot["source_files"]}
    delta["source_snapshot_hash"] = snapshot["source_snapshot_hash"]
    for shard in delta["shards"]:
        for link in shard["source_links"]:
            link["source_sha256"] = hashes[link["source_path"]]
    return delta


def write_fake_openclaw(tmp_path: Path, config_path: Path) -> Path:
    script = tmp_path / "openclaw_ocp9_fake.py"
    script.write_text(
        f"""
from __future__ import annotations
import json
from pathlib import Path
import sys

CONFIG = Path({str(config_path)!r})
args = sys.argv[1:]
if args == ["config", "file"]:
    print(CONFIG)
elif args == ["config", "schema"]:
    print(json.dumps({{"type": "object", "properties": {{"agents": {{"type": "object"}}}}}}))
elif args == ["agents", "list", "--json"]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    agents = config.get("agents", {{}}).get("list", [])
    print(json.dumps([dict(agent, isDefault=(agent.get("id") == "main")) for agent in agents]))
elif args[:3] == ["plugins", "inspect", "active-memory"]:
    print(json.dumps({{"plugin": {{"id": "active-memory", "version": "2026.6.8", "status": "loaded", "configUiHints": {{"toolsAllow": {{}}, "promptAppend": {{}}, "agents": {{}}}}}}}}))
elif args[:3] == ["plugins", "inspect", "nollm-memory-companion"]:
    print(json.dumps({{"plugin": {{"id": "nollm-memory-companion", "version": "0.1.0", "status": "loaded", "contracts": {{"tools": {repr(OCP9_CORTEX_TOOLS)}}}}}}}))
elif args[:3] == ["config", "patch", "--file"]:
    patch = json.loads(Path(args[3]).read_text(encoding="utf-8"))
    dry = "--dry-run" in args
    if not dry:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        config.setdefault("agents", {{}})["list"] = patch["agents"]["list"]
        config["tools"] = patch["tools"]
        config.setdefault("plugins", {{}}).setdefault("entries", {{}}).update(patch["plugins"]["entries"])
        CONFIG.write_text(json.dumps(config), encoding="utf-8")
    print(json.dumps({{"ok": True, "dry_run": dry}}))
elif args == ["config", "validate"]:
    print("Config valid")
else:
    print("unexpected args", args, file=sys.stderr)
    sys.exit(2)
""",
        encoding="utf-8",
    )
    cmd = tmp_path / ("openclaw_ocp9_fake.cmd" if sys.platform.startswith("win") else "openclaw_ocp9_fake")
    if sys.platform.startswith("win"):
        cmd.write_text(f"@echo off\n\"{sys.executable}\" \"{script}\" %*\n", encoding="utf-8")
    else:
        cmd.write_text(f"#!/bin/sh\nexec {sys.executable!r} {str(script)!r} \"$@\"\n", encoding="utf-8")
        cmd.chmod(0o755)
    return cmd
