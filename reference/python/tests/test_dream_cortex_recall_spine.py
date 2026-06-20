from __future__ import annotations

import copy
import json
import shutil
import sys
from pathlib import Path
from typing import Mapping

import pytest

from nollm.dream_cortex_recall import (
    FORBIDDEN_RECALL_SEMANTICS,
    cleanup_expired_wells,
    build_dream_packet,
    ingest_dreamer_fixture,
    nollm_drift,
    nollm_field_overview,
    nollm_focus,
    nollm_open_well,
    nollm_read,
    nollm_recall_trace,
    nollm_surface,
    publish_dreamer_delta,
    run_demo_report,
    source_snapshot,
)
from nollm.openclaw_active_memory_config import (
    OCP6R_CORTEX_TOOLS,
    build_ocp6r_cortex_active_memory_patch,
    build_ocp7_dreamer_agent_patch,
)
from subprocess_harness import run_subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "examples/openclaw_dream_cortex_fixture"
DREAMER_OUTPUT = FIXTURE / "dreamer_output.json"
SCRIPTS = REPO_ROOT / "reference/python/scripts"
sys.path.insert(0, str(SCRIPTS))
from run_openclaw_nollm_dreamer import build_dreamer_prompt  # noqa: E402


def test_missing_field_fails_closed_without_fixture_fallback(tmp_path: Path) -> None:
    report = nollm_field_overview(tmp_path)

    assert report["ok"] is False
    assert report["error"] == "field_unavailable"
    assert "explicit Dreamer ingestion" in report["message"]
    assert not (tmp_path / "dream_field.json").exists()


def test_dreamer_contract_accepts_mixed_language_semantic_delta(tmp_path: Path) -> None:
    before = source_snapshot(FIXTURE)
    report = ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)
    field = json.loads((tmp_path / "fields" / report["field_id"] / report["revision_id"] / "dream_field.json").read_text(encoding="utf-8"))
    after = source_snapshot(FIXTURE)

    assert report["ok"] is True
    assert report["status"] == "published"
    assert before["source_files"] == after["source_files"]
    assert before["read_only"] is True
    assert all("q" not in shard.get("dreamer_intents", {}) for shard in field["shards"])
    assert field["core_placement"]["dreamer_coordinates_accepted"] is False
    assert any("中文路径" in shard["text"] for shard in field["shards"])


def test_dreamer_contract_rejects_forbidden_fields_and_bad_source_links(tmp_path: Path) -> None:
    delta = load_delta()
    delta["shards"][0]["q"] = 1
    with pytest.raises(ValueError, match="forbidden Dreamer field"):
        publish_dreamer_delta(FIXTURE, tmp_path / "bad-q", delta)

    delta = load_delta()
    delta["shards"][0]["source_links"][0]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="source hash mismatch"):
        publish_dreamer_delta(FIXTURE, tmp_path / "bad-hash", delta)

    delta = load_delta()
    delta["shards"][0]["source_links"][0]["line_range"] = [3, 99]
    with pytest.raises(ValueError, match="exceeds source length"):
        publish_dreamer_delta(FIXTURE, tmp_path / "bad-lines", delta)

    packet = build_dream_packet(FIXTURE, field_id="openclaw-dream-field")
    delta = make_memory_only_delta(FIXTURE)
    delta["shards"][0]["source_links"][0]["line_range"] = [1, 6]
    packet["source_material"][0]["line_range"] = [3, 5]
    with pytest.raises(ValueError, match="outside dream packet material"):
        publish_dreamer_delta(FIXTURE, tmp_path / "bad-packet-span", delta, dream_packet=packet)
    assert not (tmp_path / "bad-packet-span" / "current_field.json").exists()


def test_dream_packet_prompt_has_source_meaning_no_user_query_and_forbids_coordinates() -> None:
    packet = build_dream_packet(FIXTURE, field_id="openclaw-dream-field")
    prompt = build_dreamer_prompt(packet)

    assert "Nollm must treat OpenClaw" in prompt
    assert packet["source_snapshot_hash"] in prompt
    assert packet["source_material"][0]["source_path"] == "MEMORY.md"
    assert packet["source_material"][0]["source_sha256"]
    assert packet["source_material"][0]["line_range"] == [1, 6]
    assert "what did I ask" not in prompt.lower()
    assert "current user question" not in prompt.lower()
    assert "memory_search" not in prompt
    assert "memory_get" not in prompt
    assert "q" in prompt and "HexAddress" in prompt


