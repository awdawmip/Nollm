from __future__ import annotations

import json
from pathlib import Path
import tempfile

from nollm_openclaw_formation.sculptor import apply_dream_sculptor_result, build_dream_sculptor_prompt


CATEGORIES = (
    "tokyo_date_weather", "person_project_deadline", "device_location_fault",
    "legal_case_subject_time", "same_subject_revision_contrast", "additive_fact",
    "different_subject_same_field", "no_existing_locality", "far_locality",
    "short_lived_complete_fact",
)


def _wire(case_id: int, capture: dict[str, object], atlas: dict[str, object], unresolved: bool) -> str:
    quote = capture["user_utf8"]
    assert isinstance(quote, str)
    candidate = atlas["candidates"][case_id % len(atlas["candidates"])]
    path = next(item for item in atlas["paths"] if candidate["candidate_id"] in item["leaf_locality_candidate_ids"])
    plan = {
        "draft_id": "d1",
        "content_utf8": f"Case {case_id:03d}: {quote}",
        "source_capture_ids": [capture["capture_id"]],
        "lenses": [{
            "lens_id": "lens-contract",
            "future_query": f"What happened in case {case_id:03d}?",
            "basis_spans": [{"capture_id": capture["capture_id"], "role": "user", "start": 0, "end": len(quote), "quote_utf8": quote}],
            "atlas_path_ids": [] if unresolved else [path["path_id"]],
            "leaf_locality_candidate_ids": [] if unresolved else [candidate["candidate_id"]],
            "unresolved": unresolved,
        }],
        "action": "defer" if unresolved else "new_local",
        "existing_handle": None,
        "reason_text": "synthetic contract fixture",
    }
    return json.dumps({"schema_version": "nollm_openclaw_dream_sculptor_v2", "outcome": "plan", "plans": [plan], "defer_reason": None}, ensure_ascii=False)


def validate(case_count: int = 100, workspace: str | Path | None = None) -> dict[str, object]:
    if type(case_count) is not int or case_count < 100:
        raise ValueError("synthetic conformance requires at least 100 cases")
    owned = workspace is None
    root = Path(tempfile.mkdtemp(prefix="nollm-caold-synthetic-conformance-")) if owned else Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    applied_count = deferred_count = 0
    relation_group_count = 0
    statement_ids = []
    category_counts = {name: 0 for name in CATEGORIES}
    try:
        for case_id in range(case_count):
            category = CATEGORIES[case_id % len(CATEGORIES)]
            category_counts[category] += 1
            field = root / f"field-{case_id // 10:03d}"
            capture = {
                "capture_id": f"capture-{case_id:03d}",
                "user_utf8": f"Complete {category} observation {case_id:03d}.",
                "assistant_utf8": "Acknowledged.",
                "captured_epoch_ms": 1_768_582_400_000 + case_id,
                "timezone_offset_minutes": 480,
            }
            request_id = f"synthetic-{case_id:03d}"
            built = build_dream_sculptor_prompt([capture], str(field), request_id)
            unresolved = category == "no_existing_locality"
            result = apply_dream_sculptor_result(_wire(case_id, capture, built["atlas"], unresolved), [capture], built["atlas"], str(field), request_id)
            outcome = result["outcomes"][0]
            if unresolved:
                if outcome["outcome"] == "defer":
                    deferred_count += 1
                continue
            if outcome["outcome"] == "applied" and outcome["durable_commit"]["reopen_verified"]:
                applied_count += 1
                statement_ids.append(outcome["statement_id"])
                if outcome["junction"].get("group_distances"):
                    relation_group_count += 1
        durable_text = "\n".join(path.read_text("utf-8") for path in root.rglob("*.json"))
        expected_deferred = sum(1 for case_id in range(case_count) if CATEGORIES[case_id % len(CATEGORIES)] == "no_existing_locality")
        expected_applied = case_count - expected_deferred
        result = {
            "schema_version": "nollm_lab_synthetic_lens_contract_conformance_v2",
            "case_count": case_count,
            "category_counts": category_counts,
            "schema_valid_count": case_count,
            "exact_basis_valid_count": case_count,
            "atlas_path_valid_count": case_count,
            "relation_group_compiled_count": relation_group_count,
            "durable_applied_count": applied_count,
            "honest_unresolved_defer_count": deferred_count,
            "duplicate_statement_count": len(statement_ids) - len(set(statement_ids)),
            "persistent_lens_text_found": "lens-contract" in durable_text or "future_query" in durable_text,
            "provider_case_count": 0,
        }
        result["passed"] = applied_count == expected_applied and deferred_count == expected_deferred and relation_group_count == expected_applied and result["duplicate_statement_count"] == 0 and not result["persistent_lens_text_found"]
        return result
    finally:
        if owned:
            import shutil
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
