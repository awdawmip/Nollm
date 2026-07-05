from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

from subprocess_harness import run_subprocess


ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PYTHON = ROOT / "reference" / "python"
SCRIPT = REFERENCE_PYTHON / "scripts" / "run_nollm_test_matrix.py"


def load_matrix():
    spec = importlib.util.spec_from_file_location("run_nollm_test_matrix", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tq1_plan_is_deterministic_for_tiny_git_repo(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"

    first = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo)
    first_bytes = (receipts / "matrix_plan.json").read_bytes()
    second = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo)
    second_bytes = (receipts / "matrix_plan.json").read_bytes()

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first_bytes == second_bytes
    plan = json.loads(first_bytes)
    assert plan["schema"] == "nollm.test_matrix.v1"
    assert plan["collected_count"] == 1


def test_tq1_manifest_assignment_has_no_missing_or_duplicate_nodes() -> None:
    matrix = load_matrix()
    nodes = [
        "tests/test_a.py::test_1",
        "tests/test_a.py::test_2",
        "tests/test_b.py::test_1",
        "tests/test_c.py::test_1",
    ]
    shards = matrix.assign_shards(nodes, target_node_count=2, max_shards=24)
    flattened = [node for shard in shards for node in shard["node_ids"]]

    assert flattened == nodes
    assert len(flattened) == len(set(flattened))
    assert len(shards) >= 2


def test_tq1_large_file_splits_by_contiguous_node_segments() -> None:
    matrix = load_matrix()
    nodes = [f"tests/test_big.py::test_{index}" for index in range(5)]
    shards = matrix.assign_shards(nodes, target_node_count=2, max_shards=24)

    assert [shard["node_ids"] for shard in shards] == [nodes[0:2], nodes[2:4], nodes[4:5]]


def test_tq1_assign_shards_uses_max_shards_for_large_matrix() -> None:
    matrix = load_matrix()
    nodes = [f"tests/test_{index // 4:03d}.py::test_{index}" for index in range(48)]

    shards = matrix.assign_shards(nodes, target_node_count=12, max_shards=8)

    assert len(shards) == 8
    assert [node for shard in shards for node in shard["node_ids"]] == nodes


def test_tq1_run_shard_rejects_head_drift(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    _write(repo / "tests" / "test_beta.py", "def test_b():\n    assert True\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "add beta")

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)

    assert result.returncode != 0
    assert "source_drift" in result.stderr


def test_tq1_run_shard_rejects_status_drift(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    _write(repo / "dirty.txt", "dirty\n")

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)

    assert result.returncode != 0
    assert "source_drift" in result.stderr


def test_tq1_success_receipt_verifies_and_leaves_source_clean(tmp_path: Path) -> None:
    repo = _tiny_repo(
        tmp_path,
        {
            "tests/test_alpha.py": "def test_a():\n    assert True\n",
            "tests/test_beta.py": "def test_b():\n    assert True\n",
        },
    )
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"

    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo).returncode == 0
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--all", "--workers", "1"], cwd=repo)
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert run.returncode == 0, run.stderr
    assert verify.returncode == 0, verify.stderr
    assert "FULL_MATRIX_OK" in verify.stdout
    assert _git_out(repo, "status", "--short") == ""
    assert not any(worktrees.iterdir()) if worktrees.exists() else True


def test_tq1_verify_rejects_collection_drift_by_fingerprint() -> None:
    matrix = load_matrix()
    plan = {"collection_fingerprint": matrix.fingerprint(["tests/test_a.py::test_a"])}

    try:
        matrix.assert_collection_matches(plan, ["tests/test_a.py::test_a", "tests/test_b.py::test_b"])
    except Exception as exc:
        assert exc.payload["reason"] == "collection_drift"
    else:
        raise AssertionError("collection drift was accepted")


