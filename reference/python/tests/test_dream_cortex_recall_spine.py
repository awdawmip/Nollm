from __future__ import annotations

import json
import sys
from pathlib import Path

from nollm.dream_cortex_recall import (
    FORBIDDEN_RECALL_SEMANTICS,
    ingest_dreamer_fixture,
    nollm_compose_digest,
    nollm_drift,
    nollm_focus,
    nollm_orient,
    nollm_read,
    nollm_surface,
    run_demo_report,
    source_snapshot,
)
from nollm.openclaw_active_memory_config import (
    OCP6R_CORTEX_TOOLS,
    build_ocp6r_cortex_active_memory_patch,
)
from subprocess_harness import run_subprocess


REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = REPO_ROOT / "examples/openclaw_dream_cortex_fixture"
DREAMER_OUTPUT = FIXTURE / "dreamer_output.json"


def test_source_snapshot_is_read_only_and_hashes_sources(tmp_path: Path) -> None:
    before = source_snapshot(FIXTURE)
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)
    after = source_snapshot(FIXTURE)

    assert before["source_files"] == after["source_files"]
    assert before["read_only"] is True
    assert {item["source_path"] for item in before["source_files"]} == {
        "DREAMS.md",
        "MEMORY.md",
        "memory/2026-06-20.md",
    }


def test_orientation_selects_coarse_surface_without_alias_top_k(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    report = nollm_orient(tmp_path, query="OpenClaw Active Memory 作为 Cortex 如何使用 Nollm?")

    assert report["not_alias_top_k"] is True
    assert report["orientation_mode"] == "bounded_coarse_surface"
    assert report["surfaces"][0]["surface_id"] == "surface_openclaw_nollm"
    assert report["surfaces"][0]["scale"] == "coarse"


def test_surface_and_focus_stop_at_sufficient_scale(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    surface = nollm_surface(tmp_path, surface_id="surface_openclaw_nollm")
    focus = nollm_focus(
        tmp_path,
        query="OpenClaw Active Memory Cortex recall spine",
        surface_id="surface_openclaw_nollm",
    )

    assert surface["content_bearing"] is True
    assert focus["selected"]["shard_id"] == "bridge_active_memory_cortex"
    assert focus["selected"]["scale"] == "bridge"
    assert focus["stopped_at_sufficient_scale"] is True
    assert focus["raw_span_descent_required"] is False


def test_lateral_branch_and_return_are_labeled(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    drift = nollm_drift(tmp_path, shard_id="bridge_active_memory_cortex", query="OpenClaw Cortex")

    assert drift["lateral"][0]["shard_id"] == "lateral_search_adapter_boundary"
    assert drift["lateral"][0]["label"] == "lateral"
    assert drift["return"]["shard_id"] == "surface_openclaw_nollm"
    assert "Return to the entry task" in drift["return_instruction"]
    assert drift["hard_drift_rejection"] is False


def test_unrelated_query_yields_none(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    digest = nollm_compose_digest(tmp_path, query="咖啡机保修编号是多少?")

    assert digest["nollm_recall_digest"] == "NONE"
    assert digest["primary"] == []
    assert "do not invent memory" in digest["return"]["instruction"]


def test_chinese_and_mixed_language_prompts_navigate(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    digest = nollm_compose_digest(tmp_path, query="Nollm 和 OpenClaw memory-core 的边界是什么?")
    read = nollm_read(tmp_path, shard_id="fine_chinese_return_instruction")

    assert digest["nollm_recall_digest"] == "READY"
    assert digest["primary"][0]["shard_id"] in {
        "bridge_active_memory_cortex",
        "surface_openclaw_nollm",
        "fine_no_memory_file_writes",
    }
    assert read["shard"]["source_trace_kind"] == "derived"
    assert "粗表面" in read["shard"]["text"]


def test_forbidden_recall_paths_are_not_required(tmp_path: Path) -> None:
    report = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path)

    assert report["source_files_byte_identical_after_projection"] is True
    assert all(value is False for value in FORBIDDEN_RECALL_SEMANTICS.values())
    assert all(value is False for value in report["forbidden_recall_semantics"].values())


def test_ocp6r_active_memory_config_uses_navigation_tools_only(tmp_path: Path) -> None:
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
    assert "nollm_orient" in active["promptAppend"]
    assert "NONE" in active["promptAppend"]


def test_demo_report_is_stable_across_runs(tmp_path: Path) -> None:
    first = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path / "one")
    second = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path / "two")

    assert first == second


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
    assert report["schema"] == "nollm.dream_cortex_demo_report.v1"
    assert report["ok"] is True
