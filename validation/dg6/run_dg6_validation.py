from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

from nollm.dream_geometry.adapters.snapshot_compaction import expand_snapshot_compaction_projection, project_snapshot_compaction
from tests.fixtures.dg6.fixture import empty_snapshot, isolated_duplicate_snapshot, isolated_stress_snapshot
from tests.fixtures.dx2.fixture import build_dx2_cycle


def build_report() -> str:
    empty_projection = project_snapshot_compaction(empty_snapshot())
    duplicate_snapshot = isolated_duplicate_snapshot()
    duplicate_projection = project_snapshot_compaction(duplicate_snapshot)
    stress_snapshot = isolated_stress_snapshot(1000)
    stress_projection = project_snapshot_compaction(stress_snapshot)
    with tempfile.TemporaryDirectory() as temp:
        cycle = build_dx2_cycle(Path(temp) / "dx2")
        dx2_projection = project_snapshot_compaction(cycle.assembly.snapshot)
        dx2_expanded = expand_snapshot_compaction_projection(cycle.assembly.snapshot, dx2_projection)
        dx2_trace_count = len(dx2_expanded)
        dx2_snapshot_id = cycle.assembly.snapshot.snapshot_id
        dx2_plan_id = dx2_projection.compression_plan.plan_id
    lines = [
        "# DG6 Isolated Snapshot Compaction Adapter Report",
        "",
        "## Scope",
        "",
        "DG6 validates a host-supplied finite DF1 `FiniteFieldSnapshot`, derives DG5 view-only compaction from `snapshot.replayed_traces`, and returns an immutable in-memory `SnapshotCompactionProjection`.",
        "",
        "It does not modify snapshot, admission, evidence, field, recall, runtime, storage, cache, database, CLI, OpenClaw, LLM, NLP, embedding, or semantic-search state.",
        "",
        "## Verified Facts",
        "",
        f"- empty snapshot input traces: `{empty_projection.compression_plan.input_trace_count}`",
        f"- empty snapshot view entries: `{empty_projection.compacted_trace_view.entry_count}`",
        f"- real DX2-style CI1->BA1->DA1->DF1 snapshot id: `{dx2_snapshot_id}`",
        f"- real DX2-style expanded trace count: `{dx2_trace_count}`",
        f"- real DX2-style DG5 plan id: `{dx2_plan_id}`",
        f"- isolated synthetic duplicate input traces: `{duplicate_projection.compression_plan.input_trace_count}`",
        f"- isolated synthetic duplicate compacted members: `{duplicate_projection.compression_plan.compacted_member_count}`",
        f"- isolated synthetic duplicate passthrough traces: `{len(duplicate_projection.compression_plan.passthrough_trace_ids)}`",
        f"- isolated synthetic duplicate view entries: `{duplicate_projection.compacted_trace_view.entry_count}`",
        f"- isolated synthetic duplicate estimated view-entry reduction: `{duplicate_projection.compression_plan.estimated_view_entry_reduction}`",
        f"- isolated synthetic stress input traces: `{stress_projection.compression_plan.input_trace_count}`",
        f"- isolated synthetic stress compacted members: `{stress_projection.compression_plan.compacted_member_count}`",
        f"- isolated synthetic stress passthrough traces: `{len(stress_projection.compression_plan.passthrough_trace_ids)}`",
        f"- isolated synthetic stress view entries: `{stress_projection.compacted_trace_view.entry_count}`",
        f"- isolated synthetic stress estimated view-entry reduction: `{stress_projection.compression_plan.estimated_view_entry_reduction}`",
        "",
        "The duplicate and stress rows are isolated synthetic adapter fixtures. They verify DG6/DG5 projection and expansion behavior; they do not claim that DF1 real admission naturally produced duplicate transport views.",
        "",
        "## Reasonable Inference",
        "",
        "A future controlled consumer can read this derived projection without changing the finite snapshot or upstream fact sources.",
        "",
        "## Forbidden Inference",
        "",
        "This report makes no runtime speedup, recall quality, storage compression, automatic compaction, cross-snapshot deduplication, semantic fusion, memory, token, latency, workload, or cost claim.",
        "",
        "## Pending Verification",
        "",
        "Runtime consumers, cross-snapshot policy, persistent compression, performance measurement, and real workload benefit remain unverified.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    report = build_report()
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    if args.stdout or not args.output:
        print(report, end="")


if __name__ == "__main__":
    main()
