from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4

from nollm_access import AccessDecision, AccessRecallRequest, AccessRuntime, FileHandleStore, FileStatementStore, MemoryStatement
from nollm_core import AtomHandle, BridgeSpec, CoreRuntime, GeometryAddress, GeometryAnchor, RecallBudget

from .adapter import FormationAdapterError


PLACEMENT_SCHEMA_VERSION = "nollm_openclaw_placement_v1"
RECALL_SCHEMA_VERSION = "nollm_openclaw_recall_v1"
CURSOR_SCHEMA_VERSION = "nollm_openclaw_memory_cursor_v1"
_CURSOR_LIMIT = 8
_RECALL_BUDGET = RecallBudget(2, 12, 1, 1, 1, 16)


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _workspace(path: object) -> Path:
    if type(path) is not str or not path:
        raise FormationAdapterError("invalid_workspace", "memory workspace is required")
    return Path(path).resolve()


def _open_access(root: Path) -> tuple[CoreRuntime, AccessRuntime]:
    core = CoreRuntime(root)
    try:
        return core, AccessRuntime(core, FileStatementStore(root), FileHandleStore(root))
    except Exception:
        core.close()
        raise


def _cursor_path(root: Path) -> Path:
    return root / "openclaw" / "memory_cursor.json"


def _load_cursor(root: Path, session_key: object) -> tuple[GeometryAddress, ...]:
    if type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_session", "session_key is required")
    path = _cursor_path(root)
    if not path.exists():
        return ()
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or set(value) != {"schema_version", "sessions"} or value["schema_version"] != CURSOR_SCHEMA_VERSION or type(value["sessions"]) is not dict:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor is invalid")
    raw = value["sessions"].get(session_key, [])
    if type(raw) is not list:
        raise FormationAdapterError("invalid_cursor", "MemoryCursor session is invalid")
    cells = tuple(GeometryAddress.from_mapping(item) for item in raw)
    if len(cells) > _CURSOR_LIMIT or len(set(cells)) != len(cells):
        raise FormationAdapterError("invalid_cursor", "MemoryCursor cells are invalid")
    return cells


def _store_cursor(root: Path, session_key: str, cell: GeometryAddress) -> tuple[GeometryAddress, ...]:
    path = _cursor_path(root)
    sessions: dict[str, list[dict[str, object]]] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if type(existing) is not dict or set(existing) != {"schema_version", "sessions"} or existing["schema_version"] != CURSOR_SCHEMA_VERSION or type(existing["sessions"]) is not dict:
            raise FormationAdapterError("invalid_cursor", "MemoryCursor is invalid")
        sessions = {key: list(value) for key, value in existing["sessions"].items() if type(key) is str and type(value) is list}
    previous = [GeometryAddress.from_mapping(item) for item in sessions.get(session_key, [])]
    ordered = [item for item in previous if item != cell]
    ordered.append(cell)
    ordered = ordered[-_CURSOR_LIMIT:]
    sessions[session_key] = [item.to_mapping() for item in ordered]
    payload = _canonical({"schema_version": CURSOR_SCHEMA_VERSION, "sessions": dict(sorted(sessions.items()))})
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid4().hex}.tmp"
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return tuple(ordered)


def _statement(value: object) -> MemoryStatement:
    try:
        return MemoryStatement.from_mapping(value)
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_statement", str(exc)) from exc


def _context(access: AccessRuntime, cursor: tuple[GeometryAddress, ...], request_id: str) -> list[dict[str, object]]:
    if not cursor:
        return []
    result = access.recall(AccessRecallRequest(request_id, tuple(sorted(cursor, key=lambda item: item.stable_key())), (), ("bridge", "coverage_down", "coverage_up", "lateral"), _RECALL_BUDGET))
    return [
        {
            "statement_id": item.statement_id,
            "content_utf8": item.evidence_utf8,
            "handle": item.handle.to_mapping(),
            "address": item.handle.geometry_address.to_mapping(),
            "fallback_error": item.fallback_error,
        }
        for item in result.items
        if item.evidence_utf8 is not None
    ]


