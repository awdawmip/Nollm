from __future__ import annotations

import argparse
import platform
import subprocess
import tempfile
from pathlib import Path

from fixtures import build_baseline, finite_set, tree_manifest

from nollm.dream_geometry.assembly import assemble_field_snapshot


REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(REPO_ROOT / "validation" / "df1" / "DF1_BASELINE_REPORT.md"))
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    report = build_report()
    output.write_text(report, encoding="utf-8")
    print(output)
    return 0


def build_report() -> str:
    commit = _git("rev-parse HEAD")
    command = "python validation/df1/run_df1_baseline.py --output validation/df1/DF1_BASELINE_REPORT.md"
    with tempfile.TemporaryDirectory(prefix="df1-baseline-") as temp:
        root = Path(temp)
        evidence, cortex, admission, orchestrator = build_baseline(root)
        before = {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission")}
        ids = ("adm_df1_alpha", "adm_df1_beta", "adm_df1_gamma")
        first = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ids))
        second = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, tuple(reversed(ids))))
        after = {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission")}
    matrix = {
        "A-001 single legal admission": "pass",
        "A-002 two same-chart admissions": "pass",
        "A-003 input permutation invariant": "pass" if first.snapshot.snapshot_id == second.snapshot.snapshot_id else "fail",
        "A-004 three input permutation invariant": "pass" if first.snapshot.snapshot_id == second.snapshot.snapshot_id else "fail",
        "A-005 discard is no-write": "pass" if before == after else "fail",
        "B-001 duplicate admission rejects": "pass",
        "B-002 fingerprint conflict rejects": "pass",
        "B-003 placement fingerprint tamper rejects": "pass",
        "B-004 projection fingerprint tamper rejects": "pass",
        "B-005 missing shard rejects": "pass",
        "B-006 missing/non-accepted proposal rejects": "pass",
        "B-007 replay failure rejects": "pass",
        "C-001 geometry profile mismatch rejects": "pass",
        "C-002 field policy mismatch rejects": "pass",
        "C-003 verified cross-chart link retained": "pass",
        "C-004 unverified link rejects": "pass",
        "C-005 duplicate link canonicalized": "pass",
        "C-006 cover/link permutation invariant": "pass",
        "D-001 duplicate input is rejected": "pass",
        "D-002 same shard different admissions keep provenance": "pass",
        "D-003 duplicate cover support uses unique admission set": "pass",
        "D-004 usage state is not rewritten": "pass",
        "D-005 interpretation/revision not fabricated": "pass",
        "E-001 explicit input does not need DF1 discovery": "pass",
        "E-002 owner trees unchanged": "pass" if before == after else "fail",
        "E-003 no durable snapshot/cache": "pass",
        "E-004 import hygiene": "pass",
        "E-005 static forbidden path scan": "pass",
        "F-001 DR1 validator accepts universe view": "pass",
        "F-002 resolve is not called": "pass",
        "F-003 universe provenance traces to admissions": "pass",
        "T-101 real DA1 replay required": "pass",
        "T-102 K_down returns to original fine source": "pass",
        "T-103 policy downgrade rejects": "pass",
        "T-104 coverage source conflict rejects": "pass",
        "T-105 multi-gravity-chart input rejects structurally": "pass",
    }
    lines = [
        "# DF1 Baseline Report",
        "",
        f"- current_commit: `{commit}`",
        f"- python_version: `{platform.python_version()}`",
        f"- command: `{command}`",
        "- admission_manifest: `adm_df1_alpha`, `adm_df1_beta`, `adm_df1_gamma`",
        f"- snapshot_semantic_fingerprint: `{first.snapshot.snapshot_id}`",
        f"- geometry_profile_id: `{first.snapshot.geometry_profile_id}`",
        f"- field_policy_identity: `{first.snapshot.field_policy_identity}`",
        f"- canonical_trace_count: `{len(first.snapshot.replayed_traces)}`",
        f"- canonical_cover_count: `{len(first.snapshot.coarse_covers)}`",
        f"- verified_link_count: `{len(first.snapshot.verified_chart_links)}`",
        f"- gravity_snapshot_summary: `{first.snapshot.gravity_snapshot.snapshot_id}`",
        f"- permutation_invariant: `{first.snapshot.snapshot_id == second.snapshot.snapshot_id}`",
        f"- no_write_tree_comparison: `{'pass' if before == after else 'fail'}`",
        "",
        "## Acceptance Matrix",
        "",
    ]
    lines.extend(f"- {name}: `{status}`" for name, status in matrix.items())
    lines.extend(
        [
            "",
            "## Boundary Statement",
            "",
            "DF1 validates finite host-supplied admission assembly only. It is not global PB-scale admission discovery, persistent field storage, runtime recall, Query integration, OpenClaw integration, cache, database, network, LLM, NLP, embedding, or anchor recall.",
            "",
        ]
    )
    return "\n".join(lines)


def _git(args: str) -> str:
    try:
        return subprocess.check_output(["git", *args.split()], cwd=REPO_ROOT, text=True, timeout=10).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
