from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nollm_access import AccessDecision, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import CoreRuntime, GeometryAddress
from nollm_openclaw_formation.adapter import FormationAdapterError
from nollm_openclaw_formation.memory_loop import TRAVERSAL_SCHEMA_VERSION, advance_recall_traversal, build_recall_prompt


def _workspace_hashes(workspace: Path) -> dict[str, str]:
    return {
        path.relative_to(workspace).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    }


def _decision(action: str, candidate_id: str | None = None) -> str:
    value = {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": action}
    if candidate_id is not None:
        value["candidate_id"] = candidate_id
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def validate() -> dict[str, object]:
    with TemporaryDirectory(prefix="nollm-caold-correction-") as raw_workspace:
        workspace = Path(raw_workspace)
        statement = MemoryStatement("correction-fixture", "Release code is CR-7159.")
        with CoreRuntime(workspace) as core:
            with AccessRuntime(core, FileStatementStore(workspace), FileHandleStore(workspace)) as access:
                access.capture(statement)
                access.apply(AccessDecision(
                    "correction-place",
                    statement.statement_id,
                    "new",
                    GeometryAddress("default_dream_v1", "default", 0, 0, 0),
                    reason_text="deterministic Lab fixture",
                    decided_by="fixture",
                ))

        built = build_recall_prompt("release code", str(workspace), "correction-recall")
        before = _workspace_hashes(workspace)
        invalid_category = None
        try:
            advance_recall_traversal(
                "release code",
                built["traversal_state"],
                _decision("return_to_parent"),
                str(workspace),
            )
        except FormationAdapterError as error:
            invalid_category = error.category
        after_invalid = _workspace_hashes(workspace)

        candidate_id = built["surface"]["surface_cells"][0]["candidate_id"]
        recovered = advance_recall_traversal(
            "release code",
            built["traversal_state"],
            _decision("open_physical_entries", candidate_id),
            str(workspace),
        )
        after_recovery = _workspace_hashes(workspace)
        checks = {
            "illegal_root_return_rejected": invalid_category == "invalid_surface_traversal",
            "invalid_decision_zero_write": before == after_invalid,
            "same_state_replay_recovers": recovered.get("status") == "recall_decision",
            "singleton_skips_model": recovered.get("physical_entry_model_call_skipped") is True,
            "singleton_policy_exact": recovered.get("resolution_policy_id") == "mechanical_singleton_physical_entry_v1",
            "recall_is_read_only": before == after_recovery,
            "no_persistent_traversal_state": not (workspace / "access" / "surface_state.json").exists(),
        }
        return {
            "schema_version": "nollm_traversal_correction_validation_v1",
            "invalid_category": invalid_category,
            "recovered_status": recovered.get("status"),
            "resolution_policy_id": recovered.get("resolution_policy_id"),
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
