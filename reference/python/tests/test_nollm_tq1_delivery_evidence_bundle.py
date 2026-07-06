from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from subprocess_harness import run_subprocess


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
MATRIX_SCRIPT = REFERENCE_PYTHON / "scripts" / "run_nollm_test_matrix.py"
PACKAGE_SCRIPT = REFERENCE_PYTHON / "scripts" / "package_nollm_tq1_delivery_evidence.py"
ORIGINAL_TASK = "NOLLM_TQ1_C6_JUNIT_AND_FROZEN_INPUT_EVIDENCE_INTEGRITY_FINAL_CLOSURE_TASK_20260706.md"
AMENDMENT_TASK = "NOLLM_TQ1_C6_SINGLE_BUNDLE_DELIVERY_EVIDENCE_AMENDMENT_20260706.md"
C7R_TASK = "NOLLM_TQ1_C7R_CANONICAL_EVIDENCE_REPLAY_UNIFIED_ONE_HOUR_EXECUTION_FINAL_CLOSURE_TASK_20260706.md"


def test_tq1_c6b_builds_parentless_evidence_ref_with_present_fixture(tmp_path: Path) -> None:
    repo, receipts, worktrees, verify_log = _successful_matrix(tmp_path, fixture_present=True)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    governance = _governance_files(tmp_path)

    build = _package(
        [
            "build-ref",
            "--repo-root",
            str(repo),
            "--receipt-root",
            str(receipts),
            "--final-head",
            head,
            "--final-verify-log",
            str(verify_log),
            "--governance-file",
            str(governance[0]),
            "--governance-file",
            str(governance[1]),
            "--evidence-ref",
            evidence_ref,
        ],
        cwd=repo,
    )
    verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)

    assert build.returncode == 0, build.stderr
    assert verify.returncode == 0, verify.stderr
    evidence_commit = json.loads(build.stdout)["evidence_commit"]
    assert _git_out(repo, "rev-list", "--parents", "-n", "1", evidence_commit).strip() == evidence_commit
    tree = _git_out(repo, "ls-tree", "-r", "--name-only", evidence_ref)
    assert "receipt_root/receipts/s001.json" in tree
    assert "receipt_root/junit/s001.xml" in tree
    assert "receipt_root/inputs/runtime_fixture/seed.txt" in tree
    assert "receipt_root/inputs/runtime_fixture_manifest.json" in tree
    assert _git_out(repo, "rev-parse", "HEAD").strip() == head
    assert _git_out(repo, "status", "--short") == ""


def test_tq1_c6b_build_ref_rejects_tampered_junit_without_ref(tmp_path: Path) -> None:
    repo, receipts, _worktrees, verify_log = _successful_matrix(tmp_path, fixture_present=True)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    governance = _governance_files(tmp_path)
    (receipts / "junit" / "s001.xml").write_text('<testsuite tests="1"><testcase classname="x" name="tampered"/></testsuite>', encoding="utf-8")

    build = _package(
        [
            "build-ref",
            "--repo-root",
            str(repo),
            "--receipt-root",
            str(receipts),
            "--final-head",
            head,
            "--final-verify-log",
            str(verify_log),
            "--governance-file",
            str(governance[0]),
            "--governance-file",
            str(governance[1]),
            "--evidence-ref",
            evidence_ref,
        ],
        cwd=repo,
    )

    assert build.returncode != 0
    assert "junit_evidence_" in build.stderr
    assert _git(repo, "show-ref", "--verify", "--quiet", evidence_ref).returncode != 0


