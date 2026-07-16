from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_p1_dual_fact_repair_validation.py"
SPEC = importlib.util.spec_from_file_location("p1_dual_fact_repair", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def seed_wrong_state(workspace: Path) -> None:
    statements = FileStatementStore(workspace)
    statements.put(MemoryStatement(RUNNER.BX_STATEMENT_ID, RUNNER.BX_CONTENT))
    statements.put(MemoryStatement(RUNNER.CR_STATEMENT_ID, RUNNER.CR_CONTENT))
    with CoreRuntime(workspace) as core:
        with AccessRuntime(core, statements, FileHandleStore(workspace)) as access:
            access.apply(AccessDecision(
                "seed:cr", RUNNER.CR_STATEMENT_ID, "new",
                target_cell=GeometryAddress("default_dream_v1", "default", 0, -13, 9),
                reason_text="fixture", decided_by="fixture",
            ))


def test_dry_run_restore_and_idempotent_reopen(tmp_path: Path) -> None:
    seed_wrong_state(tmp_path)
    dry = RUNNER.validate_and_optionally_restore(tmp_path)
    assert dry["repair_required_before"] is True
    assert dry["before"] == dry["after"]

    applied = RUNNER.validate_and_optionally_restore(tmp_path, True)
    assert applied["action"] == "restored_bx_current"
    assert applied["after"]["bx_handle"] is not None
    assert applied["after"]["cr_handle"] is None
    assert applied["after"]["bx_payload_utf8"] == RUNNER.BX_CONTENT

    reopened = RUNNER.validate_and_optionally_restore(tmp_path, True)
    assert reopened["action"] == "already_restored"
    assert reopened["before"] == reopened["after"]


def test_missing_source_statement_fails_before_write(tmp_path: Path) -> None:
    statements = FileStatementStore(tmp_path)
    statements.put(MemoryStatement(RUNNER.CR_STATEMENT_ID, RUNNER.CR_CONTENT))
    with pytest.raises(FileNotFoundError):
        RUNNER.validate_and_optionally_restore(tmp_path, True)
