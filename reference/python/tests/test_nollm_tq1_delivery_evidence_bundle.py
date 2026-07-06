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