def test_tq1_c6b_single_bundle_fetch_verifies_code_and_evidence_ref(tmp_path: Path) -> None:
    repo, receipts, _worktrees, verify_log = _successful_matrix(tmp_path, fixture_present=True)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    governance = _governance_files(tmp_path)
    assert _build_ref(repo, receipts, verify_log, head, evidence_ref, governance).returncode == 0
    bundle = tmp_path / "delivery.bundle"
    _git_check(repo, "bundle", "create", str(bundle), "HEAD", evidence_ref)
    audit = tmp_path / "audit"
    audit.mkdir()
    _git_check(audit, "init")
    _git_check(audit, "fetch", str(bundle), "HEAD:refs/heads/code", f"{evidence_ref}:{evidence_ref}")

    assert _git_out(audit, "rev-parse", "refs/heads/code").strip() == head
    verify = _package(["verify-ref", "--repo-root", str(audit), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=audit)

    assert verify.returncode == 0, verify.stderr
    assert _git(audit, "fsck", "--full").returncode == 0


def test_tq1_c6b_verify_ref_rejects_missing_required_file(tmp_path: Path) -> None:
    repo, receipts, _worktrees, verify_log = _successful_matrix(tmp_path, fixture_present=False)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    governance = _governance_files(tmp_path)
    assert _build_ref(repo, receipts, verify_log, head, evidence_ref, governance).returncode == 0
    commit = _git_out(repo, "rev-parse", evidence_ref).strip()
    with _temporary_index(tmp_path) as index:
        env = {"GIT_INDEX_FILE": str(index)}
        _git_check(repo, "read-tree", commit, env=env)
        _git_check(repo, "rm", "--cached", "-q", "summary/FULL_MATRIX_OK.txt", env=env)
        tree = _git_out(repo, "write-tree", env=env).strip()
    bad_commit = _git_out(repo, "commit-tree", tree, input_text="bad capsule\n").strip()
    bad_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    _git_check(repo, "update-ref", bad_ref, bad_commit)

    verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", bad_ref, "--expected-head", head], cwd=repo)

    assert verify.returncode != 0
    assert "capsule_required_file_missing" in verify.stderr


def test_tq1_c6b_fixture_absent_capsule_verifies_without_present_manifest(tmp_path: Path) -> None:
    repo, receipts, _worktrees, verify_log = _successful_matrix(tmp_path, fixture_present=False)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c6/{head}"
    governance = _governance_files(tmp_path)
    assert _build_ref(repo, receipts, verify_log, head, evidence_ref, governance).returncode == 0
    verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)
    tree = _git_out(repo, "ls-tree", "-r", "--name-only", evidence_ref)

    assert verify.returncode == 0, verify.stderr
    assert "receipt_root/inputs/runtime_fixture_manifest.json" not in tree
    assert "runtime_fixture_tree_fingerprint=absent" in (receipts / "verify.txt").read_text(encoding="utf-8")


def test_tq1_c7r_verify_ref_replays_and_rejects_tampered_receipt(tmp_path: Path) -> None:
    repo, _receipts, _worktrees, _verify_log, evidence_ref = _build_c7r_capsule(tmp_path)
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    commit = _git_out(repo, "rev-parse", evidence_ref).strip()
    staging = tmp_path / "tampered-receipt"
    _materialize_tree(repo, commit, staging)
    receipt_path = staging / "receipt_root" / "receipts" / "s001.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["status"] = "failed"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    bad_commit = _commit_ref_payload(repo, staging, "tampered receipt")
    _git_check(repo, "update-ref", evidence_ref, bad_commit)

    verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)

    assert verify.returncode != 0
    assert "receipt_not_passed" in verify.stderr


def test_tq1_c7r_verify_ref_rejects_receipt_identity_timeout_cleanup_and_fixture_claims(tmp_path: Path) -> None:
    cases = [
        ("selected_node_ids", [], "selected_node_ids_mismatch"),
        ("timeout_seconds", 90.0, "timeout_contract_mismatch"),
        ("worktree_cleanup", "failed", "worktree_cleanup_failed"),
        ("fixture_copy_verified", False, "fixture_copy_not_verified"),
        ("shard_id", "s999", "shard_id_mismatch"),
    ]
    for key, value, reason in cases:
        case_root = tmp_path / key
        case_root.mkdir()
        repo, _receipts, _worktrees, _verify_log, evidence_ref = _build_c7r_capsule(case_root)
        head = _git_out(repo, "rev-parse", "HEAD").strip()
        commit = _git_out(repo, "rev-parse", evidence_ref).strip()
        staging = case_root / "tampered"
        _materialize_tree(repo, commit, staging)
        receipt_path = staging / "receipt_root" / "receipts" / "s001.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt[key] = value
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        bad_commit = _commit_ref_payload(repo, staging, f"tampered {key}")
        _git_check(repo, "update-ref", evidence_ref, bad_commit)

        verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)

        assert verify.returncode != 0
        assert reason in verify.stderr