def test_core_placement_is_deterministic_and_semantic_intent_changes_geometry(tmp_path: Path) -> None:
    first = publish_dreamer_delta(FIXTURE, tmp_path / "one", load_delta())
    second = publish_dreamer_delta(FIXTURE, tmp_path / "two", load_delta())
    first_field = read_field(tmp_path / "one", first)
    second_field = read_field(tmp_path / "two", second)

    assert [(s["shard_id"], s["placement"]) for s in first_field["shards"]] == [
        (s["shard_id"], s["placement"]) for s in second_field["shards"]
    ]

    changed = load_delta()
    for shard in changed["shards"]:
        if shard["semantic_key"] == "lateral-search-adapter-boundary":
            shard["preferred_scale"] = "fine"
            shard["near_intents"] = ["fine-chinese-return-instruction"]
    moved = publish_dreamer_delta(FIXTURE, tmp_path / "moved", changed)
    moved_field = read_field(tmp_path / "moved", moved)

    assert placement_of(first_field, "lateral-search-adapter-boundary") != placement_of(moved_field, "lateral-search-adapter-boundary")
    assert "placement" not in changed["shards"][0]


def test_revision_evolution_and_no_change_runner(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE, workspace)
    out = tmp_path / "out"
    mock_one = tmp_path / "dreamer_one.json"
    mock_one.write_text(json.dumps(make_memory_only_delta(workspace), ensure_ascii=False), encoding="utf-8")
    script = REPO_ROOT / "reference/python/scripts/run_openclaw_nollm_dreamer.py"

    first = run_subprocess([sys.executable, str(script), "refresh", "--workspace", str(workspace), "--out", str(out), "--mock-dreamer-output", str(mock_one)], cwd=REPO_ROOT, timeout_seconds=30)
    assert first.returncode == 0, first.stderr
    first_report = json.loads(first.stdout)

    second = run_subprocess([sys.executable, str(script), "refresh", "--workspace", str(workspace), "--out", str(out), "--mock-dreamer-output", str(mock_one)], cwd=REPO_ROOT, timeout_seconds=30)
    assert second.returncode == 0, second.stderr
    second_report = json.loads(second.stdout)
    assert second_report["status"] == "no_change"
    assert second_report["dreamer_called"] is False

    before_source = source_snapshot(workspace)["source_files"]
    (workspace / "DREAMS.md").write_text((workspace / "DREAMS.md").read_text(encoding="utf-8") + "\n- 新梦句：field refresh keeps old wells stable.\n", encoding="utf-8")
    mock_two = tmp_path / "dreamer_two.json"
    delta_two = make_memory_only_delta(workspace)
    delta_two["shards"][0]["text"] = "OpenClaw memory files stay read-only while Nollm publishes a refreshed immutable dream field revision."
    mock_two.write_text(json.dumps(delta_two, ensure_ascii=False), encoding="utf-8")
    third = run_subprocess([sys.executable, str(script), "refresh", "--workspace", str(workspace), "--out", str(out), "--mock-dreamer-output", str(mock_two)], cwd=REPO_ROOT, timeout_seconds=30)
    assert third.returncode == 0, third.stderr
    third_report = json.loads(third.stdout)

    assert third_report["status"] == "published"
    assert third_report["parent_revision_id"] == first_report["revision_id"]
    assert third_report["revision_id"] != first_report["revision_id"]
    assert source_snapshot(FIXTURE)["source_files"] != []
    assert before_source != source_snapshot(workspace)["source_files"]


