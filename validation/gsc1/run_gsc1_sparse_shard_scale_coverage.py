from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gsc1.fixture import (
    BASELINE_COMMIT,
    GSC1_REPORTING_NOISE_FLOOR,
    LAYER_GAPS,
    OCCUPANCY_PATTERNS,
    SOURCE_DISTRIBUTION_CALL_COUNT,
    TARGET_RADIUS,
    THRESHOLD,
    build_collision_summaries,
    build_observations,
    experiment_window_payload,
    max_residual_mass,
    max_support_per_target,
    render_report_metric,
    total_collision_targets,
)


def build_report() -> str:
    window = experiment_window_payload()
    observations = build_observations()
    summaries = build_collision_summaries()
    lines = [
        "# GSC1 Finite Sparse-Shard / Scale-Coverage Baseline Report",
        "",
        f"- baseline commit: `{BASELINE_COMMIT}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- synthetic shard boundary: each source marker is a finite occupancy label for coverage diagnostics; it is not a persisted DreamShard, not memory content, not a merge key, and not recall input.",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- layer gaps: `{LAYER_GAPS}`",
        f"- base layers: `{window['base_layers']}`",
        f"- phase samples: `{window['phases']}`",
        f"- layer phase policies: `{window['layer_phase_policies']}`",
        f"- target radius: `{TARGET_RADIUS}`",
        f"- threshold: `{THRESHOLD:.6e}`",
        f"- source distribution call count: `{SOURCE_DISTRIBUTION_CALL_COUNT}`",
        f"- patterns: `{window['patterns']}`",
        f"- tolerance: `{window['tolerance']}`",
        f"- report metric rendering: values with absolute value at or below `GSC1_REPORTING_NOISE_FLOOR = {GSC1_REPORTING_NOISE_FLOOR:.6e}` are shown as `\u2264{GSC1_REPORTING_NOISE_FLOOR:.6e}`; raw validation still uses sealed DG1 tolerance and real float64 values.",
        "",
        "## Observation Summary",
        "",
        "| pattern | source count | observations | min kernels | max kernels | max residual mass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pattern_id, markers in OCCUPANCY_PATTERNS:
        selected = tuple(observation for observation in observations if observation.pattern_id == pattern_id)
        kernel_counts = tuple(len(observation.target_refs) for observation in selected)
        lines.append(
            "| "
            + " | ".join(
                [
                    pattern_id,
                    str(len(markers)),
                    str(len(selected)),
                    str(min(kernel_counts)),
                    str(max(kernel_counts)),
                    render_report_metric(max(observation.residual_mass for observation in selected)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Support Collision Summary",
            "",
            "| pattern | gap | base layer | phase | policy | sources | incidences | unique targets | collision targets | max marker support | max residual mass |",
            "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for summary in summaries:
        lines.append(
            "| "
            + " | ".join(
                [
                    summary.pattern_id,
                    str(summary.layer_gap),
                    str(summary.base_layer),
                    summary.phase_label,
                    summary.phase_policy,
                    str(summary.source_count),
                    str(summary.incidence_count),
                    str(summary.unique_target_count),
                    str(summary.collision_target_count),
                    str(summary.max_marker_support_per_target),
                    render_report_metric(summary.max_residual_mass),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Bounds",
            "",
            f"- observations checked: `{len(observations)}`",
            f"- summaries checked: `{len(summaries)}`",
            f"- max residual mass: `{render_report_metric(max_residual_mass(observations))}`",
            f"- max marker support per target: `{max_support_per_target(summaries)}`",
            f"- total diagnostic collision targets: `{total_collision_targets(summaries)}`",
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter.",
            "- The fixed window is limited to layer gaps `(1, 4, 8)`, base layers `(0, 8)`, phases `(0.0, 0.0)` and `(0.5, 0.0)`, and sealed DG1 layer phase policies.",
            "- All 144 source distributions are computed through sealed DG1 `compute_distribution(...)` over finite target disks.",
            "- Source geometry is independent from occupancy grouping: identical source axial labels produce identical per-source kernels across singleton and local-fork patterns.",
            "- Support collision summaries preserve marker identity as diagnostic incidence sets and do not collapse sources.",
            "- Reordered host-supplied marker input produces the same canonical observations and summaries.",
            "- Report metric rendering uses a fixed presentation noise floor only for Markdown text; it is not an acceptance threshold.",
            "",
            "## Reasonable Interpretation",
            "",
            "- Finite sparse occupancy can be replayed through DG1 scale coverage without creating a global field or runtime state.",
            "- Diagnostic collision targets identify shared finite target support, not shard equivalence.",
            "- The result is useful as a precursor validation for future sparse scale-coverage analysis.",
            "",
            "## Unverified Items",
            "",
            "- No real DreamShard is created, stored, reopened, or admitted.",
            "- No GrowthProposal, PlacementPlan, Geometry profile selection, FieldSnapshot, RecallUniverse, Query, or recall execution is created.",
            "- No parent, child, ownership, primary-source, semantic, or identity relationship is inferred from shared target support.",
            "- No exact algebraic proof is established; results use DG1 float64 tolerance.",
            "",
            "## Conclusion Limits",
            "",
            "- GSC1 is a pure validation asset and changes no production implementation.",
            "- Target windows are finite disks with radius `4`; no global admission discovery or global scale field is scanned.",
            "- Synthetic source markers are finite occupancy labels only, not persisted shards or memory records.",
            "- GSC1 does not authorize runtime, OpenClaw, CLI, network, database, cache, Field, Recall, or adapter behavior.",
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
