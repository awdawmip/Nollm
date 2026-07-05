from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess

import pytest

import nollm.dream_geometry.host_execution.bindings as hx1_bindings
from nollm.dream_geometry.host_execution import HX1ExecutionError, HostDG6VerificationBinding, HostExecutionContext, HostPlanBindings, execute_host_plan

from test_hx1_trusted_host_bridge import hx1_fixture, setup_preexisting_d


def test_hx1_rejects_repo_root_work_root_before_write() -> None:
    fixture = hx1_fixture(Path.cwd())
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    assert error.value.reason_code == "HX1_WORK_ROOT_REJECTED"


def test_hx1_rejects_forbidden_output_directory_before_stage_calls(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    (tmp_path / "work" / "cache").mkdir(parents=True)
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    assert error.value.reason_code == "HX1_WORK_ROOT_REJECTED"


def test_hx1_new_module_does_not_import_forbidden_runtime_surfaces() -> None:
    root = Path("reference/python/nollm/dream_geometry/host_execution")
    rendered = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py")).lower()
    for token in ("requests", "urllib", "socket", "sqlite3", "subprocess", "openclaw"):
        assert f"import {token}" not in rendered
        assert f"from {token}" not in rendered


def test_hx1_public_errors_do_not_expose_trace_or_paths(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    context = HostExecutionContext(tmp_path / "work" / "leaf.txt", fixture["context"].recorded_at)
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / "leaf.txt").write_text("not a directory", encoding="utf-8")
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(fixture["plan"], fixture["bindings"], context)
    rendered = str(error.value)
    for forbidden in ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\"):
        assert forbidden not in rendered


@pytest.mark.parametrize(
    "field,value",
    (
        ("recorded_at", None),
        ("batch_window_id", None),
        ("batch_policy_id", None),
        ("batch_source_ref", None),
        ("finite_set_id", None),
        ("enable_dg6_verification", "false"),
    ),
)
def test_hx1_c2_invalid_context_fields_reject_before_write(tmp_path, field, value) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    context = replace(fixture["context"], **{field: value})
    _assert_context_zero_write(fixture["plan"], fixture["bindings"], context, tmp_path / "work")


def test_hx1_c2_declared_dg6_requires_enabled_context_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    context = replace(fixture["context"], enable_dg6_verification=False)
    _assert_context_zero_write(fixture["plan"], fixture["bindings"], context, tmp_path / "work")


def test_hx1_c2_dg6_enablement_controls_projection_without_recall_influence(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "with_dg6")
    receipt = execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
    assert receipt.dg6_projection_id

    no_dg6_fixture = hx1_fixture(tmp_path / "without_dg6")
    plan = replace(no_dg6_fixture["plan"], derived_views=())
    bindings = replace(no_dg6_fixture["bindings"], dg6_binding=None)
    context = replace(no_dg6_fixture["context"], enable_dg6_verification=False)
    receipt = execute_host_plan(plan, bindings, context)
    assert receipt.status == "completed"
    assert receipt.dg6_projection_id is None
    assert receipt.recall_public_envelope is not None


def test_hx1_c3_undeclared_dg6_binding_rejects_before_write(tmp_path) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    plan = replace(fixture["plan"], derived_views=())
    bindings = replace(fixture["bindings"], dg6_binding=HostDG6VerificationBinding("view:hx1:rogue"))
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, fixture["context"])
    assert error.value.reason_code == "HX1_INVALID_BINDINGS"
    assert type(error.value) is HX1ExecutionError
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error.value)
    assert not (tmp_path / "work").exists() or list((tmp_path / "work").iterdir()) == []


@pytest.mark.parametrize("work_root", (None, 123))
def test_hx1_c3_invalid_work_root_context_type_rejects_before_write(tmp_path, work_root) -> None:
    fixture = hx1_fixture(tmp_path / "work")
    context = replace(fixture["context"], work_root=work_root)
    _assert_context_zero_write(fixture["plan"], fixture["bindings"], context, tmp_path / "work")


def test_hx1_c3_rejects_repository_descendant_work_root_before_write() -> None:
    repo_root = _repo_root()
    probe = repo_root / ".hx1_c3_repo_child_probe"
    if probe.exists():
        shutil.rmtree(probe)
    fixture = hx1_fixture(probe)
    try:
        with pytest.raises(HX1ExecutionError) as error:
            execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
        _assert_work_root_rejected(error.value)
        assert not probe.exists()
        _assert_git_status_empty(repo_root, probe)
    finally:
        if probe.exists():
            shutil.rmtree(probe)