def test_tq1_verify_rejects_bad_receipt_states(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    shard = plan["shards"][0]
    receipt = {
        "schema": "nollm.test_matrix.shard_receipt.v1",
        "status": "timed_out",
        "shard_id": shard["shard_id"],
        "git_head": plan["git_head"],
        "collection_fingerprint": plan["collection_fingerprint"],
        "manifest_fingerprint": plan["manifest_fingerprint"],
        "selection_fingerprint": shard["selection_fingerprint"],
        "selected_node_ids": shard["node_ids"],
        "junit_tests": len(shard["node_ids"]),
        "timed_out": True,
        "worktree_cleanup": "removed",
    }
    receipt_dir = receipts / "receipts"
    receipt_dir.mkdir()
    (receipt_dir / f"{shard['shard_id']}.json").write_text(json.dumps(receipt), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "verify_failed" in result.stderr


def test_tq1_junit_count_mismatch_is_not_success(tmp_path: Path) -> None:
    matrix = load_matrix()
    plan = {
        "git_head": "abc",
        "collection_fingerprint": "sha256:c",
        "manifest_fingerprint": "sha256:m",
    }
    shard = {
        "selection_fingerprint": "sha256:s",
        "node_ids": ["tests/test_a.py::test_a", "tests/test_a.py::test_b"],
    }
    receipt = {
        "status": "passed",
        "git_head": "abc",
        "collection_fingerprint": "sha256:c",
        "manifest_fingerprint": "sha256:m",
        "selection_fingerprint": "sha256:s",
        "selected_node_ids": shard["node_ids"],
        "junit_tests": 1,
        "timed_out": False,
        "worktree_cleanup": "removed",
    }

    assert matrix.validate_success_receipt(plan, shard, receipt) == "junit_count_mismatch"


def test_tq1_timeout_writes_readable_receipt_and_cleans_worktree(tmp_path: Path) -> None:
    repo = _tiny_repo(
        tmp_path,
        {"tests/test_slow.py": "import time\n\ndef test_slow():\n    time.sleep(5)\n"},
    )
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001", "--timeout-seconds", "0.1"], cwd=repo, timeout_seconds=30)
    receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))

    assert result.returncode != 0
    assert receipt["status"] == "timed_out"
    assert receipt["timed_out"] is True
    assert receipt["selected_count"] == 1
    assert receipt["worktree_cleanup"] == "removed"


def test_tq1_resume_reuses_exact_success_receipt(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    first = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)
    before = (receipts / "receipts" / "s001.json").read_text(encoding="utf-8")
    second = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001", "--resume"], cwd=repo)
    after = (receipts / "receipts" / "s001.json").read_text(encoding="utf-8")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert before == after


def test_tq1_powershell_wrapper_uses_external_defaults() -> None:
    wrapper = ROOT / "tools" / "run_nollm_test_matrix.ps1"
    if not wrapper.exists():
        return
    text = wrapper.read_text(encoding="utf-8")
    assert "C:\\Users\\chaos" in text
    assert "run_nollm_test_matrix.py plan" in text
    assert "run_nollm_test_matrix.py run-shard" in text
    assert "run_nollm_test_matrix.py verify" in text
    assert "run_tests.py" not in text
    assert "repo/out" not in text


def test_tq1_runner_does_not_replace_legacy_run_tests_gate() -> None:
    run_tests = (REFERENCE_PYTHON / "run_tests.py").read_text(encoding="utf-8")
    matrix = SCRIPT.read_text(encoding="utf-8")

    assert 'pytest_main(["-q"])' in run_tests
    assert "run_tests.py" not in matrix


def test_tq1_delivery_bundle_convention_is_documented() -> None:
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    docs = ROOT / "docs" / "testing" / "NOLLM_BOUNDED_COMPLETE_TEST_MATRIX.md"
    if not docs.exists():
        return
    rendered = agents + "\n" + docs.read_text(encoding="utf-8")

    assert "C:\\Users\\chaos\\<bundle-name>.bundle" in rendered
    assert "Do not place delivery bundles inside the repository or under repo/out" in rendered


def test_tq1_worktree_mirror_preserves_source_checkout_bytes(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = tmp_path / "repo"
    worktree = tmp_path / "worktree"
    source = repo / "docs" / "signed.md"
    target = worktree / "docs" / "signed.md"
    source.parent.mkdir(parents=True)
    target.parent.mkdir(parents=True)
    source.write_bytes(b"line one\r\nline two\r\n")
    target.write_bytes(b"line one\nline two\n")

    monkeypatch.setattr(matrix, "tracked_file_paths", lambda repo_root: ["docs/signed.md"])

    result = matrix.mirror_source_checkout_bytes(repo, worktree)

    assert result == {"copied_count": 1, "paths": ["docs/signed.md"]}
    assert target.read_bytes() == source.read_bytes()


def _matrix(args: list[str], *, cwd: Path, timeout_seconds: int = 60):
    return run_subprocess([sys.executable, str(SCRIPT), *args], cwd=cwd, timeout_seconds=timeout_seconds)


def _tiny_repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "tq1@example.invalid")
    _git(repo, "config", "user.name", "TQ1")
    for relative, text in files.items():
        _write(repo / relative, text)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "initial")
    return repo


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(repo: Path, *args: str) -> None:
    subprocess.check_call(["git", *args], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _git_out(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True)