def test_concurrent_wells_bind_immutable_revisions(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    shutil.copytree(FIXTURE, workspace)
    out = tmp_path / "out"
    rev1 = publish_dreamer_delta(workspace, out, make_delta(workspace))
    well_a = open_test_well(out, created_at="2026-06-20T00:00:00Z")
    well_b = open_test_well(out, created_at="2026-06-20T00:00:01Z")

    (workspace / "DREAMS.md").write_text((workspace / "DREAMS.md").read_text(encoding="utf-8") + "\n- Revision two changes the no-write dream sentence.\n", encoding="utf-8")
    delta2 = make_delta(workspace)
    for shard in delta2["shards"]:
        if shard["semantic_key"] == "fine-no-memory-file-writes":
            shard["text"] = "Revision two: Nollm still refuses to mutate OpenClaw memory files and reads old wells through old revisions."
    rev2 = publish_dreamer_delta(workspace, out, delta2)
    well_c = open_test_well(out, created_at="2026-06-20T00:00:02Z")

    read_a = nollm_read(out, well_id=well_a["gravity_well"]["well_id"], shard_id="fine-no-memory-file-writes")
    read_b = nollm_read(out, well_id=well_b["gravity_well"]["well_id"], shard_id="fine-no-memory-file-writes")
    read_c = nollm_read(out, well_id=well_c["gravity_well"]["well_id"], shard_id="fine-no-memory-file-writes")

    assert rev1["revision_id"] != rev2["revision_id"]
    assert read_a["revision_id"] == rev1["revision_id"]
    assert read_b["revision_id"] == rev1["revision_id"]
    assert read_c["revision_id"] == rev2["revision_id"]
    assert "Revision two" not in read_a["shard"]["text"]
    assert "Revision two" in read_c["shard"]["text"]


def test_open_well_ttl_cleanup_is_well_only(tmp_path: Path) -> None:
    publish_dreamer_delta(FIXTURE, tmp_path, load_delta())
    old = open_test_well(tmp_path, created_at="2026-06-20T00:00:00Z", ttl_seconds=1)
    fresh = open_test_well(tmp_path, created_at="2026-06-20T00:00:10Z", ttl_seconds=3600)

    report = cleanup_expired_wells(tmp_path, now_utc="2026-06-20T00:00:05Z")

    assert old["gravity_well"]["well_id"] in report["removed_wells"]
    assert fresh["gravity_well"]["well_id"] not in report["removed_wells"]
    assert (tmp_path / "current_field.json").exists()


def test_surface_focus_drift_read_and_trace_use_revision_scoped_well(tmp_path: Path) -> None:
    publish_dreamer_delta(FIXTURE, tmp_path, load_delta())
    well_id = open_test_well(tmp_path)["gravity_well"]["well_id"]

    surface = nollm_surface(tmp_path, well_id=well_id, center_shard_id="surface-openclaw-nollm", radius=2, target_scale="bridge")
    focus = nollm_focus(tmp_path, well_id=well_id, target_shard_id="bridge-active-memory-cortex", target_scale="fine")
    drift = nollm_drift(tmp_path, well_id=well_id, current_shard_id="bridge-active-memory-cortex", chosen_shard_id="lateral-search-adapter-boundary")
    read = nollm_read(tmp_path, well_id=well_id, shard_id="fine-chinese-return-instruction")
    trace = nollm_recall_trace(tmp_path, well_id=well_id, path=["surface-openclaw-nollm", "bridge-active-memory-cortex", "fine-chinese-return-instruction"])

    assert "coverage_template" in surface["relationship_methods"]
    assert focus["core_selected_target"] is False
    assert focus["gravity_report"]["S_scale_delta"] == 1
    assert drift["hard_drift_rejection"] is False
    assert drift["return_vector"]["method"] == "axial_delta_to_well"
    assert read["well_id"] == well_id
    assert read["read_unit"] == "dream_shard"
    assert read["raw_source_chunk"] is False
    assert trace["core_composed_digest"] is False
    assert trace["prose_digest"] is None
    assert_no_lexical_scores({"surface": surface, "focus": focus, "drift": drift})


def test_forbidden_recall_paths_and_demo_report_are_stable(tmp_path: Path) -> None:
    first = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path / "one")
    second = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path / "two")

    assert first == second
    assert first["schema"] == "nollm.dream_cortex_demo_report.v3"
    assert first["source_files_byte_identical_after_projection"] is True
    assert all(value is False for value in FORBIDDEN_RECALL_SEMANTICS.values())
    assert all(value is False for value in first["forbidden_recall_semantics"].values())


