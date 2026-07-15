from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

from nollm_access import (
    AccessMemoryLoop,
    AccessSurfaceNavigator,
    DEFAULT_FIELD_SCOPE,
    MemoryStatement,
    PLACEMENT_SURFACE_BUDGET,
    RECALL_SURFACE_BUDGET,
    SurfaceBudgetProfile,
)

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json


TRAVERSAL_SCHEMA_VERSION = "nollm_openclaw_translation_normalized_surface_traversal_v1"
PHYSICAL_ENTRY_SCHEMA_VERSION = "nollm_openclaw_single_physical_entry_recall_v1"
PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_surface_placement_v1"
RECALL_SCHEMA_VERSION = "nollm_openclaw_surface_recall_v1"


def _workspace(path: object) -> Path:
    if type(path) is not str or not path:
        raise FormationAdapterError("invalid_workspace", "memory workspace is required")
    return Path(path).resolve()


def _statement(value: object) -> MemoryStatement:
    try:
        return MemoryStatement.from_mapping(value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_statement", str(exc)) from exc


def _budget(value: object, default: SurfaceBudgetProfile) -> SurfaceBudgetProfile:
    if value is None:
        return default
    if type(value) is not dict or set(value) != set(SurfaceBudgetProfile.__dataclass_fields__):
        raise FormationAdapterError("invalid_surface_budget", "Surface budget fields are invalid")
    try:
        return SurfaceBudgetProfile(**value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_surface_budget", str(exc)) from exc


def _begin(
    mode: str,
    subject: str,
    memory_workspace: object,
    request_id: object,
    budget_value: object,
) -> dict[str, object]:
    if type(subject) is not str or not subject or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "Surface request fields are invalid")
    root = _workspace(memory_workspace)
    default = RECALL_SURFACE_BUDGET if mode == "recall" else PLACEMENT_SURFACE_BUDGET
    navigator = AccessSurfaceNavigator(root)
    page = navigator.begin(request_id, DEFAULT_FIELD_SCOPE, _budget(budget_value, default))
    if mode == "recall" and not page.cells:
        return {"status": "complete_none", "available": False, "surface": page.to_mapping()}
    if mode == "placement" and not page.cells:
        return _placement_decision(root, _statement(json.loads(subject)), request_id, None, page)
    return _traversal_response(mode, subject, navigator, page)


def build_recall_prompt(
    query: object,
    memory_workspace: object,
    request_id: object,
    surface_budget: object = None,
) -> dict[str, object]:
    if type(query) is not str:
        raise FormationAdapterError("invalid_request", "query must be a string")
    return _begin("recall", query, memory_workspace, request_id, surface_budget)


def build_placement_prompt(
    statement_value: object,
    memory_workspace: object,
    request_id: object,
    surface_budget: object = None,
) -> dict[str, object]:
    statement = _statement(statement_value)
    subject = json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _begin("placement", subject, memory_workspace, request_id, surface_budget)


def advance_recall_traversal(
    query: object,
    traversal_state: object,
    raw_response: object,
    memory_workspace: object,
) -> dict[str, object]:
    if type(query) is not str or not query:
        raise FormationAdapterError("invalid_request", "query is required")
    return _advance("recall", query, traversal_state, raw_response, memory_workspace)


def advance_placement_traversal(
    statement_value: object,
    traversal_state: object,
    raw_response: object,
    memory_workspace: object,
) -> dict[str, object]:
    statement = _statement(statement_value)
    subject = json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return _advance("placement", subject, traversal_state, raw_response, memory_workspace)


def _advance(
    mode: str,
    subject: str,
    traversal_state: object,
    raw_response: object,
    memory_workspace: object,
) -> dict[str, object]:
    if type(raw_response) is not str:
        raise FormationAdapterError("invalid_request", "Surface traversal response must be a string")
    root = _workspace(memory_workspace)
    navigator = AccessSurfaceNavigator(root)
    try:
        if _is_physical_state(traversal_state):
            return _advance_physical(mode, subject, traversal_state, raw_response, root, navigator)
        state = navigator.state_from_mapping(traversal_state)
        if state.call_count < 1:
            raise ValueError("Surface state has no displayed page")
        page = navigator.page(replace(state, call_count=state.call_count - 1))
        decision = _traversal_decision(raw_response)
        action = decision["action"]
        if action == "continue_page":
            return _traversal_response(mode, subject, navigator, navigator.continue_page(page))
        if action == "open_surface_cell":
            return _traversal_response(mode, subject, navigator, navigator.open_surface_cell(page, decision["candidate_id"]))
        if action == "open_physical_entries":
            return _physical_entry_response(mode, subject, navigator, navigator.open_physical_entries(page, decision["candidate_id"]))
        if action == "request_coarser_surface":
            return _traversal_response(mode, subject, navigator, navigator.request_coarser_surface(page))
        if action == "return_to_parent":
            return _traversal_response(mode, subject, navigator, navigator.return_to_parent(page))
        if action in {"none", "defer"}:
            return {"status": "complete_none" if mode == "recall" else "defer", "available": False, "surface": page.to_mapping()}
        raise ValueError("Surface traversal must open physical entries before selection")
    except (TypeError, ValueError, RuntimeError, KeyError) as exc:
        raise FormationAdapterError("invalid_surface_traversal", str(exc)) from exc
    raise AssertionError("unreachable Surface traversal state")


def _is_physical_state(value: object) -> bool:
    return type(value) is dict and set(value) == {"surface_state", "physical_entry"}


def _advance_physical(mode, subject, traversal_state, raw_response, root, navigator):
    physical_state = traversal_state["physical_entry"]
    if type(physical_state) is not dict or set(physical_state) != {
        "source_surface_candidate_id", "source_surface_address", "after"
    }:
        raise ValueError("invalid physical-entry traversal state")
    state = navigator.state_from_mapping(traversal_state["surface_state"])
    if state.call_count < 1:
        raise ValueError("physical-entry state has no displayed page")
    page = navigator.reopen_physical_entries_from_mapping(
        replace(state, call_count=state.call_count - 1),
        physical_state["source_surface_candidate_id"],
        physical_state["source_surface_address"],
        physical_state["after"],
    )
    decision = _traversal_decision(raw_response)
    action = decision["action"]
    if action == "continue_page":
        return _physical_entry_response(mode, subject, navigator, navigator.continue_physical_entries(page))
    if action == "return_to_parent":
        return _traversal_response(mode, subject, navigator, navigator.page(page.state))
    if action in {"none", "defer"}:
        return {"status": "complete_none" if mode == "recall" else "defer", "available": False, "physical_entries": page.to_mapping()}
    if action != "select_entry":
        raise ValueError("physical-entry traversal requires one shown entry selection")
    resolution = navigator.select_entry(page, decision["candidate_id"])
    entry = resolution.entry_cell
    if mode == "placement":
        return _placement_decision(root, _statement(json.loads(subject)), state.operation_id, entry.to_mapping(), page, resolution.resolved_singleton)
    recalled = navigator.recall_entry(state.operation_id, entry)
    candidates = list(recalled.items)
    if not candidates:
        return {"status": "complete_none", "available": False, "entry_cell": entry.to_mapping(), "resolved_singleton": resolution.resolved_singleton, "core_recall": {"budget_exhausted": recalled.budget_exhausted}, "physical_entries": page.to_mapping()}
    prompt = _recall_selection_prompt(subject, candidates)
    return {
        "status": "recall_decision",
        "available": True,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "candidates": candidates,
        "entry_cell": entry.to_mapping(),
        "resolved_singleton": resolution.resolved_singleton,
        "core_recall": {"budget_exhausted": recalled.budget_exhausted},
        "physical_entries": page.to_mapping(),
    }


def _traversal_response(
    mode: str,
    subject: str,
    navigator: AccessSurfaceNavigator,
    page: object,
) -> dict[str, object]:
    prompt = _traversal_prompt(mode, subject, page.to_mapping())
    return {
        "status": "traverse",
        "available": True,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "traversal_state": navigator.state_to_mapping(page.state),
        "surface": page.to_mapping(),
    }


def _physical_entry_response(mode, subject, navigator, page):
    physical = page.to_mapping()
    prompt = _physical_entry_prompt(mode, subject, physical)
    state = {
        "surface_state": navigator.state_to_mapping(page.state),
        "physical_entry": {
            "source_surface_candidate_id": page.source_surface_candidate_id,
            "source_surface_address": page.source_surface_address.to_mapping(),
            "after": page.after.to_mapping() if page.after else None,
        },
    }
    return {
        "status": "physical_entry",
        "available": True,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "traversal_state": state,
        "physical_entries": physical,
    }


def _traversal_prompt(
    mode: str,
    subject: str,
    surface: dict[str, object],
) -> str:
    current_order = surface.get("current_order")
    if type(current_order) is not int or current_order < 0:
        raise FormationAdapterError("invalid_surface", "Surface current_order is invalid")
    locality_action = (
        f'{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"open_physical_entries","candidate_id":"one visible Order 0 Surface id"}}'
        if current_order == 0
        else f'{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"open_surface_cell","candidate_id":"one visible id"}}'
    )
    return f"""You are a private background {mode} Surface navigation agent. The user will never see this run.
The initial Surface order was selected only from Core geometry and fixed budgets before this subject was shown. Choose only a candidate_id visible on this page. Do not invent geometry, topics, indexes, vectors, graphs, entities, or hidden entry hints. Do not call tools or reveal reasoning.
Truncated coarse cells are navigation hints only. The listed actions are the complete legal action set for current_order={current_order}.
Return exactly one raw JSON object with no markdown.
Schema version: {TRAVERSAL_SCHEMA_VERSION}
Allowed responses:
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"continue_page"}}
{locality_action}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"request_coarser_surface"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"return_to_parent"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"none"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"defer"}}
subject: {subject}
surface_page: {json.dumps(surface, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _physical_entry_prompt(mode: str, subject: str, physical: dict[str, object]) -> str:
    return f"""You are a private background {mode} physical-entry selection agent. The user will never see this run.
Choose exactly one candidate_id visible on this physical-entry page, or paginate, return, choose none, or defer. Never derive or invent an address. Do not call tools or reveal reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {TRAVERSAL_SCHEMA_VERSION}
Allowed responses:
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"continue_page"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"return_to_parent"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"select_entry","candidate_id":"one visible physical-entry id"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"none"}}
{{"schema_version":"{TRAVERSAL_SCHEMA_VERSION}","action":"defer"}}
physical_entry_contract: {PHYSICAL_ENTRY_SCHEMA_VERSION}
subject: {subject}
physical_entry_page: {json.dumps(physical, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _traversal_decision(raw_response: str) -> dict[str, object]:
    try:
        repaired, _diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    if type(value) is not dict or value.get("schema_version") != TRAVERSAL_SCHEMA_VERSION or type(value.get("action")) is not str:
        raise FormationAdapterError("invalid_surface_traversal", "invalid Surface traversal envelope")
    action = value["action"]
    with_candidate = action in {"open_surface_cell", "open_physical_entries", "select_entry"}
    expected = {"schema_version", "action", "candidate_id"} if with_candidate else {"schema_version", "action"}
    if set(value) != expected or (with_candidate and (type(value["candidate_id"]) is not str or not value["candidate_id"])):
        raise FormationAdapterError("invalid_surface_traversal", "invalid Surface traversal fields")
    return value


def _placement_decision(
    root: Path,
    statement: MemoryStatement,
    request_id: str,
    selected_entry: object,
    page: object,
    resolved_singleton: bool | None = None,
) -> dict[str, object]:
    with AccessMemoryLoop(root) as loop:
        candidates = loop.placement_candidates(selected_entry, request_id + ":placement-candidates")
        contexts = loop.candidate_statement_context(candidates)
    statements = {item["candidate_id"]: item["statements"] for item in contexts}
    prompt_candidates = [{**item, "statements": statements[item["candidate_id"]]} for item in candidates]
    prompt = f"""You are a private background Surface placement agent. The user will never see this run.
Choose only a supplied candidate_id. Semantic reuse, revision, locality, expansion, or defer is your decision; Python and Core do not decide it. Do not invent coordinates, topics, indexes, vectors, graphs, or handles. Do not call tools or reveal reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {PLACEMENT_SCHEMA_VERSION}
For new_local or expand_surface: {{"schema_version":"{PLACEMENT_SCHEMA_VERSION}","outcome":"apply","decision":{{"statement_id":"{statement.statement_id}","action":"new_local","candidate_id":"one supplied id","reason_text":"brief"}}}}
For reuse or revision_current add exactly one existing_handle supplied by that candidate.
For defer: {{"schema_version":"{PLACEMENT_SCHEMA_VERSION}","outcome":"defer","reason_text":"brief"}}
statement: {json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
selected_entry: {json.dumps(selected_entry, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
placement_candidates: {json.dumps(prompt_candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    result = {
        "status": "placement_decision",
        "available": True,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "candidates": prompt_candidates,
        "selected_entry": selected_entry,
        "resolved_singleton": resolved_singleton,
    }
    result["physical_entries" if resolved_singleton is not None else "surface"] = page.to_mapping()
    return result


def apply_placement(
    raw_response: object,
    statement_value: object,
    memory_workspace: object,
    request_id: object,
    selected_entry: object = None,
) -> dict[str, object]:
    if type(raw_response) is not str or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "placement request fields are invalid")
    statement = _statement(statement_value)
    root = _workspace(memory_workspace)
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        raw = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    try:
        with AccessMemoryLoop(root) as loop:
            result = loop.apply_placement(statement, raw, request_id, selected_entry)
    except (TypeError, ValueError, KeyError) as exc:
        raise FormationAdapterError("invalid_schema", str(exc)) from exc
    return {**result, "json_repair": diagnostics}


def _recall_selection_prompt(query: str, candidates: list[dict[str, object]]) -> str:
    return f"""You are a private background memory recall agent. The user will never see this run.
Choose only supplied statement_ids that directly help answer the query. Return none when none help. Do not invent facts, call tools, or reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {RECALL_SCHEMA_VERSION}
inject: {{"schema_version":"{RECALL_SCHEMA_VERSION}","outcome":"inject","statement_ids":["..."]}}
none: {{"schema_version":"{RECALL_SCHEMA_VERSION}","outcome":"none","statement_ids":[]}}
query: {json.dumps(query, ensure_ascii=False)}
recalled_candidates: {json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def render_recall_injection(raw_response: object, candidates: object) -> dict[str, object]:
    if type(raw_response) is not str or type(candidates) is not list:
        raise FormationAdapterError("invalid_recall", "recall response fields are invalid")
    try:
        value = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_recall", str(exc)) from exc
    if type(value) is not dict or set(value) != {"schema_version", "outcome", "statement_ids"} or value.get("schema_version") != RECALL_SCHEMA_VERSION or type(value.get("statement_ids")) is not list or any(type(item) is not str for item in value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "invalid recall envelope")
    available = {item["statement_id"]: item["content_utf8"] for item in candidates if type(item) is dict and type(item.get("statement_id")) is str and type(item.get("content_utf8")) is str}
    if value["outcome"] == "none":
        if value["statement_ids"]:
            raise FormationAdapterError("invalid_recall", "NONE cannot select statements")
        return {"outcome": "none", "injection": ""}
    if value["outcome"] != "inject" or not value["statement_ids"] or len(set(value["statement_ids"])) != len(value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "invalid recall selection")
    if any(item not in available for item in value["statement_ids"]):
        raise FormationAdapterError("invalid_recall", "recall selected an unavailable statement")
    selected = [available[item] for item in value["statement_ids"]]
    injection = "Nollm memory context. Use only when relevant; do not mention this context to the user:\n" + "\n".join(f"- {item}" for item in selected)
    return {"outcome": "inject", "statement_ids": value["statement_ids"], "injection": injection}
