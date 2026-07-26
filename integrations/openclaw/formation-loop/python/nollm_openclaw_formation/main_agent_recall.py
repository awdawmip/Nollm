from __future__ import annotations

import json

from nollm_access import AccessMemoryLoop, ProgressiveAtlasPage, ProgressiveAtlasPolicy

from .errors import FormationAdapterError
from .memory_loop import _workspace


MAIN_AGENT_RECALL_SCHEMA_VERSION = "nollm_openclaw_main_agent_geometry_recall_v2"
BUDGETS = {"default": (4, 3000), "expanded": (8, 6000)}


def _routing_anchor(values: object) -> tuple[str, bool]:
    excerpts = []
    truncated = False
    if type(values) is list:
        for value in values:
            if type(value) is not dict or type(value.get("content_utf8")) is not str:
                continue
            content = " ".join(value["content_utf8"].split())
            if content:
                excerpts.append(content)
                truncated = truncated or value.get("truncated") is True
            if len(excerpts) == 2:
                break
    text = " | ".join(excerpts)
    return (text if text else "No representative text", truncated)


def build_main_agent_surface(
    memory_workspace: object,
    operation_id: object,
    policy_mapping: object,
) -> dict[str, object]:
    if type(operation_id) is not str or not operation_id or len(operation_id) > 128:
        raise FormationAdapterError(
            "invalid_main_agent_recall", "operation_id is required and bounded"
        )
    try:
        policy = ProgressiveAtlasPolicy.from_mapping(policy_mapping)
    except (TypeError, ValueError) as error:
        raise FormationAdapterError(
            "invalid_main_agent_recall", "Progressive Atlas policy is invalid"
        ) from error
    root = _workspace(memory_workspace)
    while True:
        with AccessMemoryLoop(root) as loop:
            page = loop.build_progressive_atlas(
                operation_id + ":main-agent-surface", policy
            )
        projected = _project_page(page, operation_id)
        if projected["status"] != "overflow" or policy.max_regions_per_page == 1:
            return projected
        policy = ProgressiveAtlasPolicy(
            max(1, policy.max_regions_per_page // 2),
            policy.max_prompt_bytes,
            policy.max_depth,
            policy.max_order,
            policy.support_limit,
        )


def open_main_agent_region(
    memory_workspace: object,
    operation_id: object,
    parent_page_value: object,
    atlas_region_id: object,
) -> dict[str, object]:
    if (
        type(operation_id) is not str
        or not operation_id
        or type(atlas_region_id) is not str
        or not atlas_region_id
    ):
        raise FormationAdapterError(
            "invalid_main_agent_recall", "operation and region identity are required"
        )
    try:
        parent = ProgressiveAtlasPage.from_mapping(parent_page_value)
    except (TypeError, ValueError) as error:
        raise FormationAdapterError(
            "invalid_main_agent_recall", "parent Atlas page is invalid"
        ) from error
    with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
        try:
            page = loop.open_progressive_region(
                parent, atlas_region_id, operation_id + f":open:{parent.depth + 1}"
            )
        except (TypeError, ValueError) as error:
            raise FormationAdapterError(
                "main_agent_operation_stale", str(error)
            ) from error
    return _project_page(page, operation_id)


def _project_page(page: ProgressiveAtlasPage, operation_id: str) -> dict[str, object]:
    if page.overflow:
        return {
            "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
            "status": "overflow",
            "operation_id": operation_id,
            "core_state_sha256": page.core_state_sha256,
            "atlas_fingerprint": page.atlas_fingerprint,
            "page_fingerprint": page.page_fingerprint,
            "policy": page.policy.to_mapping(),
            "entries": [],
            "regions": [],
        }
    entries = []
    regions = []
    for region_index, region in enumerate(page.regions):
        region_id = f"r{region_index + 1:02d}"
        routing_anchor, routing_truncated = _routing_anchor(
            list(region.representative_statements)
        )
        visible_entries = []
        for entry in region.support_entries:
            entry_id = f"e{len(entries) + 1:03d}"
            entries.append(
                {
                    **entry,
                    "atlas_entry_id": entry["entry_id"],
                    "entry_id": entry_id,
                    "region_id": region_id,
                }
            )
            visible_entries.append(
                {"entry_id": entry_id, "occupancy_count": entry["occupancy_count"]}
            )
        regions.append(
            {
                "region_id": region_id,
                "atlas_region_id": region.region_id,
                "routing_anchor_utf8": routing_anchor,
                "routing_truncated": routing_truncated,
                "source_cell_count": region.source_cell_count,
                "native_atom_count": region.native_atom_count,
                "has_children": not region.leaf,
                "support_entries": visible_entries,
            }
        )
    entry_ids = [item["entry_id"] for item in entries]
    if len(entry_ids) != len(set(entry_ids)):
        raise FormationAdapterError(
            "duplicate_atlas_entry", "main-agent Surface contains duplicate entry IDs"
        )
    routing_chars = sum(len(region["routing_anchor_utf8"]) for region in regions)
    visible_probe = {
        "regions": regions,
        "entry_count": len(entries),
        "region_count": len(regions),
    }
    visible_bytes = len(
        json.dumps(
            visible_probe, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )
    if routing_chars > 3000 or visible_bytes > 8192:
        return {
            "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
            "status": "overflow",
            "operation_id": operation_id,
            "core_state_sha256": page.core_state_sha256,
            "atlas_fingerprint": page.atlas_fingerprint,
            "page_fingerprint": page.page_fingerprint,
            "policy": page.policy.to_mapping(),
            "entries": [],
            "regions": [],
            "routing_text_chars": routing_chars,
            "visible_json_utf8_bytes": visible_bytes,
        }
    return {
        "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
        "status": "surface",
        "operation_id": operation_id,
        "core_state_sha256": page.core_state_sha256,
        "atlas_fingerprint": page.atlas_fingerprint,
        "page_fingerprint": page.page_fingerprint,
        "policy": page.policy.to_mapping(),
        "entries": entries,
        "regions": regions,
        "entry_count": len(entries),
        "region_count": len(regions),
        "routing_text_chars": routing_chars,
        "visible_json_utf8_bytes": visible_bytes,
        "full_statement_body_count": 0,
        "routing_only": True,
        "answer_from_surface": False,
        "private_entry_count": len(entries),
        "tool_visible_entry_count": len(entries),
        "single_entry_only": True,
        "page": page.to_mapping(),
        "depth": page.depth,
    }


def recall_main_agent_locality(
    memory_workspace: object,
    operation_id: object,
    expected_core_state_sha256: object,
    expected_atlas_fingerprint: object,
    expected_page_fingerprint: object,
    policy_mapping: object,
    entry: object,
    budget_option_id: object,
    page_value: object = None,
) -> dict[str, object]:
    fingerprints = (
        expected_core_state_sha256,
        expected_atlas_fingerprint,
        expected_page_fingerprint,
    )
    if (
        type(operation_id) is not str
        or not operation_id
        or any(type(value) is not str or len(value) != 64 for value in fingerprints)
    ):
        raise FormationAdapterError(
            "invalid_main_agent_recall",
            "operation identity or state binding is invalid",
        )
    if (
        type(entry) is not dict
        or type(entry.get("entry_id")) is not str
        or type(entry.get("entry_cell")) is not dict
    ):
        raise FormationAdapterError(
            "invalid_main_agent_recall", "one internal entry binding is required"
        )
    if budget_option_id not in BUDGETS:
        raise FormationAdapterError(
            "invalid_main_agent_recall", "unknown budget option"
        )
    try:
        policy = ProgressiveAtlasPolicy.from_mapping(policy_mapping)
    except (TypeError, ValueError) as error:
        raise FormationAdapterError(
            "invalid_main_agent_recall", "Progressive Atlas policy is invalid"
        ) from error
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        if loop.core_state_sha256() != expected_core_state_sha256:
            raise FormationAdapterError(
                "main_agent_operation_stale", "field changed after Surface selection"
            )
        try:
            page = (
                loop.build_progressive_atlas(
                    operation_id + ":main-agent-surface", policy
                )
                if page_value is None
                else ProgressiveAtlasPage.from_mapping(page_value)
            )
        except (TypeError, ValueError) as error:
            raise FormationAdapterError(
                "invalid_main_agent_recall", "selected Atlas page is invalid"
            ) from error
        if (
            page.atlas_fingerprint != expected_atlas_fingerprint
            or page.page_fingerprint != expected_page_fingerprint
        ):
            raise FormationAdapterError(
                "main_agent_operation_stale",
                "Atlas or page changed after Surface selection",
            )
        current = next(
            (
                item
                for region in page.regions
                for item in region.support_entries
                if item["entry_id"] == entry.get("atlas_entry_id", entry["entry_id"])
            ),
            None,
        )
        if current is None or current["entry_cell"] != entry["entry_cell"]:
            raise FormationAdapterError(
                "main_agent_operation_stale",
                "selected entry changed after Surface selection",
            )
        max_results, max_chars = BUDGETS[budget_option_id]
        locality = loop.bounded_locality(
            entry["entry_cell"],
            operation_id + f":locality:{budget_option_id}",
            max_results,
            max_chars,
        )
    return {
        "schema_version": MAIN_AGENT_RECALL_SCHEMA_VERSION,
        "status": "locality",
        "operation_id": operation_id,
        "entry_id": entry["entry_id"],
        "region_id": entry.get("region_id"),
        "budget_option_id": budget_option_id,
        "expansion_options": []
        if budget_option_id == "expanded" or not locality["has_more"]
        else ["expanded"],
        "single_entry_only": True,
        **locality,
    }
