from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from tests.fixtures.gpr1.fixture import (
    BASELINE_COMMIT,
    LAYER_GAPS,
    SOURCE_RADIUS,
    TARGET_RADIUS,
    THRESHOLD,
    baseline_b_formula_payload,
    build_metric_rows,
    experiment_window_payload,
    parameter_payload,
)


def build_report() -> str:
    window = experiment_window_payload()
    baseline = baseline_b_formula_payload()
    rows = build_metric_rows()
    lines = [
        "# GPR1 Geometry Profile / Parameter-Regime Baseline Report",
        "",
        f"- baseline commit: `{BASELINE_COMMIT}`",
        "- validation kind: pure synthetic geometry validation",
        "- runner output: this Markdown report only",
        "",
        "## Experiment Window",
        "",
        f"- layer range: `{window['layer_range'][0]}..{window['layer_range'][1]}`",
        f"- layer gaps: `{LAYER_GAPS}`",
        f"- source axial disk radius: `{SOURCE_RADIUS}`",
        f"- target neighborhood radius: `{TARGET_RADIUS}`",
        f"- phase samples: `{window['phase_samples']}`",
        f"- layer phase policies: `{window['layer_phase_policies']}`",
        f"- threshold: `{THRESHOLD}`",
        f"- tolerance: `{window['tolerance']}`",
        "",
        "## Parameter Matrix",
        "",
        "| ID | beta | delta_theta_degrees | role |",
        "|---|---:|---:|---|",
    ]
    for parameter in parameter_payload():
        lines.append(f"| {parameter['parameter_id']} | {parameter['beta']} | {parameter['delta_theta_degrees']} | {parameter['role']} |")
    lines.extend(
        [
            "",
            "## Baseline B Scale / Density / Rotation",
            "",
            f"- beta: `{baseline['beta']}`",
            f"- single-layer area density growth: `{baseline['density_growth_per_layer']}` = `sqrt(2)` within DG1 float64 tolerance",
            "- beta is an edge-length schedule parameter; density growth is beta squared.",
            "- delta theta: `22.5` degrees",
            "- gap 8 rotation recurrence modulo 60 degrees: `true`",
            "- gap 16 rotation recurrence modulo 60 degrees: `true`",
            "",
            "| layer | side ratio | area ratio | density ratio |",
            "|---:|---:|---:|---:|",
        ]
    )
    for item in baseline["layers"]:
        if item["layer"] in {0, 1, 2, 4, 8, 16}:
            lines.append(f"| {item['layer']} | {item['side_ratio']} | {item['area_ratio']} | {item['density_ratio']} |")
    lines.extend(
        [
            "",
            "## Coverage / Residual / Entropy / Nesting Summary",
            "",
            "| parameter | gap | phase | policy | n | branch mean | branch p95 | branch max | effective mean | residual mean | residual p95 | max mass | overlap entropy | nesting | phase recurrence | rotation mod60 |",
            "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    row.parameter_id,
                    str(row.gap),
                    row.phase_label,
                    row.phase_policy,
                    str(row.distribution_count),
                    _num(row.branching_mean),
                    _num(row.branching_p95),
                    str(row.branching_max),
                    _num(row.effective_count_mean),
                    _num(row.residual_mean),
                    _num(row.residual_p95),
                    _num(row.max_mass),
                    _num(row.overlap_entropy),
                    _num(row.nesting_tendency),
                    _num(row.phase_recurrence_score),
                    "true" if row.rotation_recurrence_mod60 else "false",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Verified Facts",
            "",
            "- A-E parameter ids, beta values, delta theta values, and roles are read from the sealed DG1 parameter matrix.",
            "- Coverage distributions are built by DG1 `compute_distribution`; GPR1 does not implement polygon overlap or coverage kernels.",
            "- Every metric row is finite and reproducible as a canonical payload for the fixed window.",
            "- Baseline B has rotation recurrence modulo 60 degrees at gap 8 and gap 16.",
            "- `constant_local` and `layer_drift_control` produce separately reported phase policy rows.",
            "",
            "## Reasonable Interpretation",
            "",
            "- B is the current engineering baseline in this repository, not a proof of mathematical optimality.",
            "- Rotation recurrence, phase recurrence, quantized overlap entropy, branching, residual, and nesting are separate diagnostics.",
            "- Finite-window differences among A-E can guide further research questions but do not select a production profile.",
            "",
            "## Unverified Items",
            "",
            "- No global all-plane coverage theorem is established.",
            "- No exact algebraic-number proof is established; metrics use DG1 float64 tolerance.",
            "- No global translation policy is selected.",
            "- No memory, admission, field, recall, runtime, OpenClaw, LLM, NLP, embedding, network, database, or cache behavior is exercised.",
            "",
            "## Conclusion Limits",
            "",
            "- GPR1 does not change `FIELD_PROFILE_ID`, beta, theta, translation, or phase policy.",
            "- GPR1 does not modify DG1/DG2 or any sealed production implementation.",
            "- Validation report output is derived and disposable; it is not memory, recall, or a source of truth.",
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
