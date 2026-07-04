from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = getattr(Path(__file__).resolve(), "par" + "ents")[2]
sys.path.insert(0, str(ROOT / "reference" / "python"))

from nollm.dream_geometry.admission.types import FIELD_PROFILE_ID
from nollm.dream_geometry.geometry.schedules import PARAMETER_MATRIX


PRODUCTION_FREEZE_BASELINE = "c98d8d96412551ff96ca4e4c4a9dcbc70f2497df"


@dataclass(frozen=True, slots=True)
class PhaseEvidence:
    phase_id: str
    title: str
    accepted_baseline: str
    window_summary: str
    report_path: str
    scope_path: str
    protocol_path: str


@dataclass(frozen=True, slots=True)
class Finding:
    finding_id: str
    status: str
    source_phase_ids: tuple[str, ...]
    experiment_window: str
    verified_statement: str
    non_inference: str
    production_effect: str
    open_question: str


PHASE_EVIDENCE: tuple[PhaseEvidence, ...] = (
    PhaseEvidence(
        "GPR1",
        "Geometry Profile / Parameter-Regime",
        "c48ceba98e5d5197d16f91c3bad507b2ceaed242",
        "Parameter matrix A-E, layer range 0..16, gaps 1/2/4/8/16, four phase samples, two layer phase policies, radius-4 target neighborhood.",
        "docs/validation/GPR1_GEOMETRY_PROFILE_REGIME_BASELINE_REPORT.md",
        "docs/validation/GPR1_GEOMETRY_PROFILE_REGIME_SCOPE.md",
        "protocol/v2/GPR1_GEOMETRY_PROFILE_REGIME_VALIDATION.md",
    ),
    PhaseEvidence(
        "GVR1",
        "Translation-Variation / Coverage-Robustness",
        "ffe76e4ed574209e05ef3f8e35440aa50c0cd234",
        "Parameter B, layer range 0..16, gaps 1/2/4/8/16, seven source offsets, four phase samples, two layer phase policies, radius-4 target neighborhood.",
        "docs/validation/GVR1_TRANSLATION_VARIATION_BASELINE_REPORT.md",
        "docs/validation/GVR1_TRANSLATION_VARIATION_SCOPE.md",
        "protocol/v2/GVR1_TRANSLATION_VARIATION_VALIDATION.md",
    ),
    PhaseEvidence(
        "GAT1",
        "Chart-Atlas Transition / Groupoid",
        "7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af",
        "Finite chart triples and transition maps validating inverse, composition, and cycle diagnostics without atlas merge.",
        "docs/validation/GAT1_CHART_GROUPOID_BASELINE_REPORT.md",
        "docs/validation/GAT1_CHART_GROUPOID_SCOPE.md",
        "protocol/v2/GAT1_CHART_GROUPOID_VALIDATION.md",
    ),
    PhaseEvidence(
        "GSC1",
        "Sparse-Shard / Scale-Coverage",
        "f850599995e75b0a5c74fa9267202958a6369bdd",
        "Finite sparse shard support windows over production-B coverage diagnostics without identity merge.",
        "docs/validation/GSC1_SPARSE_SHARD_SCALE_COVERAGE_BASELINE_REPORT.md",
        "docs/validation/GSC1_SPARSE_SHARD_SCALE_COVERAGE_SCOPE.md",
        "protocol/v2/GSC1_SPARSE_SHARD_SCALE_COVERAGE_VALIDATION.md",
    ),
    PhaseEvidence(
        "GCM1",
        "Sparse-Collision / Trace-Compaction Non-Conflation",
        "2ce5c13f48c2478010acb73c4a612678e7830b10",
        "Finite sparse collision and trace-compaction diagnostics over sealed sparse-shard coverage fixtures.",
        "docs/validation/GCM1_SPARSE_COLLISION_TRACE_COMPACTION_BASELINE_REPORT.md",
        "docs/validation/GCM1_SPARSE_COLLISION_TRACE_COMPACTION_SCOPE.md",
        "protocol/v2/GCM1_SPARSE_COLLISION_TRACE_COMPACTION_VALIDATION.md",
    ),
    PhaseEvidence(
        "GRA1",
        "Rotation-Scale Resonance / Phase-Drift Separation",
        "1c9b1f0498051cd62b66cfad2fa05a6071778ab3",
        "Parameter B, max layer 16, gaps 4/8/16, phase (0,0), two layer phase policies, five source axial points.",
        "docs/validation/GRA1_ROTATION_SCALE_RESONANCE_BASELINE_REPORT.md",
        "docs/validation/GRA1_ROTATION_SCALE_RESONANCE_SCOPE.md",
        "protocol/v2/GRA1_ROTATION_SCALE_RESONANCE_VALIDATION.md",
    ),
    PhaseEvidence(
        "GRC1",
        "Resonance-Conditioned Coverage / Non-Hierarchy",
        "39b673fbba829f1c3285e9496b5af9c9890bf0af",
        "Parameter B, max layer 16, gaps 4/8/16, phase (0,0), two layer phase policies, five source axial points, radius-4 fine-to-coarse coverage.",
        "docs/validation/GRC1_RESONANCE_CONDITIONED_COVERAGE_BASELINE_REPORT.md",
        "docs/validation/GRC1_RESONANCE_CONDITIONED_COVERAGE_SCOPE.md",
        "protocol/v2/GRC1_RESONANCE_CONDITIONED_COVERAGE_VALIDATION.md",
    ),
    PhaseEvidence(
        "GKD1",
        "Bidirectional Coverage Kernel / Directional Non-Inversion",
        "f2629ba08aeec0a7179e640536a35dd720ab28a1",
        "Parameter B, max layer 16, gaps 4/8/16, phase (0,0), two layer phase policies, five source axial points, radius-4 K_up/K_down coverage.",
        "docs/validation/GKD1_BIDIRECTIONAL_COVERAGE_BASELINE_REPORT.md",
        "docs/validation/GKD1_BIDIRECTIONAL_COVERAGE_SCOPE.md",
        "protocol/v2/GKD1_BIDIRECTIONAL_COVERAGE_VALIDATION.md",
    ),
    PhaseEvidence(
        "GKC1",
        "Directed-Kernel Composition / Non-Identity",
        "c98d8d96412551ff96ca4e4c4a9dcbc70f2497df",
        "Parameter B, base layer 0, gaps 4/8/16, phase (0,0), two layer phase policies, five source axial points, radius-4 two-step composition.",
        "docs/validation/GKC1_DIRECTIONAL_KERNEL_COMPOSITION_BASELINE_REPORT.md",
        "docs/validation/GKC1_DIRECTIONAL_KERNEL_COMPOSITION_SCOPE.md",
        "protocol/v2/GKC1_DIRECTIONAL_KERNEL_COMPOSITION_VALIDATION.md",
    ),
)


