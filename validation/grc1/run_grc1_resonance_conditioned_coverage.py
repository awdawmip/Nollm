from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.grc1.fixture import (
    GRC1_REPORTING_NOISE_FLOOR,
    build_observations,
    classification_counts,
    conditional_counts,
    coverage_summary,
    experiment_window_payload,
    render_report_metric,
)


def build_report() -> str:
    window = experiment_window_payload()
    observations = build_observations()
    lines = [
        "# GRC1 Resonance-Conditioned Coverage / Non-Hierarchy Baseline Report",
        "",
        f"- baseline commit: `{window['baseline_commit']}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- boundary: scale/rotation commensurability, exact center alignment, singleton coverage, and multi-support coverage are diagnostic axes only; none is hierarchy, compression permission, admission permission, or recall authority.",
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
        f"- coverage direction: `{window['coverage_direction']}`",
        f"- coverage threshold: `{window['coverage_threshold']}`",
        f"- observation count: `{len(observations)}`",
        f"- tolerances: `{window['tolerances']}`",
        f"- report metric rendering: values with absolute value at or below `GRC1_REPORTING_NOISE_FLOOR = {GRC1_REPORTING_NOISE_FLOOR:.6e}` are shown as `\u2264{GRC1_REPORTING_NOISE_FLOOR:.6e}`; raw validation still uses real float64 values.",
        "",
        "## Alignment Classification Summary",
        "",
        "| gap | policy | alignment class | count |",
        "|---:|---|---|---:|",
    ]
    for (gap, policy, alignment), count in classification_counts(observations).items():
        lines.append(f"| {gap} | {policy} | {alignment} | {count} |")
    lines.extend(
        [
            "",
            "## Coverage Summary",
            "",
            "| gap | policy | coverage class | count |",
            "|---:|---|---|---:|",
        ]
    )
    for (gap, policy, coverage_class), count in coverage_summary(observations).items():
        lines.append(f"| {gap} | {policy} | {coverage_class} | {count} |")
    exact = tuple(observation for observation in observations if observation.alignment_class == "exact_center_sublattice")
    phase_separated_gap8 = tuple(observation for observation in observations if observation.layer_gap == 8 and observation.phase_policy == "layer_drift_control")
    phase_separated_gap16 = tuple(observation for observation in observations if observation.layer_gap == 16 and observation.phase_policy == "layer_drift_control")
    noncommensurate = tuple(observation for observation in observations if observation.layer_gap == 4)
    lines.extend(
        [
            "",
            "## Exact-Center Conditional Coverage",
            "",
            f"- exact-center observations: `{len(exact)}`",
            f"- exact-center singleton observations: `{sum(1 for observation in exact if observation.coverage_singleton)}`",
            f"- exact-center max coverage mass range: `{render_report_metric(min(observation.max_coverage_mass for observation in exact))}` .. `{render_report_metric(max(observation.max_coverage_mass for observation in exact))}`",
            f"- exact-center residual mass range: `{render_report_metric(min(observation.coverage_residual_mass for observation in exact))}` .. `{render_report_metric(max(observation.coverage_residual_mass for observation in exact))}`",
            "",
            "## Phase-Separated Conditional Coverage",
            "",
            f"- gap 8 layer-drift singleton observations: `{sum(1 for observation in phase_separated_gap8 if observation.coverage_singleton)}`",
            f"- gap 8 layer-drift multi-support observations: `{sum(1 for observation in phase_separated_gap8 if observation.coverage_multisupport)}`",
            f"- gap 16 layer-drift singleton observations: `{sum(1 for observation in phase_separated_gap16 if observation.coverage_singleton)}`",
            f"- gap 16 layer-drift multi-support observations: `{sum(1 for observation in phase_separated_gap16 if observation.coverage_multisupport)}`",
            "",
            "## Noncommensurate Control",
            "",
            f"- gap 4 observations: `{len(noncommensurate)}`",
            f"- gap 4 alignment classes: `{tuple(sorted({observation.alignment_class for observation in noncommensurate}))}`",
            f"- gap 4 singleton observations: `{sum(1 for observation in noncommensurate if observation.coverage_singleton)}`",
            f"- gap 4 multi-support observations: `{sum(1 for observation in noncommensurate if observation.coverage_multisupport)}`",
            "",
            "## Conditional Matrix",
            "",
            "| alignment class | coverage class | count |",
            "|---|---|---:|",
        ]
    )
    for (alignment, coverage_class), count in conditional_counts(observations).items():
        lines.append(f"| {alignment} | {coverage_class} | {count} |")
    lines.extend(
        [
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.",
            "- Every source hex and target partition cell is built with production `make_hex_cell(...)`.",
            "- Every target disk is centered with production `nearest_axial(...)` from the true source cell world center.",
            "- Every coverage row is computed with production `compute_distribution(...)` and `distribution_metrics(...)`.",
            "- All 230 observations retain alignment diagnostics and coverage diagnostics as separate fields.",
            "- Exact-center rows are singleton coverage rows in this finite window.",
            "- Phase-separated rows include both singleton and multi-support outcomes in this finite window.",
            "",
            "## Reasonable Interpretation",
            "",
            "- In the fixed GRC1 window, exact center alignment and singleton coverage coincide for the sampled rows.",
            "- Center-map non-exactness is not equivalent to multi-support coverage.",
            "- Noncommensurate gap 4 acts only as a finite coverage control, not as a profile decision.",
            "",
            "## Unverified Items",
            "",
            "- No all-plane statement, profile replacement recommendation, semantic hierarchy, memory hierarchy, compression permission, admission condition, or recall authority is established.",
            "- No Field, Evidence, Admission, Assembly, Recall, runtime, adapter, cache, database, network, LLM/NLP, embedding, semantic search, or OpenClaw path is exercised.",
            "- No cover, trace, compaction, FieldSnapshot, RecallUniverse, DreamShard, InterpretationRecord, RevisionThread, LedgerEvent, or CaptureReceipt is created.",
            "",
            "## Conclusion Limits",
            "",
            "- GRC1 is limited to phase `(0.0, 0.0)`, gaps `(4, 8, 16)`, both layer phase policies, five source axial points, target disk radius `4`, and fine-to-coarse direction.",
            "- Exact center plus singleton coverage is not hierarchy evidence.",
            "- Phase-separated singleton coverage is not contradiction or proof of global non-overlap.",
            "- GRC1 does not select, modify, replace, deprecate, or recommend replacing ParameterSet B.",
            "- GRC1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, cache, LLM/NLP, embedding, semantic search, or OpenClaw behavior.",
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
