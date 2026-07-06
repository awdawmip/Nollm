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
    first_receipts = tmp_path / "receipts-a"
    second_receipts = tmp_path / "receipts-b"

    first = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(first_receipts), "--target-node-count", "1"], cwd=repo)
    first_bytes = (first_receipts / "matrix_plan.json").read_bytes()
    second = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(second_receipts), "--target-node-count", "1"], cwd=repo)
    second_bytes = (second_receipts / "matrix_plan.json").read_bytes()

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first_bytes == second_bytes
    plan = json.loads(first_bytes)
    assert plan["schema"] == "nollm.test_matrix.v1"
    assert plan["collected_count"] == 1
    assert plan["clean_status_before"] == ""
    assert plan["execution_contract"] == {
        "schema": "nollm.test_matrix.execution_contract.v1",
        "planned_shard_timeout_seconds": 90.0,
        "retry_policy": "forbidden",
        "receipt_overwrite": "forbidden",
        "execution_mode": "single_pass",
    }


def test_tq1_c7r_plan_can_freeze_one_hour_execution_contract(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"

    result = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1", "--planned-shard-timeout-seconds", "3600"], cwd=repo)
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr
    assert plan["execution_contract"] == {
        "schema": "nollm.test_matrix.execution_contract.v1",
        "planned_shard_timeout_seconds": 3600.0,
        "retry_policy": "forbidden",
        "receipt_overwrite": "forbidden",
        "execution_mode": "single_pass",
    }


def test_tq1_c4_plan_refuses_existing_receipt_root_without_overwrite(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    first = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo)
    before = {
        "plan": (receipts / "matrix_plan.json").read_bytes(),
        "marker": (receipts / ".nollm_test_matrix_root.json").read_bytes(),
    }

    second = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo)

    assert first.returncode == 0, first.stderr
    assert second.returncode != 0
    assert "receipt_root_exists" in second.stderr
    assert (receipts / "matrix_plan.json").read_bytes() == before["plan"]
    assert (receipts / ".nollm_test_matrix_root.json").read_bytes() == before["marker"]


def test_tq1_plan_rejects_dirty_source_without_receipt_root(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    _write(repo / "tests" / "test_alpha.py", "def test_a():\n    assert False\n")

    result = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo)

    assert result.returncode != 0
    assert "source_not_clean" in result.stderr
    assert not receipts.exists()


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
    assert not any(_matrix_root(worktrees, receipts).glob("s*"))
    receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))
    assert "source_checkout_mirror" not in receipt
    assert receipt["worktree_created_by_this_call"] is True
    assert receipt["worktree_add_succeeded"] is True
    assert receipt["worktree_marker_written"] is True
    assert receipt["failure_stage"] is None
    assert receipt["receipt_persisted"] is True
    assert receipt["runtime_fixture_state"] == "absent"
    assert receipt["fixture_copy_verified"] is True
    assert "runtime_fixture_tree_fingerprint=absent" in verify.stdout
    assert "receipt_json_count=2" in verify.stdout
    assert "junit_xml_count=2" in verify.stdout
    assert receipt["junit_relative_path"] == "junit/s001.xml"
    assert isinstance(receipt["junit_sha256"], str)
    assert len(receipt["junit_sha256"]) == 64
    assert receipt["junit_size_bytes"] > 0


def test_tq1_c4_cleanup_return_failure_makes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text('<testsuite tests="1"><testcase classname="tests.test_alpha" name="test_a"/></testsuite>', encoding="utf-8")
        return 0, False

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    monkeypatch.setattr(matrix, "remove_worktree", lambda repo_root, worktree: "failed")

    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    try:
        assert receipt["status"] == "failed"
        assert receipt["reason"] == "cleanup_failed"
        assert receipt["primary_reason"] == "cleanup_failed"
        assert receipt["failure_stage"] == "cleanup"
        assert receipt["returncode"] != 0
        assert receipt["worktree_cleanup"] == "failed"
        assert receipt["worktree_cleanup_error"] == "cleanup_failed"
        _assert_failure_receipt_contract(receipt)
        assert matrix.validate_success_receipt(plan, plan["shards"][0], receipt) == "status_failed"
    finally:
        _git(repo, "worktree", "remove", "--force", receipt["worktree_path"])


