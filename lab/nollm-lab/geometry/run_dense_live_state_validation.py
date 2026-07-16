from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "packages/nollm-core/src"),
    str(ROOT / "packages/nollm-access/src"),
]

from nollm_access import (  # noqa: E402
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    PLACEMENT_SURFACE_BUDGET,
)
from nollm_core import CoreRuntime, PhysicalFieldScope  # noqa: E402


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _tree_sha256(root: Path) -> str:
    digest = sha256()
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _pages(navigator: AccessSurfaceNavigator):
    page = navigator.begin("dense-live-state-validation", SCOPE, PLACEMENT_SURFACE_BUDGET)
    pages = [page]
    while page.has_more:
        page = navigator.continue_page(page)
        pages.append(page)
    return tuple(pages)


def validate(workspace: Path, *, dense_prefix: str = "青岚展厅", minimum_current: int = 8) -> dict[str, object]:
    workspace = workspace.resolve()
    before_sha = _tree_sha256(workspace)
    statements = FileStatementStore(workspace)
    binding_document = json.loads(FileHandleStore(workspace).state_bytes().decode("utf-8"))
    bindings = binding_document["bindings"]
    current_ids = tuple(item["current_statement_id"] for item in bindings)
    supporting_ids = tuple(
        statement_id
        for item in bindings
        for statement_id in item["supporting_statement_ids"]
    )
    current_dense = tuple(
        statement_id
        for statement_id in current_ids
        if statements.get(statement_id).content_utf8.startswith(dense_prefix)
    )
    supporting_dense = tuple(
        statement_id
        for statement_id in supporting_ids
        if statements.get(statement_id).content_utf8.startswith(dense_prefix)
    )

    with CoreRuntime(workspace) as core:
        core_handles = {
            handle
            for address in core.occupied_cells()
            for handle, _atom in core.atoms_at(address)
        }
        atom_count = core.placement_count()
        occupied_cell_count = len(core.occupied_cells())

    pages = _pages(AccessSurfaceNavigator(workspace))
    surface_cells = tuple(cell for page in pages for cell in page.cells)
    truncated = tuple(cell for cell in surface_cells if cell.truncated)
    visible_ids = {
        preview.statement_id
        for cell in surface_cells
        for preview in cell.statements
    }
    hidden_dense = tuple(statement_id for statement_id in current_dense if statement_id not in visible_ids)
    binding_handles = tuple(
        (
            item["handle"]["geometry_address"]["q"],
            item["handle"]["geometry_address"]["r"],
            item["handle"]["local_atom_id"],
        )
        for item in bindings
    )
    core_handle_keys = {
        (handle.geometry_address.q, handle.geometry_address.r, handle.local_atom_id)
        for handle in core_handles
    }
    dense_cells = sorted({
        (
            item["handle"]["geometry_address"]["q"],
            item["handle"]["geometry_address"]["r"],
        )
        for item in bindings
        if item["current_statement_id"] in current_dense
    })
    after_sha = _tree_sha256(workspace)
    checks = {
        "read_only": before_sha == after_sha,
        "current_statement_minimum": len(current_dense) >= minimum_current,
        "binding_atom_count_match": len(bindings) == atom_count,
        "every_binding_has_core_atom": set(binding_handles) == core_handle_keys,
        "truncation_observed": bool(truncated),
        "remaining_count_positive": any(cell.remaining_count > 0 for cell in truncated),
        "hidden_dense_statement_exists": bool(hidden_dense),
        "no_dense_statement_is_orphaned": all(
            statement_id in current_ids or statement_id in supporting_ids
            for statement_id in (*current_dense, *supporting_dense)
        ),
    }
    return {
        "schema_version": "nollm_dense_live_state_validation_v1",
        "workspace": str(workspace),
        "workspace_tree_sha256": before_sha,
        "statement_count": len(tuple((workspace / "access" / "statements").rglob("*.json"))),
        "binding_count": len(bindings),
        "atom_count": atom_count,
        "occupied_cell_count": occupied_cell_count,
        "dense_prefix": dense_prefix,
        "dense_current_statement_ids": list(current_dense),
        "dense_current_count": len(current_dense),
        "dense_supporting_statement_ids": list(supporting_dense),
        "dense_supporting_count": len(supporting_dense),
        "dense_cells": [{"q": q, "r": r} for q, r in dense_cells],
        "surface_page_count": len(pages),
        "truncated_cells": [cell.to_mapping() for cell in truncated],
        "hidden_dense_statement_ids": list(hidden_dense),
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.workspace)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
