from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gvr1.fixture import (
    BASELINE_COMMIT,
    LAYER_GAPS,
    TARGET_RADIUS,
    THRESHOLD,
    TRANSLATION_RADIUS,
    build_metric_rows,
    experiment_window_payload,
)


def build_report() -> str:
    window = experiment_window_payload()
    rows = build_metric_rows()
    lines = [
        "# GVR1 Finite Translation-Variation / Coverage-Robustness Baseline Report",
        "",
        f"- baseline commit: `{BASELINE_COMMIT}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "",
        "## Experiment Window",
        "",
        f"- parameter id: `{window['parameter_id']}`",
        f"- layer range: `{window['layer_range'][0]}..{window['layer_range'][1]}`",
        f"- layer gaps: `{LAYER_GAPS}`",
        f"- base layer sampling rule: `{window['base_layer_rule']}`",
        f"- base layer counts by gap: `{window['base_layer_counts']}`",
        f"- translation radius: `{TRANSLATION_RADIUS}`",
        f"- translation offsets: `{window['translation_offsets']}`",
        f"- offset count: `{window['offset_count']}`",
        f"- target neighborhood radius: `{TARGET_RADIUS}`",
        f"- phase samples: `{window['phase_samples']}`",
        f"- layer phase policies: `{window['layer_phase_policies']}`",
        f"- threshold: `{THRESHOLD}`",
        f"- tolerance: `{window['tolerance']}`",
        "",
        "## Coverage / Translation Variation Summary",
        "",
        "`n` is the number of real DG1 coverage distributions for the row: all legal base layers times all seven source offsets. Therefore `n = 7 * (17 - gap)`. Phase recurrence is a chart/phase schedule diagnostic; it is not multiplied by source-offset count.",
        "",
        "| parameter | gap | phase | policy | base layers | offsets | n | branch mean | branch p95 | branch max | effective mean | effective p95 | residual mean | residual p95 | residual max | max mass | overlap entropy | nesting | phase recurrence | rotation mod60 | branch span | max-mass span | residual span |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.parameter_id,
                    str(row.gap),
                    row.phase_label,
                    row.phase_policy,
                    str(row.base_layer_count),
                    str(row.offset_count),
                    str(row.distribution_count),
                    _num(row.branching_mean),
                    _num(row.branching_p95),
                    str(row.branching_max),
                    _num(row.effective_count_mean),
                    _num(row.effective_count_p95),
                    _num(row.residual_mean),
                    _num(row.residual_p95),
                    _num(row.residual_max),
                    _num(row.max_mass),
                    _num(row.overlap_entropy),
                    _num(row.nesting_tendency),
                    _num(row.phase_recurrence_score),
                    "true" if row.rotation_recurrence_mod60 else "false",
                    _num(row.envelope.branching_mean_span),
                    _num(row.envelope.max_mass_mean_span),
                    _num(row.envelope.residual_mean_span),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Translation Variation Envelope",
            "",
            "Per-offset means aggregate sealed DG1 `distribution_metrics(...)` over every legal base layer for one source offset. The span columns are finite descriptive envelopes, not geometry scores and not profile selectors.",
            "",
            "| gap | phase | policy | branching min | branching max | branching span | max-mass min | max-mass max | max-mass span | residual min | residual max | residual span |",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        envelope = row.envelope
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.gap),
                    row.phase_label,
                    row.phase_policy,
                    _num(envelope.branching_mean_min),
                    _num(envelope.branching_mean_max),
                    _num(envelope.branching_mean_span),
                    _num(envelope.max_mass_mean_min),
                    _num(envelope.max_mass_mean_max),
                    _num(envelope.max_mass_mean_span),
                    _num(envelope.residual_mean_min),
                    _num(envelope.residual_mean_max),
                    _num(envelope.residual_mean_span),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Verified Facts",
            "",
            "- Parameter B is the only parameter sampled.",
            "- Every row samples every legal base layer `l` where `l + gap <= 16` and every source offset in `disk(AxialCoord(0, 0), 1)`.",
            "- Coverage distributions are built by sealed DG1 `ScaleRotationSchedule`, `chart_for_layer`, `make_hex_cell`, `nearest_axial`, `disk`, and `compute_distribution`.",
            "- Row sample counts are `112`, `105`, `91`, `63`, and `7` for gaps `1`, `2`, `4`, `8`, and `16` respectively.",
            "- Center-offset coverage is independently reconstructable with the same DG1 public API calls as the GPR1-C1 B baseline input.",
            "- Variation envelope values are ordinary min, max, and span summaries over sealed DG1 `distribution_metrics(...)` outputs.",
            "",
            "## Reasonable Interpretation",
            "",
            "- The finite seven-offset stencil can reveal local source-translation sensitivity inside the fixed GVR1 window.",
            "- A zero span means no variation was observed in this finite stencil for that metric; it is not a full-plane translation-invariance proof.",
            "- A positive span means finite-window variation was observed; it is not a geometry defect and not evidence that B is inferior.",
            "- Phase recurrence is reported once per base-layer phase tuple and is not multiplied by source-offset count.",
            "",
            "## Unverified Items",
            "",
            "- No all-plane or all-atlas theorem is established.",
            "- No exact algebraic-number proof is established; metrics use DG1 float64 tolerance.",
            "- No production profile is selected or changed.",
            "- No beta, theta, translation policy, phase policy, or `FIELD_PROFILE_ID` is changed.",
            "",
            "## Conclusion Limits",
            "",
            "- Layer window is limited to `0..16`.",
            "- Translation stencil is only axial disk radius `1`, exactly seven source offsets.",
            "- Target radius is `4`; coverage outside the supplied finite target partition remains residual mass.",
            "- GVR1 does not touch memory, capture, admission, assembly, recall, OpenClaw, runtime, network, database, cache, LLM, NLP, embedding, or semantic search behavior.",
            "- This report is derived validation output; it is not memory, recall, or a source of truth.",
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


def _num(value: float) -> str:
    return format(float(value), ".6f")


if __name__ == "__main__":
    raise SystemExit(main())
