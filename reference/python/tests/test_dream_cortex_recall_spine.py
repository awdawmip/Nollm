from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Mapping

from nollm.dream_cortex_recall import (
    FORBIDDEN_RECALL_SEMANTICS,
    ingest_dreamer_fixture,
    nollm_drift,
    nollm_field_overview,
    nollm_focus,
    nollm_open_well,
    nollm_read,
    nollm_recall_trace,
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


def test_missing_field_fails_closed_without_fixture_fallback(tmp_path: Path) -> None:
    report = nollm_field_overview(tmp_path)

    assert report["ok"] is False
    assert report["error"] == "field_unavailable"
    assert "explicit Dreamer ingestion" in report["message"]
    assert not (tmp_path / "dream_field.json").exists()


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


def test_overview_has_no_query_or_lexical_ranking(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    overview = nollm_field_overview(tmp_path)

    assert overview["selection_role"] == "cortex_must_choose_entry"
    assert overview["query_score"] is None
    assert overview["coarse_cells"][0]["shard_id"] in {"surface_openclaw_nollm", "surface_unrelated_lab"}
    assert_no_lexical_scores(overview)


def test_open_well_requires_explicit_cortex_anchor_vector(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)

    well = open_test_well(tmp_path)

    assert well["gravity_well"]["anchor_vector"] == {"cortex": 0.7, "nollm": 1.0, "openclaw": 1.0}
    assert well["entry_shard_id"] == "surface_openclaw_nollm"
    assert well["core_anchor_extraction"] is False


def test_surface_focus_drift_use_geometry_and_gravity(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)
    well_id = open_test_well(tmp_path)["gravity_well"]["well_id"]

    surface = nollm_surface(tmp_path, well_id=well_id, center_shard_id="surface_openclaw_nollm", radius=2, target_scale="bridge")
    focus = nollm_focus(tmp_path, well_id=well_id, target_shard_id="bridge_active_memory_cortex", target_scale="fine")
    drift = nollm_drift(
        tmp_path,
        well_id=well_id,
        current_shard_id="bridge_active_memory_cortex",
        chosen_shard_id="lateral_search_adapter_boundary",
    )

    assert "coverage_template" in surface["relationship_methods"]
    assert focus["core_selected_target"] is False
    assert focus["gravity_report"]["R_column_ring"] is not None
    assert focus["gravity_report"]["S_scale_delta"] == 1
    assert focus["gravity_report"]["projection_method"] in {"coverage_template", "approximate_center"}
    assert drift["selected"]["gravity_report"]["drift_class"] in {
        "core",
        "halo",
        "near_drift",
        "far_coherent",
        "far_weak",
        "semantic_break",
    }
    assert drift["hard_drift_rejection"] is False
    assert drift["return_vector"]["method"] == "axial_delta_to_well"
    assert_no_lexical_scores(surface)
    assert_no_lexical_scores(focus)
    assert_no_lexical_scores(drift)


def test_coordinate_perturbation_changes_geometry_behavior(tmp_path: Path) -> None:
    base_out = tmp_path / "base"
    moved_out = tmp_path / "moved"
    moved_dreamer = tmp_path / "moved_dreamer.json"
    data = json.loads(DREAMER_OUTPUT.read_text(encoding="utf-8"))
    for shard in data["shards"]:
        if shard["shard_id"] == "lateral_search_adapter_boundary":
            shard["placement"]["q"] = -4
            shard["placement"]["r"] = 4
        if shard["shard_id"] == "bridge_active_memory_cortex":
            shard["placement"]["q"] = -2
            shard["placement"]["r"] = 3
    moved_dreamer.write_text(json.dumps(data, indent=2), encoding="utf-8")

    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, base_out)
    ingest_dreamer_fixture(FIXTURE, moved_dreamer, moved_out)
    base_well = open_test_well(base_out)["gravity_well"]["well_id"]
    moved_well = open_test_well(moved_out)["gravity_well"]["well_id"]
    base_drift = nollm_drift(base_out, well_id=base_well, current_shard_id="bridge_active_memory_cortex", chosen_shard_id="lateral_search_adapter_boundary")
    moved_drift = nollm_drift(moved_out, well_id=moved_well, current_shard_id="bridge_active_memory_cortex", chosen_shard_id="lateral_search_adapter_boundary")

    assert base_drift["selected"]["gravity_report"] != moved_drift["selected"]["gravity_report"]
    assert base_drift["return_vector"] != moved_drift["return_vector"]


def test_read_and_trace_are_exact_and_structural(tmp_path: Path) -> None:
    ingest_dreamer_fixture(FIXTURE, DREAMER_OUTPUT, tmp_path)
    well_id = open_test_well(tmp_path)["gravity_well"]["well_id"]

    read = nollm_read(tmp_path, shard_id="fine_chinese_return_instruction")
    trace = nollm_recall_trace(
        tmp_path,
        well_id=well_id,
        path=["surface_openclaw_nollm", "bridge_active_memory_cortex", "fine_chinese_return_instruction"],
    )

    assert read["read_unit"] == "dream_shard"
    assert read["raw_source_chunk"] is False
    assert read["gravity_mark"]["content_id"] == "fine_chinese_return_instruction"
    assert trace["core_composed_digest"] is False
    assert trace["prose_digest"] is None
    assert [item["shard_id"] for item in trace["trace"]] == trace["path"]


def test_forbidden_recall_paths_are_not_required(tmp_path: Path) -> None:
    report = run_demo_report(FIXTURE, DREAMER_OUTPUT, tmp_path)

    assert report["source_files_byte_identical_after_projection"] is True
    assert all(value is False for value in FORBIDDEN_RECALL_SEMANTICS.values())
    assert all(value is False for value in report["forbidden_recall_semantics"].values())


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
    assert report["schema"] == "nollm.dream_cortex_demo_report.v2"
    assert report["ok"] is True


def open_test_well(out_dir: Path) -> dict[str, object]:
    return nollm_open_well(
        out_dir,
        entry_shard_id="surface_openclaw_nollm",
        entry_task="Cortex-selected OpenClaw/Nollm integration entry",
        anchor_vector={"openclaw": 1.0, "nollm": 1.0, "cortex": 0.7},
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