def test_ocp6r_active_memory_config_uses_geometry_navigation_tools_only(tmp_path: Path) -> None:
    patch = build_ocp6r_cortex_active_memory_patch(
        config_before={"agents": {"list": [{"id": "main"}]}},
        repo_root=REPO_ROOT,
        workspace_root=FIXTURE,
        transcript_dir=str(tmp_path / "transcripts"),
    )
    active = patch["plugins"]["entries"]["active-memory"]["config"]
    agent = patch["agents"]["list"][-1]

    assert active["toolsAllow"] == OCP6R_CORTEX_TOOLS
    assert "memory_search" not in active["toolsAllow"]
    assert "memory_get" not in active["toolsAllow"]
    assert "memory_search" in agent["tools"]["deny"]
    assert "nollm_field_overview" in active["promptAppend"]
    assert "nollm_recall_trace" in active["promptAppend"]
    assert "Core does not compose prose" in active["promptAppend"]


def test_ocp7_dreamer_agent_config_is_restricted() -> None:
    patch = build_ocp7_dreamer_agent_patch(config_before={"agents": {"list": [{"id": "main"}]}}, workspace_root=FIXTURE)
    agent = patch["agents"]["list"][-1]

    assert agent["id"] == "nollm-dreamer"
    assert agent["contextInjection"] == "never"
    assert agent["memorySearch"] == {"provider": "none", "fallback": "none"}
    assert agent["tools"]["alsoAllow"] == []
    assert "memory_search" in agent["tools"]["deny"]
    assert "write" in agent["tools"]["deny"]


def test_dreamer_configure_dry_run_and_apply_are_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    config_path = tmp_path / "openclaw.json"
    config_before = {"agents": {"list": [{"id": "main", "model": "ollama/qwen2.5:7b"}], "defaults": {"model": {"primary": "ollama/qwen2.5:7b"}}}}
    config_path.write_text(json.dumps(config_before), encoding="utf-8")
    fake = write_fake_openclaw_for_dreamer(tmp_path, config_path)
    script = REPO_ROOT / "reference/python/scripts/run_openclaw_nollm_dreamer.py"

    dry = run_subprocess([sys.executable, str(script), "configure", "--openclaw-bin", str(fake), "--workspace", str(workspace), "--config-path", str(config_path), "--dry-run"], cwd=REPO_ROOT, timeout_seconds=30)
    assert dry.returncode == 0, dry.stderr
    assert json.loads(config_path.read_text(encoding="utf-8")) == config_before

    first = run_subprocess([sys.executable, str(script), "configure", "--openclaw-bin", str(fake), "--workspace", str(workspace), "--config-path", str(config_path), "--apply"], cwd=REPO_ROOT, timeout_seconds=30)
    second = run_subprocess([sys.executable, str(script), "configure", "--openclaw-bin", str(fake), "--workspace", str(workspace), "--config-path", str(config_path), "--apply"], cwd=REPO_ROOT, timeout_seconds=30)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    report = json.loads(second.stdout)
    assert report["agent_visible"] is True
    config_after = json.loads(config_path.read_text(encoding="utf-8"))
    assert [agent["id"] for agent in config_after["agents"]["list"]].count("nollm-dreamer") == 1
    dreamer = config_after["agents"]["list"][-1]
    assert dreamer["contextInjection"] == "never"
    assert dreamer["tools"]["alsoAllow"] == []
    assert "promptAppend" not in dreamer


def test_demo_script_outputs_json(tmp_path: Path) -> None:
    script = REPO_ROOT / "reference/python/scripts/run_dream_cortex_demo.py"
    completed = run_subprocess(
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(REPO_ROOT),
            "--workspace",
            str(FIXTURE),
            "--dreamer-output",
            str(DREAMER_OUTPUT),
            "--out",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        timeout_seconds=30,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / "dream_cortex_demo_report.json").read_text(encoding="utf-8"))
    assert report["schema"] == "nollm.dream_cortex_demo_report.v3"
    assert report["ok"] is True


def load_delta() -> dict[str, object]:
    return json.loads(DREAMER_OUTPUT.read_text(encoding="utf-8"))


def make_delta(workspace: Path) -> dict[str, object]:
    delta = copy.deepcopy(load_delta())
    snapshot = source_snapshot(workspace)
    hashes = {item["source_path"]: item["sha256"] for item in snapshot["source_files"]}
    delta["source_snapshot_hash"] = snapshot["source_snapshot_hash"]
    for shard in delta["shards"]:
        for link in shard["source_links"]:
            link["source_sha256"] = hashes[link["source_path"]]
    return delta


