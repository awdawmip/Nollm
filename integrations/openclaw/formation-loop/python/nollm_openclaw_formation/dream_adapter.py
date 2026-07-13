from __future__ import annotations

import hashlib
import json
import re
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


DREAM_PROMPT_VERSION = "dream-json-p1"
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
    if prompt_version not in {"dream-v1", "dream-v2", "dream-json-p1", "dream-json-p2", "dream-json-p3"}:
        raise FormationAdapterError("invalid_prompt_version", "unsupported Dream prompt version")
    turns = [item.to_mapping() for item in request.material.turns]
    refinement = ""
    if prompt_version in {"dream-v2", "dream-json-p1", "dream-json-p2", "dream-json-p3"}:
        refinement = """
Prefer explicit user preferences, stable constraints, and facts likely to help in a later conversation.
Defer one-off requests, transient status, pleasantries, and facts introduced only by the assistant reply.
Do not turn an assistant promise to remember something into a user fact."""
    if prompt_version == "dream-json-p1":
        refinement += """
JSON discipline: begin with {, end with }, use double-quoted keys and strings, and do not emit a trailing comma."""
    if prompt_version == "dream-json-p2":
        refinement += f"""
Schema discipline: the only valid envelope fields are the fields in this canonical schema: {dream_schema_bytes().decode('utf-8')}. Check field names, enum spelling, and comma placement before responding."""
    if prompt_version == "dream-json-p3":
        refinement += """
Before responding, silently verify that the output is one parseable JSON object with exactly the permitted fields. Emit only that verified object."""
    return f"""You are a private background memory-forming agent. The user will never see this run.
Decide whether the bounded conversation material contains durable information worth retaining.
You may rewrite, split, merge, remove conversational phrasing, and resolve references using only supplied material.
Produce self-contained statements. Preserve important negation, conditions, time, and uncertainty.
Do not invent facts. When uncertain or nothing is durable, defer. Do not reveal hidden reasoning.{refinement}
Do not call tools. Return exactly one raw JSON object with no markdown or commentary.
Schema version: {DREAM_SCHEMA_VERSION}
emit: {{"schema_version":"{DREAM_SCHEMA_VERSION}","outcome":"emit","drafts":[{{"draft_id":"d1","content_utf8":"...","scope_hint":null,"stability_hint":null,"uncertainty_hint":null}}],"defer_reason":null}}
defer: {{"schema_version":"{DREAM_SCHEMA_VERSION}","outcome":"defer","drafts":[],"defer_reason":"short reason"}}
Drafts must be unique and ordered by draft_id. Maximum drafts: {request.max_statements}.
Maximum characters per draft: {request.max_statement_chars}. Maximum total draft characters: {request.max_total_chars}.
prompt_version: {prompt_version}
request_id: {request.request_id}
conversation_material: {json.dumps(turns, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""


def build_dream_format_repair_prompt(raw: str, failure: str) -> str:
    """Ask the same model to format its own visible response without changing meaning."""
    return f"""Return exactly one strict JSON object and nothing else.