def test_tq1_c4_cleanup_oserror_writes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text('<testsuite tests="1"><testcase classname="tests.test_alpha" name="test_a"/></testsuite>', encoding="utf-8")
        return 0, False

    def fail_remove(repo_root, worktree):
        raise OSError("remove failed")

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    monkeypatch.setattr(matrix, "remove_worktree", fail_remove)

    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    try:
        assert receipt["status"] == "failed"
        assert receipt["reason"] == "cleanup_failed"
        assert receipt["failure_stage"] == "cleanup"
        assert receipt["worktree_cleanup"] == "failed"
        assert receipt["worktree_cleanup_error"] == "cleanup_failed"
        assert (receipts / "receipts" / "s001.json").exists()
        _assert_failure_receipt_contract(receipt)
    finally:
        _git(repo, "worktree", "remove", "--force", receipt["worktree_path"])


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
    assert _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", shard["shard_id"]], cwd=repo).returncode == 0
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
        "shard_id": "s001",
        "selection_fingerprint": "sha256:s",
        "node_ids": ["tests/test_a.py::test_a", "tests/test_a.py::test_b"],
    }
    receipt = {
        "schema": "nollm.test_matrix.shard_receipt.v1",
        "status": "passed",
        "shard_id": "s001",
        "git_head": "abc",
        "collection_fingerprint": "sha256:c",
        "manifest_fingerprint": "sha256:m",
        "selection_fingerprint": "sha256:s",
        "selected_node_ids": shard["node_ids"],
        "selected_count": len(shard["node_ids"]),
        "junit_relative_path": "junit/s001.xml",
        "junit_sha256": "0" * 64,
        "junit_size_bytes": 1,
        "junit_tests": 1,
        "junit_reported_tests": 1,
        "timed_out": False,
        "worktree_cleanup": "removed",
    }

    assert matrix.validate_success_receipt(plan, shard, receipt) == "junit_count_mismatch"


def test_tq1_c3_actual_junit_count_mismatch_writes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text(
            '<testsuite tests="2"><testcase classname="tests.test_alpha" name="test_a"/>'
            '<testcase classname="tests.test_alpha" name="test_b"/></testsuite>',
            encoding="utf-8",
        )
        return 0, False

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "junit_count_mismatch"
    assert receipt["failure_stage"] == "junit_parse"
    assert receipt["junit_tests"] == 2
    assert receipt["junit_reported_tests"] == 2
    assert matrix.validate_success_receipt(plan, plan["shards"][0], receipt) == "status_failed"


