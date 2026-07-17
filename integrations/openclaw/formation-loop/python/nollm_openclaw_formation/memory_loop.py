from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from time import perf_counter

from nollm_access import (
    AccessMemoryLoop,
    AccessSurfaceNavigator,
    DEFAULT_FIELD_SCOPE,
    MemoryStatement,
    PLACEMENT_SURFACE_BUDGET,
    PLACEMENT_ACTION_SEMANTICS_VERSION,
    RECALL_SURFACE_BUDGET,
    REVISION_CONFIRMATION_SCHEMA_VERSION,
    ProvisionalRevisionDecision,
    RevisionConfirmationResult,
    RevisionTargetExcludedError,
    SurfaceBudgetProfile,
    placement_action_semantics_prompt,
    FileHandleStore,
    FileStatementStore,
)
from nollm_core import AtomHandle, CoreRuntime

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json


TRAVERSAL_SCHEMA_VERSION = "nollm_openclaw_bounded_approximate_surface_traversal_v1"
PHYSICAL_ENTRY_SCHEMA_VERSION = "nollm_openclaw_single_physical_entry_recall_v1"
PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_surface_placement_v1"
RECALL_SCHEMA_VERSION = "nollm_openclaw_surface_recall_v1"
FAST_RECALL_SCHEMA_VERSION = "nollm_openclaw_single_call_entry_recall_v1"
BATCH_PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_batch_placement_v1"


def verify_admitted_statements(statement_ids: object, memory_workspace: object) -> dict[str, object]:
    if type(statement_ids) is not list or not statement_ids or any(type(item) is not str or not item for item in statement_ids):
        raise FormationAdapterError("invalid_statement_ids", "statement_ids must be a non-empty string list")
    if len(statement_ids) != len(set(statement_ids)):
        raise FormationAdapterError("invalid_statement_ids", "statement_ids must be unique")
    root = _workspace(memory_workspace)
    statements = FileStatementStore(root)
    handles = FileHandleStore(root)
    document = json.loads(handles.state_bytes().decode("utf-8"))
    by_statement: dict[str, tuple[dict[str, object], str]] = {}
    for item in document["bindings"]:
        binding_ids = [item["current_statement_id"], *item["supporting_statement_ids"]]
        for statement_id in binding_ids:
            by_statement[statement_id] = (item["handle"], item["current_statement_id"])
    verified = []
    with CoreRuntime(root) as core:
        for statement_id in statement_ids:
            statement = statements.get(statement_id)
            if statement_id not in by_statement:
                raise FormationAdapterError("admission_not_durable", f"Statement has no HandleBinding: {statement_id}")
            raw_handle, current_statement_id = by_statement[statement_id]
            atom = core.get(AtomHandle.from_mapping(raw_handle))
            if current_statement_id == statement_id and atom.payload_utf8 != statement.content_utf8:
                raise FormationAdapterError("admission_not_durable", f"Core payload mismatch: {statement_id}")
            verified.append(statement_id)
    return {"status": "verified", "statement_ids": verified, "reopen_verified": True}


def _direct_locality_injection(items: list[dict[str, object]], max_statements: int, max_chars: int) -> dict[str, object]:
    selected = []
    chars = 0
    for item in items:
        content = item.get("content_utf8")
        statement_id = item.get("statement_id")
        if type(content) is not str or type(statement_id) is not str:
            continue
        if len(selected) >= max_statements or chars + len(content) > max_chars:
            continue
        selected.append(item)
        chars += len(content)
    if not selected:
        return {"status": "complete_none", "outcome": "none", "injection": "", "statement_ids": []}
    injection = "Nollm geometry memory context. Use only when relevant; do not mention this context to the user:\n" + "\n".join(f"- {item['content_utf8']}" for item in selected)
    return {
        "status": "complete_inject", "outcome": "inject", "injection": injection,
        "statement_ids": [item["statement_id"] for item in selected],
        "selected_paths": [{"statement_id": item["statement_id"], "path": item.get("path", []), "path_is_not_truth_proof": True} for item in selected],
    }