def test_tq1_c7r_verify_ref_rejects_tampered_junit_fixture_summary_and_run_log(tmp_path: Path) -> None:
    cases = [
        ("junit", "junit_evidence_hash_mismatch"),
        ("fixture", "runtime_fixture_manifest_mismatch"),
        ("summary", "summary_evidence_mismatch"),
        ("runlog", "run_log_retry_present"),
    ]
    for kind, reason in cases:
        case_root = tmp_path / kind
        case_root.mkdir()
        repo, _receipts, _worktrees, _verify_log, evidence_ref = _build_c7r_capsule(case_root)
        head = _git_out(repo, "rev-parse", "HEAD").strip()
        commit = _git_out(repo, "rev-parse", evidence_ref).strip()
        staging = case_root / "tampered"
        _materialize_tree(repo, commit, staging)
        if kind == "junit":
            _write(staging / "receipt_root" / "junit" / "s001.xml", '<testsuite tests="1"><testcase classname="x" name="tampered"/></testsuite>')
        elif kind == "fixture":
            _write(staging / "receipt_root" / "inputs" / "runtime_fixture" / "seed.txt", "B")
        elif kind == "summary":
            summary_path = staging / "summary" / "FINAL_MATRIX_EVIDENCE.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["passed"] = 0
            summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        elif kind == "runlog":
            log_path = staging / "logs" / "06_matrix_run_all.txt"
            log_path.write_text(log_path.read_text(encoding="utf-8") + "\nretry forbidden text\n", encoding="utf-8")
        bad_commit = _commit_ref_payload(repo, staging, f"tampered {kind}")
        _git_check(repo, "update-ref", evidence_ref, bad_commit)

        verify = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)

        assert verify.returncode != 0
        assert reason in verify.stderr


def _successful_matrix(tmp_path: Path, *, fixture_present: bool) -> tuple[Path, Path, Path, Path]:
    files = {
        ".gitignore": "out/\n",
        "tests/test_alpha.py": "def test_a():\n    assert True\n",
    }
    if fixture_present:
        files["tests/test_runtime.py"] = "from pathlib import Path\n\ndef test_runtime_seed():\n    assert Path('out/nollm_runtime/seed.txt').read_text(encoding='utf-8') == 'A'\n"
    repo = _tiny_repo(tmp_path, files)
    if fixture_present:
        _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")
    receipts = tmp_path / ("receipts-present" if fixture_present else "receipts-absent")
    worktrees = tmp_path / ("worktrees-present" if fixture_present else "worktrees-absent")
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo).returncode == 0
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--all", "--workers", "1"], cwd=repo)
    assert run.returncode == 0, run.stderr
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)
    assert verify.returncode == 0, verify.stderr
    verify_log = receipts / "verify.txt"
    verify_log.write_text(verify.stdout + verify.stderr, encoding="utf-8")
    return repo, receipts, worktrees, verify_log


def _build_c7r_capsule(tmp_path: Path) -> tuple[Path, Path, Path, Path, str]:
    repo = _tiny_repo(
        tmp_path,
        {
            ".gitignore": "out/\n",
            "tests/test_runtime.py": "from pathlib import Path\n\ndef test_runtime_seed():\n    assert Path('out/nollm_runtime/seed.txt').read_text(encoding='utf-8') == 'A'\n",
        },
    )
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")
    receipts = tmp_path / "receipts-c7r"
    worktrees = tmp_path / "worktrees-c7r"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1", "--planned-shard-timeout-seconds", "3600"], cwd=repo).returncode == 0
    command_line = f"COMMAND {sys.executable} {MATRIX_SCRIPT} run-shard --repo-root {repo} --receipt-root {receipts} --worktree-root {worktrees} --all --workers 4 --timeout-seconds 3600\n"
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--all", "--workers", "4", "--timeout-seconds", "3600"], cwd=repo)
    assert run.returncode == 0, run.stderr
    run_log = receipts / "run_all.txt"
    run_log.write_text(command_line + run.stdout + run.stderr, encoding="utf-8")
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)
    assert verify.returncode == 0, verify.stderr
    verify_log = receipts / "verify.txt"
    verify_log.write_text(verify.stdout + verify.stderr, encoding="utf-8")
    head = _git_out(repo, "rev-parse", "HEAD").strip()
    evidence_ref = f"refs/nollm-delivery/tq1-c7r/{head}"
    governance = _governance_c7r_file(tmp_path)
    build = _package(
        [
            "build-ref",
            "--repo-root",
            str(repo),
            "--receipt-root",
            str(receipts),
            "--final-head",
            head,
            "--final-verify-log",
            str(verify_log),
            "--governance-file",
            str(governance),
            "--log",
            f"06_matrix_run_all.txt={run_log}",
            "--evidence-ref",
            evidence_ref,
        ],
        cwd=repo,
    )
    assert build.returncode == 0, build.stderr
    verify_ref = _package(["verify-ref", "--repo-root", str(repo), "--evidence-ref", evidence_ref, "--expected-head", head], cwd=repo)
    assert verify_ref.returncode == 0, verify_ref.stderr
    return repo, receipts, worktrees, verify_log, evidence_ref


