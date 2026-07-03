from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gat1.fixture import (
    BASELINE_COMMIT,
    CHART_LAYER_TRIPLES,
    WITNESS_AXIALS,
    build_cycle_checks,
    experiment_window_payload,
    max_cycle_residual,
    max_pair_residual,
    max_rotation_error,
    max_scale_error,
    negative_control_payload,
    render_report_metric,
)


def build_report() -> str:
    window = experiment_window_payload()
    checks = build_cycle_checks()
    negatives = negative_control_payload()
    lines = [
        "# GAT1 Finite Chart-Atlas Transition / Groupoid Baseline Report",
        "",
        f"- baseline commit: `{BASELINE_COMMIT}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "- synthetic correspondence boundary: same axial label is a coordinate-test fixture, not an overlap witness, not chart merge evidence, and not recall traversal authorization.",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- layer range: `{window['layer_range'][0]}..{window['layer_range'][1]}`",
        f"- chart layer triples: `{CHART_LAYER_TRIPLES}`",
        f"- witness axial labels: `{tuple((axial.q, axial.r) for axial in WITNESS_AXIALS)}`",
        f"- phase samples: `{window['phase_samples']}`",
        f"- layer phase policies: `{window['layer_phase_policies']}`",
        f"- cycle count: `{window['cycle_count']}`",
        f"- reference scale rule: `{window['reference_scale_rule']}`",
        f"- tolerance: `{window['tolerance']}`",
        "- report metric rendering: values with absolute value at or below `GAT1_REPORTING_NOISE_FLOOR = 1.000000e-12` are shown as `\u22641.000000e-12`; raw validation still uses sealed DG1 tolerance and real float64 values.",
        "",
        "## Pair And Cycle Summary",
        "",
        "| triple | phase | policy | cycle state | witness geometry | cycle max residual | cycle rms residual | linear identity error | translation identity error | max pair residual | max scale error | max rotation error |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for check in checks:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(check.triple),
                    check.phase_label,
                    check.phase_policy,
                    check.cycle.state_recommendation,
                    check.cycle.witness_geometry_status,
                    render_report_metric(check.cycle.max_residual),
                    render_report_metric(check.cycle.rms_residual),
                    render_report_metric(check.cycle.linear_identity_error),
                    render_report_metric(check.cycle.translation_identity_error),
                    render_report_metric(max(pair.validation.residual.max_residual for pair in check.pair_checks)),
                    render_report_metric(max(pair.scale_error for pair in check.pair_checks)),
                    render_report_metric(max(pair.rotation_error for pair in check.pair_checks)),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Aggregate Bounds",
            "",
            f"- cycles checked: `{len(checks)}`",
            f"- directed pair validations checked: `{len(checks) * 3}`",
            f"- max pair residual: `{render_report_metric(max_pair_residual(checks))}`",
            f"- max cycle residual: `{render_report_metric(max_cycle_residual(checks))}`",
            f"- max scale-ratio error: `{render_report_metric(max_scale_error(checks))}`",
            f"- max rotation-delta error: `{render_report_metric(max_rotation_error(checks))}`",
            "",
            "## Negative Controls",
            "",
            f"- shifted target witness validation state: `{negatives['shifted_target']}`",
            f"- duplicate witness validation state: `{negatives['duplicate_witness']}`",
            f"- tampered cycle residual state: `{negatives['tampered_cycle']}`",
            f"- orientation reversing validation state: `{negatives['orientation_reversing']}`",
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only sampled parameter.",
            "- All charts are constructed from sealed DG1 `ScaleRotationSchedule.chart_for_layer(...)` with sealed default phase samples and layer phase policies.",
            "- Each synthetic pair uses four fixed same-label axial witnesses; fit uses the first two witness pairs and validation uses all four.",
            "- All 32 finite cycles are computed from real pair fits, inverse checks, pair composition checks, and DG1 `cycle_residual(...)`.",
            "- Scale ratio and rotation delta consistency are finite checks against the source and target chart geometry.",
            "- Report metric rendering uses a fixed presentation noise floor only for Markdown text; it is not an acceptance threshold.",
            "- Negative controls do not verify.",
            "",
            "## Reasonable Interpretation",
            "",
            "- Under finite synthetic coordinate correspondence, DG1 transform primitives agree with the sealed schedule chart geometry.",
            "- The result is useful as a precursor signal for future real overlap-witness atlas work.",
            "- The result is not itself atlas evidence and does not authorize runtime traversal.",
            "",
            "## Unverified Items",
            "",
            "- No real overlap witness is created or verified.",
            "- No ChartTransformRecord, TransformCycleCheck, Atlas registry, global chart connectivity, atlas merge, or cross-chart recall is created.",
            "- No DreamShard physical or semantic identity is inferred.",
            "- No exact algebraic proof is established; results use DG1 float64 tolerance.",
            "",
            "## Conclusion Limits",
            "",
            "- Layer window is limited to `0..16`.",
            "- Chart triples are fixed to the four listed triples.",
            "- Correspondence stencil is fixed to four axial labels and remains synthetic.",
            "- Same axial label does not prove the same physical location or semantic object.",
            "- GAT1 does not change profile, beta, theta, phase policy, translation policy, memory, admission, assembly, recall, adapter, or runtime behavior.",
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
