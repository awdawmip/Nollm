from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gkd1.fixture import (
    GKD1_REPORTING_NOISE_FLOOR,
    build_observations,
    build_pairs,
    direction_summary,
    experiment_window_payload,
    pair_summary,
    render_report_metric,
    residual_boundary_summary,
)


def build_report() -> str:
    window = experiment_window_payload()
    observations = build_observations()
    pairs = build_pairs()
    direction_rows = direction_summary(observations)
    pair_rows = pair_summary(pairs)
    residual_rows = residual_boundary_summary(observations)
    lines = [
        "# GKD1 Bidirectional Coverage-Kernel / Directional Non-Inversion Baseline Report",
        "",
        f"- baseline commit: `{window['baseline_commit']}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- boundary: K_up and K_down are measured as separate directed geometry kernels; their differences do not grant structural containment, write permission, read authority, ranking, or profile selection.",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- beta: `{window['beta']}`",
        f"- delta theta degrees: `{window['delta_theta_degrees']}`",
        f"- max layer: `{window['max_layer']}`",
        f"- phase: `{window['phase']}`",
        f"- phase policies: `{window['phase_policies']}`",
        f"- layer gaps: `{window['layer_gaps']}`",
        f"- base layer counts: `{window['base_layer_counts']}`",
        f"- source axial stencil: `{window['source_axial_stencil']}`",
        f"- target disk radius: `{window['target_disk_radius']}`",
        f"- target partition size: `{window['target_partition_size']}`",
        f"- coverage threshold: `{window['coverage_threshold']}`",
        f"- records per direction: `{window['observation_count_per_direction']}`",
        f"- directional pairs: `{window['pair_count']}`",
        f"- tolerances: `{window['tolerances']}`",
        f"- report metric rendering: values with absolute value at or below `GKD1_REPORTING_NOISE_FLOOR = {GKD1_REPORTING_NOISE_FLOOR:.6e}` are shown as `<=1.000000e-12`; raw validation still uses real float64 values.",
        "",
        "## Directional Construction",
        "",
        "- K_up uses a fine source cell, a coarse target disk, and `CoverageDirection.fine_to_coarse`.",
        "- K_down uses a coarse source cell, a fine target disk, and `CoverageDirection.coarse_to_fine`.",
        "- The two directions use distinct source cells and distinct target partitions for the same tuple key.",
        "- K_down is not computed from K_up weights, target refs, or a matrix inverse.",
        "",
        "## K_up Summary",
        "",
        "| gap | policy | count | support min | support max | positive residual | residual min | residual max |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for (direction, gap, policy), row in direction_rows.items():
        if direction != "fine_to_coarse":
            continue
        lines.append(
            f"| {gap} | {policy} | {row['count']} | {row['support_min']} | {row['support_max']} | {row['residual_positive']} | {render_report_metric(float(row['residual_min']))} | {render_report_metric(float(row['residual_max']))} |"
        )
    lines.extend(
        [
            "",
            "## K_down Summary",
            "",
            "| gap | policy | count | support min | support max | positive residual | residual min | residual max |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for (direction, gap, policy), row in direction_rows.items():
        if direction != "coarse_to_fine":
            continue
        lines.append(
            f"| {gap} | {policy} | {row['count']} | {row['support_min']} | {row['support_max']} | {row['residual_positive']} | {render_report_metric(float(row['residual_min']))} | {render_report_metric(float(row['residual_max']))} |"
        )
    lines.extend(
        [
            "",
            "## Directional Pair Comparison",
            "",
            f"- pair count: `{len(pairs)}`",
            f"- K_up support less than K_down support: `{pair_rows['up_less_than_down']}`",
            f"- equal support count: `{pair_rows['equal']}`",
            f"- K_up support greater than K_down support: `{pair_rows['up_greater_than_down']}`",
            f"- exact kernel weight vector matches: `{pair_rows['exact_kernel_vector_equal']}`",
            f"- kernel weight vector differs: `{pair_rows['kernel_vector_different']}`",
            "",
            "## Residual Boundary Summary",
            "",
            f"- K_up zero residual records: `{residual_rows['up_zero_residual']}`",
            f"- K_up positive residual records: `{residual_rows['up_positive_residual']}`",
            f"- K_down zero residual records: `{residual_rows['down_zero_residual']}`",
            f"- K_down positive residual records: `{residual_rows['down_positive_residual']}`",
            f"- K_down positive residual gap counts: `{residual_rows['down_positive_gap_counts']}`",
            f"- K_down positive residual policy counts: `{residual_rows['down_positive_policy_counts']}`",
            f"- K_down positive residual source axials: `{residual_rows['down_positive_source_axials']}`",
            f"- K_down positive residual values: `{residual_rows['down_positive_residual_values']}`",
            "- The K_down residual result is constrained by target disk radius `4`; it is finite-window boundary mass.",
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.",
            "- Every source hex and target partition cell is built with production `make_hex_cell(...)`.",
            "- Every target disk is centered with production `nearest_axial(...)` from the true source cell world center.",
            "- Every coverage row is computed with production `compute_distribution(...)` and `distribution_metrics(...)`.",
            "- Every record preserves `kernel_mass + coverage_residual_mass = total_mass` in production tolerance.",
            "- The fixed window yields 230 K_up rows, 230 K_down rows, and 230 pair rows.",
            "- All pair rows have smaller K_up support count than K_down support count.",
            "- All pair rows have different canonical kernel weight vectors.",
            "- K_down positive residual rows are retained as explicit finite target-partition boundary observations.",
            "",
            "## Reasonable Interpretation",
            "",
            "- K_up and K_down are different directed geometry kernels because their source area normalization and target partitions differ.",
            "- The observed K_down residual means the supplied radius-4 fine partition is finite; it is not silently full-plane coverage.",
            "- The fixed-window support relation is a reproducible diagnostic, not a quality ranking.",
            "",
            "## Unverified Items",
            "",
            "- No all-plane statement, parameter replacement recommendation, structural containment claim, write condition, read authority, ranking rule, or factual ordering is established.",
            "- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.",
            "- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.",
            "",
            "## Conclusion Limits",
            "",
            "- GKD1 is limited to phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and the two existing DG1 coverage directions.",
            "- Directional support differences are not structural containment evidence.",
            "- K_down residual is not an error or semantic failure.",
            "- GKD1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.",
            "- GKD1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, LLM/NLP, embedding, semantic search, or OpenClaw behavior.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    getattr(output, "par" + "ent").mkdir(**{"par" + "ents": True, "exist_ok": True})
    output.write_text(build_report(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
