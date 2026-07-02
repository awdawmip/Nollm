from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = REPO_ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.dream_geometry.capture import (  # noqa: E402
    CandidateTrigger,
    CaptureDiagnostics,
    CaptureError,
    CaptureIngress,
    CaptureLineage,
    CaptureOrigin,
    CapturePersistence,
    CapturePolicy,
    CaptureStateStore,
    CaptureStatus,
    CaptureVisibility,
    DeferredCandidateRequest,
    PromotionMode,
    VisibilityScope,
)
from nollm.dream_geometry.evidence import open_store  # noqa: E402
from nollm.dream_geometry.protocol.contracts import OriginKind  # noqa: E402


def build_report() -> str:
    with tempfile.TemporaryDirectory(prefix="nollm_cx1_") as tmp:
        root = Path(tmp)
        state_matrix = _state_matrix(root / "matrix")
        retry_reopen = _retry_reopen(root / "retry")
        local_failure = _local_failure_closure(root / "failure")
        visibility = _visibility_read_only(root / "visibility")
        formal_isolation = _formal_path_isolation(root / "formal")
    lines = [
        "# CX1 Capture / Deferred / Visibility Synthetic Validation Report",
        "",
        f"- baseline_head: `3e2d96afa8ff503614907c73c3d1aac56b028bd5`",
        f"- validation_head: `{_git('rev-parse HEAD')}`",
        "- command: `python validation/cx1/run_cx1_synthetic_validation.py --output docs/validation/CX1_CAPTURE_DEFERRED_VISIBILITY_SYNTHETIC_REPORT.md`",
        "- public_objects_used: `CaptureIngress`, `CapturePolicy`, `CaptureVisibility`, `CaptureStateStore`, `MemorySubstrateStore`",
        "- formal_paths_used: `none`",
        "",
        "## Evidence",
        "",
        f"- cx1_state_matrix: `{'pass' if state_matrix else 'fail'}`",
        f"- cx1_retry_reopen: `{'pass' if retry_reopen else 'fail'}`",
        f"- cx1_local_failure_closure: `{'pass' if local_failure else 'fail'}`",
        f"- cx1_visibility_read_only: `{'pass' if visibility else 'fail'}`",
        f"- cx1_formal_path_isolation: `{'pass' if formal_isolation else 'fail'}`",
        "",
        "## Acceptance Matrix",
        "",
        f"- CX1-01 ephemeral zero-write/current-turn boundary: `{'pass' if state_matrix else 'fail'}`",
        f"- CX1-02 captured/deferred/persistent_explicit visibility distinction: `{'pass' if state_matrix else 'fail'}`",
        f"- CX1-03 retry and reopen deterministic replay: `{'pass' if retry_reopen else 'fail'}`",
        f"- CX1-04 local failure does not publish success receipt or public candidate: `{'pass' if local_failure else 'fail'}`",
        f"- CX1-05 visibility is explicit, physical, and read-only: `{'pass' if visibility else 'fail'}`",
        f"- CX1-06 formal DA1/DF1/DR1/DI1 path isolation: `{'pass' if formal_isolation else 'fail'}`",
        "",
        "## Known Non-Goals",
        "",
        "CX1 is synthetic validation only. It does not implement or invoke LLM/NLP, GrowthProposal, PlacementPlan, DA1 admission, geometry, field, DF1 assembly, recall, global discovery, runtime, OpenClaw, CLI, network, database, cache, or real memory integration.",
    ]
    return "\n".join(lines) + "\n"


