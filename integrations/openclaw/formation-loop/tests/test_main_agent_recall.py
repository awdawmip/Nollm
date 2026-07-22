import json

import pytest

from nollm_openclaw_formation.adapter import FormationAdapterError
from nollm_openclaw_formation.main_agent_recall import (
    MAIN_AGENT_RECALL_SCHEMA_VERSION,
    build_main_agent_surface,
    recall_main_agent_locality,
)
from nollm_openclaw_formation.memory_loop import (
    BATCH_PLACEMENT_SCHEMA_VERSION,
    apply_batch_placement,
    build_batch_placement_prompt,
)
from nollm_access import ProgressiveAtlasPolicy


POLICY = ProgressiveAtlasPolicy().to_mapping()


def recall(workspace, operation_id, surface, entry, budget):
    return recall_main_agent_locality(
        str(workspace), operation_id, surface["core_state_sha256"],
        surface["atlas_fingerprint"], surface["page_fingerprint"], surface["policy"], entry, budget,
    )


def seed(workspace, count: int, request_id: str = "seed") -> None:
    statements = [
        {"statement_id": f"{request_id}-statement-{index:02d}", "content_utf8": f"fact {index:02d} " + "x" * 20, "source_handle": None, "context_refs": []}
        for index in range(count)
    ]
    built = build_batch_placement_prompt(statements, str(workspace), request_id, count, count)
    empty = [item for item in built["candidates"] if item["occupancy"]["count"] == 0]
    statements = statements[:len(empty)]
    decisions = [{
        "statement_id": statement["statement_id"],
        "outcome": "apply",
        "action": "expand_surface" if empty[index]["relation_kind"] == "expand_surface" else "new_local",
        "candidate_id": empty[index]["candidate_id"],
        "reason_text": "main-agent locality fixture",
    } for index, statement in enumerate(statements)]
    result = apply_batch_placement(
        json.dumps({"schema_version": BATCH_PLACEMENT_SCHEMA_VERSION, "decisions": decisions}),
        statements, str(workspace), request_id, built["view_fingerprint"], count, count,
    )
    assert all(item["outcome"] == "applied" for item in result["outcomes"])


def test_main_agent_surface_hides_coordinates_and_recall_is_single_entry_bounded(tmp_path):
    seed(tmp_path, 8)
    surface = build_main_agent_surface(str(tmp_path), "operation-one", POLICY)
    assert surface["schema_version"] == MAIN_AGENT_RECALL_SCHEMA_VERSION
    assert surface["single_entry_only"] is True
    assert surface["entry_count"] >= 1
    assert all("entry_cell" not in entry for region in surface["regions"] for entry in region["support_entries"])
    assert all("representative_statements" not in region for region in surface["regions"])
    assert all("statements" not in entry for region in surface["regions"] for entry in region["support_entries"])
    assert surface["routing_only"] is True and surface["answer_from_surface"] is False
    assert all(len(region["routing_anchor_utf8"]) <= 96 for region in surface["regions"])
    assert surface["full_statement_body_count"] == 0
    assert surface["routing_text_chars"] <= 3000
    assert surface["visible_json_utf8_bytes"] <= 8192
    assert '"q"' not in json.dumps(surface["regions"], sort_keys=True)
    entry = surface["entries"][0]
    default = recall(tmp_path, "operation-one", surface, entry, "default")
    assert default["entry_id"] == entry["entry_id"]
    assert default["result_count"] <= 4
    assert default["rendered_chars"] <= 3000
    assert all(item["entry_relative_rank"] >= 1 for item in default["items"])
    assert all("score_q16" in item and "path" in item for item in default["items"])
    assert all("address" not in item and "handle" not in item for item in default["items"])
    expanded = recall(tmp_path, "operation-one", surface, entry, "expanded")
    assert expanded["entry_id"] == default["entry_id"]
    assert expanded["result_count"] >= default["result_count"]
    assert expanded["max_results"] == 8


def test_main_agent_operation_is_invalid_after_field_mutation(tmp_path):
    seed(tmp_path, 1, "first")
    surface = build_main_agent_surface(str(tmp_path), "stale-operation", POLICY)
    seed(tmp_path, 1, "second")
    with pytest.raises(FormationAdapterError, match="field changed"):
        recall(tmp_path, "stale-operation", surface, surface["entries"][0], "default")


@pytest.mark.parametrize("budget", ["large", "", None, 4])
def test_main_agent_recall_rejects_unknown_budget_options(tmp_path, budget):
    seed(tmp_path, 1)
    surface = build_main_agent_surface(str(tmp_path), "budget-operation", POLICY)
    with pytest.raises(FormationAdapterError, match="unknown budget"):
        recall(tmp_path, "budget-operation", surface, surface["entries"][0], budget)


def test_nondefault_policy_is_reused_for_recall(tmp_path):
    seed(tmp_path, 8)
    policy = ProgressiveAtlasPolicy(max_regions_per_page=8, max_prompt_bytes=32768, max_depth=6).to_mapping()
    surface = build_main_agent_surface(str(tmp_path), "nondefault-policy", policy)
    result = recall(tmp_path, "nondefault-policy", surface, surface["entries"][0], "default")
    assert result["status"] == "locality"
    assert surface["policy"] == policy


def test_recall_rejects_changed_policy_and_page_identity(tmp_path):
    seed(tmp_path, 2)
    surface = build_main_agent_surface(str(tmp_path), "policy-stale", POLICY)
    changed = {**surface["policy"], "max_depth": 7}
    with pytest.raises(FormationAdapterError, match="Atlas or page changed"):
        recall_main_agent_locality(
            str(tmp_path), "policy-stale", surface["core_state_sha256"], surface["atlas_fingerprint"],
            surface["page_fingerprint"], changed, surface["entries"][0], "default",
        )