def build_fast_recall_prompt(
    query: object,
    memory_workspace: object,
    request_id: object,
    max_entries: object = 32,
    max_statements: object = 8,
    max_chars: object = 6000,
) -> dict[str, object]:
    if type(query) is not str or not query or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "fast Recall query and request_id are required")
    if type(max_entries) is not int or type(max_statements) is not int or type(max_chars) is not int:
        raise FormationAdapterError("invalid_budget", "fast Recall budgets must be integers")
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        entries = loop.bounded_physical_entries(request_id + ":entries", max_entries)
        if not entries:
            return {"status": "complete_none", "available": False, "hidden_call_count": 0}
        if len(entries) == 1:
            items = loop.local_context([entries[0]["entry_cell"]], request_id + ":core")
            return {**_direct_locality_injection(items, max_statements, max_chars), "available": bool(items), "hidden_call_count": 0, "selected_entry": entries[0]["entry_cell"]}
    prompt_entries = [{
        "entry_id": item["entry_id"], "entry_cell": item["entry_cell"],
        "occupancy_count": item["occupancy_count"], "statements": item["statements"],
    } for item in entries]
    prompt = f"""You are a private background geometry-entry selector. Choose at most one supplied entry_id that is likely to contain memory useful for the query, or choose none. The entries are a finite geometry-ordered projection, not a semantic index. Do not select individual statements, invent facts, addresses, topics, vectors, graphs, or hidden routes. Do not call tools or reveal reasoning.
Return exactly one raw JSON object with no markdown.
select: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"select","entry_id":"one supplied id"}}
none: {{"schema_version":"{FAST_RECALL_SCHEMA_VERSION}","outcome":"none","entry_id":null}}
query: {json.dumps(query, ensure_ascii=False)}
physical_entries: {json.dumps(prompt_entries, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "status": "entry_decision", "available": True, "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(), "entries": prompt_entries,
        "max_statements": max_statements, "max_chars": max_chars, "hidden_call_count": 1,
    }


def apply_fast_recall_selection(
    raw_response: object,
    entries: object,
    memory_workspace: object,
    request_id: object,
    max_statements: object = 8,
    max_chars: object = 6000,
) -> dict[str, object]:
    if type(raw_response) is not str or type(entries) is not list or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_fast_recall", "fast Recall selection fields are invalid")
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    if type(value) is not dict or set(value) != {"schema_version", "outcome", "entry_id"} or value.get("schema_version") != FAST_RECALL_SCHEMA_VERSION:
        raise FormationAdapterError("invalid_fast_recall", "invalid fast Recall envelope")
    if value["outcome"] == "none" and value["entry_id"] is None:
        return {"status": "complete_none", "outcome": "none", "injection": "", "statement_ids": [], "hidden_call_count": 1, "json_repair": diagnostics}
    if value["outcome"] != "select" or type(value["entry_id"]) is not str:
        raise FormationAdapterError("invalid_fast_recall", "fast Recall must select one entry or NONE")
    by_id = {item["entry_id"]: item for item in entries if type(item) is dict and type(item.get("entry_id")) is str and type(item.get("entry_cell")) is dict}
    if value["entry_id"] not in by_id:
        raise FormationAdapterError("invalid_fast_recall", "fast Recall selected an unavailable entry")
    selected = by_id[value["entry_id"]]
    with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
        items = loop.local_context([selected["entry_cell"]], request_id + ":core")
    return {**_direct_locality_injection(items, max_statements, max_chars), "hidden_call_count": 1, "selected_entry": selected["entry_cell"], "json_repair": diagnostics}


def build_batch_placement_prompt(
    statements: object,
    memory_workspace: object,
    request_id: object,
    max_existing: object = 16,
    max_empty: object = 16,
) -> dict[str, object]:
    if type(statements) is not list or not statements or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_batch", "batch placement requires Statements and request_id")
    try:
        formed = [_statement(item) for item in statements]
    except FormationAdapterError:
        raise
    if len({item.statement_id for item in formed}) != len(formed):
        raise FormationAdapterError("invalid_batch", "batch Statement identities must be unique")
    with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
        view = loop.batch_placement_view(request_id + ":view", max_existing, max_empty)
    statement_wire = [item.to_mapping() for item in formed]
    prompt = f"""You are a private background batch geometry placement agent. The user will never see this run.