def build_placement_prompt(statement_value: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    statement = _statement(statement_value)
    if type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "request_id is required")
    root = _workspace(memory_workspace)
    core, access = _open_access(root)
    try:
        cursor = _load_cursor(root, session_key)
        nearby = _context(access, cursor, request_id + ":placement-context")
    finally:
        access.close(); core.close()
    prompt = f"""You are a private background geometry placement agent. The user will never see this run.
Decide one explicit placement action for this newly formed memory statement. You may only use the supplied local MemoryCursor and local geometry context. Do not infer a global topic, entity, source, graph, vector, or semantic index. Core validates and executes, you only decide.
Return exactly one raw JSON object with no markdown.
Schema version: {PLACEMENT_SCHEMA_VERSION}
For a new memory, `decision.statement_id` MUST be exactly `{statement.statement_id}`. Copy that literal value unchanged; do not use a placeholder, a draft id, or the statement text. The exact new-memory object is {{\"schema_version\":\"{PLACEMENT_SCHEMA_VERSION}\",\"outcome\":\"apply\",\"decision\":{{\"statement_id\":\"{statement.statement_id}\",\"action\":\"new\",\"target_cell\":{{\"profile_id\":\"eisenstein_exact_v1\",\"chart_id\":\"default\",\"layer\":0,\"q\":0,\"r\":0,\"phase\":null}},\"reason_text\":\"brief\"}}}}
For a known equivalent or revision, use action reuse, revision_current, move, or revision_keep_history with one supplied existing_handle where required. For no safe action use {{\"schema_version\":\"{PLACEMENT_SCHEMA_VERSION}\",\"outcome\":\"defer\",\"reason_text\":\"brief\"}}. Do not invent handles. Do not call tools.
statement: {json.dumps(statement.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
memory_cursor: {json.dumps([cell.to_mapping() for cell in cursor], ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
local_geometry_context: {json.dumps(nearby, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {"prompt": prompt, "schema_version": PLACEMENT_SCHEMA_VERSION, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}


def _decision(raw: object, statement: MemoryStatement, request_id: str) -> AccessDecision | None:
    if type(raw) is not dict or raw.get("schema_version") != PLACEMENT_SCHEMA_VERSION or type(raw.get("outcome")) is not str:
        raise FormationAdapterError("invalid_placement", "invalid placement envelope")
    if raw["outcome"] == "defer":
        if set(raw) != {"schema_version", "outcome", "reason_text"} or type(raw["reason_text"]) is not str:
            raise FormationAdapterError("invalid_placement", "invalid deferred placement")
        return None
    if raw["outcome"] != "apply" or set(raw) != {"schema_version", "outcome", "decision"} or type(raw["decision"]) is not dict:
        raise FormationAdapterError("invalid_placement", "invalid placement outcome")
    value = raw["decision"]
    if value.get("statement_id") != statement.statement_id or type(value.get("action")) is not str or type(value.get("reason_text")) is not str:
        raise FormationAdapterError("invalid_placement", "decision does not bind the formed statement")
    action = value["action"]
    target = GeometryAddress.from_mapping(value["target_cell"]) if value.get("target_cell") is not None else None
    handle = AtomHandle.from_mapping(value["existing_handle"]) if value.get("existing_handle") is not None else None
    if action == "stitch":
        spec_value = value.get("bridge_spec")
        if type(spec_value) is not dict:
            raise FormationAdapterError("invalid_placement", "stitch requires bridge_spec")
        bridge = BridgeSpec.from_mapping(spec_value)
    else:
        bridge = None
    return AccessDecision(f"placement:{request_id}:{statement.statement_id}", statement.statement_id, action, target, handle, bridge, value["reason_text"], "llm")


def apply_placement(raw_response: object, statement_value: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    if type(raw_response) is not str or type(request_id) is not str or not request_id or type(session_key) is not str or not session_key:
        raise FormationAdapterError("invalid_request", "placement request fields are invalid")
    statement = _statement(statement_value)
    root = _workspace(memory_workspace)
    try:
        raw = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_placement", str(exc)) from exc
    decision = _decision(raw, statement, request_id)
    if decision is None:
        return {"outcome": "defer", "statement_id": statement.statement_id, "core_write_count": 0}
    core, access = _open_access(root)
    try:
        access.capture(statement)
        result = access.apply(decision)
        if isinstance(result, AtomHandle):
            cursor = _store_cursor(root, session_key, result.geometry_address)
            handle = result.to_mapping()
        else:
            cursor = _load_cursor(root, session_key)
            handle = None
    finally:
        access.close(); core.close()
    return {"outcome": "applied", "statement_id": statement.statement_id, "action": decision.action, "handle": handle, "cursor": [cell.to_mapping() for cell in cursor], "core_write_count": 1 if decision.action in {"new", "move", "revision_current", "revision_keep_history", "stitch"} else 0}


def build_recall_prompt(query: object, session_key: object, memory_workspace: object, request_id: object) -> dict[str, object]:
    if type(query) is not str or not query or type(session_key) is not str or not session_key or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_request", "recall request fields are invalid")
    root = _workspace(memory_workspace)
    core, access = _open_access(root)
    try:
        cursor = _load_cursor(root, session_key)
        candidates = _context(access, cursor, request_id)
    finally:
        access.close(); core.close()
    if not candidates:
        return {"available": False, "candidate_count": 0}
    prompt = f"""You are a private background memory recall agent. The user will never see this run.
Given the new user query and finite geometry-recalled statements, choose only statements that directly help answer the query. Return NONE when none help. Do not invent facts, do not call tools, and do not reveal hidden reasoning.
Return exactly one raw JSON object with no markdown.
Schema version: {RECALL_SCHEMA_VERSION}
inject: {{\"schema_version\":\"{RECALL_SCHEMA_VERSION}\",\"outcome\":\"inject\",\"statement_ids\":[\"...\"]}}
none: {{\"schema_version\":\"{RECALL_SCHEMA_VERSION}\",\"outcome\":\"none\",\"statement_ids\":[]}}
query: {json.dumps(query, ensure_ascii=False)}
recalled_candidates: {json.dumps(candidates, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    return {"available": True, "prompt": prompt, "candidates": candidates, "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest()}


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