def test_hx1_c4_external_cwd_rejects_source_repo_descendant_before_write(tmp_path, monkeypatch) -> None:
    repo_root = _repo_root()
    probe = repo_root / ".hx1_c4_external_cwd_probe"
    if probe.exists():
        shutil.rmtree(probe)
    external_cwd = tmp_path / "external_cwd"
    external_cwd.mkdir()
    fixture = hx1_fixture(probe)
    try:
        monkeypatch.chdir(external_cwd)
        with pytest.raises(HX1ExecutionError) as error:
            execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
        _assert_work_root_rejected(error.value)
        assert not probe.exists()
        _assert_git_status_empty(repo_root, probe)
    finally:
        monkeypatch.chdir(repo_root)
        if probe.exists():
            shutil.rmtree(probe)


def test_hx1_c4_external_cwd_rejects_source_repo_root_before_write(tmp_path, monkeypatch) -> None:
    repo_root = _repo_root()
    marker = repo_root / ".hx1_host_execution_root.json"
    external_cwd = tmp_path / "external_cwd"
    external_cwd.mkdir()
    fixture = hx1_fixture(repo_root)
    try:
        monkeypatch.chdir(external_cwd)
        with pytest.raises(HX1ExecutionError) as error:
            execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
        _assert_work_root_rejected(error.value)
        assert not marker.exists()
    finally:
        monkeypatch.chdir(repo_root)


def test_hx1_c4_external_cwd_allows_external_temporary_root(tmp_path, monkeypatch) -> None:
    repo_root = _repo_root()
    external_cwd = tmp_path / "external_cwd"
    work_root = tmp_path / "owned_work_root"
    external_cwd.mkdir()
    probe = repo_root / ".hx1_c4_external_temp_probe"
    if probe.exists():
        shutil.rmtree(probe)
    try:
        monkeypatch.chdir(external_cwd)
        setup_preexisting_d(work_root)
        fixture = hx1_fixture(work_root)
        receipt = execute_host_plan(fixture["plan"], fixture["bindings"], fixture["context"])
        assert receipt.status == "completed"
        _assert_no_forbidden_dirs(work_root)
        assert not probe.exists()
        _assert_git_status_empty(repo_root, probe)
    finally:
        monkeypatch.chdir(repo_root)
        if probe.exists():
            shutil.rmtree(probe)


def test_hx1_c4_repository_root_detection_accepts_git_file_marker(tmp_path) -> None:
    fake_repo = tmp_path / "fake_worktree"
    nested = fake_repo / "package" / "module.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("# fake module\n", encoding="utf-8")
    (fake_repo / ".git").write_text("gitdir: ../actual.git/worktrees/fake\n", encoding="utf-8")
    assert hx1_bindings._nearest_repository_root(nested) == fake_repo


def test_hx1_c4_repository_root_detection_has_no_non_git_fallback(tmp_path) -> None:
    outside = tmp_path / "not_a_repo" / "child"
    outside.mkdir(parents=True)
    assert hx1_bindings._nearest_repository_root(outside) is None


def _assert_context_zero_write(plan, bindings: HostPlanBindings, context, work_root) -> None:
    with pytest.raises(HX1ExecutionError) as error:
        execute_host_plan(plan, bindings, context)
    assert error.value.reason_code == "HX1_INVALID_CONTEXT"
    assert type(error.value) is HX1ExecutionError
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error.value)
    assert not work_root.exists() or list(work_root.iterdir()) == []


def _repo_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def _assert_work_root_rejected(error: HX1ExecutionError) -> None:
    assert error.reason_code == "HX1_WORK_ROOT_REJECTED"
    assert type(error) is HX1ExecutionError
    assert "protected repository roots" in str(error)
    for forbidden in ("Traceback", "AttributeError", "TypeError", "KeyError", "ValueError", "AssertionError", "nollm.dream_geometry", "\\"):
        assert forbidden not in str(error)


def _assert_no_forbidden_dirs(work_root: Path) -> None:
    for name in ("field", "assembly", "recall", "cache", "database", "global-field"):
        assert not (work_root / name).exists()


def _assert_git_status_empty(repo_root: Path, path: Path) -> None:
    relative = path.relative_to(repo_root).as_posix()
    result = subprocess.run(
        ["git", "status", "--short", "--", relative],
        cwd=repo_root,
        text=True,
        capture_output=True,
        timeout=10,
        check=True,
    )
    assert result.stdout == ""