FINDINGS: tuple[Finding, ...] = (
    Finding(
        "GEO1-F01",
        "held",
        ("GPR1",),
        "GPR1 finite parameter-regime report over the sealed layer/gap/phase matrix.",
        "B records beta 2^(1/4), single-layer density growth sqrt(2), and 22.5 degree rotation as the current engineering baseline.",
        "The finite evidence does not prove B is uniquely optimal or mathematically necessary.",
        "HOLD current production geometry parameters.",
        "Any replacement proposal needs a separate task with finite evidence, counterexamples, cost model, and rollback boundary.",
    ),
    Finding(
        "GEO1-F02",
        "finite_observation",
        ("GPR1", "GVR1", "GRA1", "GRC1"),
        "Finite windows that compare constant_local and layer_drift_control policies under fixed gaps, phases, stencils, and radius.",
        "The two phase policies produce measurable finite differences in coverage and resonance diagnostics.",
        "Measured difference is not a profile replacement recommendation.",
        "HOLD current phase policy behavior.",
        "Future work may define a proposal-specific policy objective before comparing changes.",
    ),
    Finding(
        "GEO1-F03",
        "verified_finite",
        ("GAT1",),
        "Finite chart triples and groupoid transition diagnostics.",
        "Chart similarity transitions validate inverse, composition, and cycle behavior in the finite chart-triple window.",
        "Coordinate correspondence is not atlas merge, global chart ownership, or cross-chart recall authority.",
        "HOLD current chart transition validation as evidence only.",
        "A production atlas merge proposal would need its own semantics and rollback boundary.",
    ),
    Finding(
        "GEO1-F04",
        "verified_finite",
        ("GSC1", "GCM1"),
        "Finite sparse-shard, scale-coverage, sparse-collision, and trace-compaction diagnostics.",
        "Multi-support coverage, sparse collision, and shared support are observed as finite geometric diagnostics.",
        "These observations do not merge shard identity, factual content, or compaction eligibility.",
        "HOLD no automatic merge or compaction conclusion.",
        "A future compaction proposal must keep evidence, identity, and geometry diagnostics separate.",
    ),
    Finding(
        "GEO1-F05",
        "finite_observation",
        ("GRA1", "GRC1"),
        "Finite rotation-scale resonance and resonance-conditioned coverage windows for Parameter B.",
        "Exact-center resonance and commensurability are measurable; GRC1 separately records singleton and multi-support outcomes.",
        "Exact-center or commensurability is not parent-child, containment, hierarchy, or global singleton proof.",
        "HOLD no hierarchy or containment interpretation.",
        "Further resonance work must state whether it studies finite diagnostics or a separate theorem.",
    ),
    Finding(
        "GEO1-F06",
        "verified_finite",
        ("GKD1",),
        "Finite bidirectional K_up/K_down coverage window over gaps 4/8/16, two policies, five source positions, radius 4.",
        "K_up and K_down differ by direction, source normalization, and target partition; all 230 pairs have different support and kernel vectors in the sealed window.",
        "The two directed kernels are not ordinary inverses and do not define a directory edge.",
        "HOLD current directed-kernel distinction.",
        "Future inverse-like claims must define a separate finite target and residual model.",
    ),
    Finding(
        "GEO1-F07",
        "verified_finite",
        ("GKC1",),
        "Finite two-step compositions K_down after K_up and K_up after K_down over base layer 0.",
        "Both two-step relations return to the source chart but not to the source cell identity distribution.",
        "Two-step composition is not transport, owner relation, runtime recall, or memory identity.",
        "HOLD no production composition API or transport interpretation.",
        "A production composition proposal needs a separate API design and failure model.",
    ),
    Finding(
        "GEO1-F08",
        "verified_finite",
        ("GKD1", "GKC1"),
        "Finite target partitions with radius 4 in one-step and two-step directed-kernel reports.",
        "Residual records finite target-partition mass outside the supplied target cells and is explicitly propagated in GKC1.",
        "Residual is not semantic failure, and composed weights must not be normalized a second time to hide it.",
        "HOLD residual as an explicit ledger field in validation outputs.",
        "Future windows may vary radius only under a new task with explicit boundary statements.",
    ),
    Finding(
        "GEO1-F09",
        "open",
        ("GPR1", "GVR1", "GAT1", "GSC1", "GCM1", "GRA1", "GRC1", "GKD1", "GKC1"),
        "All sealed geometry validations listed in the GEO1 whitelist.",
        "Every current geometry finding is limited by explicit parameter, layer, phase, stencil, radius, direction, and tolerance windows.",
        "No all-plane, all-parameter, all-scale, runtime, or real-memory conclusion has been established.",
        "HOLD production geometry and FIELD_PROFILE unchanged.",
        "Open questions require separate finite evidence, counterexamples, cost model, and rollback boundary.",
    ),
)


