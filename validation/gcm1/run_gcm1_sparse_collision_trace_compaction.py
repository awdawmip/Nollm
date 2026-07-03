from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gcm1.fixture import build_collision_witness, build_trace_scenarios, evaluate_scenario, experiment_window_payload, scenario_payload, witness_payload


def build_report() -> str:
    window = experiment_window_payload()
    witness = build_collision_witness()
    witness_data = witness_payload(witness)
    scenarios = build_trace_scenarios()
    lines = [
        "# GCM1 Sparse-Collision / Trace-Compaction Non-Conflation Baseline Report",
        "",
        f"- baseline commit: `{window['baseline_commit']}`",
        "- validation kind: pure synthetic compaction validation",
        "- runner output: this Markdown report only",
        "- boundary: collision is shared finite DG1/GSC1 support only; it is not compaction eligibility, not evidence deletion, not DreamShard merge, and not recall authority.",
        "",
        "## Experiment Window",
        "",
        f"- source phase: `{window['source_phase']}`",
        f"- parameter id: `{window['parameter_id']}`",
        f"- pattern id: `{window['pattern_id']}`",
        f"- scenario ids: `{window['scenario_ids']}`",
        "",
        "## Collision Witness",
        "",
        f"- pattern id: `{witness_data['pattern_id']}`",
        f"- layer gap: `{witness_data['layer_gap']}`",
        f"- base layer: `{witness_data['base_layer']}`",
        f"- phase: `{witness_data['phase_label']}`",
        f"- phase policy: `{witness_data['phase_policy']}`",
        f"- target ref: `{witness_data['target_ref']}`",
        f"- supporting marker ids: `{witness_data['supporting_marker_ids']}`",
        f"- reconstructed hex cell ref: `{witness_data['hex_cell_ref']}`",
        f"- reconstructed chart fingerprint id: `{witness_data['chart_fingerprint_chart_id']}`",
        "",
        "## Scenario Results",
        "",
        "| scenario | input traces | compactions | member ids | uncompacted trace ids |",
        "|---|---:|---:|---|---|",
    ]
    for scenario in scenarios:
        payload = scenario_payload(scenario)
        compactions = payload["actual_compactions"]
        member_ids = tuple(trace_id for compaction in compactions for trace_id in compaction["member_trace_ids"])
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario.scenario_id,
                    str(len(scenario.input_traces)),
                    str(len(compactions)),
                    str(member_ids),
                    str(payload["actual_uncompacted_trace_ids"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Expansion Manifest Check",
            "",
        ]
    )
    duplicate = next(scenario for scenario in scenarios if scenario.scenario_id == "exact_duplicate_transport_view")
    compaction = evaluate_scenario(duplicate)[0]
    lines.extend(
        [
            f"- compaction id: `{compaction.compaction_id}`",
            f"- member trace ids: `{compaction.member_trace_ids}`",
            f"- expansion manifest: `{compaction.expansion_manifest}`",
            f"- aggregate mass: `{compaction.aggregate_mass:.17g}`",
            "- expansion returns both original `GrowthTrace` values from the supplied in-memory trace index.",
            "",
            "## Verified Facts",
            "",
            "- The witness is selected from sealed GSC1 `build_collision_summaries()` as the canonical first `local_fork` summary with `collision_target_count > 0`.",
            "- The target `HexCell` is reconstructed from the same GSC1 schedule, base layer, phase, phase policy, and target `CellRef`.",
            "- Shared support cell and support key do not compact traces across distinct `origin_shard_id` values.",
            "- Distinct proposal ids and distinct derivation proxies do not compact.",
            "- Exact duplicate transport views compact only when every canonical evidence-bound field matches except `trace_id`.",
            "- Compaction manifest and member ids are canonical and identical.",
            "- `expand_compaction(...)` returns all original trace identities without deleting, replacing, or rewriting inputs.",
            "- Reversed input order produces the same canonical compaction payload.",
            "",
            "## Reasonable Interpretation",
            "",
            "- DG2 trace compaction preserves evidence boundaries in this finite GSC1-supported collision witness.",
            "- Shared geometric support is insufficient by itself to authorize trace compaction.",
            "- Compaction is a reversible derived view over in-memory trace values, not an evidence mutation.",
            "",
            "## Unverified Items",
            "",
            "- Synthetic trace is not a DreamShard, AdmissionRecord, GrowthProposal, PlacementPlan, FieldSnapshot, RecallUniverse, or RecallDigest.",
            "- The distinct revision proxy scenario is not a RevisionThread, current resolver, retired resolver, or real revision data model.",
            "- No cover crystallization, gravity ranking, profile selection, recall traversal, runtime, OpenClaw, network, database, cache, LLM/NLP, or semantic search is exercised.",
            "",
            "## Conclusion Limits",
            "",
            "- GCM1 is limited to one canonical finite GSC1 `local_fork` collision witness.",
            "- GCM1 does not modify production compaction, geometry, field, evidence, admission, assembly, recall, adapter, or runtime code.",
            "- A support collision is not a merge signal, owner signal, parent-child signal, primary-source signal, current/retired signal, truth signal, trust signal, or compression recommendation.",
        ]
    )
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