def make_memory_only_delta(workspace: Path) -> dict[str, object]:
    snapshot = source_snapshot(workspace)
    memory = next(item for item in snapshot["source_files"] if item["source_path"] == "MEMORY.md")
    return {
        "schema": "nollm.dreamer_delta.v1",
        "source_snapshot_hash": snapshot["source_snapshot_hash"],
        "field_id": "openclaw-dream-field",
        "shards": [
            {
                "semantic_key": "memory-source-plane",
                "text": "OpenClaw memory files are the read-only source plane for Nollm dream-field distillation.",
                "status": "source_backed",
                "preferred_scale": "coarse",
                "anchors": ["OpenClaw", "Nollm", "read-only"],
                "source_links": [{"source_path": "MEMORY.md", "line_range": [3, 5], "source_sha256": memory["sha256"]}],
                "continuity": {"prior_semantic_key": None},
                "near_intents": [],
                "bridge_intents": ["memory-cortex-entry"],
            },
            {
                "semantic_key": "memory-cortex-entry",
                "text": "Active Memory can act as Cortex while Nollm Core owns dream shards and geometry.",
                "status": "derived",
                "preferred_scale": "bridge",
                "anchors": ["Active Memory", "Cortex", "geometry"],
                "source_links": [{"source_path": "MEMORY.md", "line_range": [4, 5], "source_sha256": memory["sha256"]}],
                "continuity": {"prior_semantic_key": None},
                "near_intents": ["memory-source-plane"],
                "bridge_intents": [],
            },
        ],
        "cluster_intents": [{"label": "Memory source plane", "members": ["memory-source-plane", "memory-cortex-entry"]}],
    }


def read_field(out: Path, report: Mapping[str, object]) -> dict[str, object]:
    return json.loads((out / "fields" / str(report["field_id"]) / str(report["revision_id"]) / "dream_field.json").read_text(encoding="utf-8"))


def placement_of(field: Mapping[str, object], shard_id: str) -> Mapping[str, object]:
    for shard in field["shards"]:
        if shard["shard_id"] == shard_id:
            return shard["placement"]
    raise AssertionError(f"missing shard {shard_id}")


def open_test_well(out_dir: Path, *, created_at: str = "2026-06-20T00:00:00Z", ttl_seconds: int = 3600) -> dict[str, object]:
    return nollm_open_well(
        out_dir,
        entry_shard_id="surface-openclaw-nollm",
        entry_task="Cortex-selected OpenClaw/Nollm integration entry",
        anchor_vector={"openclaw": 1.0, "nollm": 1.0, "cortex": 0.7},
        created_at_utc=created_at,
        ttl_seconds=ttl_seconds,
    )


def assert_no_lexical_scores(value: object) -> None:
    forbidden = {"entry_overlap", "token_score", "rank_score", "alias_score", "raw_source_top_k_score", "query_rank"}
    if isinstance(value, Mapping):
        assert not (set(value) & forbidden)
        for item in value.values():
            assert_no_lexical_scores(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_lexical_scores(item)


def write_fake_openclaw_for_dreamer(tmp_path: Path, config_path: Path) -> Path:
    script = tmp_path / "openclaw_dreamer_fake.py"
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
    print(json.dumps({{"type": "object"}}))
elif args == ["agents", "list", "--json"]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    agents = config.get("agents", {{}}).get("list", [])
    print(json.dumps([dict(agent, isDefault=(agent.get("id") == "main")) for agent in agents]))
elif args[:3] == ["config", "patch", "--file"]:
    patch = json.loads(Path(args[3]).read_text(encoding="utf-8"))
    dry = "--dry-run" in args
    if not dry:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        config.setdefault("agents", {{}})["list"] = patch["agents"]["list"]
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
    cmd = tmp_path / ("openclaw_dreamer_fake.cmd" if sys.platform.startswith("win") else "openclaw_dreamer_fake")
    if sys.platform.startswith("win"):
        cmd.write_text(f"@echo off\n\"{sys.executable}\" \"{script}\" %*\n", encoding="utf-8")
    else:
        cmd.write_text(f"#!/bin/sh\nexec {sys.executable!r} {str(script)!r} \"$@\"\n", encoding="utf-8")
        cmd.chmod(0o755)
    return cmd
