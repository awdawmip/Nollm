from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = REPO_ROOT / "reference" / "python"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from nollm.dream_geometry.admission import AdmissionOutcome, AdmissionPlacementPlan, MemoryAdmissionOrchestrator  # noqa: E402
from nollm.dream_geometry.batch_admission import (  # noqa: E402
    BA1CommitInterrupted,
    BA1Rejection,
    BatchAdmissionCoordinator,
)
from tests.fixtures.ba1.fixture import build_ba1_environment, batch_request, tree_manifest  # noqa: E402


def build_report() -> str:
    with tempfile.TemporaryDirectory(prefix="nollm_ba1_") as tmp:
        root = Path(tmp)
        success = _success(root / "success")
        order = _order(root / "order")
        preflight = _preflight_zero_commit(root / "preflight")
        retry = _retry(root / "retry")
        interruption = _interruption(root / "interruption")
        isolation = _isolation(root / "isolation")
        boundary = _dependency_boundary()
    lines = [
        "# BA1 Batch Admission Coordinator Baseline Report",
        "",
        "- baseline_head: `1f5a66dcd639f944b1aa522a0e8ddb7a0ef3edec`",
        f"- validation_head: `{_git('rev-parse HEAD')}`",
        "- command: `python validation/ba1/run_ba1_batch_admission.py --output docs/validation/BA1_BATCH_ADMISSION_BASELINE_REPORT.md`",
        "- public_objects_used: `BatchAdmissionCoordinator`, `CaptureStateStore`, `MemorySubstrateStore`, `MemoryAdmissionOrchestrator`",
        "- formal_paths_called_by_BA1: `DA1 preflight`, `DA1 admit`",
        "",
        "## Evidence",
        "",
        f"- ba1_01_two_deferred_candidates: `{'pass' if success else 'fail'}`",
        f"- ba1_02_canonical_order: `{'pass' if order else 'fail'}`",
        f"- ba1_03_preflight_zero_commit: `{'pass' if preflight else 'fail'}`",
        f"- ba1_04_retry_reopen: `{'pass' if retry else 'fail'}`",
        f"- ba1_05_commit_interruption_recovery: `{'pass' if interruption else 'fail'}`",
        f"- ba1_06_candidate_state_isolation: `{'pass' if isolation else 'fail'}`",
        f"- ba1_07_dependency_boundary: `{'pass' if boundary else 'fail'}`",
        "",
        "## Acceptance Matrix",
        "",
        f"- BA1-01 independent deferred admission: `{'pass' if success else 'fail'}`",
        f"- BA1-02 input order determinism: `{'pass' if order else 'fail'}`",
        f"- BA1-03 all-member preflight rejects before DA1 commit: `{'pass' if preflight else 'fail'}`",
        f"- BA1-04 reopen retry via DA1 idempotency: `{'pass' if retry else 'fail'}`",
        f"- BA1-05 commit interruption reports completed members: `{'pass' if interruption else 'fail'}`",
        f"- BA1-06 no candidate mutation or evidence crossing: `{'pass' if isolation else 'fail'}`",
        f"- BA1-07 no direct forbidden dependencies or discovery: `{'pass' if boundary else 'fail'}`",
        "",
        "## Known Non-Goals",
        "",
        "BA1 does not select candidates, generate PromotionDecision values, generate GrowthProposal or PlacementPlan values, mutate CI1 candidate state, persist batch state, assemble FieldSnapshots, execute recall, scan global stores, run OpenClaw/CLI/runtime, use network/database/cache, or call LLM/NLP/embedding systems.",
    ]
    return "\n".join(lines) + "\n"


def _success(root: Path) -> bool:
    evidence, cortex, admission, _capture_state, coordinator, request = build_ba1_environment(root)
    before_capture = tree_manifest(root / "capture")
    receipt = coordinator.submit(request)
    for member_receipt in receipt.member_receipts:
        record = admission.get_admission_record(member_receipt.admission_receipt.admission_id)
        MemoryAdmissionOrchestrator(evidence, cortex, admission).replay_record(record)
    return (
        tuple(item.member_id for item in receipt.member_receipts) == ("bam_ba1_01", "bam_ba1_02")
        and all(item.admission_receipt.outcome is AdmissionOutcome.committed for item in receipt.member_receipts)
        and len(admission.records()) == 2
        and tree_manifest(root / "capture") == before_capture
        and not any((root / name).exists() for name in ("field", "recall", "assembly", "batch"))
    )