def _state_matrix(root: Path) -> bool:
    evidence = open_store(root / "evidence")
    ingress = CaptureIngress(root / "ci1")
    ephemeral = ingress.capture(
        _request("cap_cx_ephemeral", "ephemeral", ("turn:cx",), VisibilityScope.current_turn),
        _policy("cp_cx_ephemeral", persistence=CapturePersistence.ephemeral, diagnostics=CaptureDiagnostics.off, allowed=(VisibilityScope.current_turn,)),
        evidence,
    )
    captured = ingress.capture(_request("cap_cx_captured", "captured", ("session:cx",), VisibilityScope.session_window), _policy("cp_cx_captured"), evidence)
    deferred = ingress.capture(
        replace(
            _request("cap_cx_deferred", "deferred", ("source:cx",), VisibilityScope.source_window),
            deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
        ),
        _policy(
            "cp_cx_deferred",
            persistence=CapturePersistence.persistent,
            lineage=CaptureLineage.minimal,
            allowed=(VisibilityScope.source_window,),
            promotion_mode=PromotionMode.manual,
        ),
        evidence,
    )
    persistent = ingress.capture(
        _request("cap_cx_persistent", "persistent", ("explicit:cx",), VisibilityScope.persistent_explicit),
        _policy("cp_cx_persistent", persistence=CapturePersistence.persistent, allowed=(VisibilityScope.persistent_explicit,)),
        evidence,
    )
    visibility = CaptureVisibility(ingress.state_store, evidence)
    return (
        ephemeral.status is CaptureStatus.ephemeral
        and ephemeral.shard_id is None
        and captured.status is CaptureStatus.captured
        and deferred.status is CaptureStatus.deferred
        and persistent.status is CaptureStatus.captured
        and len(evidence.read_ledger()) == 3
        and visibility.session_window_ids("session:cx") == (captured.shard_id,)
        and visibility.source_window_ids("source:cx") == (deferred.shard_id,)
        and visibility.session_window_ids("explicit:cx") == ()
        and visibility.persistent_explicit((persistent.shard_id, persistent.shard_id))[0].content == "persistent"
        and not _contains_forbidden_formal_tokens(root / "ci1")
    )


def _retry_reopen(root: Path) -> bool:
    evidence = open_store(root / "evidence")
    ingress = CaptureIngress(root / "ci1")
    request = replace(
        _request("cap_cx_reopen", "reopen deferred", ("session:reopen",), VisibilityScope.session_window),
        deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.manual_window,)),
    )
    policy = _policy(
        "cp_cx_reopen",
        persistence=CapturePersistence.persistent,
        lineage=CaptureLineage.minimal,
        allowed=(VisibilityScope.session_window,),
        promotion_mode=PromotionMode.manual,
    )
    first = ingress.capture(request, policy, evidence)
    before = (_manifest(root / "evidence"), _manifest(root / "ci1"))
    reopened_evidence = open_store(root / "evidence")
    reopened_ingress = CaptureIngress(root / "ci1")
    second = reopened_ingress.capture(request, policy, reopened_evidence)
    return (
        second == first
        and len(reopened_evidence.read_ledger()) == 1
        and (_manifest(root / "evidence"), _manifest(root / "ci1")) == before
        and CaptureVisibility(reopened_ingress.state_store, reopened_evidence).session_window("session:reopen")[0].content == "reopen deferred"
        and reopened_ingress.state_store.get_candidate(first.deferred_candidate_id).shard_id == first.shard_id
    )


def _local_failure_closure(root: Path) -> bool:
    for failpoint in ("visibility", "candidate", "receipt", "identity", "diagnostic"):
        case = root / failpoint
        evidence = open_store(case / "evidence")
        ingress = CaptureIngress(case / "ci1")
        request = replace(
            _request("cap_cx_fail_" + failpoint, "failure " + failpoint, ("session:failure",), VisibilityScope.session_window),
            deferred_candidate_request=DeferredCandidateRequest(True, (CandidateTrigger.explicit_pin,)),
            diagnostic_retention_until="2026-07-03T00:00:00Z",
        )
        policy = _policy(
            "cp_cx_fail_" + failpoint,
            persistence=CapturePersistence.persistent,
            lineage=CaptureLineage.minimal,
            diagnostics=CaptureDiagnostics.verbose if failpoint == "diagnostic" else CaptureDiagnostics.on_failure,
            allowed=(VisibilityScope.session_window,),
            promotion_mode=PromotionMode.manual,
        )
        if failpoint == "visibility":
            ingress.state_store.append_visibility = _fail  # type: ignore[method-assign]
        elif failpoint == "candidate":
            ingress.state_store.put_candidate = _fail  # type: ignore[method-assign]
        elif failpoint == "receipt":
            ingress.state_store.put_receipt = _fail  # type: ignore[method-assign]
        elif failpoint == "identity":
            ingress.state_store.put_capture_identity = _fail  # type: ignore[method-assign]
        else:
            ingress.state_store.put_diagnostic = _fail  # type: ignore[method-assign]
        try:
            ingress.capture(request, policy, evidence)
            return False
        except CaptureError as exc:
            if exc.code != "CI1_COMMIT_FAILED":
                return False
        try:
            ingress.state_store.get_receipt_by_capture_id(request.capture_id)
            return False
        except CaptureError:
            pass
        for candidate_id in _candidate_ids(case / "ci1"):
            try:
                ingress.state_store.get_candidate(candidate_id)
                return False
            except CaptureError:
                pass
        retry = CaptureIngress(case / "ci1").capture(request, policy, evidence)
        if retry.status is not CaptureStatus.deferred or len(evidence.read_ledger()) != 1:
            return False
        if CaptureStateStore(case / "ci1").get_candidate(retry.deferred_candidate_id).shard_id != retry.shard_id:
            return False
    return True


