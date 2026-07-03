from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gra1.fixture import build_observations, classification_totals, experiment_window_payload, recurrence_candidates, summary_counts


def build_report() -> str:
    window = experiment_window_payload()
    observations = build_observations()
    totals = classification_totals(observations)
    lines = [
        "# GRA1 Rotation-Scale Resonance / Phase-Drift Separation Baseline Report",
        "",
        f"- baseline commit: `{window['baseline_commit']}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- boundary: scale/rotation commensurability is not exact center-sublattice alignment, not cover authority, not parent/child structure, not compression permission, and not recall authority.",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- beta: `{window['beta']}`",
        f"- delta theta degrees: `{window['delta_theta_degrees']}`",
        f"- max layer: `{window['max_layer']}`",
        f"- layer gaps: `{window['layer_gaps']}`",
        f"- base layer counts: `{window['base_layer_counts']}`",
        f"- phase samples: `{window['phase_samples']}`",
        f"- phase policies: `{window['phase_policies']}`",
        f"- axial center stencil: `{window['axial_center_stencil']}`",
        f"- observation count: `{len(observations)}`",
        f"- tolerances: `{window['tolerances']}`",
        "",
        "## Recurrence Candidates",
        "",
        "| gap | side ratio | rotation mod hex degrees | nearest integer scale | scale integer error |",
        "|---:|---:|---:|---:|---:|",
    ]
    for gap in (1, 2, 4, 8, 16):
        first = next(observation for observation in observations if observation.layer_gap == gap)
        lines.append(
            f"| {gap} | {first.side_ratio:.12g} | {first.rotation_mod_hex_degrees:.12g} | {first.nearest_integer_scale} | {first.scale_integer_error:.12g} |"
        )
    lines.extend(
        [
            "",
            "## Observation Counts",
            "",
            f"- total observations: `{len(observations)}`",
            f"- exact center-sublattice: `{totals['exact_center_sublattice']}`",
            f"- commensurate phase-separated: `{totals['commensurate_phase_separated']}`",
            f"- noncommensurate: `{totals['noncommensurate']}`",
            "",
            "## Classification Summary",
            "",
            "| gap | phase policy | classification | count |",
            "|---:|---|---|---:|",
        ]
    )
    for (gap, policy, classification), count in summary_counts(observations).items():
        lines.append(f"| {gap} | {policy} | {classification} | {count} |")
    lines.extend(
        [
            "",
            "## Constant-Local Findings",
            "",
            "| gap | phase | count | classifications | max center residual |",
            "|---:|---|---:|---|---:|",
        ]
    )
    for gap in (8, 16):
        selected = tuple(observation for observation in observations if observation.layer_gap == gap and observation.phase_label == "(0,0)" and observation.phase_policy == "constant_local")
        classes = tuple(sorted({observation.classification for observation in selected}))
        max_residual = max(observation.max_center_map_residual for observation in selected)
        lines.append(f"| {gap} | (0,0) | {len(selected)} | {classes} | {max_residual:.12g} |")
    lines.extend(
        [
            "",
            "## Layer-Drift Findings",
            "",
            "| gap | phase | count | classifications | max center residual | relative phase samples |",
            "|---:|---|---:|---|---:|---|",
        ]
    )
    for gap in (8, 16):
        selected = tuple(observation for observation in observations if observation.layer_gap == gap and observation.phase_label == "(0,0)" and observation.phase_policy == "layer_drift_control")
        classes = tuple(sorted({observation.classification for observation in selected}))
        max_residual = max(observation.max_center_map_residual for observation in selected)
        relative_samples = tuple((f"{observation.relative_phase.q:.6g}", f"{observation.relative_phase.r:.6g}") for observation in selected[:3])
        lines.append(f"| {gap} | (0,0) | {len(selected)} | {classes} | {max_residual:.12g} | {relative_samples} |")
    candidate_counts = {classification: 0 for classification in ("exact_center_sublattice", "commensurate_phase_separated", "noncommensurate")}
    for observation in recurrence_candidates(observations):
        candidate_counts[observation.classification] += 1
    lines.extend(
        [
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter and is read from production `PARAMETER_MATRIX`.",
            "- Each gap samples every legal base layer in the finite `0..16` layer window.",
            "- All four production default phase samples and both production layer phase policies are included.",
            "- All 432 observations use production `ScaleRotationSchedule.chart_for_layer(...)`, `axial_to_world(...)`, `world_to_fractional_axial(...)`, `normalized_phase(...)`, and `relative_phase(...)`.",
            "- Gap 8 and gap 16 are the only sampled integer-scale, hex-orientation commensurate gaps under the fixed tolerances.",
            f"- Candidate recurrence classifications across gap 8 and 16: `{candidate_counts}`.",
            "- Each observation stores five center-map rows and can be reclassified from recorded numeric fields.",
            "",
            "## Reasonable Interpretation",
            "",
            "- Gap 8 and gap 16 expose finite scale/rotation recurrence candidates for engineering baseline B.",
            "- Exact center-sublattice alignment, when present, is a finite chart-center mapping result.",
            "- Phase drift can separate commensurate scale/rotation from exact center-grid alignment in the sampled stencil.",
            "",
            "## Unverified Items",
            "",
            "- No polygon overlap, coverage kernel, trace, cover, gravity, compaction, admission, field snapshot, recall universe, or recall digest is computed.",
            "- Commensurate phase-separated is not a proof of global non-overlap or full-plane anti-resonance.",
            "- Exact center-sublattice alignment is not semantic hierarchy, memory hierarchy, parent/child relation, cover eligibility, compression permission, admission permission, or recall permission.",
            "",
            "## Conclusion Limits",
            "",
            "- GRA1 does not choose, replace, deprecate, or modify ParameterSet B.",
            "- GRA1 does not recommend a production profile replacement.",
            "- The result is limited to the finite layers, gaps, phases, policies, and five-point center stencil listed above.",
            "- GRA1 changes no production geometry, field, evidence, admission, assembly, recall, adapter, runtime, CLI, network, database, cache, LLM/NLP, embedding, semantic search, or OpenClaw behavior.",
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
