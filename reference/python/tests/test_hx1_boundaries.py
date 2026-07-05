from __future__ import annotations

from pathlib import Path

import pytest

from nollm.dream_geometry.host_execution import HX1ExecutionError, HostExecutionContext, execute_host_plan

from test_hx1_trusted_host_bridge import hx1_fixture


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
    for forbidden in ("Traceback", "AttributeError", "KeyError", "TypeError", "ValueError", "nollm.dream_geometry"):
        assert forbidden not in rendered
