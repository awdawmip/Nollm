from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress, MemoryAtom, PutCommand


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "lab/nollm-lab/geometry/run_dense_live_state_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location("dense_live_state_validation", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dense_live_state_reports_hidden_current_statements_without_writes() -> None:
    with TemporaryDirectory(prefix="nollm-dense-live-state-") as raw_workspace:
        workspace = Path(raw_workspace)
        statements = tuple(
            MemoryStatement(f"dense-{index}", f"dense topic fact {index}")
            for index in range(8)
        )
        with CoreRuntime(workspace) as core:
            handles = core.apply_batch(tuple(
                PutCommand(MemoryAtom(statement.statement_id, statement.content_utf8), GeometryAddress("default_dream_v1", "default", 0, 3, 4))
                for statement in statements
            ))
        statement_store = FileStatementStore(workspace)
        handle_store = FileHandleStore(workspace)
        for statement, handle in zip(statements, handles, strict=True):
            statement_store.put(statement)
            handle_store.put(statement.statement_id, handle)

        result = _module().validate(workspace, dense_prefix="dense topic", minimum_current=8)

        assert result["passed"]
        assert result["dense_current_count"] == 8
        assert result["truncated_cells"][0]["remaining_count"] == 5
        assert len(result["hidden_dense_statement_ids"]) == 5