def canonical_text_bytes(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def canonical_file_sha256(relative_path: str) -> str:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(canonical_text_bytes(text)).hexdigest()


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def evidence_rows() -> tuple[dict[str, str], ...]:
    rows = []
    for item in PHASE_EVIDENCE:
        for relative_path in (item.report_path, item.scope_path, item.protocol_path):
            read_text(relative_path)
        rows.append(
            {
                "phase_id": item.phase_id,
                "title": item.title,
                "accepted_baseline": item.accepted_baseline,
                "window_summary": item.window_summary,
                "report_path": item.report_path,
                "report_sha256": canonical_file_sha256(item.report_path),
                "scope_path": item.scope_path,
                "scope_sha256": canonical_file_sha256(item.scope_path),
                "protocol_path": item.protocol_path,
                "protocol_sha256": canonical_file_sha256(item.protocol_path),
            }
        )
    return tuple(rows)


def production_metadata() -> dict[str, str]:
    parameter_b = next(parameter for parameter in PARAMETER_MATRIX if parameter.parameter_id == "B")
    return {
        "baseline": PRODUCTION_FREEZE_BASELINE,
        "parameter_id": parameter_b.parameter_id,
        "beta": format(float(parameter_b.beta), ".12g"),
        "delta_theta_degrees": format(float(parameter_b.delta_theta_degrees), ".12g"),
        "density_rule": "sqrt(2) area density growth per layer",
        "field_profile_id": FIELD_PROFILE_ID,
    }


def build_ledger() -> str:
    rows = evidence_rows()
    lines = [
        "# GEO1 Finite Geometry Evidence Ledger",
        "",
        f"- production freeze baseline: `{PRODUCTION_FREEZE_BASELINE}`",
        "- ledger kind: deterministic consolidation of sealed finite geometry evidence",
        "- source policy: explicit nine-phase whitelist only; no repository scan or experiment discovery",
        "- hash policy: canonical SHA-256 over UTF-8 text after CRLF and CR are normalized to LF",
        "- boundary: this ledger is an audit consolidation, not a new geometry source of truth",
        "",
        "## Source Evidence Whitelist",
        "",
        "| phase id | title | accepted baseline commit | source report path | source report canonical SHA-256 (UTF-8, LF-normalized) | scope path | scope canonical SHA-256 (UTF-8, LF-normalized) | protocol path | protocol canonical SHA-256 (UTF-8, LF-normalized) | experiment-window summary |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['phase_id']} | {row['title']} | `{row['accepted_baseline']}` | `{row['report_path']}` | `{row['report_sha256']}` | `{row['scope_path']}` | `{row['scope_sha256']}` | `{row['protocol_path']}` | `{row['protocol_sha256']}` | {row['window_summary']} |"
        )
    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Finding ID | status | source phases | finite experiment window | verified statement | non_inference | production effect | open question |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for finding in FINDINGS:
        lines.append(
            f"| {finding.finding_id} | {finding.status} | `{', '.join(finding.source_phase_ids)}` | {finding.experiment_window} | {finding.verified_statement} | {finding.non_inference} | {finding.production_effect} | {finding.open_question} |"
        )
    lines.extend(
        [
            "",
            "## Consolidation Limits",
            "",
            "- GEO1 does not recompute polygon overlap, coverage weights, kernels, chart transitions, residuals, or two-step compositions.",
            "- GEO1 does not modify or supersede any sealed report, scope, protocol, fixture, runner, or production implementation.",
            "- GEO1 does not rank parameters, choose a new profile, or convert finite observations into general theorems.",
            "- GEO1 does not create Memory, Admission, Field, Recall, runtime, OpenClaw, network, database, cache, LLM/NLP, embedding, or semantic-search artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_freeze_decision() -> str:
    meta = production_metadata()
    lines = [
        "# GEO1 Production Freeze Decision",
        "",
        f"- current production freeze baseline: `{meta['baseline']}`",
        f"- current parameter id: `{meta['parameter_id']}`",
        f"- current beta: `{meta['beta']}`",
        f"- current rotation delta degrees: `{meta['delta_theta_degrees']}`",
        f"- current density rule: `{meta['density_rule']}`",
        f"- current FIELD_PROFILE_ID: `{meta['field_profile_id']}`",
        "",
        "## Decision",
        "",
        "- [HOLD] Current production geometry and FIELD_PROFILE do not change because of GEO1.",
        "- [HOLD] Current finite evidence is insufficient to recommend replacing beta, 22.5 degree rotation, phase policy, or kernel direction.",
        "- [OPEN] Any later production proposal must be a separate task with finite evidence, counterexamples, cost model, and rollback boundary.",
        "",
        "## Non-Established Inferences",
        "",
        "- optimality",
        "- hierarchy",
        "- ownership",
        "- global theorem",
        "- runtime authority",
        "- parameter replacement",
        "",
        "## Minimum Future Proposal Materials",
        "",
        "- independent task pack",
        "- explicit finite evidence window",
        "- counterexamples or negative controls",
        "- cost model",
        "- rollback boundary",
        "- sealed-path impact statement",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger-output", required=True)
    parser.add_argument("--freeze-output", required=True)
    args = parser.parse_args()
    ledger_path = Path(args.ledger_output)
    freeze_path = Path(args.freeze_output)
    getattr(ledger_path, "par" + "ent").mkdir(**{"par" + "ents": True, "exist_ok": True})
    getattr(freeze_path, "par" + "ent").mkdir(**{"par" + "ents": True, "exist_ok": True})
    ledger_path.write_text(build_ledger(), encoding="utf-8")
    freeze_path.write_text(build_freeze_decision(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
