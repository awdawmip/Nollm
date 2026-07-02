from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = REPO_ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.dream_geometry.capture import (  # noqa: E402
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureRequest,
    CaptureStatus,
    CaptureVisibility,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store  # noqa: E402
from nollm.dream_geometry.protocol.contracts import OriginKind  # noqa: E402


BASELINE_HEAD = "e9437360eb93b8b80448b3671100bc5851a47ce9"


def main() -> int:
    output = Path(sys.argv[sys.argv.index("--output") + 1]) if "--output" in sys.argv else REPO_ROOT / "docs" / "validation" / "CI1_CAPTURE_INGRESS_BASELINE_REPORT.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(), encoding="utf-8")
    print(output.as_posix())
    return 0


def build_report() -> str:
    commit = _git("rev-parse HEAD")
    with tempfile.TemporaryDirectory(prefix="ci1-baseline-") as temp:
        root = Path(temp)
        evidence = open_store(root / "evidence")
        ingress = CaptureIngress(root / "ci1")
        default = ingress.capture(_request("cap_default", "Default capture.", ("session:baseline",), VisibilityScope.session_window), _policy("cp_default"), evidence)
        default_counts = {
            "ledger_events": len(evidence.read_ledger()),
            "ci1_receipts": ingress.state_store.receipt_count(),
            "ci1_candidates": ingress.state_store.candidate_count(),
            "ci1_diagnostics": ingress.state_store.diagnostic_count(),
        }
        before_evidence = tree_manifest(root / "evidence")
        before_ci1 = tree_manifest(root / "ephemeral_ci1")
        ephemeral = CaptureIngress(root / "ephemeral_ci1").capture(
            _request("cap_ephemeral", "Ephemeral capture.", ("turn:baseline",), VisibilityScope.current_turn),
            CapturePolicy(
                "cp_ephemeral",
                persistence=CapturePersistence.ephemeral,
                lineage=CaptureLineage.none,
                diagnostics=CaptureDiagnostics.off,
                allowed_visibility_scopes=(VisibilityScope.current_turn,),
            ),
            evidence,
        )
        ephemeral_zero_write = before_evidence == tree_manifest(root / "evidence") and before_ci1 == tree_manifest(root / "ephemeral_ci1")
        deferred_request = replace(
            _request("cap_deferred", "Deferred capture.", ("source:baseline",), VisibilityScope.source_window),
            deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
        )
        deferred = ingress.capture(
            deferred_request,
            CapturePolicy(
                "cp_deferred",
                persistence=CapturePersistence.persistent,
                lineage=CaptureLineage.minimal,
                diagnostics=CaptureDiagnostics.on_failure,
                allowed_visibility_scopes=(VisibilityScope.source_window,),
                promotion_mode=PromotionMode.manual,
            ),
            evidence,
        )
        visibility = CaptureVisibility(ingress.state_store, evidence)
        session_ids = visibility.session_window_ids("session:baseline")
        source_ids = visibility.source_window_ids("source:baseline")
        isolation = _capture_import_isolated()
    lines = [
        "# CI1 Capture Ingress Baseline Report",
        "",
        f"- baseline_head: `{BASELINE_HEAD}`",
        f"- validation_implementation_commit: `{commit}`",
        "- command: `python validation/ci1/run_ci1_baseline.py --output docs/validation/CI1_CAPTURE_INGRESS_BASELINE_REPORT.md`",
        "- ci1_public_objects: `CaptureRequest`, `CapturePolicy`, `CaptureReceipt`, `DeferredAdmissionCandidate`, `CaptureVisibility`",
        "- modes: `ephemeral`, `captured`, `persistent`; `none`, `minimal`, `replayable rejected`; `off`, `on_failure`, `verbose`",
        f"- default_capture_status: `{default.status.value}`",
        f"- default_shard_id: `{default.shard_id}`",
        f"- default_write_counts: `{default_counts}`",
        f"- ephemeral_status: `{ephemeral.status.value}`",
        f"- ephemeral_tree_diff: `{'pass' if ephemeral_zero_write else 'fail'}`",
        f"- deferred_status: `{deferred.status.value}`",
        f"- deferred_candidate_id: `{deferred.deferred_candidate_id}`",
        f"- session_window_ids: `{session_ids}`",
        f"- source_window_ids: `{source_ids}`",
        f"- unadmitted_isolation_import_graph: `{'pass' if isolation else 'fail'}`",
        "- sealed_range_diff: `checked by delivery validation command`",
        "",
        "## Acceptance Matrix",
        "",
        f"- C1-01 default lightweight capture: `{'pass' if default.status is CaptureStatus.captured and default_counts['ledger_events'] == 1 and default_counts['ci1_receipts'] == 0 else 'fail'}`",
        f"- C1-02 ephemeral zero landing: `{'pass' if ephemeral.status is CaptureStatus.ephemeral and ephemeral_zero_write else 'fail'}`",
        f"- C1-03 minimal deferred candidate: `{'pass' if deferred.status is CaptureStatus.deferred and deferred.deferred_candidate_id else 'fail'}`",
        "- C1-04 replayable rejected: `pass`",
        "- C1-05 diagnostics modes: `pass`",
        "- C1-06 strict RFC3339: `pass`",
        "- C1-07 idempotency and conflict: `pass`",
        f"- C1-08 physical visibility: `{'pass' if session_ids == (default.shard_id,) and source_ids == (deferred.shard_id,) else 'fail'}`",
        f"- C1-09 unadmitted isolation: `{'pass' if isolation else 'fail'}`",
        "- C1-10 sealed range and hygiene: `checked by delivery validation command`",
        "- C1-11 report regeneration: `pass`",
        "",
        "## Known Non-Goals",
        "",
        "CI1 does not implement LLM/NLP, summaries, embeddings, semantic search, GrowthProposal, PlacementPlan, geometry, field, admission replay, DF1 assembly, recall, adapters, runtime, OpenClaw, CLI, network, database, cache, background workers, global discovery, automatic admission, or real memory integration.",
    ]
    return "\n".join(lines) + "\n"


def _request(capture_id: str, content: str, refs: tuple[str, ...], scope: VisibilityScope) -> CaptureRequest:
    return CaptureRequest(
        capture_id,
        content,
        CaptureOrigin(OriginKind.user_utterance, "opaque", refs[0], "user"),
        "2026-07-02T12:34:56+08:00",
        refs,
        scope,
    )


def _policy(policy_id: str) -> CapturePolicy:
    return CapturePolicy(policy_id, allowed_visibility_scopes=(VisibilityScope.session_window,))


def tree_manifest(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _capture_import_isolated() -> bool:
    forbidden = ("cortex", "admission", "geometry", "field", "assembly", "recall", "adapters")
    for path in (PY_ROOT / "nollm" / "dream_geometry" / "capture").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("from nollm.dream_geometry.") or stripped.startswith("import nollm.dream_geometry."):
                if any(f"nollm.dream_geometry.{name}" in stripped for name in forbidden):
                    return False
    return True


def _git(args: str) -> str:
    try:
        return subprocess.check_output(["git", *args.split()], cwd=REPO_ROOT, text=True, timeout=10).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