def _build_ref(repo: Path, receipts: Path, verify_log: Path, head: str, evidence_ref: str, governance: tuple[Path, Path]):
    return _package(
        [
            "build-ref",
            "--repo-root",
            str(repo),
            "--receipt-root",
            str(receipts),
            "--final-head",
            head,
            "--final-verify-log",
            str(verify_log),
            "--governance-file",
            str(governance[0]),
            "--governance-file",
            str(governance[1]),
            "--evidence-ref",
            evidence_ref,
        ],
        cwd=repo,
    )


def _package(args: list[str], *, cwd: Path):
    return run_subprocess([sys.executable, str(PACKAGE_SCRIPT), *args], cwd=cwd, timeout_seconds=90)


def _matrix(args: list[str], *, cwd: Path):
    return run_subprocess([sys.executable, str(MATRIX_SCRIPT), *args], cwd=cwd, timeout_seconds=90)


def _governance_files(tmp_path: Path) -> tuple[Path, Path]:
    original = tmp_path / ORIGINAL_TASK
    amendment = tmp_path / AMENDMENT_TASK
    original.write_text("# original C6 task\n", encoding="utf-8")
    amendment.write_text("# amendment C6 task\n", encoding="utf-8")
    return original, amendment


def _governance_c7r_file(tmp_path: Path) -> Path:
    task = tmp_path / C7R_TASK
    task.write_text("# C7R task\n", encoding="utf-8")
    return task


def _materialize_tree(repo: Path, commit: str, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    names = _git_out(repo, "ls-tree", "-r", "-z", "--name-only", commit).split("\0")
    for name in [item for item in names if item]:
        data = subprocess.run(["git", "cat-file", "-p", f"{commit}:{name}"], cwd=repo, capture_output=True, timeout=60)
        assert data.returncode == 0, data.stderr.decode("utf-8", errors="replace")
        path = target / Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data.stdout)


def _commit_ref_payload(repo: Path, staging: Path, message: str) -> str:
    _refresh_payload_inventory_and_manifest(staging)
    git_dir = _git_out(repo, "rev-parse", "--git-dir").strip()
    with _temporary_index(staging.parent) as index:
        env = {"GIT_INDEX_FILE": str(index)}
        _git_check(repo, "-c", "core.autocrlf=false", "--git-dir", git_dir, "--work-tree", str(staging), "add", "-A", env=env)
        tree = _git_out(repo, "-c", "core.autocrlf=false", "--git-dir", git_dir, "--work-tree", str(staging), "write-tree", env=env).strip()
    return _git_out(repo, "commit-tree", tree, input_text=message + "\n").strip()


def _refresh_payload_inventory_and_manifest(staging: Path) -> None:
    import hashlib

    files = []
    for path in sorted(staging.rglob("*")):
        if path.is_file():
            relative = path.relative_to(staging).as_posix()
            if relative in {"CAPSULE_MANIFEST.json", "PAYLOAD_INVENTORY.json"}:
                continue
            data = path.read_bytes()
            files.append({"path": relative, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    inventory_path = staging / "PAYLOAD_INVENTORY.json"
    inventory_path.write_text(json.dumps({"schema": "nollm.tq1.delivery-evidence-payload-inventory.v1", "files": files}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = staging / "CAPSULE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["payload_inventory_sha256"] = hashlib.sha256(inventory_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _temporary_index(tmp_path: Path):
    class TemporaryIndex:
        def __enter__(self):
            self.path = tmp_path / "temp.index"
            if self.path.exists():
                self.path.unlink()
            return self.path

        def __exit__(self, exc_type, exc, tb):
            if self.path.exists():
                self.path.unlink()

    return TemporaryIndex()


def _tiny_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_check(repo, "init")
    _git_check(repo, "config", "user.email", "tq1@example.invalid")
    _git_check(repo, "config", "user.name", "TQ1")
    for relative, text in files.items():
        _write(repo / relative, text)
    _git_check(repo, "add", ".")
    _git_check(repo, "commit", "-m", "initial")
    return repo


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo: Path, *args: str, env: dict[str, str] | None = None, input_text: str | None = None):
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, env=full_env, input=input_text, timeout=60)


def _git_check(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    result = _git(repo, *args, env=env)
    assert result.returncode == 0, result.stderr


def _git_out(repo: Path, *args: str, env: dict[str, str] | None = None, input_text: str | None = None) -> str:
    result = _git(repo, *args, env=env, input_text=input_text)
    assert result.returncode == 0, result.stderr
    return result.stdout
