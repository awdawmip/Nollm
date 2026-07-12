from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nollm_access import (
    ConversationMaterial,
    DreamFormationRequest,
    DreamFormationResult,
    DreamMemoryDraft,
    FileStatementStore,
    MemoryStatement,
    form_dream_statements,
)

from .adapter import FormationAdapterError


DREAM_PROMPT_VERSION = "dream-v1"
DREAM_SCHEMA_VERSION = "nollm_access_dream_formation_v1"


def dream_schema_bytes() -> bytes:
    value = {
        "schema_version": DREAM_SCHEMA_VERSION,
        "emit_required": ["schema_version", "outcome", "drafts"],
        "defer_required": ["schema_version", "outcome", "drafts", "defer_reason"],
        "draft_required": ["draft_id", "content_utf8", "scope_hint", "stability_hint", "uncertainty_hint"],
    }
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_dream_prompt(request: DreamFormationRequest, prompt_version: str = DREAM_PROMPT_VERSION) -> str:
    if prompt_version not in {"dream-v1", "dream-v2"}:
        raise FormationAdapterError("invalid_prompt_version", "unsupported Dream prompt version")
    turns = [item.to_mapping() for item in request.material.turns]
    refinement = ""
    if prompt_version == "dream-v2":
        refinement = """
Prefer explicit user preferences, stable constraints, and facts likely to help in a later conversation.
Defer one-off requests, transient status, pleasantries, and facts introduced only by the assistant reply.
Do not turn an assistant promise to remember something into a user fact."""
    return f"""You are a private background memory-forming agent. The user will never see this run.
Decide whether the bounded conversation material contains durable information worth retaining.
You may rewrite, split, merge, remove conversational phrasing, and resolve references using only supplied material.
Produce self-contained statements. Preserve important negation, conditions, time, and uncertainty.
Do not invent facts. When uncertain or nothing is durable, defer. Do not reveal hidden reasoning.{refinement}
Do not call tools. Return exactly one raw JSON object with no markdown or commentary.
Schema version: {DREAM_SCHEMA_VERSION}
emit: {{"schema_version":"{DREAM_SCHEMA_VERSION}","outcome":"emit","drafts":[{{"draft_id":"d1","content_utf8":"...","scope_hint":null,"stability_hint":null,"uncertainty_hint":null}}]}}
defer: {{"schema_version":"{DREAM_SCHEMA_VERSION}","outcome":"defer","drafts":[],"defer_reason":"short reason"}}
Drafts must be unique and ordered by draft_id. Maximum drafts: {request.max_statements}.
Maximum characters per draft: {request.max_statement_chars}. Maximum total draft characters: {request.max_total_chars}.
prompt_version: {prompt_version}
request_id: {request.request_id}
conversation_material: {json.dumps(turns, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def parse_dream_result(raw: str, request: DreamFormationRequest, result_id: str) -> DreamFormationResult:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    common = {"schema_version", "outcome", "drafts"}
    if type(value) is not dict or value.get("schema_version") != DREAM_SCHEMA_VERSION or type(value.get("drafts")) is not list:
        raise FormationAdapterError("invalid_schema", "invalid Dream Formation envelope")
    outcome = value.get("outcome")
    if outcome == "defer":
        if set(value) != common | {"defer_reason"}:
            raise FormationAdapterError("invalid_schema", "defer has incorrect fields")
        return DreamFormationResult(result_id, request.request_id, "defer", (), value["defer_reason"], "llm")
    if outcome != "emit" or set(value) != common:
        raise FormationAdapterError("invalid_schema", "emit has incorrect fields")
    try:
        drafts = tuple(DreamMemoryDraft.from_mapping(item) for item in value["drafts"])
        result = DreamFormationResult(result_id, request.request_id, "emit", drafts, None, "llm")
        form_dream_statements(request, result)
        return result
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_dream_result", str(exc)) from exc


def process_dream_result(raw: str, request: DreamFormationRequest, result_id: str, workspace: Path | None) -> dict[str, object]:
    result = parse_dream_result(raw, request, result_id)
    statements = tuple(
        MemoryStatement(_stable_statement_id(result.result_id, draft.draft_id), draft.content_utf8)
        for draft in result.drafts
    )
    if workspace is not None:
        store = FileStatementStore(workspace)
        for statement in statements:
            store.put(statement)
    return {
        "result": {
            "result_id": result.result_id,
            "request_id": result.request_id,
            "outcome": result.outcome,
            "drafts": [item.to_mapping() for item in result.drafts],
            "defer_reason": result.defer_reason,
            "decided_by": result.decided_by,
            "schema_version": result.schema_version,
        },
        "statements": [item.to_mapping() for item in statements],
        "statement_store_write_count": len(statements) if workspace is not None else 0,
    }


def _stable_statement_id(result_id: str, draft_id: str) -> str:
    payload = f"{DREAM_SCHEMA_VERSION}\0{result_id}\0{draft_id}".encode("utf-8")
    return f"dream:{hashlib.sha256(payload).hexdigest()}"


def request_from_mapping(value: object) -> DreamFormationRequest:
    if type(value) is not dict or set(value) != {"request_id", "material", "max_statements", "max_statement_chars", "max_total_chars", "schema_version"}:
        raise FormationAdapterError("invalid_event", "Dream request has incorrect fields")
    return DreamFormationRequest(
        value["request_id"], ConversationMaterial.from_mapping(value["material"]),
        value["max_statements"], value["max_statement_chars"], value["max_total_chars"], value["schema_version"],
    )


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
