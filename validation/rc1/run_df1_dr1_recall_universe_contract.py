from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = REPO_ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.dream_geometry.assembly import assemble_field_snapshot, recall_universe_from_snapshot  # noqa: E402
from nollm.dream_geometry.cortex import compile_query  # noqa: E402
from nollm.dream_geometry.geometry.types import CellRef, HexCell  # noqa: E402
from nollm.dream_geometry.recall import RecallDigestStatus, RecallPolicy, resolve_recall  # noqa: E402
from tests.fixtures.df1_assembly.fixture import build_df1_environment, finite_set, tree_manifest  # noqa: E402


BASELINE = "1def9e0d4d2b0deb2ab2ad9db74f6d01d4a3dbf7"


def build_report() -> str:
    with tempfile.TemporaryDirectory(prefix="nollm_rc1_") as tmp:
        root = Path(tmp)
        single = _single(root / "single")
        views = _views(root / "views")
        multi = _multi(root / "multi")
        reconstructed = _reconstructed(root / "reconstructed")
    lines = [
        "# RC1 DF1 to DR1 RecallUniverse Contract Report",
        "",
        f"- baseline_head: `{BASELINE}`",
        f"- validation_head: `{_git('rev-parse HEAD')}`",
        "- command: `python validation/rc1/run_df1_dr1_recall_universe_contract.py --output docs/validation/RC1_DF1_DR1_RECALL_UNIVERSE_CONTRACT_REPORT.md`",
        "- production_fix_path: `reference/python/nollm/dream_geometry/assembly/builder.py`",
        "",
        "## Evidence",
        "",
        f"- rc1_01_single_admission_df1_to_dr1: `{'pass' if single else 'fail'}`",
        f"- rc1_02_snapshot_universe_view_split: `{'pass' if views else 'fail'}`",
        f"- rc1_03_multi_admission_determinism: `{'pass' if multi else 'fail'}`",
        f"- rc1_04_public_reconstruction_path: `{'pass' if reconstructed else 'fail'}`",
        "",
        "## Contract",
        "",
        "- `FiniteFieldSnapshot.coarse_covers` remains the DG2 local view with `CellRef` support cells.",
        "- `RecallUniverse.covers` is the DR1 executable view with `HexCell` support cells bound from same-call replay traces.",
        "- RC1 does not complete DX2; DX2 must restart from the RC1 delivery head after independent acceptance.",
    ]
    return "\n".join(lines) + "\n"


def _single(root: Path) -> bool:
    evidence, cortex, admission, orchestrator = build_df1_environment(root)
    before = _manifest(root)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    digest = resolve_recall(_probe(), result.universe, evidence, policy=RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2))
    return digest.status is RecallDigestStatus.resolved and tuple(item.shard_id for item in digest.items) == ("shard:df1:alpha",) and bool(digest.traversal_records) and _manifest(root) == before


def _views(root: Path) -> bool:
    evidence, cortex, admission, orchestrator = build_df1_environment(root)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    snapshot_cover = result.snapshot.coarse_covers[0]
    universe_cover = result.universe.covers[0]
    return (
        isinstance(snapshot_cover.support_cell, CellRef)
        and isinstance(universe_cover.support_cell, HexCell)
        and universe_cover.support_cell.cell_ref == snapshot_cover.support_cell
        and universe_cover.support_cell.chart_fingerprint == snapshot_cover.chart_fingerprint
        and result.universe.gravity_snapshot is not None
        and result.universe.gravity_snapshot.snapshot_id == result.snapshot.gravity_snapshot.snapshot_id
    )


def _multi(root: Path) -> bool:
    specs = (
        ("adm_df1_alpha", "shard:df1:alpha", "gp_df1_alpha", "Kunming rain alpha."),
        ("adm_df1_beta", "shard:df1:beta", "gp_df1_beta", "Kunming rain beta."),
        ("adm_df1_gamma", "shard:df1:gamma", "gp_df1_gamma", "Kunming rain gamma."),
    )
    evidence, cortex, admission, orchestrator = build_df1_environment(root, specs)
    first = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha", "adm_df1_beta", "adm_df1_gamma")))
    second = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_gamma", "adm_df1_alpha", "adm_df1_beta")))
    first_digest = resolve_recall(_probe(), first.universe, evidence, policy=RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2))
    second_digest = resolve_recall(_probe(), second.universe, evidence, policy=RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2))
    return (
        first.snapshot.snapshot_id == second.snapshot.snapshot_id
        and first.universe.universe_id == second.universe.universe_id
        and tuple(item.shard_id for item in first_digest.items) == tuple(item.shard_id for item in second_digest.items)
        and first_digest.status is second_digest.status
    )


def _reconstructed(root: Path) -> bool:
    evidence, cortex, admission, orchestrator = build_df1_environment(root)
    result = assemble_field_snapshot(finite_set(evidence, cortex, admission, orchestrator, ("adm_df1_alpha",)))
    universe = recall_universe_from_snapshot(result.snapshot, result.universe.proposal_records)
    digest = resolve_recall(_probe(), universe, evidence, policy=RecallPolicy(min_required_axis_matches=2, max_lateral_hops=2))
    return all(isinstance(cover.support_cell, HexCell) for cover in universe.covers) and digest.status is RecallDigestStatus.resolved


def _probe():
    return compile_query(
        {
            "contract_version": "dc1.v1",
            "probe_id": "probe_rc1_kunming_rain",
            "query_text": "Kunming rain",
            "reference_instant": "2026-07-02T10:00:00+08:00",
            "requires_runtime_resolution": False,
            "ephemeral": True,
            "budget": {"max_axes": 4, "max_charts": 8, "max_layers": 4, "max_cells_per_layer": 32},
            "do_not_infer": ["rc1 synthetic fixture only"],
            "forbidden_inferences": ["no semantic fallback"],
            "axes": [
                {"axis_id": "location", "ray": [{"step_id": "step_q_location", "expression": "Kunming", "basis": "explicit_in_query", "basis_refs": [{"ref_type": "text_span", "record_id": "probe_rc1_kunming_rain", "start_char": 0, "end_char": 7, "quoted_text": "Kunming"}], "rationale": None}]},
                {"axis_id": "phenomenon", "ray": [{"step_id": "step_q_phenomenon", "expression": "rain", "basis": "explicit_in_query", "basis_refs": [{"ref_type": "text_span", "record_id": "probe_rc1_kunming_rain", "start_char": 8, "end_char": 12, "quoted_text": "rain"}], "rationale": None}]},
            ],
        }
    )


def _manifest(root: Path) -> dict[str, tuple[tuple[str, str], ...]]:
    return {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission")}


def _git(args: str) -> str:
    try:
        return subprocess.check_output(["git", *args.split()], cwd=REPO_ROOT, text=True, timeout=10).strip()
    except Exception as exc:
        return f"unavailable: {exc}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
        print(args.output)
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