def _visibility_read_only(root: Path) -> bool:
    evidence = open_store(root / "evidence")
    ingress = CaptureIngress(root / "ci1")
    first = ingress.capture(_request("cap_cx_read_1", "one", ("session:read",), VisibilityScope.session_window), _policy("cp_cx_read"), evidence)
    second = ingress.capture(_request("cap_cx_read_2", "two", ("session:read",), VisibilityScope.session_window), _policy("cp_cx_read"), evidence)
    before = (_manifest(root / "evidence"), _manifest(root / "ci1"))
    visibility = CaptureVisibility(ingress.state_store, evidence)
    return (
        visibility.session_window_ids("session:read") == (first.shard_id, second.shard_id)
        and [shard.content for shard in visibility.session_window("session:read")] == ["one", "two"]
        and not any(hasattr(visibility, name) for name in ("list_all", "search", "rank", "recent_global"))
        and (_manifest(root / "evidence"), _manifest(root / "ci1")) == before
    )


def _formal_path_isolation(root: Path) -> bool:
    evidence = open_store(root / "evidence")
    receipt = CaptureIngress(root / "ci1").capture(_request("cap_cx_formal", "formal isolation", ("session:formal",), VisibilityScope.session_window), _policy("cp_cx_formal"), evidence)
    return (
        receipt.shard_id is not None
        and not _contains_forbidden_formal_tokens(root / "ci1")
        and not any((root / name).exists() for name in ("admission", "assembly", "recall", "integration", "field", "geometry"))
        and _capture_imports_do_not_cross_formal_paths()
    )


def _request(capture_id: str, content: str, refs: tuple[str, ...], scope: VisibilityScope):
    return __import__("nollm.dream_geometry.capture", fromlist=["CaptureRequest"]).CaptureRequest(
        capture_id,
        content,
        CaptureOrigin(OriginKind.user_utterance, "turn:cx", refs[0], "user"),
        "2026-07-02T12:34:56+08:00",
        refs,
        scope,
    )


def _policy(
    policy_id: str,
    *,
    persistence: CapturePersistence = CapturePersistence.captured,
    lineage: CaptureLineage = CaptureLineage.none,
    diagnostics: CaptureDiagnostics = CaptureDiagnostics.on_failure,
    allowed: tuple[VisibilityScope, ...] = (VisibilityScope.session_window,),
    promotion_mode: PromotionMode = PromotionMode.disabled,
) -> CapturePolicy:
    return CapturePolicy(
        policy_id,
        persistence=persistence,
        lineage=lineage,
        diagnostics=diagnostics,
        allowed_visibility_scopes=allowed,
        promotion_mode=promotion_mode,
    )


def _candidate_ids(root: Path) -> tuple[str, ...]:
    candidate_root = root / "candidates"
    if not candidate_root.exists():
        return ()
    return tuple(json.loads(path.read_text(encoding="utf-8"))["candidate_id"] for path in sorted(candidate_root.glob("*.json")))


def _manifest(root: Path) -> tuple[tuple[str, str], ...]:
    if not root.exists():
        return ()
    return tuple(sorted((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest()) for path in root.rglob("*") if path.is_file()))


def _contains_forbidden_formal_tokens(root: Path) -> bool:
    forbidden = ("GrowthProposal", "PlacementPlan", "AdmissionRecord", "FieldSnapshot", "RecallUniverse", "VerifiedChartLink")
    if not root.exists():
        return False
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.json"))
    return any(token in text for token in forbidden)


def _capture_imports_do_not_cross_formal_paths() -> bool:
    source = PY_ROOT / "nollm" / "dream_geometry" / "capture"
    forbidden_modules = {"admission", "geometry", "field", "assembly", "recall", "adapters"}
    for path in source.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name.startswith("nollm.dream_geometry." + module) for name in names for module in forbidden_modules):
                return False
    return True


def _fail(*_args, **_kwargs):
    raise RuntimeError("synthetic cx1 commit failure")


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