def _order(root: Path) -> bool:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(root)
    reversed_request = replace(request, members=tuple(reversed(request.members)))
    first = coordinator.submit(reversed_request)
    second = coordinator.submit(request)
    return (
        tuple(item.member_id for item in first.member_receipts) == ("bam_ba1_01", "bam_ba1_02")
        and first.request_fingerprint == second.request_fingerprint
        and all(item.admission_receipt.outcome is AdmissionOutcome.idempotent for item in second.member_receipts)
        and len(admission.records()) == 2
    )


def _preflight_zero_commit(root: Path) -> bool:
    _evidence, _cortex, admission, _capture_state, coordinator, request = build_ba1_environment(root)
    bad_members = list(request.members)
    bad_request = replace(
        bad_members[1].admission_request,
        placement_plan=AdmissionPlacementPlan("apl_ba1_bad", bad_members[1].admission_request.placement_plan.axis_placements[:1]),
    )
    bad_members[1] = replace(bad_members[1], admission_request=bad_request)
    before = {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")}
    try:
        coordinator.submit(batch_request(tuple(bad_members), member_shard_ids=request.window.member_shard_ids))
        return False
    except BA1Rejection:
        return len(admission.records()) == 0 and {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")} == before


def _retry(root: Path) -> bool:
    evidence, cortex, admission, capture_state, coordinator, request = build_ba1_environment(root)
    first = coordinator.submit(request)
    before = {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")}
    reopened = BatchAdmissionCoordinator(capture_state, evidence, MemoryAdmissionOrchestrator(evidence, cortex, admission))
    second = reopened.submit(request)
    return (
        all(item.admission_receipt.outcome is AdmissionOutcome.idempotent for item in second.member_receipts)
        and tuple(item.admission_receipt.projection_fingerprint for item in second.member_receipts)
        == tuple(item.admission_receipt.projection_fingerprint for item in first.member_receipts)
        and {name: tree_manifest(root / name) for name in ("evidence", "cortex", "admission", "capture")} == before
    )


def _interruption(root: Path) -> bool:
    evidence, cortex, admission, capture_state, coordinator, request = build_ba1_environment(root)
    original_put = admission.put_admission_record

    def fail_second(record):
        if record.admission_id == request.members[1].admission_request.admission_id:
            raise RuntimeError("synthetic BA1 second member failure")
        return original_put(record)

    admission.put_admission_record = fail_second  # type: ignore[method-assign]
    try:
        coordinator.submit(request)
        return False
    except BA1CommitInterrupted as exc:
        interrupted = exc
    admission.put_admission_record = original_put  # type: ignore[method-assign]
    retry = BatchAdmissionCoordinator(capture_state, evidence, MemoryAdmissionOrchestrator(evidence, cortex, admission)).submit(request)
    return (
        tuple(item.member_id for item in interrupted.completed_member_receipts) == ("bam_ba1_01",)
        and interrupted.failed_member_id == "bam_ba1_02"
        and tuple(item.admission_receipt.outcome for item in retry.member_receipts) == (AdmissionOutcome.idempotent, AdmissionOutcome.committed)
        and len(evidence.read_ledger()) == 2
    )


def _isolation(root: Path) -> bool:
    _evidence, _cortex, _admission, _capture_state, coordinator, request = build_ba1_environment(root)
    before_capture = tree_manifest(root / "capture")
    bad = replace(request.members[0], admission_request=replace(request.members[0].admission_request, dream_shard=request.members[1].admission_request.dream_shard))
    try:
        coordinator.preflight(batch_request((bad,), member_shard_ids=(request.members[0].admission_request.dream_shard.shard_id,)))
        return False
    except BA1Rejection:
        return tree_manifest(root / "capture") == before_capture


def _dependency_boundary() -> bool:
    source = PY_ROOT / "nollm" / "dream_geometry" / "batch_admission"
    forbidden_imports = {"cortex", "geometry", "field", "assembly", "recall", "adapters"}
    forbidden_tokens = ("glob(", "rglob(", ".records(", "FieldSnapshot", "RecallUniverse", "GrowthTrace", "CoarseCover", "GravitySnapshot", "datetime.now", "utcnow")
    for path in source.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            return False
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(name.startswith("nollm.dream_geometry." + module) for name in names for module in forbidden_imports):
                return False
    return True


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
