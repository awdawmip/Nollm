from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from nollm_access import (
    AccessMemoryLoop,
    ProgressiveAtlasPage,
    validate_dream_sculptor_plans,
)

from .adapter import FormationAdapterError
from .dream_adapter import repair_dream_json
from .sculptor import _captures, _workspace


PROPOSITION_WRITER_SCHEMA_VERSION = "nollm_openclaw_contextual_proposition_writer_v2"
LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION = "nollm_openclaw_proposition_writer_v1"
FIELD_CARTOGRAPHER_SCHEMA_VERSION = "nollm_openclaw_field_cartographer_v2"
PROPOSITION_WRITER_PROMPT_VERSION = "proposition-writer-v2-bounded-narrative-context"
FIELD_CARTOGRAPHER_PROMPT_VERSION = "field-cartographer-v2-shared-retrieval-entry"
MAX_PROMPT_BYTES = 65536
MAX_CARTOGRAPHER_TURNS = 4
MAX_CONTEXT_CAPTURES = 4
MAX_CONTEXT_CHARS = 6000


def build_proposition_writer_prompt(
    captures: object,
    request_id: object,
    max_statements: object = 8,
    context_captures: object = None,
) -> dict[str, object]:
    clean = _captures(captures)
    context = _validated_context_captures(clean, context_captures)
    if type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_writer_request", "request_id is required")
    if type(max_statements) is not int or not 1 <= max_statements <= 8:
        raise FormationAdapterError("invalid_writer_budget", "max_statements must be in [1,8]")
    def wire(items: list[dict[str, object]]) -> list[dict[str, object]]:
        return [{
        "capture_id": item["capture_id"],
        "user_utf8": item["user_utf8"],
        "user_length_chars": len(item["user_utf8"]),
        "assistant_utf8": item["assistant_utf8"],
        "assistant_length_chars": len(item["assistant_utf8"]),
        "reference_epoch_ms": item["captured_epoch_ms"],
        "timezone_offset_minutes": item["timezone_offset_minutes"],
        } for item in items]
    prompt = f"""You are Nollm's private Contextual Proposition Writer.
Form complete Evidence-backed MemoryStatements for absorption_sources only. context_only_evidence is bounded earlier conversation used only to resolve pronouns, time, location, and event continuity; never copy it into a new Statement and never treat it as a new absorption source. Generic assistant advice is not user memory unless the user supplied or adopted it.
Every proposition cites exact Python-style Unicode evidence_spans. Any normalized absolute date, location, or coreference not verbatim in the source requires a resolved_reference with explicit Capture/span basis. Separate direct_queries, which the new proposition answers, from broader entry_queries, which name a plausible shared retrieval neighborhood a future reader could enter before knowing the new answer. Do not inspect or mention any field, Atlas, region, Locality, action, Handle, coordinate, Topic, entity, vector, graph, or placement.
Return exactly one raw JSON object with no markdown.
schema_version: {PROPOSITION_WRITER_SCHEMA_VERSION}
plan: {{"schema_version":"{PROPOSITION_WRITER_SCHEMA_VERSION}","outcome":"plan","propositions":[{{"draft_id":"d1","content_utf8":"complete proposition","source_capture_ids":["source capture id"],"evidence_spans":[{{"capture_id":"source or context capture id","role":"user|assistant","start":0,"end":1,"quote_utf8":"exact slice"}}],"context_statement_refs":[],"resolved_references":[{{"kind":"temporal|coreference|location","normalized_value":"resolved value","basis_capture_ids":["capture id"],"basis_span_indexes":[0]}}],"direct_queries":[{{"query_id":"direct-1","query_utf8":"question directly answered by the new proposition"}}],"entry_queries":[{{"query_id":"entry-1","query_utf8":"broader shared retrieval question"}}]}}],"defer_reason":null}}
terminal: {{"schema_version":"{PROPOSITION_WRITER_SCHEMA_VERSION}","outcome":"no_memory|defer","propositions":[],"defer_reason":"brief"}}
Draft IDs and source Capture IDs must be unique and sorted. Maximum Statements: {max_statements}.
request_id: {request_id}
absorption_sources: {json.dumps(wire(clean), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
context_only_evidence: {json.dumps(wire(context), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"""
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes > MAX_PROMPT_BYTES:
        raise FormationAdapterError("writer_prompt_overflow", "Contextual Writer prompt exceeds 64 KiB")
    return {
        "status": "writer_decision",
        "prompt": prompt,
        "prompt_version": PROPOSITION_WRITER_PROMPT_VERSION,
        "schema_version": PROPOSITION_WRITER_SCHEMA_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_utf8_bytes": prompt_bytes,
        "captures": clean,
        "context_captures": context,
        "context_capture_count": len(context),
        "context_chars": sum(len(item["user_utf8"]) + len(item["assistant_utf8"]) for item in context),
        "field_input_count": 0,
    }