def test_tq1_c3_fixture_copy_error_writes_receipt_and_cleans_owned_worktree(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_copy(receipt_root, worktree, plan):
        raise OSError("copy failed")

    monkeypatch.setattr(matrix, "copy_runtime_fixture_snapshot", fail_copy)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "fixture_snapshot_copy_failed"
    assert receipt["failure_stage"] == "fixture_snapshot_copy"
    assert receipt["worktree_cleanup"] == "removed"
    assert (receipts / "receipts" / "s001.json").exists()
    _assert_failure_receipt_contract(receipt)


def test_tq1_c3_pytest_start_error_writes_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_start(*args, **kwargs):
        raise OSError("pytest start failed")

    monkeypatch.setattr(matrix, "run_process", fail_start)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "pytest_start_failed"
    assert receipt["failure_stage"] == "pytest_start"
    assert (receipts / "receipts" / "s001.json").exists()
    _assert_failure_receipt_contract(receipt)


def test_tq1_c3_malformed_junit_writes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text('<testsuite tests="not-an-int"></testsuite>', encoding="utf-8")
        return 0, False

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "junit_missing_or_malformed"
    assert receipt["failure_stage"] == "junit_parse"
    assert receipt["junit_tests"] is None
    assert (receipts / "receipts" / "s001.json").exists()
    _assert_failure_receipt_contract(receipt)


def test_tq1_c5_missing_tests_attribute_writes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text('<testsuite><testcase classname="x" name="y"/></testsuite>', encoding="utf-8")
        return 0, False

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "junit_missing_or_malformed"
    assert receipt["failure_stage"] == "junit_parse"
    assert receipt["returncode"] != 0
    assert receipt["junit_tests"] is None
    assert receipt["worktree_cleanup"] == "removed"
    assert (receipts / "receipts" / "s001.json").exists()


def test_tq1_c5_nested_invalid_tests_attribute_writes_failed_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fake_run_process(command, *, cwd, env, timeout_seconds, stdout_path, stderr_path):
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        Path(command[5]).write_text('<testsuites><testsuite tests="bad"><testcase classname="x" name="y"/></testsuite></testsuites>', encoding="utf-8")
        return 0, False

    monkeypatch.setattr(matrix, "run_process", fake_run_process)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "junit_missing_or_malformed"
    assert receipt["failure_stage"] == "junit_parse"
    assert receipt["returncode"] != 0
    assert (receipts / "receipts" / "s001.json").exists()


def test_tq1_c5_add_worktree_oserror_uses_stage_reason(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_add(repo_root, worktree, head):
        raise OSError("plain add failure")

    monkeypatch.setattr(matrix, "add_worktree", fail_add)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 1.0, False)

    assert receipt["status"] == "failed"
    assert receipt["failure_stage"] == "worktree_add"
    assert receipt["reason"] == "worktree_add_failed"
    assert receipt["reason"] != "pytest_start_failed"
    assert receipt["worktree_add_succeeded"] is False
    assert receipt["worktree_cleanup"] == "not_started"


def test_tq1_c5_verify_rejects_tampered_receipt_schema(tmp_path: Path) -> None:
    matrix, repo, receipts, worktrees, plan, shard, receipt_path = _successful_single_shard_matrix(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["schema"] = "other"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert matrix.validate_success_receipt(plan, shard, receipt) == "receipt_schema_mismatch"
    assert result.returncode != 0
    assert "receipt_schema_mismatch" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c5_verify_rejects_tampered_receipt_shard_identity(tmp_path: Path) -> None:
    matrix, repo, receipts, worktrees, plan, shard, receipt_path = _successful_single_shard_matrix(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["shard_id"] = "not-s001"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert matrix.validate_success_receipt(plan, shard, receipt) == "receipt_identity_mismatch"
    assert result.returncode != 0
    assert "receipt_identity_mismatch" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c5_verify_rejects_extra_receipt_json_without_deleting(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    extra = receipts / "receipts" / "s999.json"
    extra.write_text("{}", encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "extra_receipt_entries" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout
    assert extra.exists()


def test_tq1_c5_verify_rejects_extra_receipt_directory_and_non_json_without_deleting(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    extra_dir = receipts / "receipts" / "extra_dir"
    extra_file = receipts / "receipts" / "notes.txt"
    extra_dir.mkdir()
    extra_file.write_text("not a receipt\n", encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "extra_receipt_entries" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout
    assert extra_dir.exists()
    assert extra_file.exists()


def test_tq1_c6_verify_rejects_missing_junit_evidence(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    junit = receipts / "junit" / "s001.xml"
    junit.unlink()

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "junit_missing" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout
    assert not junit.exists()


def test_tq1_c6_verify_rejects_junit_content_hash_or_size_mismatch(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    junit = receipts / "junit" / "s001.xml"
    junit.write_text('<testsuite tests="1"><testcase classname="x" name="changed"/></testsuite>', encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "junit_evidence_" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c6_verify_rejects_malformed_junit_evidence_without_raw_escape(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    receipt_path = receipts / "receipts" / "s001.json"
    junit = receipts / "junit" / "s001.xml"
    junit.write_text("<testsuite><testcase classname='x' name='y'/></testsuite>", encoding="utf-8")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["junit_sha256"] = _sha256(junit)
    receipt["junit_size_bytes"] = junit.stat().st_size
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "junit_evidence_malformed" in result.stderr
    assert "KeyError" not in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c6_verify_rejects_extra_junit_entries_without_deleting(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)
    extra_xml = receipts / "junit" / "s999.xml"
    extra_txt = receipts / "junit" / "notes.txt"
    extra_dir = receipts / "junit" / "extra_dir"
    extra_xml.write_text("<testsuite tests='0'></testsuite>", encoding="utf-8")
    extra_txt.write_text("not junit\n", encoding="utf-8")
    extra_dir.mkdir()

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "extra_junit_entries" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout
    assert extra_xml.exists()
    assert extra_txt.exists()
    assert extra_dir.exists()


def test_tq1_c6_success_receipt_junit_evidence_tampering_is_rejected(tmp_path: Path) -> None:
    matrix, repo, receipts, worktrees, plan, shard, receipt_path = _successful_single_shard_matrix(tmp_path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["junit_relative_path"] = "junit/not-s001.xml"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert matrix.validate_success_receipt(plan, shard, receipt) == "junit_evidence_path_mismatch"
    assert result.returncode != 0
    assert "junit_evidence_path_mismatch" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c6_verify_rejects_missing_runtime_fixture_manifest(tmp_path: Path) -> None:
    repo, receipts, worktrees = _successful_fixture_present_matrix(tmp_path)
    manifest = receipts / "inputs" / "runtime_fixture_manifest.json"
    manifest.unlink()

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "runtime_fixture_manifest_missing" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c6_verify_rejects_runtime_fixture_manifest_mismatch(tmp_path: Path) -> None:
    repo, receipts, worktrees = _successful_fixture_present_matrix(tmp_path)
    manifest = receipts / "inputs" / "runtime_fixture_manifest.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["files"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    result = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "runtime_fixture_manifest_mismatch" in result.stderr
    assert "FULL_MATRIX_OK" not in result.stdout


def test_tq1_c6_fixture_present_success_verifies_junit_and_manifest(tmp_path: Path) -> None:
    repo, receipts, worktrees = _successful_fixture_present_matrix(tmp_path)

    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)
    receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))

    assert verify.returncode == 0, verify.stderr
    assert "FULL_MATRIX_OK" in verify.stdout
    assert "junit_xml_count=1" in verify.stdout
    assert "runtime_fixture_tree_fingerprint=sha256:" in verify.stdout
    assert receipt["junit_sha256"] == _sha256(receipts / "junit" / "s001.xml")


def test_tq1_c6_fixture_absent_success_does_not_require_present_manifest(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, _receipt_path = _successful_single_shard_matrix(tmp_path)

    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert verify.returncode == 0, verify.stderr
    assert "runtime_fixture_tree_fingerprint=absent" in verify.stdout
    assert not (receipts / "inputs" / "runtime_fixture_manifest.json").exists()


def test_tq1_c4_marker_write_failure_records_add_and_cleanup(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_marker(worktree, receipt_root, plan, shard):
        raise matrix.MatrixError("worktree_marker_write_failed", "marker write failed")

    monkeypatch.setattr(matrix, "write_shard_worktree_marker", fail_marker)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "worktree_marker_write_failed"
    assert receipt["failure_stage"] == "worktree_marker_write"
    assert receipt["worktree_add_succeeded"] is True
    assert receipt["worktree_marker_written"] is False
    assert receipt["worktree_created_by_this_call"] is False
    assert receipt["worktree_cleanup"] == "removed"
    assert not Path(receipt["worktree_path"]).exists()
    _assert_failure_receipt_contract(receipt)


def test_tq1_plan_owned_runtime_snapshot_ignores_later_source_changes(tmp_path: Path) -> None:
    repo = _tiny_repo(
        tmp_path,
        {
            ".gitignore": "out/\n",
            "tests/test_runtime.py": "from pathlib import Path\n\ndef test_runtime_seed():\n    assert Path('out/nollm_runtime/seed.txt').read_text(encoding='utf-8') == 'A'\n",
        },
    )
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")

    plan = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo)
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "B")
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)

    assert plan.returncode == 0, plan.stderr
    assert run.returncode == 0, run.stderr
    plan_data = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))
    assert plan_data["runtime_fixture"]["state"] == "present"
    assert receipt["runtime_fixture_state"] == "present"
    assert receipt["runtime_fixture_manifest_fingerprint"] == plan_data["runtime_fixture"]["manifest_fingerprint"]


def test_tq1_verify_rejects_runtime_snapshot_drift(tmp_path: Path) -> None:
    repo = _tiny_repo(
        tmp_path,
        {
            ".gitignore": "out/\n",
            "tests/test_runtime.py": "from pathlib import Path\n\ndef test_runtime_seed():\n    assert Path('out/nollm_runtime/seed.txt').read_text(encoding='utf-8') == 'A'\n",
        },
    )
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo).returncode == 0
    assert _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo).returncode == 0
    _write(receipts / "inputs" / "runtime_fixture" / "seed.txt", "B")

    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert verify.returncode != 0
    assert "fixture_snapshot_drift" in verify.stderr


def test_tq1_c3_runtime_snapshot_drift_writes_receipt_before_pytest(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(
        tmp_path,
        {
            ".gitignore": "out/\n",
            "tests/test_runtime.py": "def test_runtime():\n    assert True\n",
        },
    )
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    _write(receipts / "inputs" / "runtime_fixture" / "seed.txt", "B")
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_if_started(*args, **kwargs):
        raise AssertionError("pytest must not start after fixture drift")

    monkeypatch.setattr(matrix, "run_process", fail_if_started)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 10.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "fixture_snapshot_drift"
    assert receipt["failure_stage"] == "fixture_snapshot_copy"
    assert receipt["fixture_copy_verified"] is False


def test_tq1_absent_runtime_fixture_state_is_stable(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"

    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo).returncode == 0
    assert _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo).returncode == 0
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert verify.returncode == 0, verify.stderr
    assert "runtime_fixture_tree_fingerprint=absent" in verify.stdout


def test_tq1_runtime_fixture_symlink_is_rejected_without_plan(tmp_path: Path) -> None:
    if not hasattr(Path, "symlink_to"):
        return
    repo = _tiny_repo(tmp_path, {".gitignore": "out/\n", "tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    fixture = repo / "out" / "nollm_runtime"
    fixture.mkdir(parents=True)
    target = fixture / "target.txt"
    target.write_text("A", encoding="utf-8")
    try:
        (fixture / "link.txt").symlink_to(target)
    except OSError:
        return

    result = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo)

    assert result.returncode != 0
    assert "fixture_snapshot_rejected" in result.stderr
    assert not receipts.exists()


def test_tq1_c7r_runtime_fixture_forbidden_dev_path_is_rejected_without_plan(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {".gitignore": "out/\n", "tests/test_alpha.py": "def test_a():\n    assert True\n"})
    _write(repo / "out" / "nollm_runtime" / "workspace" / ".git" / "config", "[core]\n")
    receipts = tmp_path / "receipts"

    result = _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo)

    assert result.returncode != 0
    assert "fixture_snapshot_rejected" in result.stderr
    assert not receipts.exists()


def test_tq1_timeout_writes_readable_receipt_and_cleans_worktree(tmp_path: Path) -> None:
    repo = _tiny_repo(
        tmp_path,
        {"tests/test_slow.py": "import time\n\ndef test_slow():\n    time.sleep(5)\n"},
    )
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--planned-shard-timeout-seconds", "0.1"], cwd=repo).returncode == 0

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001", "--timeout-seconds", "0.1"], cwd=repo, timeout_seconds=30)
    receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))

    assert result.returncode != 0
    assert receipt["status"] == "timed_out"
    assert receipt["timed_out"] is True
    assert receipt["selected_count"] == 1
    assert receipt["worktree_cleanup"] == "removed"


def test_tq1_c7r_run_rejects_timeout_contract_mismatch_without_receipt(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--planned-shard-timeout-seconds", "3600"], cwd=repo).returncode == 0

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001", "--timeout-seconds", "90"], cwd=repo)

    assert result.returncode != 0
    assert "execution_contract_timeout_mismatch" in result.stderr
    assert not (receipts / "receipts" / "s001.json").exists()


def test_tq1_c7r_verify_rejects_success_receipt_timeout_drift(tmp_path: Path) -> None:
    _repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(_repo), "--receipt-root", str(receipts), "--target-node-count", "1", "--planned-shard-timeout-seconds", "3600"], cwd=_repo).returncode == 0
    assert _matrix(["run-shard", "--repo-root", str(_repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001", "--timeout-seconds", "3600"], cwd=_repo).returncode == 0
    receipt_path = receipts / "receipts" / "s001.json"
    original = json.loads(receipt_path.read_text(encoding="utf-8"))
    for value in (90.0, 300.0, 600.0, 3601.0):
        receipt = dict(original)
        receipt["timeout_seconds"] = value
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verify = _matrix(["verify", "--repo-root", str(_repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=_repo)
        assert verify.returncode != 0
        assert "timeout_contract_mismatch" in verify.stderr


def test_tq1_c7r_existing_receipt_reexecution_is_rejected_without_overwrite(tmp_path: Path) -> None:
    _matrix_module, repo, receipts, worktrees, _plan, _shard, receipt_path = _successful_single_shard_matrix(tmp_path)
    before = receipt_path.read_bytes()

    result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--all", "--workers", "1"], cwd=repo)

    assert result.returncode != 0
    assert "receipt_overwrite_forbidden" in result.stderr
    assert receipt_path.read_bytes() == before


def test_tq1_c7r_runtime_manifest_uses_canonical_posix_path_order(tmp_path: Path) -> None:
    matrix = load_matrix()
    root = tmp_path / "fixture"
    _write(root / "openclaw_live_eval" / "z" / "workspace" / "SOUL.md", "A")
    _write(root / "openclaw_live_eval" / "z" / "workspace" / "memory" / ".dreams" / "events.jsonl", "{}\n")

    entries = matrix.build_runtime_manifest_entries(root)

    assert [entry["path"] for entry in entries] == [
        "openclaw_live_eval/z/workspace/SOUL.md",
        "openclaw_live_eval/z/workspace/memory/.dreams/events.jsonl",
    ]


def test_tq1_preexisting_worktree_is_not_deleted_and_writes_receipt(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    shard_path = _matrix_root(worktrees, receipts) / "s001"
    shard_path.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "--detach", str(shard_path), "HEAD")
    try:
        result = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)
        receipt = json.loads((receipts / "receipts" / "s001.json").read_text(encoding="utf-8"))

        assert result.returncode != 0
        assert receipt["status"] == "failed"
        assert receipt["reason"] == "worktree_exists"
        assert receipt["worktree_cleanup"] == "not_owned"
        assert shard_path.exists()
        assert str(shard_path).replace("\\", "/") in _git_out(repo, "worktree", "list")
    finally:
        _git(repo, "worktree", "remove", "--force", str(shard_path))


def test_tq1_c3_cleanup_refuses_expected_shard_path_without_matching_marker(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    assert _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo).returncode == 0
    shard_path = _matrix_root(worktrees, receipts) / "s001"
    _git(repo, "worktree", "add", "--detach", str(shard_path), "HEAD")
    try:
        result = _matrix(["cleanup", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

        assert result.returncode != 0
        assert "cleanup_refused" in result.stderr
        assert shard_path.exists()
        assert str(shard_path).replace("\\", "/") in _git_out(repo, "worktree", "list")
    finally:
        _git(repo, "worktree", "remove", "--force", str(shard_path))


def test_tq1_c3_cleanup_removes_owned_leftover_with_exact_shard_marker(tmp_path: Path) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    shard = plan["shards"][0]
    matrix.ensure_worktree_root_marker(worktrees, receipts.resolve(), plan)
    shard_path = _matrix_root(worktrees, receipts) / "s001"
    _git(repo, "worktree", "add", "--detach", str(shard_path), "HEAD")
    matrix.write_shard_worktree_marker(shard_path, receipts.resolve(), plan, shard)

    result = _matrix(["cleanup", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode == 0, result.stderr
    assert not shard_path.exists()


def test_tq1_c4_cleanup_refuses_missing_receipt_root_marker_without_deleting(tmp_path: Path) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    shard = plan["shards"][0]
    matrix.ensure_worktree_root_marker(worktrees, receipts.resolve(), plan)
    shard_path = _matrix_root(worktrees, receipts) / "s001"
    _git(repo, "worktree", "add", "--detach", str(shard_path), "HEAD")
    matrix.write_shard_worktree_marker(shard_path, receipts.resolve(), plan, shard)
    (receipts / ".nollm_test_matrix_root.json").unlink()
    try:
        result = _matrix(["cleanup", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

        assert result.returncode != 0
        assert "cleanup_refused" in result.stderr
        assert shard_path.exists()
        assert str(shard_path).replace("\\", "/") in _git_out(repo, "worktree", "list")
    finally:
        _git(repo, "worktree", "remove", "--force", str(shard_path))


def test_tq1_add_worktree_failure_writes_receipt(tmp_path: Path, monkeypatch) -> None:
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))

    def fail_add(repo_root, worktree, head):
        raise matrix.MatrixError("worktree_add_failed", "boom")

    monkeypatch.setattr(matrix, "add_worktree", fail_add)
    receipt = matrix.run_one_shard(repo, receipts, worktrees, plan, "s001", 1.0, False)

    assert receipt["status"] == "failed"
    assert receipt["reason"] == "worktree_add_failed"
    assert receipt["failure_stage"] == "worktree_add"
    assert receipt["worktree_add_succeeded"] is False
    assert receipt["worktree_created_by_this_call"] is False
    assert (receipts / "receipts" / "s001.json").exists()
    _assert_failure_receipt_contract(receipt)


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


def test_tq1_cleanup_refuses_missing_worktree_marker(tmp_path: Path) -> None:
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    protected = _matrix_root(worktrees, receipts) / "protected"
    protected.mkdir(parents=True)

    result = _matrix(["cleanup", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)

    assert result.returncode != 0
    assert "cleanup_refused" in result.stderr
    assert protected.exists()


def _matrix(args: list[str], *, cwd: Path, timeout_seconds: int = 60):
    return run_subprocess([sys.executable, str(SCRIPT), *args], cwd=cwd, timeout_seconds=timeout_seconds)


def _matrix_root(worktrees: Path, receipts: Path) -> Path:
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    return worktrees / plan["matrix_id"]


def _assert_failure_receipt_contract(receipt: dict) -> None:
    assert receipt["status"] in {"failed", "timed_out"}
    assert receipt["reason"]
    assert receipt["failure_stage"]
    assert receipt["shard_id"]
    assert receipt["git_head"]
    assert receipt["worktree_path"]
    assert "worktree_add_succeeded" in receipt
    assert "worktree_marker_written" in receipt
    assert "worktree_created_by_this_call" in receipt
    assert "worktree_cleanup" in receipt


def _successful_single_shard_matrix(tmp_path: Path):
    matrix = load_matrix()
    repo = _tiny_repo(tmp_path, {"tests/test_alpha.py": "def test_a():\n    assert True\n"})
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts)], cwd=repo).returncode == 0
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)
    assert run.returncode == 0, run.stderr
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)
    assert verify.returncode == 0, verify.stderr
    assert "receipt_json_count=1" in verify.stdout
    plan = json.loads((receipts / "matrix_plan.json").read_text(encoding="utf-8"))
    shard = plan["shards"][0]
    return matrix, repo, receipts, worktrees, plan, shard, receipts / "receipts" / "s001.json"


def _successful_fixture_present_matrix(tmp_path: Path):
    repo = _tiny_repo(
        tmp_path,
        {
            ".gitignore": "out/\n",
            "tests/test_runtime.py": "from pathlib import Path\n\ndef test_runtime_seed():\n    assert Path('out/nollm_runtime/seed.txt').read_text(encoding='utf-8') == 'A'\n",
        },
    )
    _write(repo / "out" / "nollm_runtime" / "seed.txt", "A")
    receipts = tmp_path / "receipts"
    worktrees = tmp_path / "worktrees"
    assert _matrix(["plan", "--repo-root", str(repo), "--receipt-root", str(receipts), "--target-node-count", "1"], cwd=repo).returncode == 0
    run = _matrix(["run-shard", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees), "--shard", "s001"], cwd=repo)
    assert run.returncode == 0, run.stderr
    verify = _matrix(["verify", "--repo-root", str(repo), "--receipt-root", str(receipts), "--worktree-root", str(worktrees)], cwd=repo)
    assert verify.returncode == 0, verify.stderr
    return repo, receipts, worktrees


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


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
