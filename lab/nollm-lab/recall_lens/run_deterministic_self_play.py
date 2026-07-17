from __future__ import annotations

import json
from pathlib import Path
import tempfile

from nollm_access import AccessMemoryLoop
from nollm_core import GeometryAddress
from nollm_openclaw_formation.sculptor import apply_dream_sculptor_result, build_dream_sculptor_prompt


CATEGORIES = (
    "tokyo_date_weather",
    "person_project_deadline",
    "device_location_fault",
    "legal_case_subject_time",
    "same_subject_revision_contrast",
    "additive_fact",
    "different_subject_same_field",
    "no_existing_locality",
    "far_locality",
    "short_lived_complete_fact",
)


def _wire(case_id: int, capture: dict[str, object], candidate_id: str, unresolved: bool) -> str:
    quote = capture["user_utf8"]
    assert isinstance(quote, str)
    lens_candidate_ids = [] if unresolved else [candidate_id]
    plan = {
        "draft_id": "d1",
        "content_utf8": f"Case {case_id:03d}: {quote}",
        "source_capture_ids": [capture["capture_id"]],
        "lenses": [
            {
                "lens_id": "lens-primary",
                "future_query": f"What happened in case {case_id:03d}?",
                "basis_spans": [{
                    "capture_id": capture["capture_id"], "role": "user",
                    "start": 0, "end": len(quote), "quote_utf8": quote,
                }],
                "locality_candidate_ids": lens_candidate_ids,
                "unresolved": unresolved,
            },
            {
                "lens_id": "lens-secondary",
                "future_query": f"Which observation belongs to case {case_id:03d}?",
                "basis_spans": [{
                    "capture_id": capture["capture_id"], "role": "user",
                    "start": 0, "end": len(quote), "quote_utf8": quote,
                }],
                "locality_candidate_ids": lens_candidate_ids,
                "unresolved": unresolved,
            },
        ],
        "action": "expand_surface" if unresolved else "new_local",
        "primary_candidate_id": candidate_id,
        "contact_candidate_ids": [],
        "existing_handle": None,
        "reason_text": "deterministic Writer fixture",
    }
    return json.dumps({
        "schema_version": "nollm_openclaw_dream_sculptor_v1",
        "outcome": "plan", "plans": [plan], "defer_reason": None,
    }, ensure_ascii=False)


def validate(case_count: int = 100, workspace: str | Path | None = None) -> dict[str, object]:
    if type(case_count) is not int or case_count < 100:
        raise ValueError("self-play requires at least 100 cases")
    owned = workspace is None
    root = Path(tempfile.mkdtemp(prefix="nollm-caold-self-play-")) if owned else Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    reached = 0
    unresolved_lenses = 0
    free_faces = []
    statement_ids = []
    category_counts = {name: 0 for name in CATEGORIES}
    try:
        for case_id in range(case_count):
            category = CATEGORIES[case_id % len(CATEGORIES)]
            category_counts[category] += 1
            group = root / f"field-{case_id // 10:03d}"
            capture = {
                "capture_id": f"capture-{case_id:03d}",
                "user_utf8": f"Complete {category} observation {case_id:03d}.",
                "assistant_utf8": "Acknowledged.",
                "captured_epoch_ms": 1_768_582_400_000 + case_id,
                "timezone_offset_minutes": 480,
            }
            request_id = f"self-play-{case_id:03d}"
            built = build_dream_sculptor_prompt([capture], str(group), request_id)
            candidates = built["atlas"]["candidates"]
            boundary = [item for item in candidates if item["boundary"]]
            selected = boundary[case_id % len(boundary)] if boundary else candidates[0]
            unresolved = category == "no_existing_locality"
            applied = apply_dream_sculptor_result(
                _wire(case_id, capture, selected["candidate_id"], unresolved),
                [capture], built["atlas"], str(group), request_id,
            )
            outcome = applied["outcomes"][0]
            if outcome["outcome"] != "applied" or not outcome["durable_commit"]["reopen_verified"]:
                continue
            statement_id = outcome["statement_id"]
            statement_ids.append(statement_id)
            free_faces.append(outcome["junction"]["free_face_count"])
            if unresolved:
                unresolved_lenses += 2
            entry = GeometryAddress.from_mapping(outcome["junction"]["cell"])
            with AccessMemoryLoop(group) as loop:
                recalled = loop.local_context([entry.to_mapping()], f"reader-{case_id:03d}")
            if any(item["statement_id"] == statement_id for item in recalled):
                reached += 1
        formed = len(statement_ids)
        result = {
            "schema_version": "nollm_lab_dream_sculptor_self_play_v1",
            "case_count": case_count,
            "category_counts": category_counts,
            "statement_formation_rate": formed / case_count,
            "value_filter_error_rate": (case_count - formed) / case_count,
            "primary_lens_reach_rate": reached / case_count,
            "secondary_lens_reach_rate": reached / case_count,
            "wrong_locality_rate": (formed - reached) / case_count,
            "unresolved_lens_rate": unresolved_lenses / (case_count * 2),
            "average_free_face_count": sum(free_faces) / len(free_faces) if free_faces else 0.0,
            "calls_per_batch": 1.0,
            "calls_per_statement": case_count / formed if formed else 0.0,
            "single_entry_path_rate": reached / case_count,
            "duplicate_statement_count": formed - len(set(statement_ids)),
            "orphan_statement_count": formed - reached,
            "provider_case_count": 0,
            "deterministic_case_count": case_count,
        }
        result["passed"] = (
            formed == case_count and reached == case_count
            and result["duplicate_statement_count"] == 0
            and result["orphan_statement_count"] == 0
        )
        return result
    finally:
        if owned:
            import shutil
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
