from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from nollm.dream_geometry.compression import plan_trace_compaction
from nollm.dream_geometry.compression.view import build_compacted_trace_view, expand_compression_plan
from tests.fixtures.dg5.fixture import mixed_fixture, stress_fixture, trace_index


def build_report() -> str:
    mixed = mixed_fixture()
    mixed_plan = plan_trace_compaction(mixed)
    mixed_view = build_compacted_trace_view(mixed_plan, trace_index(mixed))
    mixed_expanded = expand_compression_plan(mixed_plan, trace_index(mixed))
    stress = stress_fixture(1000)
    stress_plan = plan_trace_compaction(stress)
    stress_view = build_compacted_trace_view(stress_plan, trace_index(stress))
    stress_expanded = expand_compression_plan(stress_plan, trace_index(stress))
    independent_passthrough_count = sum(1 for trace_id in mixed_plan.passthrough_trace_ids if trace_id.startswith("pass-"))
    independent_passthrough_count += sum(1 for trace_id in stress_plan.passthrough_trace_ids if trace_id.startswith("pass-"))
    non_conflation_witness_count = sum(1 for trace_id in mixed_plan.passthrough_trace_ids if trace_id in {"collision-a", "same-cell-distinct"})
    non_conflation_witness_count += sum(1 for trace_id in stress_plan.passthrough_trace_ids if trace_id.startswith("near-"))
    lines = [
        "# DG5 Evidence-Preserving Trace Compaction Validation Report",
        "",
        "- validation kind: finite synthetic validation of derived, in-memory compacted transport views",
        "- policy: `dg5_exact_transport_view` version `1`, mode `view_only`",
        "- sealed dependency: DG2 `compact_traces` and `expand_compaction`",
        "",
        "## Verified Facts",
        "",
        "- Exact duplicate transport views in the finite fixture form compacted view entries.",
        "- Lossless expansion returns every original `GrowthTrace` in canonical input order.",
        "- Distinct evidence identity, proposal, derivation, shared support, or same-cell differences remain passthrough.",
        "- The plan and view are pure-memory, read-only, and disposable derived objects.",
        "",
        "## Finite Counts",
        "",
        "| fixture | input traces | compacted members | passthrough traces | view entries | estimated view-entry reduction | lossless expansion |",
        "|---|---:|---:|---:|---:|---:|---|",
        f"| mixed | {mixed_plan.input_trace_count} | {mixed_plan.compacted_member_count} | {len(mixed_plan.passthrough_trace_ids)} | {mixed_view.entry_count} | {mixed_plan.estimated_view_entry_reduction} | {str(len(mixed_expanded) == mixed_plan.input_trace_count).lower()} |",
        f"| stress | {stress_plan.input_trace_count} | {stress_plan.compacted_member_count} | {len(stress_plan.passthrough_trace_ids)} | {stress_view.entry_count} | {stress_plan.estimated_view_entry_reduction} | {str(len(stress_expanded) == stress_plan.input_trace_count).lower()} |",
        "",
        f"- independent passthrough trace count: `{independent_passthrough_count}`",
        f"- non-conflation witness trace count: `{non_conflation_witness_count}`",
        f"- mixed plan fingerprint: `{mixed_plan.plan_fingerprint}`",
        f"- mixed view fingerprint: `{mixed_view.view_fingerprint}`",
        f"- stress plan fingerprint: `{stress_plan.plan_fingerprint}`",
        f"- stress view fingerprint: `{stress_view.view_fingerprint}`",
        "",
        "## Reasonable Inference",
        "",
        "- A future controlled consumer may choose to read this derived view without changing the original fact source.",
        "",
        "## Prohibited Inference",
        "",
        "- DG5 does not implement permanent storage compression.",
        "- DG5 does not improve recall or runtime behavior.",
        "- DG5 does not establish global cost reduction.",
        "- DG5 does not prove large-scale workload benefit.",
        "- DG5 does not create parent/child hierarchy, fact ranking, identity merge, or cross-evidence semantic merge.",
        "",
        "## Limits",
        "",
        "- This report records estimated view-entry reduction only.",
        "- Aggregate mass remains geometric accounting for a view entry; it is not factual importance, truth, trust, rank, or recall priority.",
        "- The validation does not access Evidence, Admission, FieldSnapshot, Recall, runtime, OpenClaw, network, database, cache, LLM/NLP, or embeddings.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