Make one independent semantic decision for every supplied Statement using only the supplied finite geometry candidates. Python and Core do not decide similarity, reuse, locality, or whether a fact is new. Different subjects with analogous attributes remain distinct. Additive facts are not revisions.
Use new_local for a suitable existing or lateral locality, expand_surface only with a candidate whose relation_kind is expand_surface, reuse only with one exact existing_handle from that candidate, and defer when uncertain. revision_current is not available in this common batch path and must be deferred for separate confirmation.
Do not invent coordinates, candidate IDs, handles, topics, indexes, vectors, or graphs. Do not call tools or reveal reasoning.
Return exactly one raw JSON object with no markdown.
schema: {{"schema_version":"{BATCH_PLACEMENT_SCHEMA_VERSION}","decisions":[...]}}
apply new: {{"statement_id":"...","outcome":"apply","action":"new_local","candidate_id":"...","reason_text":"brief"}}
apply reuse: {{"statement_id":"...","outcome":"apply","action":"reuse","candidate_id":"...","existing_handle":{{...}},"reason_text":"brief"}}
defer: {{"statement_id":"...","outcome":"defer","reason_text":"brief"}}
Decisions must be ordered exactly like Statements. Two new Statements must not choose the same empty candidate.
statements: {json.dumps(statement_wire, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
geometry_view: {json.dumps(view, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "status": "batch_placement_decision", "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "view_fingerprint": view["view_fingerprint"], "statements": statement_wire,
        "candidate_count": len(view["candidates"]), "candidates": view["candidates"],
    }


def apply_batch_placement(
    raw_response: object,
    statements: object,
    memory_workspace: object,
    request_id: object,
    view_fingerprint: object,
    max_existing: object = 16,
    max_empty: object = 16,
) -> dict[str, object]:
    if type(raw_response) is not str or type(statements) is not list or type(request_id) is not str or type(view_fingerprint) is not str:
        raise FormationAdapterError("invalid_batch", "batch placement apply fields are invalid")
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    if type(value) is not dict or set(value) != {"schema_version", "decisions"} or value.get("schema_version") != BATCH_PLACEMENT_SCHEMA_VERSION or type(value.get("decisions")) is not list:
        raise FormationAdapterError("invalid_batch", "invalid batch placement envelope")
    try:
        with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
            result = loop.apply_batch_placements(statements, value["decisions"], request_id, view_fingerprint, max_existing, max_empty)
    except (TypeError, ValueError, KeyError, RuntimeError) as exc:
        raise FormationAdapterError("invalid_batch", str(exc)) from exc
    return {**result, "json_repair": diagnostics}


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
        decision = _traversal_decision(raw_response, page.legal_actions)
        action = decision["action"]
        if action == "continue_page":
            return _traversal_response(mode, subject, navigator, navigator.continue_page(page))
        if action == "open_surface_cell":
            return _traversal_response(mode, subject, navigator, navigator.open_surface_cell(page, decision["candidate_id"]))
        if action == "open_physical_entries":
            return _physical_entry_response(mode, subject, root, navigator, navigator.open_physical_entries(page, decision["candidate_id"]))
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
    decision = _traversal_decision(raw_response, page.legal_actions)
    action = decision["action"]
    if action == "continue_page":
        return _physical_entry_response(mode, subject, root, navigator, navigator.continue_physical_entries(page))
    if action == "return_to_parent":
        return _traversal_response(mode, subject, navigator, navigator.page(page.state))
    if action in {"none", "defer"}:
        return {"status": "complete_none" if mode == "recall" else "defer", "available": False, "physical_entries": page.to_mapping()}
    if action != "select_entry":
        raise ValueError("physical-entry traversal requires one shown entry selection")
    started = perf_counter()
    resolution = navigator.select_entry(page, decision["candidate_id"])
    return _resolved_physical_entry(
        mode,
        subject,
        root,
        navigator,
        page,
        resolution,
        round((perf_counter() - started) * 1000),
        physical_entry_model_call_skipped=False,
    )


def _resolved_physical_entry(
    mode,
    subject,
    root,
    navigator,
    page,
    resolution,
    physical_entry_resolution_ms,
    *,
    physical_entry_model_call_skipped,
):
    entry = resolution.entry_cell
    if mode == "placement":
        return _placement_decision(
            root,
            _statement(json.loads(subject)),
            page.state.operation_id,
            entry.to_mapping(),
            page,
            resolution.resolved_singleton,
            resolution.resolution_policy_id,
            physical_entry_model_call_skipped,
        )
    started = perf_counter()
    recalled = navigator.recall_entry(page.state.operation_id, entry)
    recall_core_ms = round((perf_counter() - started) * 1000)
    operation_timing = {
        "physical_entry_resolution_ms": physical_entry_resolution_ms,
        "physical_entry_model_call_skipped": physical_entry_model_call_skipped,
        "recall_core_ms": recall_core_ms,
    }
    candidates = list(recalled.items)
    if not candidates:
        return {"status": "complete_none", "available": False, "entry_cell": entry.to_mapping(), "resolved_singleton": resolution.resolved_singleton, "resolution_policy_id": resolution.resolution_policy_id, "physical_entry_model_call_skipped": physical_entry_model_call_skipped, "core_recall": {"budget_exhausted": recalled.budget_exhausted}, "physical_entries": page.to_mapping(), "operation_timing": operation_timing}
    prompt = _recall_selection_prompt(subject, candidates)
    return {
        "status": "recall_decision",
        "available": True,
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "candidates": candidates,
        "entry_cell": entry.to_mapping(),
        "resolved_singleton": resolution.resolved_singleton,
        "resolution_policy_id": resolution.resolution_policy_id,
        "physical_entry_model_call_skipped": physical_entry_model_call_skipped,
        "core_recall": {"budget_exhausted": recalled.budget_exhausted},
        "operation_timing": operation_timing,
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


def _physical_entry_response(mode, subject, root, navigator, page):
    physical = page.to_mapping()
    if page.total_candidate_count == 1 and len(page.candidates) == 1 and not page.has_more:
        started = perf_counter()
        resolution = navigator.resolve_singleton_entry(page)
        return _resolved_physical_entry(
            mode,
            subject,
            root,
            navigator,
            page,
            resolution,
            round((perf_counter() - started) * 1000),
            physical_entry_model_call_skipped=True,
        )
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
    legal_actions = _legal_actions(surface)
    responses = _allowed_responses(legal_actions, physical=False)
    return f"""You are a private background {mode} Surface navigation agent. The user will never see this run.
The initial Surface order was selected only from Core geometry and fixed budgets before this subject was shown. Choose only a candidate_id visible on this page. Do not invent geometry, topics, indexes, vectors, graphs, entities, or hidden entry hints. Do not call tools or reveal reasoning.
Truncated coarse cells are navigation hints only. The listed actions are the complete legal action set for current_order={current_order}.
Return exactly one raw JSON object with no markdown.
Schema version: {TRAVERSAL_SCHEMA_VERSION}
Allowed responses:
{responses}
subject: {subject}
surface_page: {json.dumps(surface, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _physical_entry_prompt(mode: str, subject: str, physical: dict[str, object]) -> str:
    legal_actions = _legal_actions(physical)
    responses = _allowed_responses(legal_actions, physical=True)
    return f"""You are a private background {mode} physical-entry selection agent. The user will never see this run.
Choose exactly one candidate_id visible on this physical-entry page, or paginate, return, choose none, or defer. Never derive or invent an address. Do not call tools or reveal reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {TRAVERSAL_SCHEMA_VERSION}
Allowed responses:
{responses}
physical_entry_contract: {PHYSICAL_ENTRY_SCHEMA_VERSION}
subject: {subject}
physical_entry_page: {json.dumps(physical, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def _legal_actions(page: dict[str, object]) -> tuple[str, ...]:
    value = page.get("legal_actions")
    if type(value) is not list or not value or any(type(action) is not str for action in value):
        raise FormationAdapterError("invalid_surface", "page legal_actions are invalid")
    if len(value) != len(set(value)):
        raise FormationAdapterError("invalid_surface", "page legal_actions must be unique")
    return tuple(value)


def _allowed_responses(legal_actions: tuple[str, ...], *, physical: bool) -> str:
    examples = {
        "continue_page": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "continue_page"},
        "open_surface_cell": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "open_surface_cell", "candidate_id": "one visible id"},
        "open_physical_entries": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "open_physical_entries", "candidate_id": "one visible Order 0 Surface id"},
        "request_coarser_surface": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "request_coarser_surface"},
        "return_to_parent": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "return_to_parent"},
        "select_entry": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "select_entry", "candidate_id": "one visible physical-entry id"},
        "none": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "none"},
        "defer": {"schema_version": TRAVERSAL_SCHEMA_VERSION, "action": "defer"},
    }
    allowed = {"continue_page", "return_to_parent", "select_entry", "none", "defer"} if physical else set(examples) - {"select_entry"}
    if any(action not in allowed for action in legal_actions):
        raise FormationAdapterError("invalid_surface", "page advertises an unknown legal action")
    return "\n".join(json.dumps(examples[action], ensure_ascii=False, separators=(",", ":")) for action in legal_actions)


