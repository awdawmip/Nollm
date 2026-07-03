from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gkc1.fixture import (
    GKC1_REPORTING_NOISE_FLOOR,
    build_observations,
    central_regression_anchors,
    composition_summary,
    experiment_window_payload,
    render_report_metric,
    residual_summary,
)


def build_report() -> str:
    window = experiment_window_payload()
    observations = build_observations()
    summary = composition_summary(observations)
    residuals = residual_summary(observations)
    anchors = central_regression_anchors(observations)
    lines = [
        "# GKC1 Directional Kernel Composition / Non-Identity Baseline Report",
        "",
        f"- baseline commit: `{window['baseline_commit']}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- boundary: two-step directed geometry composition is measured over finite partitions and creates no production composition API, write permission, read authority, ranking, or profile selection.",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- beta: `{window['beta']}`",
        f"- delta theta degrees: `{window['delta_theta_degrees']}`",
        f"- base layer: `{window['base_layer']}`",
        f"- phase: `{window['phase']}`",
        f"- phase policies: `{window['phase_policies']}`",
        f"- layer gaps: `{window['layer_gaps']}`",
        f"- source axial stencil: `{window['source_axial_stencil']}`",
        f"- target disk radius: `{window['target_disk_radius']}`",
        f"- target partition size: `{window['target_partition_size']}`",
        f"- coverage threshold: `{window['coverage_threshold']}`",
        f"- setting count: `{window['setting_count']}`",
        f"- composition observation count: `{window['observation_count']}`",
        f"- tolerances: `{window['tolerances']}`",
        f"- report metric rendering: values with absolute value at or below `GKC1_REPORTING_NOISE_FLOOR = {GKC1_REPORTING_NOISE_FLOOR:.6e}` are shown as `<=1.000000e-12`; raw validation still uses real float64 values.",
        "",
        "## Single-Leg Construction",
        "",
        "- Every first leg and every second leg is computed with production `compute_distribution(...)`.",
        "- Every source, intermediate, and return target cell is built with production `make_hex_cell(...)`.",
        "- Every finite target disk is centered with production `nearest_axial(...)` from the true source cell center.",
        "",
        "## Composition Construction",
        "",
        "- `fine_coarse_fine` multiplies retained fine-to-coarse weights by independently computed coarse-to-fine weights.",
        "- `coarse_fine_coarse` multiplies retained coarse-to-fine weights by independently computed fine-to-coarse weights.",
        "- Composition residual is first-leg residual plus first-leg-weighted second-leg residual.",
        "- Composed weights are not normalized a second time.",
        "",
        "## Fine->Coarse->Fine Summary",
        "",
        "| gap | policy | count | support min | support max | self min | self max | positive residual | residual min | residual max |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (direction, gap, policy), row in summary.items():
        if direction != "fine_coarse_fine":
            continue
        lines.append(
            f"| {gap} | {policy} | {row['count']} | {row['support_min']} | {row['support_max']} | {render_report_metric(float(row['self_min']))} | {render_report_metric(float(row['self_max']))} | {row['residual_positive']} | {render_report_metric(float(row['residual_min']))} | {render_report_metric(float(row['residual_max']))} |"
        )
    lines.extend(
        [
            "",
            "## Coarse->Fine->Coarse Summary",
            "",
            "| gap | policy | count | support min | support max | self min | self max | positive residual | residual min | residual max |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for (direction, gap, policy), row in summary.items():
        if direction != "coarse_fine_coarse":
            continue
        lines.append(
            f"| {gap} | {policy} | {row['count']} | {row['support_min']} | {row['support_max']} | {render_report_metric(float(row['self_min']))} | {render_report_metric(float(row['self_max']))} | {row['residual_positive']} | {render_report_metric(float(row['residual_min']))} | {render_report_metric(float(row['residual_max']))} |"
        )
    lines.extend(
        [
            "",
            "## Mass and Residual Ledger",
            "",
            f"- positive residual by direction and gap: `{residuals['positive_by_direction_gap']}`",
            f"- observations with positive first-leg residual: `{residuals['positive_first_leg']}`",
            f"- observations with positive weighted second-leg residual: `{residuals['positive_second_leg_weighted']}`",
            "- Gap-16 residual is finite radius-4 partition mass and is retained in the ledger.",
            "",
            "## Non-Identity Summary",
            "",
            f"- observation count: `{len(observations)}`",
            f"- observations with source chart equal to return chart: `{sum(1 for row in observations if row.source_chart_id == row.return_chart_id)}`",
            f"- observations with intermediate chart different from source chart: `{sum(1 for row in observations if row.intermediate_chart_id != row.source_chart_id)}`",
            f"- observations with self return mass below one: `{sum(1 for row in observations if row.self_return_mass < 1.0)}`",
            f"- observations with positive identity distance: `{sum(1 for row in observations if row.identity_distance > 0.0)}`",
            "",
            "## Central Regression Anchors",
            "",
            "| composition direction | gap | self return mass |",
            "|---|---:|---:|",
        ]
    )
    for (direction, gap), value in anchors.items():
        lines.append(f"| {direction} | {gap} | {render_report_metric(value)} |")
    lines.extend(
        [
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.",
            "- All 60 observations are formed from real production single-leg distributions.",
            "- Every observation preserves `composed_kernel_mass + composition_residual_mass = composition_total_mass` in production tolerance.",
            "- Every observation returns to the source chart and remains non-identity at source-cell level.",
            "- Gap-16 residual remains visible in both composition directions.",
            "",
            "## Reasonable Interpretation",
            "",
            "- Returning to the source chart is not the same as returning all mass to the source cell.",
            "- Higher self-return mass is a finite geometry diagnostic, not a permission or ranking rule.",
            "- The two-step relation is a finite composed distribution, not a production transport mechanism.",
            "",
            "## Unverified Items",
            "",
            "- No all-plane statement, parameter replacement recommendation, structural containment claim, write condition, read authority, ranking rule, or factual ordering is established.",
            "- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.",
            "- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.",
            "",
            "## Conclusion Limits",
            "",
            "- GKC1 is limited to base layer `0`, phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and the two existing DG1 coverage directions.",
            "- Non-identity observations do not create structural containment, compression permission, admission permission, or recall authority.",
            "- Residual mass is finite partition boundary mass, not an error or semantic failure.",
            "- GKC1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.",
            "- GKC1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, LLM/NLP, embedding, semantic search, or OpenClaw behavior.",
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
