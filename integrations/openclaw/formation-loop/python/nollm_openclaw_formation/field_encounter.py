from __future__ import annotations

import json
from time import time_ns

from nollm_access import (
    AccessMemoryLoop,
    EncounterCommitRequest,
    FieldEncounterEngine,
    FieldEncounterRequest,
    MemoryStatement,
    PendingProposition,
    ProgressiveAtlasPolicy,
    RevisionConfirmationResult,
)
from nollm_core import PhysicalFieldScope

from .errors import FormationAdapterError
from .main_agent_recall import _project_page
from .memory_loop import _workspace
from .json_repair import repair_json_envelope


FIELD_ENCOUNTER_BRIDGE_SCHEMA_VERSION = "nollm_openclaw_field_encounter_v1"
TERMINAL_ACTIONS = frozenset({"select_fact", "select_vacancy", "none", "defer"})


def _exact_mapping(value: object, keys: set[str], name: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise FormationAdapterError("invalid_field_encounter", f"{name} is not canonical")
    return value


def _pending(value: object) -> PendingProposition | None:
    if value is None:
        return None
    item = _exact_mapping(
        value,
        {
            "proposition_id",
            "content_utf8",
            "evidence_refs",
            "origin_kinds",
            "derived_from_statement_ids",
            "formation_version",
        },
        "pending proposition",
    )
    for name in ("evidence_refs", "origin_kinds", "derived_from_statement_ids"):
        if type(item[name]) is not list:
            raise FormationAdapterError(
                "invalid_field_encounter", f"pending proposition {name} must be an array"
            )
    try:
        return PendingProposition(
            item["proposition_id"],
            item["content_utf8"],
            tuple(item["evidence_refs"]),
            tuple(item["origin_kinds"]),
            tuple(item["derived_from_statement_ids"]),
            item["formation_version"],
        )
    except (TypeError, ValueError) as error:
        raise FormationAdapterError("invalid_field_encounter", str(error)) from error


def _request(
    root: object,
    operation_id: object,
    request_value: object,
) -> FieldEncounterRequest:
    item = _exact_mapping(
        request_value,
        {
            "scope_id",
            "workspace_id",
            "stimulus_material",
            "optional_pending_proposition",
            "field_scope",
            "surface_policy",
            "locality_max_results",
            "locality_max_chars",
            "vacancy_budget",
            "expected_state_identity",
            "created_at_ms",
            "ttl_ms",
        },
        "Encounter request",
    )
    if type(item["stimulus_material"]) is not list:
        raise FormationAdapterError(
            "invalid_field_encounter", "stimulus_material must be an array"
        )
    expected = item["expected_state_identity"]
    if expected is None:
        with AccessMemoryLoop(root) as loop:
            expected = loop.core_state_sha256()
    created = item["created_at_ms"]
    if created is None:
        created = time_ns() // 1_000_000
    try:
        return FieldEncounterRequest(
            operation_id,
            item["scope_id"],
            item["workspace_id"],
            tuple(item["stimulus_material"]),
            _pending(item["optional_pending_proposition"]),
            PhysicalFieldScope.from_mapping(item["field_scope"]),
            ProgressiveAtlasPolicy.from_mapping(item["surface_policy"]),
            item["locality_max_results"],
            item["locality_max_chars"],
            item["vacancy_budget"],
            expected,
            created,
            item["ttl_ms"],
        )
    except (TypeError, ValueError) as error:
        raise FormationAdapterError("invalid_field_encounter", str(error)) from error


def _request_mapping(request: FieldEncounterRequest) -> dict[str, object]:
    return {
        "scope_id": request.scope_id,
        "workspace_id": request.workspace_id,
        "stimulus_material": list(request.stimulus_material),
        "optional_pending_proposition": (
            request.optional_pending_proposition.to_mapping()
            if request.optional_pending_proposition
            else None
        ),
        "field_scope": request.field_scope.to_mapping(),
        "surface_policy": request.surface_policy.to_mapping(),
        "locality_max_results": request.locality_max_results,
        "locality_max_chars": request.locality_max_chars,
        "vacancy_budget": request.vacancy_budget,
        "expected_state_identity": request.expected_state_identity,
        "created_at_ms": request.created_at_ms,
        "ttl_ms": request.ttl_ms,
    }


def _visible_page(operation: object) -> dict[str, object]:
    projected = _project_page(operation.current_page, operation.request.operation_id)
    return {
        key: value
        for key, value in projected.items()
        if key not in {"entries", "page", "core_state_sha256", "atlas_fingerprint", "page_fingerprint", "policy"}
    }


def _page_bindings(operation: object) -> tuple[dict[str, str], dict[str, tuple[str, str]]]:
    projected = _project_page(operation.current_page, operation.request.operation_id)
    regions = {
        item["region_id"]: item["atlas_region_id"] for item in projected.get("regions", [])
    }
    entries = {
        item["entry_id"]: (item["region_id"], item["atlas_entry_id"])
        for item in projected.get("entries", [])
    }
    return regions, entries


def _visible_locality(locality: object) -> dict[str, object]:
    return {
        "schema_version": FIELD_ENCOUNTER_BRIDGE_SCHEMA_VERSION,
        "status": "locality",
        "operation_id": locality.operation_id,
        "root_identity": locality.root_identity,
        "page_fingerprint": locality.page_fingerprint,
        "entry_id": locality.entry_id,
        "facts": [
            {
                "fact_id": item.fact_id,
                "statement_id": item.statement_id,
                "content_utf8": item.content_utf8,
                "revision_eligible": item.revision_eligible,
                "provenance_sha256": item.provenance_sha256,
            }
            for item in locality.facts
        ],
        "vacancies": [
            {
                "vacancy_id": item.vacancy_id,
                "vacancy_kind": item.vacancy_kind,
                "capacity": item.capacity,
                "boundary": item.boundary,
                "relation_group_count": len(item.relation_groups),
                "free_face_count": item.free_face_count,
                "expires_at_ms": item.expires_at_ms,
            }
            for item in locality.vacancies
        ],
        "legal_actions": [action for action in locality.legal_actions if action != "cancel"],
        "single_entry_only": True,
    }


def _result_mapping(engine: FieldEncounterEngine, result: object) -> dict[str, object]:
    effect = result.effect
    return {
        "schema_version": FIELD_ENCOUNTER_BRIDGE_SCHEMA_VERSION,
        "status": "terminal",
        "operation_id": result.operation_id,
        "terminal_kind": result.terminal_kind,
        "semantic_relation": result.semantic_relation,
        "recalled_statement_ids": list(result.recalled_statement_ids),
        "state_identity": result.state_identity,
        "path_digest": result.path_digest,
        "terminal_result_identity": engine.result_identity(result),
        "effect": {
            "effect_kind": effect.effect_kind,
            "pending_proposition_identity": effect.pending_proposition_identity,
            "selected_fact_id": effect.selected_fact_id,
            "selected_vacancy_id": effect.selected_vacancy_id,
            "provisional_revision": (
                effect.provisional_revision.to_mapping()
                if effect.provisional_revision
                else None
            ),
            "retryable": effect.retryable,
            "commit_eligible": effect.commit_eligible,
        },
        "single_entry_only": True,
    }


def _commit(
    engine: FieldEncounterEngine,
    request: FieldEncounterRequest,
    result: object,
    value: object,
) -> dict[str, object]:
    item = _exact_mapping(value, {"statement", "revision_confirmation"}, "commit")
    try:
        statement = MemoryStatement.from_mapping(item["statement"])
        confirmation = (
            RevisionConfirmationResult.from_mapping(item["revision_confirmation"])
            if item["revision_confirmation"] is not None
            else None
        )
        committed = engine.commit(
            EncounterCommitRequest(
                request.operation_id,
                result.state_identity,
                engine.result_identity(result),
                request.optional_pending_proposition.identity,
                statement,
                confirmation,
            )
        )
    except (TypeError, ValueError) as error:
        raise FormationAdapterError("invalid_field_encounter", str(error)) from error
    return {
        "commit_state": committed.commit_state,
        "statement_id": committed.statement_id,
        "handle": committed.handle.to_mapping() if committed.handle else None,
        "core_write_count": committed.core_write_count,
        "reopen_verified": committed.reopen_verified,
        "error_type": committed.error_type,
    }


def run_field_encounter(
    memory_workspace: object,
    operation_id: object,
    request_value: object,
    history_value: object,
    terminal_value: object = None,
    commit_value: object = None,
) -> dict[str, object]:
    if type(operation_id) is not str or not operation_id or len(operation_id) > 128:
        raise FormationAdapterError("invalid_field_encounter", "operation_id is required and bounded")
    if type(history_value) is not list or len(history_value) > 12:
        raise FormationAdapterError("invalid_field_encounter", "history must be a bounded array")
    root = _workspace(memory_workspace)
    request = _request(root, operation_id, request_value)
    engine = FieldEncounterEngine(root)
    try:
        operation = engine.begin(request)
        locality = None
        for index, raw in enumerate(history_value):
            if type(raw) is not dict or raw.get("action") not in {"open_region", "enter_locality"}:
                raise FormationAdapterError("invalid_field_encounter", "history action is invalid")
            if raw["action"] == "open_region":
                if set(raw) != {"action", "region_id"} or locality is not None:
                    raise FormationAdapterError("invalid_field_encounter", "open_region history is invalid")
                regions, _entries = _page_bindings(operation)
                internal = regions.get(raw["region_id"])
                if internal is None:
                    raise FormationAdapterError("field_encounter_stale", "region is no longer visible")
                operation = engine.open_region(operation_id, internal)
                continue
            if set(raw) != {"action", "region_id", "entry_id"} or index != len(history_value) - 1:
                raise FormationAdapterError("invalid_field_encounter", "enter_locality must be the final path action")
            _regions, entries = _page_bindings(operation)
            binding = entries.get(raw["entry_id"])
            if binding is None or binding[0] != raw["region_id"]:
                raise FormationAdapterError("field_encounter_stale", "entry is no longer visible")
            projected = _project_page(operation.current_page, operation_id)
            internal_region = next(
                item["atlas_region_id"]
                for item in projected["regions"]
                if item["region_id"] == raw["region_id"]
            )
            locality = engine.enter_locality(operation_id, internal_region, binding[1])
        response: dict[str, object]
        result = None
        if terminal_value is not None:
            if locality is None:
                raise FormationAdapterError("invalid_field_encounter", "terminal requires one Locality")
            terminal = _exact_mapping(
                terminal_value,
                {"action", "candidate_id", "semantic_relation", "recalled_fact_ids"},
                "terminal",
            )
            if terminal["action"] not in TERMINAL_ACTIONS or type(terminal["recalled_fact_ids"]) is not list:
                raise FormationAdapterError("invalid_field_encounter", "terminal action is invalid")
            try:
                result = engine.resolve(
                    operation_id,
                    terminal["action"],
                    terminal["candidate_id"],
                    terminal["semantic_relation"],
                    tuple(terminal["recalled_fact_ids"]),
                )
            except (TypeError, ValueError) as error:
                raise FormationAdapterError("invalid_field_encounter", str(error)) from error
            response = _result_mapping(engine, result)
        elif locality is not None:
            response = _visible_locality(locality)
        else:
            response = {
                "schema_version": FIELD_ENCOUNTER_BRIDGE_SCHEMA_VERSION,
                "status": "surface" if not history_value else "region",
                "operation_id": operation_id,
                "root_identity": operation.root_identity,
                "page": _visible_page(operation),
                "single_entry_only": True,
            }
        if commit_value is not None:
            if result is None or request.optional_pending_proposition is None:
                raise FormationAdapterError("invalid_field_encounter", "commit requires a pending terminal")
            response["commit"] = _commit(engine, request, result, commit_value)
        return {"request": _request_mapping(request), **response}
    finally:
        engine.cancel(operation_id)


def evidence_ref_tokens(value: object) -> list[str]:
    if type(value) is not list:
        raise FormationAdapterError("invalid_field_encounter", "evidence_refs must be an array")
    tokens = []
    for item in value:
        if type(item) is not dict:
            raise FormationAdapterError("invalid_field_encounter", "Evidence ref must be an object")
        tokens.append(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return tokens


def build_field_encounter_prompt(
    response: object, pending_proposition: object, turn: object
) -> dict[str, object]:
    if type(response) is not dict or response.get("status") not in {
        "surface",
        "region",
        "locality",
    }:
        raise FormationAdapterError("invalid_field_encounter", "Encounter response is not navigable")
    if type(turn) is not int or not 1 <= turn <= 12:
        raise FormationAdapterError("invalid_field_encounter", "Encounter turn is invalid")
    status = response["status"]
    if status in {"surface", "region"}:
        page = response.get("page")
        if type(page) is not dict or type(page.get("regions")) is not list:
            raise FormationAdapterError("invalid_field_encounter", "Encounter page is invalid")
        instruction = (
            'Return {"action":"open_region","region_id":"visible id"} or '
            '{"action":"enter_locality","region_id":"visible id","entry_id":"visible id"}.'
        )
    else:
        instruction = (
            'Return exactly {"action":"select_fact|select_vacancy|none|defer",'
            '"candidate_id":"visible id or null","semantic_relation":"same|revision|related_distinct|unrelated|uncertain or null",'
            '"recalled_fact_ids":[],"revision_confirmation":null}. '
            "For a revision, revision_confirmation must be the exact canonical confirmation envelope; "
            "for every other action it must be null. Select only visible IDs."
        )
    prompt = (
        "You are continuing the Proposition Writer in the same Host session. "
        "Navigate the operation-neutral Field Encounter and choose one physical terminal. "
        "Do not invent IDs, coordinates, facts, vacancies, or semantic relations. "
        "Return one raw JSON object and no markdown.\n"
        + instruction
        + "\nPending proposition:\n"
        + json.dumps(pending_proposition, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\nVisible Encounter state:\n"
        + json.dumps(response, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )
    if len(prompt.encode("utf-8")) > 65536:
        raise FormationAdapterError("field_encounter_prompt_overflow", "Encounter prompt exceeds 65536 bytes")
    return {
        "schema_version": FIELD_ENCOUNTER_BRIDGE_SCHEMA_VERSION,
        "status": "encounter_decision",
        "turn": turn,
        "prompt": prompt,
    }


def parse_field_encounter_decision(
    raw_model_response: object, response: object
) -> dict[str, object]:
    if type(raw_model_response) is not str or not raw_model_response:
        raise FormationAdapterError("invalid_field_encounter", "model response is required")
    if type(response) is not dict:
        raise FormationAdapterError("invalid_field_encounter", "Encounter response is invalid")
    try:
        repaired, _diagnostics = repair_json_envelope(raw_model_response)
        value = json.loads(repaired)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise FormationAdapterError("invalid_json", str(error)) from error
    status = response.get("status")
    if status in {"surface", "region"}:
        if type(value) is not dict or value.get("action") not in {"open_region", "enter_locality"}:
            raise FormationAdapterError("invalid_field_encounter", "navigation decision is invalid")
        keys = {"action", "region_id"} if value["action"] == "open_region" else {"action", "region_id", "entry_id"}
        if set(value) != keys:
            raise FormationAdapterError("invalid_field_encounter", "navigation decision is not canonical")
        regions = response.get("page", {}).get("regions", [])
        region = next((item for item in regions if item.get("region_id") == value.get("region_id")), None)
        if region is None:
            raise FormationAdapterError("invalid_field_encounter", "selected region is not visible")
        if value["action"] == "enter_locality" and value.get("entry_id") not in {
            item.get("entry_id") for item in region.get("support_entries", [])
        }:
            raise FormationAdapterError("invalid_field_encounter", "selected entry is not visible")
        return value
    if status != "locality" or type(value) is not dict or set(value) != {
        "action", "candidate_id", "semantic_relation", "recalled_fact_ids", "revision_confirmation"
    }:
        raise FormationAdapterError("invalid_field_encounter", "terminal decision is not canonical")
    action = value.get("action")
    if action not in TERMINAL_ACTIONS or type(value.get("recalled_fact_ids")) is not list:
        raise FormationAdapterError("invalid_field_encounter", "terminal action is invalid")
    fact_ids = {item.get("fact_id") for item in response.get("facts", [])}
    vacancy_ids = {item.get("vacancy_id") for item in response.get("vacancies", [])}
    if any(item not in fact_ids for item in value["recalled_fact_ids"]):
        raise FormationAdapterError("invalid_field_encounter", "recalled fact is not visible")
    if action == "select_fact" and value.get("candidate_id") not in fact_ids:
        raise FormationAdapterError("invalid_field_encounter", "selected fact is not visible")
    if action == "select_vacancy" and value.get("candidate_id") not in vacancy_ids:
        raise FormationAdapterError("invalid_field_encounter", "selected vacancy is not visible")
    if action in {"none", "defer"} and value.get("candidate_id") is not None:
        raise FormationAdapterError("invalid_field_encounter", "NONE/defer cannot select a candidate")
    return value
