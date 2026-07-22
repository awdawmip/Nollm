from __future__ import annotations

from nollm_access import AccessMemoryLoop, ProgressiveAtlasPolicy

from .adapter import FormationAdapterError
from .sculptor import _workspace


MAIN_AGENT_RECALL_SCHEMA_VERSION = "nollm_openclaw_main_agent_geometry_recall_v1"
BUDGETS = {"default": (4, 3000), "expanded": (8, 6000)}


def _statement_preview(value: object) -> dict[str, object] | None:
    if type(value) is not dict or type(value.get("statement_id")) is not str or type(value.get("content_utf8")) is not str:
        return None
    return {"statement_id": value["statement_id"], "content_utf8": value["content_utf8"]}


def build_main_agent_surface(
    memory_workspace: object,
    operation_id: object,
    max_entries: object = 32,
) -> dict[str, object]:
    if type(operation_id) is not str or not operation_id or len(operation_id) > 128:
        raise FormationAdapterError("invalid_main_agent_recall", "operation_id is required and bounded")
    if type(max_entries) is not int or not 1 <= max_entries <= 32:
        raise FormationAdapterError("invalid_main_agent_recall", "max_entries must be in [1,32]")
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        page = loop.build_progressive_atlas(
            operation_id + ":main-agent-surface",
            ProgressiveAtlasPolicy(max_regions_per_page=max_entries),
        )
        if page.overflow:
            return {
                "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
                "status": "overflow",
                "operation_id": operation_id,
                "core_state_sha256": page.core_state_sha256,
                "entries": [],
                "regions": [],
            }
        entries = [
            {**entry, "region_id": region.region_id}
            for region in page.regions
            for entry in region.support_entries
        ]
        entry_ids = [item["entry_id"] for item in entries]
        if len(entry_ids) != len(set(entry_ids)):
            raise FormationAdapterError("duplicate_atlas_entry", "main-agent Surface contains duplicate entry IDs")
        regions = [{
            "region_id": region.region_id,
            "source_cell_count": region.source_cell_count,
            "native_atom_count": region.native_atom_count,
            "representative_statements": [
                preview for item in region.representative_statements
                if (preview := _statement_preview(item)) is not None
            ],
            "support_entries": [{
                "entry_id": entry["entry_id"],
                "occupancy_count": entry["occupancy_count"],
                "statements": [
                    preview for item in entry["statements"]
                    if (preview := _statement_preview(item)) is not None
                ],
            } for entry in region.support_entries],
        } for region in page.regions]
    return {
        "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
        "status": "surface",
        "operation_id": operation_id,
        "core_state_sha256": page.core_state_sha256,
        "atlas_fingerprint": page.atlas_fingerprint,
        "entries": entries,
        "regions": regions,
        "entry_count": len(entries),
        "single_entry_only": True,
    }


def recall_main_agent_locality(
    memory_workspace: object,
    operation_id: object,
    expected_core_state_sha256: object,
    entry: object,
    budget_option_id: object,
) -> dict[str, object]:
    if type(operation_id) is not str or not operation_id or type(expected_core_state_sha256) is not str or len(expected_core_state_sha256) != 64:
        raise FormationAdapterError("invalid_main_agent_recall", "operation identity or state binding is invalid")
    if type(entry) is not dict or type(entry.get("entry_id")) is not str or type(entry.get("entry_cell")) is not dict:
        raise FormationAdapterError("invalid_main_agent_recall", "one internal entry binding is required")
    if budget_option_id not in BUDGETS:
        raise FormationAdapterError("invalid_main_agent_recall", "unknown budget option")
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        if loop.core_state_sha256() != expected_core_state_sha256:
            raise FormationAdapterError("main_agent_operation_stale", "field changed after Surface selection")
        page = loop.build_progressive_atlas(operation_id + ":main-agent-reopen")
        current = next((
            item
            for region in page.regions
            for item in region.support_entries
            if item["entry_id"] == entry["entry_id"]
        ), None)
        if current is None or current["entry_cell"] != entry["entry_cell"]:
            raise FormationAdapterError("main_agent_operation_stale", "selected entry changed after Surface selection")
        max_results, max_chars = BUDGETS[budget_option_id]
        locality = loop.bounded_locality(
            entry["entry_cell"], operation_id + f":locality:{budget_option_id}", max_results, max_chars,
        )
    return {
        "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
        "status": "locality",
        "operation_id": operation_id,
        "entry_id": entry["entry_id"],
        "budget_option_id": budget_option_id,
        "expansion_options": [] if budget_option_id == "expanded" or not locality["has_more"] else ["expanded"],
        "single_entry_only": True,
        **locality,
    }
