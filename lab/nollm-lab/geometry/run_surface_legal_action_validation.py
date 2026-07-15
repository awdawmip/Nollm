from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    AccessDecision,
    AccessRuntime,
    AccessSurfaceNavigator,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
    SurfaceBudgetProfile,
)
from nollm_core import CoreRuntime, GeometryAddress, PhysicalFieldScope


SCOPE = PhysicalFieldScope("default_dream_v1", "default", (0,), 0)


def _place(workspace: Path, statement_id: str, q: int) -> None:
    statement = MemoryStatement(statement_id, f"legal action fixture {statement_id}")
    with CoreRuntime(workspace) as core:
        with AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace)) as access:
            access.capture(statement)
            access.apply(AccessDecision(
                f"decision:{statement_id}",
                statement_id,
                "new",
                GeometryAddress("default_dream_v1", "default", 0, q, 0),
                reason_text="deterministic Lab fixture",
                decided_by="fixture",
            ))


def validate() -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-caold-legal-actions-") as raw_workspace:
        workspace = Path(raw_workspace)
        for index in range(3):
            _place(workspace, f"statement-{index}", index)
        navigator = AccessSurfaceNavigator(workspace)

        paged_budget = SurfaceBudgetProfile(1, 20, 100, 1, 1, 1000, 8, 8, 24)
        root = navigator.begin("legal-root", SCOPE, paged_budget)
        continued = navigator.continue_page(root)
        coarser = navigator.request_coarser_surface(root)
        child = navigator.open_surface_cell(coarser, coarser.cells[0].candidate_id)
        returned = navigator.return_to_parent(child)

        coarse_budget = SurfaceBudgetProfile(8, 1, 1, 1, 1, 1, 8, 8, 24)
        hard_max = navigator.begin("legal-hard-max", SCOPE, coarse_budget)
        leaf = hard_max
        while leaf.state.order > 0:
            leaf = navigator.open_surface_cell(leaf, leaf.cells[0].candidate_id)
        physical = navigator.open_physical_entries(leaf, leaf.cells[0].candidate_id)
        singleton = navigator.resolve_singleton_entry(physical)

        matrices = {
            "root": list(root.legal_actions),
            "continued": list(continued.legal_actions),
            "coarser": list(coarser.legal_actions),
            "child": list(child.legal_actions),
            "returned": list(returned.legal_actions),
            "hard_max": list(hard_max.legal_actions),
            "order_zero": list(leaf.legal_actions),
            "physical_singleton": list(physical.legal_actions),
        }
        checks = {
            "continuation_only_when_available": ("continue_page" in root.legal_actions) == root.has_more,
            "continued_page_is_distinct": continued.state.after is not None,
            "root_has_no_parent_return": "return_to_parent" not in root.legal_actions,
            "coarser_child_can_return": "return_to_parent" in child.legal_actions,
            "return_restores_parent_order": returned.state.order == coarser.state.order,
            "hard_max_has_no_coarser_action": "request_coarser_surface" not in hard_max.legal_actions,
            "order_zero_opens_physical_only": "open_physical_entries" in leaf.legal_actions and "open_surface_cell" not in leaf.legal_actions,
            "singleton_is_mechanical": singleton.resolved_singleton and singleton.resolution_policy_id == "mechanical_singleton_physical_entry_v1",
            "no_select_entries_action": all("select_entries" not in actions for actions in matrices.values()),
            "no_persistent_traversal_state": not (workspace / "access" / "surface_state.json").exists(),
        }
        return {
            "schema_version": "nollm_surface_legal_action_validation_v1",
            "legal_action_matrix": matrices,
            "checks": checks,
            "passed": all(checks.values()),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