def _traversal_decision(raw_response: str, legal_actions: tuple[str, ...]) -> dict[str, object]:
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
    if action not in legal_actions:
        raise FormationAdapterError("invalid_surface_traversal", f"action {action} is not legal for the current page")
    return value


def _placement_decision(
    root: Path,
    statement: MemoryStatement,
    request_id: str,
    selected_entry: object,
    page: object,
    resolved_singleton: bool | None = None,
    resolution_policy_id: str | None = None,
    physical_entry_model_call_skipped: bool = False,
) -> dict[str, object]:
    with AccessMemoryLoop(root) as loop:
        candidates = loop.placement_candidates(selected_entry, request_id + ":placement-candidates")
        contexts = loop.candidate_statement_context(candidates)
    statements = {item["candidate_id"]: item["statements"] for item in contexts}
    prompt_candidates = [{**item, "statements": statements[item["candidate_id"]]} for item in candidates]
    prompt = f"""You are a private background Surface placement agent. The user will never see this run.
Choose only a supplied candidate_id. Semantic reuse, revision, locality, expansion, or defer is your decision; Python and Core do not decide it. Similar wording, the same field label, the same document type, or the same locality is never enough for revision. Different subjects with analogous attributes must remain distinct current facts. An additive fact about the same subject is not a revision.
Action semantics ({PLACEMENT_ACTION_SEMANTICS_VERSION}):
{placement_action_semantics_prompt()}
Do not invent coordinates, topics, indexes, vectors, graphs, or handles. Do not call tools or reveal reasoning.
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
        "resolution_policy_id": resolution_policy_id,
        "physical_entry_model_call_skipped": physical_entry_model_call_skipped,
    }
    result["physical_entries" if resolved_singleton is not None else "surface"] = page.to_mapping()
    return result


def apply_placement(
    raw_response: object,
    statement_value: object,
    memory_workspace: object,
    request_id: object,
    selected_entry: object = None,
    revision_confirmation: object = None,
    excluded_revision_targets: object = None,
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
            result = loop.apply_placement(
                statement, raw, request_id, selected_entry,
                revision_confirmation=revision_confirmation,
                excluded_revision_targets=excluded_revision_targets,
            )
    except RevisionTargetExcludedError as exc:
        raise FormationAdapterError("revision_target_excluded", str(exc)) from exc
    except (TypeError, ValueError, KeyError) as exc:
        raise FormationAdapterError("invalid_schema", str(exc)) from exc
    return {**result, "json_repair": diagnostics}


def build_revision_confirmation_prompt(provisional_value: object) -> dict[str, object]:
    try:
        provisional = ProvisionalRevisionDecision.from_mapping(provisional_value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_revision_provisional", str(exc)) from exc
    prompt = f"""You are a private revision confirmation agent. The user will never see this run.
