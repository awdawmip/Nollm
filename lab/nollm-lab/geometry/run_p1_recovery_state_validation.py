from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from nollm_access import FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime


def _workspace_hashes(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    }


def _statements(workspace: Path) -> tuple[MemoryStatement, ...]:
    result = []
    roots = (workspace / "access" / "statements", workspace / "access" / "evidence")
    for path in sorted(candidate for root in roots if root.is_dir() for candidate in root.rglob("*.json")):
        value = json.loads(path.read_bytes().decode("utf-8"))
        if type(value) is dict and type(value.get("statement")) is dict:
            result.append(MemoryStatement.from_mapping(value["statement"]))
    return tuple(result)


def validate(workspace: Path, statement_id: str, expect_bound: bool = False) -> dict[str, object]:
    workspace = workspace.resolve()
    before = _workspace_hashes(workspace)
    store = FileStatementStore(workspace)
    bindings = FileHandleStore(workspace)
    all_statements = _statements(workspace)
    statement = store.get(statement_id) if store.exists(statement_id) else None
    bound = bindings.exists(statement_id)
    matching_content_ids = sorted(
        item.statement_id for item in all_statements
        if statement is not None and item.content_utf8 == statement.content_utf8
    )

    matching_atoms = []
    with CoreRuntime(workspace) as core:
        placement_count = core.placement_count()
        occupied_cell_count = len(core.occupied_cells())
        for address in core.occupied_cells():
            for handle, atom in core.atoms_at(address):
                if atom.atom_id == statement_id or (statement is not None and atom.payload_utf8 == statement.content_utf8):
                    matching_atoms.append({"handle": handle.to_mapping(), "atom_id": atom.atom_id})
    after = _workspace_hashes(workspace)
    candidate_exists = statement is not None
    reuse_eligible = candidate_exists and not bound and not matching_atoms and matching_content_ids == [statement_id]
    bound_complete = candidate_exists and bound and len(matching_atoms) == 1 and matching_content_ids == [statement_id]
    checks = {
        "candidate_state_consistent": bound_complete if expect_bound else (
            (not candidate_exists and not bound and not matching_atoms) or reuse_eligible
        ),
        "inventory_is_read_only": before == after,
    }
    return {
        "schema_version": "nollm_p1_recovery_state_validation_v1",
        "workspace": str(workspace),
        "statement_id": statement_id,
        "candidate_exists": candidate_exists,
        "reuse_eligible": reuse_eligible,
        "bound_complete": bound_complete,
        "expected_state": "bound" if expect_bound else "pre_recovery",
        "statement_content_sha256": sha256(statement.content_utf8.encode("utf-8")).hexdigest() if statement else None,
        "statement_count": len(all_statements),
        "matching_content_statement_ids": matching_content_ids,
        "binding_exists": bound,
        "matching_core_atoms": matching_atoms,
        "core_placement_count": placement_count,
        "core_occupied_cell_count": occupied_cell_count,
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--statement-id", required=True)
    parser.add_argument("--expect", choices=("pre-recovery", "bound"), default="pre-recovery")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.workspace, args.statement_id, args.expect == "bound")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
