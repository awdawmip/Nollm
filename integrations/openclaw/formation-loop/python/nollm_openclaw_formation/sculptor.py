from __future__ import annotations

import hashlib
import json

from nollm_access import (
    AccessMemoryLoop,
    DREAM_SCULPTOR_SCHEMA_VERSION,
    LocalityAtlas,
    validate_dream_sculptor_plans,
)

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json


DREAM_SCULPTOR_PROMPT_VERSION = "dream-sculptor-v2-lens-causal"


def build_dream_sculptor_prompt(
    captures: object,
    memory_workspace: object,
    request_id: object,
    candidate_limit: object = 32,
    max_statements: object = 8,
) -> dict[str, object]:
    clean = _captures(captures)
    if type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_sculptor_request", "request_id is required")
    if type(candidate_limit) is not int or not 1 <= candidate_limit <= 32 or type(max_statements) is not int or not 1 <= max_statements <= 8:
        raise FormationAdapterError("invalid_sculptor_budget", "Dream Sculptor budgets are invalid")
    with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
        atlas = loop.build_locality_atlas(request_id + ":atlas", candidate_limit)
    captures_wire = [{
        "capture_id": item["capture_id"],
        "user_utf8": item["user_utf8"],
        "user_length_chars": len(item["user_utf8"]),
        "assistant_utf8": item["assistant_utf8"],
        "assistant_length_chars": len(item["assistant_utf8"]),
        "reference_epoch_ms": item["captured_epoch_ms"],
        "timezone_offset_minutes": item["timezone_offset_minutes"],
    } for item in clean]
    prompt = f"""You are Nollm's private Dream Sculptor. Compile complete Evidence-backed propositions and plan their placement in one batch operation.
Never filter a complete proposition by importance, durability, predicted usefulness, or short lifetime. Weather, appointments, cancellations, temporary plans, preferences, and subjective observations are valid.
Form user-grounded memory. Do not turn generic assistant explanations, suggestions, tool limitations, or newly generated background knowledge into user memory unless the user explicitly supplied or adopted that proposition.
Use no_memory only when there is no standalone proposition, the material is empty/tool noise, or it is exact no-new-information. Use defer when a proposition exists but a safe plan cannot be produced.
Positive example: "今天东京下雨了" is a complete weather proposition. Resolve "今天" from its Capture instant, form the Statement, and teach location, absolute-time, and weather-shaped future questions without requiring three entries.
Bad value-filter example: never discard that Tokyo rain fact because weather is short-lived or supposedly low-value.
Bad knowledge-graph example: do not emit Tokyo->weather edges, entities, predicates, topics, or an ontology.
Bad coordinate example: do not invent Cell q/r values. Select only Atlas candidate IDs and let Core solve the Cell.
Bad fanout example: do not force one physical entry per Lens or persist a fact-to-entries map.
For relative time, resolve it once from the Capture reference_epoch_ms and timezone_offset_minutes. Keep the original relative wording only in Capture; make the Statement self-contained and absolute when resolution is possible.
For every Statement, imagine one to four future Recall Lenses. Each Lens is operation-local teaching material and must cite exact character spans from supplied Capture text. It is not a Topic, entity, index, axis registry, or persistent query route.
Span offsets use Python-style Unicode character indices: start is inclusive and end is exclusive. Each role includes its exact length. Prefer the whole supporting role text with start 0 and end equal to that role's supplied length; for a substring, count exactly and ensure text[start:end] equals quote_utf8.
Mark a Lens unresolved when its useful future perspective has no supplied Locality. An unresolved Lens is valid teaching output and must use empty atlas_path_ids and leaf_locality_candidate_ids.
For every resolved Lens, choose complete supplied Atlas path_id values and leaf Locality candidate_id values exposed by those paths. Never output q/r coordinates. There is no separate primary/contact choice: Access compiles resolved Lenses in order into relation groups, and Core chooses the precise Junction Cell.
Use reuse only for materially the same current fact and supply its exact existing_handle. Use revision_current only for the same subject and proposition slot with a superseding value. Additive facts and analogous fields on different subjects are new_local/expand_surface. Defer uncertain revision.
Do not force multiple entries, duplicate a fact, propose Bridge/Stitch, call tools, or reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
schema_version: {DREAM_SCULPTOR_SCHEMA_VERSION}
plan: {{"schema_version":"{DREAM_SCULPTOR_SCHEMA_VERSION}","outcome":"plan","plans":[{{"draft_id":"d1","content_utf8":"complete proposition","source_capture_ids":["capture id"],"lenses":[{{"lens_id":"l1","future_query":"natural future question","basis_spans":[{{"capture_id":"capture id","role":"user|assistant","start":0,"end":1,"quote_utf8":"exact slice"}}],"atlas_path_ids":["supplied path id"],"leaf_locality_candidate_ids":["supplied leaf id"],"unresolved":false}}],"action":"reuse|new_local|expand_surface|revision_current|defer","existing_handle":null,"reason_text":"brief"}}],"defer_reason":null}}
no_memory/defer: {{"schema_version":"{DREAM_SCULPTOR_SCHEMA_VERSION}","outcome":"no_memory|defer","plans":[],"defer_reason":"brief"}}
Draft IDs, source Capture IDs, Lens IDs, path IDs, and leaf candidate ID lists must be unique; fields documented as canonical must be sorted. Maximum Statements: {max_statements}.
request_id: {request_id}
captures: {json.dumps(captures_wire, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
locality_atlas: {json.dumps(atlas.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "status": "sculptor_decision",
        "prompt": prompt,
        "prompt_version": DREAM_SCULPTOR_PROMPT_VERSION,
        "schema_version": DREAM_SCULPTOR_SCHEMA_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "atlas": atlas.to_mapping(),
        "atlas_fingerprint": atlas.atlas_fingerprint,
        "captures": clean,
    }


def parse_dream_sculptor_result(
    raw_response: object,
    captures: object,
    atlas_value: object,
    request_id: object,
) -> dict[str, object]:
    if type(raw_response) is not str or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_sculptor_result", "raw response and request_id are required")
    clean = _captures(captures)
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    keys = {"schema_version", "outcome", "plans", "defer_reason"}
    if type(value) is not dict or set(value) != keys or value.get("schema_version") != DREAM_SCULPTOR_SCHEMA_VERSION or type(value.get("plans")) is not list:
        raise FormationAdapterError("invalid_sculptor_schema", "invalid Dream Sculptor envelope")
    if value["outcome"] in {"no_memory", "defer"}:
        if value["plans"] or type(value["defer_reason"]) is not str or not value["defer_reason"]:
            raise FormationAdapterError("invalid_sculptor_schema", "terminal Sculptor outcome is invalid")
        return {"outcome": value["outcome"], "plans": [], "defer_reason": value["defer_reason"], "json_repair": diagnostics}
    if value["outcome"] != "plan" or not value["plans"] or value["defer_reason"] is not None:
        raise FormationAdapterError("invalid_sculptor_schema", "planned Sculptor outcome is invalid")
    try:
        atlas = LocalityAtlas.from_mapping(atlas_value)
        plans = validate_dream_sculptor_plans(request_id, value["plans"], clean, atlas)
    except (KeyError, TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_sculptor_plan", str(exc)) from exc
    return {"outcome": "plan", "plans": [item.to_mapping() for item in plans], "defer_reason": None, "json_repair": diagnostics}


def apply_dream_sculptor_result(
    raw_response: object,
    captures: object,
    atlas_value: object,
    memory_workspace: object,
    request_id: object,
    revision_confirmations: object = None,
    only_statement_ids: object = None,
) -> dict[str, object]:
    parsed = parse_dream_sculptor_result(raw_response, captures, atlas_value, request_id)
    if parsed["outcome"] != "plan":
        return parsed
    clean = _captures(captures)
    atlas = LocalityAtlas.from_mapping(atlas_value)
    repaired, _diagnostics = repair_dream_json(raw_response)
    raw = json.loads(repaired)
    plans = validate_dream_sculptor_plans(request_id, raw["plans"], clean, atlas)
    if only_statement_ids is not None:
        if type(only_statement_ids) is not list or not only_statement_ids or any(type(item) is not str or not item for item in only_statement_ids):
            raise FormationAdapterError("invalid_sculptor_filter", "only_statement_ids must be a non-empty string list")
        selected = frozenset(only_statement_ids)
        plans = tuple(plan for plan in plans if plan.statement.statement_id in selected)
        if len(plans) != len(selected):
            raise FormationAdapterError("invalid_sculptor_filter", "only_statement_ids contains an unknown Statement")
    with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
        applied = loop.apply_junction_plans(plans, atlas, request_id, revision_confirmations)
    return {**parsed, **applied}


def _captures(value: object) -> list[dict[str, object]]:
    keys = {"capture_id", "user_utf8", "assistant_utf8", "captured_epoch_ms", "timezone_offset_minutes"}
    if type(value) is not list or not value or len(value) > 16:
        raise FormationAdapterError("invalid_sculptor_captures", "Captures must be a bounded non-empty list")
    clean = []
    for item in value:
        if type(item) is not dict or set(item) != keys or type(item["capture_id"]) is not str or type(item["user_utf8"]) is not str or type(item["assistant_utf8"]) is not str:
            raise FormationAdapterError("invalid_sculptor_captures", "Capture fields are invalid")
        if type(item["captured_epoch_ms"]) is not int or type(item["timezone_offset_minutes"]) is not int or not -840 <= item["timezone_offset_minutes"] <= 840:
            raise FormationAdapterError("invalid_sculptor_captures", "Capture reference instant is invalid")
        clean.append(item)
    ids = [item["capture_id"] for item in clean]
    if len(ids) != len(set(ids)):
        raise FormationAdapterError("invalid_sculptor_captures", "Capture IDs must be unique")
    return clean


def _workspace(value: object):
    from pathlib import Path
    if type(value) is not str or not value:
        raise FormationAdapterError("invalid_workspace", "memory_workspace is required")
    return Path(value).resolve()