The following visible output was rejected only because it is not strict JSON: {failure}
Do not add, remove, rename, infer, summarize, or alter any field or string value.
Do not use markdown fences. Do not call tools.
visible_output:
{raw}"""


def parse_dream_result(raw: str, request: DreamFormationRequest, result_id: str) -> DreamFormationResult:
    result, _ = parse_dream_result_with_diagnostics(raw, request, result_id)
    return result


def parse_dream_result_with_diagnostics(
    raw: str, request: DreamFormationRequest, result_id: str,
) -> tuple[DreamFormationResult, dict[str, object]]:
    try:
        repaired, diagnostics = repair_dream_json(raw)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    common = {"schema_version", "outcome", "drafts"}
    if type(value) is not dict or value.get("schema_version") != DREAM_SCHEMA_VERSION or type(value.get("drafts")) is not list:
        raise FormationAdapterError("invalid_schema", "invalid Dream Formation envelope")
    outcome = value.get("outcome")
    if outcome == "defer":
        if set(value) != common | {"defer_reason"}:
            raise FormationAdapterError("invalid_schema", "defer has incorrect fields")
        return DreamFormationResult(result_id, request.request_id, "defer", (), value["defer_reason"], "llm"), diagnostics
    if outcome != "emit" or set(value) != common | {"defer_reason"} or value["defer_reason"] is not None:
        raise FormationAdapterError("invalid_schema", "emit has incorrect fields")
    try:
        drafts = tuple(DreamMemoryDraft.from_mapping(item) for item in value["drafts"])
        result = DreamFormationResult(result_id, request.request_id, "emit", drafts, None, "llm")
        form_dream_statements(request, result)
        return result, diagnostics
    except (TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_dream_result", str(exc)) from exc


def repair_dream_json(raw: str) -> tuple[str, dict[str, object]]:
    """Apply only the explicitly allowed non-semantic JSON envelope repairs."""
    if type(raw) is not str:
        raise json.JSONDecodeError("response must be text", "", 0)
    before_sha256 = sha256_hex(raw.encode("utf-8"))
    text = raw
    repairs: list[str] = []
    if text.startswith("\ufeff"):
        text = text[1:]
        repairs.append("bom")
    trimmed = text.strip()
    if trimmed != text:
        text = trimmed
        repairs.append("outer_whitespace")
    fenced = _unfence_single_json(text)
    if fenced != text:
        text = fenced
        repairs.append("single_json_fence")
    object_text = _extract_single_complete_object(text)
    if object_text != text:
        text = object_text
        repairs.append("single_object_outer_text")
    comma_repaired = _remove_trailing_commas(text)
    if comma_repaired != text:
        text = comma_repaired
        repairs.append("trailing_comma")
    if _json_string_tokens(raw) != _json_string_tokens(text):
        raise json.JSONDecodeError("repair would modify a JSON string value", raw, 0)
    return text, {
        "repair_types": repairs,
        "before_sha256": before_sha256,
        "after_sha256": sha256_hex(text.encode("utf-8")),
        "string_values_unchanged": True,
        "fields_added": False,
        "fields_removed": False,
    }


def _unfence_single_json(text: str) -> str:
    lines = text.splitlines()
    if len(lines) < 3 or not re.fullmatch(r"```(?:json)?[ \t]*", lines[0], re.IGNORECASE) or lines[-1].strip() != "```":
        return text
    return "\n".join(lines[1:-1]).strip()


def _extract_single_complete_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise json.JSONDecodeError("response must contain one JSON object", text, 0)
    end = _complete_object_end(text, start)
    if end is None:
        raise json.JSONDecodeError("response has no complete JSON object", text, start)
    prefix = text[:start].strip()
    remainder = text[end + 1 :]
    if prefix not in {"", "JSON:", "Here is the JSON:", "Here is the requested JSON:"}:
        raise json.JSONDecodeError("response has unsupported outer text", text, 0)
    if remainder.strip() or _contains_object_start(remainder):
        raise json.JSONDecodeError("response contains multiple JSON objects", text, end + 1)
    return text[start : end + 1]


def _complete_object_end(text: str, start: int) -> int | None:
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
            if depth < 0:
                return None
    return None


def _contains_object_start(text: str) -> bool:
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == "{":
            return True
    return False


def _remove_trailing_commas(text: str) -> str:
    output: list[str] = []
    quoted = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            index += 1
            continue
        if char == '"':
            quoted = True
            output.append(char)
            index += 1
            continue
        if char == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "]}":
                index += 1
                continue
        output.append(char)
        index += 1
    return "".join(output)


def _json_string_tokens(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    start: int | None = None
    escaped = False
    for index, char in enumerate(text):
        if start is None:
            if char == '"':
                start = index
            continue
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == '"':
            tokens.append(text[start : index + 1])
            start = None
    if start is not None:
        raise json.JSONDecodeError("unterminated JSON string", text, start)
    return tuple(tokens)


def process_dream_result(raw: str, request: DreamFormationRequest, result_id: str, workspace: Path | None) -> dict[str, object]:
    result, diagnostics = parse_dream_result_with_diagnostics(raw, request, result_id)
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
        "json_repair": diagnostics,
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