The proposed revision_current is destructive. Confirm it only when all three conditions are true: the Statements concern the same subject or referent; they occupy the same proposition slot; and the proposed value explicitly supersedes the current value. Similar wording, analogous fields on different subjects, the same document type, the same locality, or an additive fact is not enough. When uncertain, defer. Do not call tools or reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {REVISION_CONFIRMATION_SCHEMA_VERSION}
Fields: schema_version, outcome, relation.
confirm_revision requires relation same_subject_same_slot_supersedes.
reject_revision requires relation different_subject_or_non_superseding.
defer requires relation uncertain.
provisional_revision: {json.dumps(provisional.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {
        "status": "revision_confirmation",
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "provisional_revision": provisional.to_mapping(),
    }


def parse_revision_confirmation(raw_response: object, provisional_value: object) -> dict[str, object]:
    if type(raw_response) is not str:
        raise FormationAdapterError("invalid_request", "revision confirmation response must be a string")
    try:
        provisional = ProvisionalRevisionDecision.from_mapping(provisional_value)
        repaired, diagnostics = repair_dream_json(raw_response)
        confirmation = RevisionConfirmationResult.from_wire_mapping(
            json.loads(repaired), provisional.provisional_id,
        )
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_revision_confirmation", str(exc)) from exc
    if confirmation.provisional_id != provisional.provisional_id:
        raise FormationAdapterError("invalid_revision_confirmation", "confirmation does not bind the provisional decision")
    return {"confirmation": confirmation.to_mapping(), "json_repair": diagnostics}


def build_revision_redecision_prompt(
    original_prompt: object,
    provisional_value: object,
    confirmation_value: object,
) -> dict[str, object]:
    if type(original_prompt) is not str or not original_prompt:
        raise FormationAdapterError("invalid_request", "original placement prompt is required")
    try:
        provisional = ProvisionalRevisionDecision.from_mapping(provisional_value)
        confirmation = RevisionConfirmationResult.from_mapping(confirmation_value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_revision_redecision", str(exc)) from exc
    if confirmation.provisional_id != provisional.provisional_id or confirmation.confirmed:
        raise FormationAdapterError("invalid_revision_redecision", "redecision requires a rejected or deferred exact provisional revision")
    prompt = f"""{original_prompt}

The provisional revision_current below was rejected without changing Statement, Handle, or Core state. The exact existing_handle is blacklisted for revision_current for this operation. Make one new decision using new_local, expand_surface, reuse only if materially identical, or defer. Do not select revision_current because the bounded confirmation call has been consumed.
rejected_provisional_id: {provisional.provisional_id}
blacklisted_revision_handle: {json.dumps(provisional.existing_handle.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
Return exactly one placement JSON object."""
    return {
        "status": "revision_redecision",
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "excluded_revision_targets": [provisional.existing_handle.to_mapping()],
    }


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
