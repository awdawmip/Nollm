from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess


INPUT_BUNDLE = "nollm_caold_write_policy_legal_traversal_p1_dense_live_20260715_f61efd5.bundle"
INPUT_BUNDLE_SHA256 = "e1f9b2d70551266eb40c83213d5949065c6e128a9fdc5b78423b714721055084"
INPUT_HEAD = "f61efd5dcb46ffc8c8c79a5ca0ae588562346f8d"


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path.name} must contain a JSON object")
    return value


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def validate(
    evidence: Path,
    summary: Path,
    *,
    validation_dir: Path | None = None,
) -> dict[str, object]:
    payload = evidence.read_bytes()
    if not payload or not payload.endswith(b"\n"):
        raise ValueError("Evidence must be non-empty and newline terminated")
    rows = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid Evidence line {line_number}") from error
        if type(row) is not dict:
            raise ValueError(f"Evidence line {line_number} must be an object")
        rows.append(row)

    providers = sorted({row["resolved_provider"] for row in rows if type(row.get("resolved_provider")) is str})
    models = sorted({row["resolved_model_ref"] for row in rows if type(row.get("resolved_model_ref")) is str})
    result: dict[str, object] = {
        "schema_version": "nollm_live_evidence_freeze_summary_v1",
        "input_bundle": INPUT_BUNDLE,
        "input_bundle_sha256": INPUT_BUNDLE_SHA256,
        "input_head": INPUT_HEAD,
        "implementation_head_at_freeze": _head(),
        "evidence": {
            "path": evidence.as_posix(),
            "line_count": len(rows),
            "size_bytes": len(payload),
            "sha256": sha256(payload).hexdigest(),
            "status_counts": dict(sorted(Counter(row.get("status", "missing") for row in rows).items())),
            "stage_counts": dict(sorted(Counter(row.get("stage", "none") for row in rows).items())),
        },
        "provider": providers,
        "model": models,
    }

    checks = {
        "evidence_nonempty": bool(rows),
        "all_rows_objects": True,
        "provider_observed": bool(providers),
        "model_observed": bool(models),
    }
    if validation_dir is not None:
        contrast = _load(validation_dir / "caold_revision_semantic_contrast_validation.json")
        p1 = _load(validation_dir / "caold_p1_dual_fact_repair_validation.json")
        dense = _load(validation_dir / "caold_dense_live_state_validation.json")
        recall = _load(validation_dir / "caold_hidden_preview_recall_validation.json")
        regression = _load(validation_dir / "caold_regression_results.json")
        outcomes = contrast["outcomes"]
        result.update({
            "workspace_identity": {
                "p1_before": p1["before"]["workspace_tree_sha256"],
                "p1_after": p1["after"]["workspace_tree_sha256"],
                "dense_final": dense["workspace_tree_sha256"],
                "recall_before": recall["workspace_tree_sha256_before"],
                "recall_after": recall["workspace_tree_sha256_after"],
            },
            "p1": {
                "bx_statement_id": "dream:91b6c843119549038dd2bbb0a40a8452f82edf5c158cac39c877c691f22280dc",
                "bx_handle": p1["after"]["bx_handle"],
                "cr_statement_id": "dream:82b8b33fc8c0cf13220db726e34f67fe781ddaa073d5033c7d739766e3e268d9",
                "cr_handle": p1["after"]["cr_handle"],
            },
            "revision_contrast": {
                "outcomes": [{"case_id": item["case_id"], "action": item["action"], "passed": item["passed"]} for item in outcomes],
                "revision_confirmation_count": sum(item["confirmation"] is not None for item in outcomes),
                "rejected_revision_zero_write": contrast["checks"]["sandbox_zero_write"],
            },
            "dense": {
                "statement_count": dense["statement_count"],
                "binding_count": dense["binding_count"],
                "atom_count": dense["atom_count"],
                "current_statement_count": dense["dense_current_count"],
                "supporting_statement_count": dense["dense_supporting_count"],
                "truncated_cells": dense["truncated_cells"],
                "hidden_statement_ids": dense["hidden_dense_statement_ids"],
            },
            "hidden_preview_recall": {
                "entry_cell": recall["entry_cell"],
                "selected_statement_ids": recall["selected_statement_ids"],
                "visible_answer_excerpt": recall["visible_answer_excerpt"],
                "visible_answer_sha256": recall["visible_answer_sha256"],
            },
            "regressions": regression,
        })
        checks.update({
            "contrast_passed": contrast.get("passed") is True,
            "p1_passed": p1.get("passed") is True,
            "dense_passed": dense.get("passed") is True,
            "hidden_preview_recall_passed": recall.get("passed") is True,
            "regression_receipt_valid": (
                regression.get("schema_version") == "nollm_aold_regression_results_v1"
                and type(regression.get("results")) is dict
                and type(regression.get("passed")) is bool
            ),
        })

    result["checks"] = checks
    result["passed"] = all(checks.values())
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.evidence, args.summary, validation_dir=args.evidence.parent)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