def parse_proposition_writer_result(
    raw_response: object,
    captures: object,
    request_id: object,
    context_captures: object = None,
) -> dict[str, object]:
    clean = _captures(captures)
    context = _validated_context_captures(clean, context_captures)
    if type(raw_response) is not str or type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_writer_result", "Writer response and request_id are required")
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    keys = {"schema_version", "outcome", "propositions", "defer_reason"}
    if type(value) is not dict or set(value) != keys or value.get("schema_version") not in {PROPOSITION_WRITER_SCHEMA_VERSION, LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION} or type(value.get("propositions")) is not list:
        raise FormationAdapterError("invalid_writer_schema", "invalid Proposition Writer envelope")
    if value["outcome"] in {"no_memory", "defer"}:
        if value["propositions"] or type(value["defer_reason"]) is not str or not value["defer_reason"]:
            raise FormationAdapterError("invalid_writer_schema", "invalid terminal Writer outcome")
        return {"outcome": value["outcome"], "propositions": [], "defer_reason": value["defer_reason"], "json_repair": diagnostics}
    if value["outcome"] != "plan" or not 1 <= len(value["propositions"]) <= 8 or value["defer_reason"] is not None:
        raise FormationAdapterError("invalid_writer_schema", "invalid planned Writer outcome")
    source_map = {item["capture_id"]: item for item in clean}
    evidence_map = {item["capture_id"]: item for item in clean + context}
    legacy = value["schema_version"] == LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION
    propositions = tuple(_proposition(item, source_map, evidence_map, legacy) for item in value["propositions"])
    draft_ids = [item["draft_id"] for item in propositions]
    if draft_ids != sorted(set(draft_ids)):
        raise FormationAdapterError("invalid_writer_schema", "Writer draft IDs must be canonical and unique")
    return {
        "outcome": "plan", "propositions": list(propositions), "defer_reason": None,
        "context_capture_ids": [item["capture_id"] for item in context],
        "json_repair": diagnostics,
    }


def build_field_cartographer_prompt(
    writer_result: object,
    memory_workspace: object,
    request_id: object,
    turn: object = 1,
    page_value: object = None,
    local_detail: object = None,
) -> dict[str, object]:
    propositions = _writer_propositions(writer_result)
    if type(request_id) is not str or not request_id or type(turn) is not int or not 1 <= turn <= MAX_CARTOGRAPHER_TURNS:
        raise FormationAdapterError("invalid_cartographer_request", "Cartographer request identity or turn is invalid")
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        page = loop.build_progressive_atlas(request_id + ":root") if page_value is None else ProgressiveAtlasPage.from_mapping(page_value)
    if page.overflow:
        return {
            "status": "atlas_page_overflow", "retryable": True, "turn": turn,
            "page": page.to_mapping(), "atlas_fingerprint": page.atlas_fingerprint,
        }
    if local_detail is not None and type(local_detail) is not dict:
        raise FormationAdapterError("invalid_cartographer_request", "local detail must be an object")
    prompt = _cartographer_prompt(propositions, page, request_id, turn, local_detail)
    prompt_bytes = len(prompt.encode("utf-8"))
    if prompt_bytes > page.policy.max_prompt_bytes:
        raise FormationAdapterError("cartographer_prompt_overflow", "Cartographer prompt exceeds the active byte budget")
    return {
        "status": "cartographer_decision",
        "prompt": prompt,
        "prompt_version": FIELD_CARTOGRAPHER_PROMPT_VERSION,
        "schema_version": FIELD_CARTOGRAPHER_SCHEMA_VERSION,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "prompt_utf8_bytes": prompt_bytes,
        "turn": turn,
        "max_turns": MAX_CARTOGRAPHER_TURNS,
        "page": page.to_mapping(),
        "atlas_fingerprint": page.atlas_fingerprint,
    }


