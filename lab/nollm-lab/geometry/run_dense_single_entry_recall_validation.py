from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import (
    AccessRecallRequest,
    AccessRuntime,
    FileHandleStore,
    FileStatementStore,
    MemoryStatement,
)
from nollm_core import (
    CoreRuntime,
    GeometryAddress,
    MemoryAtom,
    PutCommand,
    RecallBudget,
    expand_physical_coverage,
)


def _coordinates(radius: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (q, r)
        for q in range(-radius, radius + 1)
        for r in range(-radius, radius + 1)
        if max(abs(q), abs(r), abs(q + r)) <= radius
    )


def _place_fixture(workspace: Path, cell_count: int, atom_count: int):
    entry_a = GeometryAddress("default_dream_v1", "default", 0, 0, 0)
    expansion = expand_physical_coverage(entry_a, "coverage_down")
    target = max(expansion.members, key=lambda member: (member.weight_q16, member.target.stable_key())).target
    alternatives = tuple(
        member.target
        for member in expansion.members
        if member.target != target and target in member.target.lateral(1)
    )
    entry_b = next((
        candidate
        for candidate in entry_a.lateral(1)
        if target in {member.target for member in expand_physical_coverage(candidate, "coverage_down").members}
    ), None)

    dense_addresses = tuple(
        GeometryAddress("default_dream_v1", "default", 1, q, r)
        for q, r in _coordinates(10)[:cell_count]
    )
    base = [("entry-a", entry_a), ("target", target)]
    if entry_b is not None:
        base.append(("entry-b", entry_b))
    remaining = atom_count - len(base)
    if remaining < len(dense_addresses):
        raise ValueError("atom_count must occupy every dense fixture cell")
    assignments = list(base)
    assignments.extend(
        (f"distractor-{index:04d}", dense_addresses[index % len(dense_addresses)])
        for index in range(remaining)
    )
    with CoreRuntime(workspace) as core:
        handles = core.apply_batch(tuple(
            PutCommand(MemoryAtom(atom_id, f"payload {atom_id}"), address)
            for atom_id, address in assignments
        ))
    statements = FileStatementStore(workspace)
    bindings = FileHandleStore(workspace)
    bound_ids = {"entry-a", "entry-b", "target"}
    bound_ids.update(f"distractor-{index:04d}" for index in range(min(61, remaining)))
    for (atom_id, _address), handle in zip(assignments, handles):
        if atom_id not in bound_ids:
            continue
        statements.put(MemoryStatement(atom_id, f"payload {atom_id}"))
        bindings.put(atom_id, handle)
    return entry_a, entry_b, target, alternatives, len({address for _atom_id, address in assignments})


def _item(result, statement_id: str):
    return next((item for item in result.items if item.statement_id == statement_id), None)


def validate(*, cell_count: int = 300, atom_count: int = 1000) -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-caold-dense-recall-") as raw_workspace:
        workspace = Path(raw_workspace)
        entry_a, entry_b, target, alternatives, occupied_cell_count = _place_fixture(workspace, cell_count, atom_count)
        enabled_budget = RecallBudget(2, 64, 2, 1, 0, 64)
        disabled_budget = RecallBudget(2, 64, 2, 1, 0, 64)
        with CoreRuntime(workspace) as core:
            with AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace)) as access:
                enabled_request = AccessRecallRequest(
                    "dense-entry-a-enabled",
                    (entry_a,),
                    (),
                    ("coverage_down", "lateral"),
                    enabled_budget,
                )
                disabled_request = AccessRecallRequest(
                    "dense-entry-a-disabled", (entry_a,), (), (), disabled_budget
                )
                enabled = access.recall(enabled_request)
                disabled = access.recall(disabled_request)
                observation_runs = []
                for label, entry in (("A", entry_a), ("B", entry_b)):
                    if entry is None:
                        observation_runs.append({"entry": label, "available": False, "target_reached": False, "path": None})
                        continue
                    result = access.recall(AccessRecallRequest(
                        f"natural-entry-{label}",
                        (entry,),
                        (),
                        ("coverage_down", "lateral"),
                        enabled_budget,
                    ))
                    target_item = _item(result, "target")
                    observation_runs.append({
                        "entry": label,
                        "available": True,
                        "entry_cell": entry.to_mapping(),
                        "request_entry_count": 1,
                        "target_reached": target_item is not None,
                        "path": list(target_item.path) if target_item else None,
                        "result_count": len(result.items),
                        "budget_exhausted": result.budget_exhausted,
                    })

        target_enabled = _item(enabled, "target")
        target_disabled = _item(disabled, "target")
        target_items = tuple(item for item in enabled.items if item.statement_id == "target")
        checks = {
            "full_dense_cell_minimum": cell_count >= 300,
            "full_dense_atom_minimum": atom_count >= 1000,
            "single_entry_request": len(enabled_request.entry_cells) == 1,
            "target_reached_with_geometry": target_enabled is not None,
            "target_absent_without_geometry": target_disabled is None,
            "single_entry_path_deduplicated": len(target_items) == 1,
            "alternative_path_exists_in_geometry": bool(alternatives),
            "target_path_is_kernel_path": target_enabled is not None and target_enabled.path == ("coverage_down",),
            "interference_present": len(enabled.items) > 3,
            "bounded_results": len(enabled.items) <= enabled_budget.max_results,
            "natural_observation_uses_separate_single_entry_requests": all(
                not item["available"] or item["request_entry_count"] == 1
                for item in observation_runs
            ),
        }
        return {
            "schema_version": "nollm_dense_single_entry_recall_validation_v1",
            "fixture": {
                "requested_dense_cell_count": cell_count,
                "occupied_cell_count": occupied_cell_count,
                "atom_count": atom_count,
                "bound_statement_limit": 64,
                "entry_a": entry_a.to_mapping(),
                "entry_b": entry_b.to_mapping() if entry_b else None,
                "target": target.to_mapping(),
                "alternative_path_intermediates": [item.to_mapping() for item in alternatives],
                "semantic_index_used": False,
                "persisted_entry_hint_used": False,
            },
            "enabled": {
                "entry_count": len(enabled_request.entry_cells),
                "kernels": list(enabled_request.allowed_kernels),
                "result_count": len(enabled.items),
                "budget_exhausted": enabled.budget_exhausted,
                "target_path": list(target_enabled.path) if target_enabled else None,
                "target_score_q16": target_enabled.score_q16 if target_enabled else None,
                "unique_handle_count": len({item.handle for item in enabled.items}),
            },
            "disabled": {
                "entry_count": len(disabled_request.entry_cells),
                "kernels": [],
                "result_count": len(disabled.items),
                "target_reached": target_disabled is not None,
            },
            "natural_multi_entry_observation": {
                "minimum_required": 0,
                "combined_request_used": False,
                "persisted_fact_to_entries": False,
                "runs": observation_runs,
                "entries_reaching_target": sum(item["target_reached"] for item in observation_runs),
            },
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