def advance_field_cartographer(
    raw_response: object,
    writer_result: object,
    page_value: object,
    memory_workspace: object,
    request_id: object,
    turn: object,
) -> dict[str, object]:
    propositions = _writer_propositions(writer_result)
    if type(raw_response) is not str or type(request_id) is not str or not request_id or type(turn) is not int:
        raise FormationAdapterError("invalid_cartographer_result", "Cartographer response fields are invalid")
    page = ProgressiveAtlasPage.from_mapping(page_value)
    try:
        repaired, diagnostics = repair_dream_json(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    if type(value) is not dict or value.get("schema_version") != FIELD_CARTOGRAPHER_SCHEMA_VERSION or type(value.get("action")) is not str:
        raise FormationAdapterError("invalid_cartographer_schema", "invalid Cartographer envelope")
    if value["action"] == "open_region":
        if set(value) != {"schema_version", "action", "region_id"} or type(value["region_id"]) is not str:
            raise FormationAdapterError("invalid_cartographer_schema", "invalid open_region action")
        if turn >= MAX_CARTOGRAPHER_TURNS:
            raise FormationAdapterError("cartographer_turn_budget", "Cartographer turn budget is exhausted")
        try:
            with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
                child = loop.open_progressive_region(page, value["region_id"], request_id + f":turn:{turn + 1}")
        except (TypeError, ValueError) as exc:
            raise FormationAdapterError("invalid_cartographer_region", str(exc)) from exc
        built = build_field_cartographer_prompt(
            {"outcome": "plan", "propositions": propositions}, memory_workspace,
            request_id, turn + 1, child.to_mapping(),
        )
        return {**built, "action": "open_region", "json_repair": diagnostics}
    if value["action"] == "request_local_detail":
        if set(value) != {"schema_version", "action", "region_id"} or type(value["region_id"]) is not str:
            raise FormationAdapterError("invalid_cartographer_schema", "invalid local detail action")
        if turn >= MAX_CARTOGRAPHER_TURNS:
            raise FormationAdapterError("cartographer_turn_budget", "Cartographer turn budget is exhausted")
        try:
            with AccessMemoryLoop(_workspace(memory_workspace)) as loop:
                detail = loop.local_detail_page(
                    page, value["region_id"], request_id + f":detail:{turn + 1}", limit=32,
                )
        except (TypeError, ValueError) as exc:
            raise FormationAdapterError("invalid_cartographer_region", str(exc)) from exc
        built = build_field_cartographer_prompt(
            {"outcome": "plan", "propositions": propositions}, memory_workspace,
            request_id, turn + 1, page.to_mapping(), detail.to_mapping(),
        )
        return {**built, "action": "request_local_detail", "local_detail": detail.to_mapping(), "json_repair": diagnostics}
    if value["action"] == "defer":
        if set(value) != {"schema_version", "action", "reason_text"} or type(value["reason_text"]) is not str or not value["reason_text"]:
            raise FormationAdapterError("invalid_cartographer_schema", "invalid Cartographer defer")
        return {"status": "complete", "outcome": "defer", "reason_text": value["reason_text"], "plans": [], "turn": turn, "json_repair": diagnostics}
    if value["action"] != "resolve" or set(value) != {"schema_version", "action", "plans"} or type(value["plans"]) is not list:
        raise FormationAdapterError("invalid_cartographer_schema", "invalid Cartographer resolution")
    plans = _cartography_plans(value["plans"], propositions, page)
    return {"status": "complete", "outcome": "plan", "plans": plans, "turn": turn, "page": page.to_mapping(), "json_repair": diagnostics}


def apply_field_cartography_result(
    cartography_result: object,
    writer_result: object,
    captures: object,
    memory_workspace: object,
    request_id: object,
    revision_confirmations: object = None,
    only_statement_ids: object = None,
) -> dict[str, object]:
    propositions = _writer_propositions(writer_result)
    if type(cartography_result) is not dict or cartography_result.get("outcome") != "plan" or type(cartography_result.get("plans")) is not list:
        raise FormationAdapterError("invalid_cartographer_apply", "completed Cartographer plans are required")
    if type(request_id) is not str or not request_id:
        raise FormationAdapterError("invalid_cartographer_apply", "request_id is required")
    root = _workspace(memory_workspace)
    with AccessMemoryLoop(root) as loop:
        atlas = loop.build_locality_atlas(request_id + ":apply-atlas", 512)
    if atlas.overflow:
        raise FormationAdapterError("atlas_overflow", "active apply Atlas exceeds the bounded compatibility view")
    proposition_map = {item["draft_id"]: item for item in propositions}
    old_plans = []
    for plan in cartography_result["plans"]:
        proposition = proposition_map[plan["draft_id"]]
        lenses = []
        for resolution, entry_query in zip(plan["entry_resolutions"], proposition["entry_queries"]):
            lens = {
                "lens_id": entry_query["query_id"],
                "future_query": entry_query["query_utf8"],
                "basis_spans": proposition["evidence_spans"],
            }
            if resolution["unresolved"]:
                lenses.append({**lens, "atlas_path_ids": [], "leaf_locality_candidate_ids": [], "unresolved": True})
                continue
            cell = resolution["entry_cell"]
            candidate = next((item for item in atlas.candidates if cell in [address.to_mapping() for address in item.geometry_addresses]), None)
            if candidate is None:
                raise FormationAdapterError("cartography_entry_stale", "resolved Cartographer entry is absent from the apply Atlas")
            path = next(item for item in atlas.paths if candidate.candidate_id in item.leaf_locality_candidate_ids)
            lenses.append({
                **lens,
                "atlas_path_ids": [path.path_id],
                "leaf_locality_candidate_ids": [candidate.candidate_id],
                "unresolved": False,
            })
        action = {
            "related_growth": "new_local",
            "independent_seed": "independent_seed",
            "reuse": "reuse",
            "revision_current": "revision_current",
            "defer": "defer",
        }[plan["placement_mode"]]
        old_plans.append({
            "draft_id": plan["draft_id"], "content_utf8": proposition["content_utf8"],
            "source_capture_ids": proposition["source_capture_ids"], "lenses": lenses,
            "action": action, "existing_handle": plan["existing_handle"], "reason_text": plan["reason_text"],
        })
    clean = _captures(captures)
    try:
        validated = validate_dream_sculptor_plans(request_id, old_plans, clean, atlas)
        if only_statement_ids is not None:
            if type(only_statement_ids) is not list or not only_statement_ids or any(type(item) is not str for item in only_statement_ids):
                raise TypeError("only_statement_ids must be a nonempty text list")
            selected = set(only_statement_ids)
            validated = tuple(item for item in validated if item.statement_id in selected)
            if len(validated) != len(selected):
                raise ValueError("only_statement_ids contains an unknown Statement")
        with AccessMemoryLoop(root) as loop:
            applied = loop.apply_junction_plans(validated, atlas, request_id, revision_confirmations)
    except (KeyError, TypeError, ValueError) as exc:
        raise FormationAdapterError("invalid_cartographer_apply", str(exc)) from exc
    return {"outcome": "plan", "plans": [item.to_mapping() for item in validated], **applied}


def _validated_context_captures(
    sources: list[dict[str, object]],
    context_captures: object,
) -> list[dict[str, object]]:
    context = [] if context_captures is None else _captures(context_captures)
    source_ids = {item["capture_id"] for item in sources}
    if len(context) > MAX_CONTEXT_CAPTURES or sum(len(item["user_utf8"]) + len(item["assistant_utf8"]) for item in context) > MAX_CONTEXT_CHARS:
        raise FormationAdapterError("invalid_writer_context", "Writer context exceeds its active budget")
    if any(item["capture_id"] in source_ids for item in context):
        raise FormationAdapterError("invalid_writer_context", "Writer context and absorption sources must be disjoint")
    ordered = sorted(context, key=lambda item: (item["captured_epoch_ms"], item["capture_id"]))
    if ordered != context:
        raise FormationAdapterError("invalid_writer_context", "Writer context must be chronological")
    first_source = min((item["captured_epoch_ms"], item["capture_id"]) for item in sources)
    if any((item["captured_epoch_ms"], item["capture_id"]) >= first_source for item in context):
        raise FormationAdapterError("invalid_writer_context", "Writer context must precede every absorption source")
    return context


def _proposition(
    value: object,
    sources: dict[str, dict[str, object]],
    evidence: dict[str, dict[str, object]],
    legacy: bool,
) -> dict[str, object]:
    if legacy:
        return _legacy_proposition(value, sources, evidence)
    keys = {
        "draft_id", "content_utf8", "source_capture_ids", "evidence_spans",
        "context_statement_refs", "resolved_references", "direct_queries", "entry_queries",
    }
    if type(value) is not dict or set(value) != keys:
        raise FormationAdapterError("invalid_writer_schema", "invalid contextual Writer proposition fields")
    if type(value["draft_id"]) is not str or not value["draft_id"] or type(value["content_utf8"]) is not str or not value["content_utf8"]:
        raise FormationAdapterError("invalid_writer_schema", "Writer proposition identity and content are required")
    source_ids = value["source_capture_ids"]
    if type(source_ids) is not list or not source_ids or source_ids != sorted(set(source_ids)) or any(item not in sources for item in source_ids):
        raise FormationAdapterError("invalid_writer_schema", "Writer source Capture IDs are invalid")
    spans = _evidence_spans(value["evidence_spans"], evidence)
    if not any(span["capture_id"] in source_ids for span in spans):
        raise FormationAdapterError("invalid_writer_schema", "each proposition requires source-Capture Evidence")
    if value["context_statement_refs"] != []:
        raise FormationAdapterError("invalid_writer_schema", "context Statement refs require a supplied current-Statement window")
    references = _resolved_references(value["resolved_references"], spans, evidence)
    direct = _queries(value["direct_queries"], "direct")
    entry = _queries(value["entry_queries"], "entry")
    _validate_absolute_dates(value["content_utf8"], spans, references, evidence)
    return {
        **value,
        "source_capture_ids": source_ids,
        "evidence_spans": spans,
        "resolved_references": references,
        "direct_queries": direct,
        "entry_queries": entry,
    }


def _legacy_proposition(
    value: object,
    sources: dict[str, dict[str, object]],
    evidence: dict[str, dict[str, object]],
) -> dict[str, object]:
    keys = {"draft_id", "content_utf8", "source_capture_ids", "lenses"}
    if type(value) is not dict or set(value) != keys:
        raise FormationAdapterError("invalid_writer_schema", "invalid legacy Writer proposition fields")
    source_ids = value["source_capture_ids"]
    if type(source_ids) is not list or not source_ids or source_ids != sorted(set(source_ids)) or any(item not in sources for item in source_ids):
        raise FormationAdapterError("invalid_writer_schema", "Writer source Capture IDs are invalid")
    if type(value["lenses"]) is not list or not 1 <= len(value["lenses"]) <= 4:
        raise FormationAdapterError("invalid_writer_schema", "legacy Writer proposition requires one to four Lenses")
    lenses = [_writer_lens(item, evidence) for item in value["lenses"]]
    spans = []
    seen = set()
    for lens in lenses:
        for span in lens["basis_spans"]:
            identity = json.dumps(span, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            if identity not in seen:
                spans.append(span); seen.add(identity)
    return {
        "draft_id": value["draft_id"], "content_utf8": value["content_utf8"],
        "source_capture_ids": source_ids, "evidence_spans": spans,
        "context_statement_refs": [], "resolved_references": [],
        "direct_queries": [{"query_id": lens["lens_id"], "query_utf8": lens["future_query"]} for lens in lenses],
        "entry_queries": [{"query_id": lens["lens_id"], "query_utf8": lens["future_query"]} for lens in lenses],
    }


def _evidence_spans(value: object, captures: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    if type(value) is not list or not 1 <= len(value) <= 8:
        raise FormationAdapterError("invalid_writer_schema", "Writer Evidence spans are invalid")
    output = []
    for span in value:
        if type(span) is not dict or set(span) != {"capture_id", "role", "start", "end", "quote_utf8"}:
            raise FormationAdapterError("invalid_writer_schema", "invalid Writer Evidence span")
        capture = captures.get(span["capture_id"])
        if capture is None or span["role"] not in {"user", "assistant"} or type(span["start"]) is not int or type(span["end"]) is not int:
            raise FormationAdapterError("invalid_writer_schema", "Writer Evidence span reference is invalid")
        content = capture[f"{span['role']}_utf8"]
        if not 0 <= span["start"] < span["end"] <= len(content) or content[span["start"]:span["end"]] != span["quote_utf8"]:
            raise FormationAdapterError("invalid_writer_schema", "Writer Evidence span does not match exact Capture text")
        output.append(span)
    return output


def _queries(value: object, kind: str) -> list[dict[str, str]]:
    if type(value) is not list or not 1 <= len(value) <= 4:
        raise FormationAdapterError("invalid_writer_schema", f"Writer {kind} queries are invalid")
    if any(type(item) is not dict or set(item) != {"query_id", "query_utf8"} or type(item["query_id"]) is not str or not item["query_id"] or type(item["query_utf8"]) is not str or not item["query_utf8"] for item in value):
        raise FormationAdapterError("invalid_writer_schema", f"Writer {kind} query is invalid")
    if len({item["query_id"] for item in value}) != len(value):
        raise FormationAdapterError("invalid_writer_schema", f"Writer {kind} query IDs must be unique")
    return value


def _resolved_references(
    value: object,
    spans: list[dict[str, object]],
    captures: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    if type(value) is not list or len(value) > 8:
        raise FormationAdapterError("invalid_writer_schema", "Writer resolved references are invalid")
    output = []
    for item in value:
        keys = {"kind", "normalized_value", "basis_capture_ids", "basis_span_indexes"}
        if type(item) is not dict or set(item) != keys or item["kind"] not in {"temporal", "coreference", "location"} or type(item["normalized_value"]) is not str or not item["normalized_value"]:
            raise FormationAdapterError("invalid_writer_schema", "invalid Writer resolved reference")
        capture_ids = item["basis_capture_ids"]
        indexes = item["basis_span_indexes"]
        if type(capture_ids) is not list or capture_ids != sorted(set(capture_ids)) or any(capture_id not in captures for capture_id in capture_ids):
            raise FormationAdapterError("invalid_writer_schema", "resolved reference Capture basis is invalid")
        if type(indexes) is not list or indexes != sorted(set(indexes)) or any(type(index) is not int or not 0 <= index < len(spans) for index in indexes):
            raise FormationAdapterError("invalid_writer_schema", "resolved reference span basis is invalid")
        if not capture_ids and not indexes:
            raise FormationAdapterError("invalid_writer_schema", "resolved reference requires explicit Evidence basis")
        output.append(item)
    return output


def _validate_absolute_dates(
    content: str,
    spans: list[dict[str, object]],
    references: list[dict[str, object]],
    captures: dict[str, dict[str, object]],
) -> None:
    dates = set()
    for match in re.finditer(r"(?<!\d)(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})(?:日)?", content):
        try:
            dates.add(datetime(int(match.group(1)), int(match.group(2)), int(match.group(3))).date().isoformat())
        except ValueError as exc:
            raise FormationAdapterError("unsupported_absolute_date", "Writer produced an invalid absolute date") from exc
    span_text = "\n".join(str(span["quote_utf8"]) for span in spans)
    for date_text in dates:
        year, month, day = (int(part) for part in date_text.split("-"))
        variants = {date_text, f"{year}/{month}/{day}", f"{year}年{month}月{day}日"}
        if any(variant in span_text for variant in variants):
            continue
        matching = [item for item in references if item["kind"] == "temporal" and item["normalized_value"] == date_text]
        if not matching or not any(_temporal_basis_matches(date_text, item, spans, captures) for item in matching):
            raise FormationAdapterError("unsupported_absolute_date", f"Writer absolute date {date_text} has no Evidence basis")


def _temporal_basis_matches(
    date_text: str,
    reference: dict[str, object],
    spans: list[dict[str, object]],
    captures: dict[str, dict[str, object]],
) -> bool:
    for capture_id in reference["basis_capture_ids"]:
        capture = captures[capture_id]
        offset = timezone(timedelta(minutes=capture["timezone_offset_minutes"]))
        observed = datetime.fromtimestamp(capture["captured_epoch_ms"] / 1000, tz=offset).date().isoformat()
        if observed == date_text:
            return True
    year, month, day = (int(part) for part in date_text.split("-"))
    variants = {date_text, f"{year}/{month}/{day}", f"{year}年{month}月{day}日"}
    return any(any(variant in spans[index]["quote_utf8"] for variant in variants) for index in reference["basis_span_indexes"])


def _writer_lens(value: object, captures: dict[str, dict[str, object]]) -> dict[str, object]:
    keys = {"lens_id", "future_query", "basis_spans"}
    if type(value) is not dict or set(value) != keys or type(value["lens_id"]) is not str or not value["lens_id"] or type(value["future_query"]) is not str or not value["future_query"]:
        raise FormationAdapterError("invalid_writer_schema", "invalid Writer Lens")
    if type(value["basis_spans"]) is not list or not 1 <= len(value["basis_spans"]) <= 8:
        raise FormationAdapterError("invalid_writer_schema", "Writer Lens basis spans are invalid")
    for span in value["basis_spans"]:
        if type(span) is not dict or set(span) != {"capture_id", "role", "start", "end", "quote_utf8"}:
            raise FormationAdapterError("invalid_writer_schema", "invalid Writer Lens basis span")
        capture = captures.get(span["capture_id"])
        if capture is None or span["role"] not in {"user", "assistant"} or type(span["start"]) is not int or type(span["end"]) is not int:
            raise FormationAdapterError("invalid_writer_schema", "Writer Lens basis reference is invalid")
        content = capture[f"{span['role']}_utf8"]
        if not 0 <= span["start"] < span["end"] <= len(content) or content[span["start"]:span["end"]] != span["quote_utf8"]:
            raise FormationAdapterError("invalid_writer_schema", "Writer Lens basis span does not match exact Capture text")
    return value


def _writer_propositions(value: object) -> list[dict[str, object]]:
    if type(value) is not dict or value.get("outcome") != "plan" or type(value.get("propositions")) is not list or not value["propositions"]:
        raise FormationAdapterError("invalid_writer_result", "planned Writer propositions are required")
    return value["propositions"]


def _cartographer_prompt(
    propositions: list[dict[str, object]],
    page: ProgressiveAtlasPage,
    request_id: str,
    turn: int,
    local_detail: dict[str, object] | None,
) -> str:
    return f"""You are Nollm's private Field Cartographer in one bounded background session.
Resolve every entry_query to a plausible shared retrieval neighborhood visible on the complete Atlas page, or mark it unresolved. An entry query is broader than a direct query: the existing region need not already contain the new answer. Resolve when a future reader could reasonably enter the region for a shared place, time, event continuation, comparison, cause, or consequence and then discover the new fact nearby. Representatives are navigation hints, never complete local truth.
Positive examples: a Tokyo trip continuation may grow near an existing Tokyo/Asakusa memory; notes written "that evening" may grow near the referenced meeting; Osaka sunshine on the same date may grow near that date's Tokyo weather as a comparison. Negative examples: audit retention is unrelated to Tokyo weather; a 2 AM server backup is not related to a meeting merely because both mention time. Never use keyword overlap alone.
Use open_region when a region must be inspected. Use request_local_detail before reuse or revision_current when exact current Statements are not present. Use independent_seed only when every entry query is unresolved. Use related_growth when at least one entry query resolves. Do not invent coordinates, regions, Topics, entities, vectors, graphs, facts, or persistent relation labels. Do not modify Statement text.
Return exactly one raw JSON object with no markdown.
schema_version: {FIELD_CARTOGRAPHER_SCHEMA_VERSION}
open: {{"schema_version":"{FIELD_CARTOGRAPHER_SCHEMA_VERSION}","action":"open_region","region_id":"visible region id"}}
detail: {{"schema_version":"{FIELD_CARTOGRAPHER_SCHEMA_VERSION}","action":"request_local_detail","region_id":"visible region id"}}
resolve: {{"schema_version":"{FIELD_CARTOGRAPHER_SCHEMA_VERSION}","action":"resolve","plans":[{{"draft_id":"d1","placement_mode":"related_growth|independent_seed|reuse|revision_current|defer","entry_resolutions":[{{"entry_query_id":"entry-1","region_id":"visible region id or null","entry_id":"visible support entry id or null","unresolved":false}}],"existing_handle":null,"reason_text":"brief"}}]}}
defer: {{"schema_version":"{FIELD_CARTOGRAPHER_SCHEMA_VERSION}","action":"defer","reason_text":"brief"}}
request_id: {request_id}
turn: {turn}/{MAX_CARTOGRAPHER_TURNS}
propositions_and_queries: {json.dumps(propositions, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
progressive_atlas_page: {json.dumps(page.to_mapping(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))}
local_detail_page: {json.dumps(local_detail, ensure_ascii=False, sort_keys=True, separators=(',', ':')) if local_detail is not None else 'null'}"""


def _cartography_plans(values: list[object], propositions: list[dict[str, object]], page: ProgressiveAtlasPage) -> list[dict[str, object]]:
    if len(values) != len(propositions):
        raise FormationAdapterError("invalid_cartographer_schema", "Cartographer must decide every proposition")
    proposition_map = {item["draft_id"]: item for item in propositions}
    region_map = {item.region_id: item for item in page.regions}
    output = []
    seen_drafts = set()
    for value in values:
        keys = {"draft_id", "placement_mode", "entry_resolutions", "existing_handle", "reason_text"}
        if type(value) is not dict or set(value) != keys or value.get("draft_id") not in proposition_map or value["draft_id"] in seen_drafts:
            raise FormationAdapterError("invalid_cartographer_schema", "invalid Cartographer plan identity")
        seen_drafts.add(value["draft_id"])
        proposition = proposition_map[value["draft_id"]]
        if type(value["entry_resolutions"]) is not list or len(value["entry_resolutions"]) != len(proposition["entry_queries"]):
            raise FormationAdapterError("invalid_cartographer_schema", "Cartographer must decide every entry query")
        resolutions = []
        for raw, entry_query in zip(value["entry_resolutions"], proposition["entry_queries"]):
            if type(raw) is not dict or set(raw) != {"entry_query_id", "region_id", "entry_id", "unresolved"} or raw.get("entry_query_id") != entry_query["query_id"] or type(raw.get("unresolved")) is not bool:
                raise FormationAdapterError("invalid_cartographer_schema", "invalid entry-query resolution")
            if raw["unresolved"]:
                if raw["region_id"] is not None or raw["entry_id"] is not None:
                    raise FormationAdapterError("invalid_cartographer_schema", "unresolved Lens cannot claim an entry")
                resolutions.append({**raw, "entry_cell": None})
                continue
            region = region_map.get(raw["region_id"])
            if region is None:
                raise FormationAdapterError("invalid_cartographer_schema", "resolved Lens selected an unavailable region")
            entry = next((item for item in region.support_entries if item["entry_id"] == raw["entry_id"]), None)
            if entry is None:
                raise FormationAdapterError("invalid_cartographer_schema", "resolved Lens selected an unavailable support entry")
            resolutions.append({**raw, "entry_cell": entry["entry_cell"]})
        mode = value["placement_mode"]
        if mode not in {"related_growth", "independent_seed", "reuse", "revision_current", "defer"}:
            raise FormationAdapterError("invalid_cartographer_schema", "invalid Cartographer placement mode")
        resolved_count = sum(not item["unresolved"] for item in resolutions)
        resolved_cells = [
            json.dumps(item["entry_cell"], sort_keys=True, separators=(",", ":"))
            for item in resolutions if not item["unresolved"]
        ]
        if len(resolved_cells) != len(set(resolved_cells)):
            raise FormationAdapterError("invalid_cartographer_schema", "resolved Lens relation groups must be unique")
        if mode == "independent_seed" and resolved_count != 0:
            raise FormationAdapterError("invalid_cartographer_schema", "independent_seed requires every Lens unresolved")
        if mode in {"related_growth", "reuse", "revision_current"} and resolved_count == 0:
            raise FormationAdapterError("invalid_cartographer_schema", "related placement requires a resolved Lens")
        if mode in {"reuse", "revision_current"} and value["existing_handle"] is None:
            raise FormationAdapterError("invalid_cartographer_schema", "reuse and revision require an exact Handle")
        if type(value["reason_text"]) is not str or not value["reason_text"]:
            raise FormationAdapterError("invalid_cartographer_schema", "Cartographer reason_text is required")
        output.append({**value, "entry_resolutions": resolutions})
    return output
