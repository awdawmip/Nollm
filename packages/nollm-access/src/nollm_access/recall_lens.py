from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from nollm_core import AtomHandle

from .locality import LocalityAtlas
from .statement import MemoryStatement


DREAM_SCULPTOR_SCHEMA_VERSION = "nollm_openclaw_dream_sculptor_v1"
SCULPTOR_ACTIONS = frozenset({"reuse", "new_local", "expand_surface", "revision_current", "defer"})


@dataclass(frozen=True)
class LensBasisSpan:
    capture_id: str
    role: str
    start: int
    end: int
    quote_utf8: str

    def __post_init__(self) -> None:
        if type(self.capture_id) is not str or not self.capture_id or self.role not in {"user", "assistant"}:
            raise TypeError("Lens basis capture and role are invalid")
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start < self.end:
            raise ValueError("Lens basis offsets are invalid")
        if type(self.quote_utf8) is not str or not self.quote_utf8:
            raise TypeError("Lens basis quote is required")

    def to_mapping(self) -> dict[str, object]:
        return {"capture_id": self.capture_id, "role": self.role, "start": self.start, "end": self.end, "quote_utf8": self.quote_utf8}


@dataclass(frozen=True)
class RecallLens:
    lens_id: str
    future_query: str
    basis_spans: tuple[LensBasisSpan, ...]
    locality_candidate_ids: tuple[str, ...]
    unresolved: bool

    def __post_init__(self) -> None:
        if type(self.lens_id) is not str or not self.lens_id or type(self.future_query) is not str or not self.future_query:
            raise TypeError("Lens identity and future_query are required")
        if type(self.basis_spans) is not tuple or not self.basis_spans or len(self.basis_spans) > 8 or any(type(item) is not LensBasisSpan for item in self.basis_spans):
            raise ValueError("Lens basis spans are invalid")
        if type(self.locality_candidate_ids) is not tuple or len(self.locality_candidate_ids) > 4 or any(type(item) is not str or not item for item in self.locality_candidate_ids):
            raise ValueError("Lens Locality candidates are invalid")
        if tuple(sorted(set(self.locality_candidate_ids))) != self.locality_candidate_ids or type(self.unresolved) is not bool:
            raise ValueError("Lens candidates must be canonical and unresolved must be bool")

    def to_mapping(self) -> dict[str, object]:
        return {
            "lens_id": self.lens_id,
            "future_query": self.future_query,
            "basis_spans": [item.to_mapping() for item in self.basis_spans],
            "locality_candidate_ids": list(self.locality_candidate_ids),
            "unresolved": self.unresolved,
        }


@dataclass(frozen=True)
class JunctionSemanticPlan:
    statement: MemoryStatement
    source_capture_ids: tuple[str, ...]
    lenses: tuple[RecallLens, ...]
    action: str
    primary_candidate_id: str | None
    contact_candidate_ids: tuple[str, ...]
    existing_handle: AtomHandle | None
    reason_text: str

    def __post_init__(self) -> None:
        if type(self.statement) is not MemoryStatement or self.action not in SCULPTOR_ACTIONS:
            raise ValueError("Statement or sculptor action is invalid")
        if type(self.source_capture_ids) is not tuple or not self.source_capture_ids or tuple(sorted(set(self.source_capture_ids))) != self.source_capture_ids:
            raise ValueError("source_capture_ids must be a canonical non-empty tuple")
        if type(self.lenses) is not tuple or not 1 <= len(self.lenses) <= 4 or any(type(item) is not RecallLens for item in self.lenses):
            raise ValueError("each Statement requires one to four Recall Lenses")
        if self.primary_candidate_id is not None and (type(self.primary_candidate_id) is not str or not self.primary_candidate_id):
            raise TypeError("primary_candidate_id must be null or text")
        if type(self.contact_candidate_ids) is not tuple or len(self.contact_candidate_ids) > 3 or tuple(sorted(set(self.contact_candidate_ids))) != self.contact_candidate_ids:
            raise ValueError("contact_candidate_ids must be canonical and bounded")
        if self.existing_handle is not None and type(self.existing_handle) is not AtomHandle:
            raise TypeError("existing_handle must be null or AtomHandle")
        if self.action in {"reuse", "revision_current"} and self.existing_handle is None:
            raise ValueError("reuse and revision_current require existing_handle")
        if self.action in {"new_local", "expand_surface", "reuse", "revision_current"} and self.primary_candidate_id is None:
            raise ValueError("non-deferred action requires primary_candidate_id")
        if type(self.reason_text) is not str or not self.reason_text:
            raise TypeError("reason_text is required")

    def to_mapping(self) -> dict[str, object]:
        return {
            "statement": self.statement.to_mapping(),
            "source_capture_ids": list(self.source_capture_ids),
            "lenses": [item.to_mapping() for item in self.lenses],
            "action": self.action,
            "primary_candidate_id": self.primary_candidate_id,
            "contact_candidate_ids": list(self.contact_candidate_ids),
            "existing_handle": None if self.existing_handle is None else self.existing_handle.to_mapping(),
            "reason_text": self.reason_text,
        }


def validate_dream_sculptor_plans(
    request_id: str,
    values: object,
    captures: object,
    atlas: LocalityAtlas,
) -> tuple[JunctionSemanticPlan, ...]:
    if type(request_id) is not str or not request_id or type(values) is not list or not values:
        raise ValueError("Dream Sculptor plans require request identity and values")
    if type(captures) is not list or not captures or type(atlas) is not LocalityAtlas:
        raise TypeError("Dream Sculptor Captures and Atlas are required")
    capture_map = {}
    for capture in captures:
        keys = {"capture_id", "user_utf8", "assistant_utf8", "captured_epoch_ms", "timezone_offset_minutes"}
        if type(capture) is not dict or set(capture) != keys or type(capture["capture_id"]) is not str:
            raise ValueError("invalid Dream Sculptor Capture")
        capture_map[capture["capture_id"]] = capture
    candidate_map = {item.candidate_id: item for item in atlas.candidates}
    plans = []
    draft_ids = []
    keys = {"draft_id", "content_utf8", "source_capture_ids", "lenses", "action", "primary_candidate_id", "contact_candidate_ids", "existing_handle", "reason_text"}
    for value in values:
        if type(value) is not dict or set(value) != keys:
            raise ValueError("invalid Dream Sculptor Statement plan fields")
        draft_id = value["draft_id"]
        if type(draft_id) is not str or not draft_id or type(value["content_utf8"]) is not str or not value["content_utf8"]:
            raise TypeError("draft_id and content_utf8 are required")
        draft_ids.append(draft_id)
        source_ids = _canonical_ids(value["source_capture_ids"], "source_capture_ids", 8, require=True)
        if any(item not in capture_map for item in source_ids):
            raise ValueError("unknown source Capture")
        lenses = tuple(_lens(item, capture_map, candidate_map) for item in value["lenses"] if type(item) is dict)
        if len(lenses) != len(value["lenses"]):
            raise ValueError("invalid Recall Lens")
        primary = value["primary_candidate_id"]
        if primary is not None and primary not in candidate_map:
            raise ValueError("unknown primary Locality candidate")
        contacts = _canonical_ids(value["contact_candidate_ids"], "contact_candidate_ids", 3)
        if any(item not in candidate_map or item == primary for item in contacts):
            raise ValueError("unknown or duplicate contact Locality candidate")
        handle = None if value["existing_handle"] is None else AtomHandle.from_mapping(value["existing_handle"])
        statement_payload = f"{DREAM_SCULPTOR_SCHEMA_VERSION}\0{request_id}\0{draft_id}".encode("utf-8")
        statement = MemoryStatement(
            f"dream:{sha256(statement_payload).hexdigest()}", value["content_utf8"],
            context_refs=tuple(f"capture:{item}" for item in source_ids),
        )
        plans.append(JunctionSemanticPlan(statement, source_ids, lenses, value["action"], primary, contacts, handle, value["reason_text"]))
    if draft_ids != sorted(set(draft_ids)):
        raise ValueError("Dream Sculptor drafts must be canonical and unique")
    return tuple(plans)


def _lens(value: dict[str, object], captures: dict[str, dict[str, object]], candidates: dict[str, object]) -> RecallLens:
    keys = {"lens_id", "future_query", "basis_spans", "locality_candidate_ids", "unresolved"}
    if set(value) != keys or type(value["basis_spans"]) is not list:
        raise ValueError("invalid Recall Lens fields")
    spans = []
    for raw in value["basis_spans"]:
        if type(raw) is not dict or set(raw) != {"capture_id", "role", "start", "end", "quote_utf8"}:
            raise ValueError("invalid Lens basis span")
        span = LensBasisSpan(raw["capture_id"], raw["role"], raw["start"], raw["end"], raw["quote_utf8"])
        if span.capture_id not in captures:
            raise ValueError("Lens basis references unknown Capture")
        field = "user_utf8" if span.role == "user" else "assistant_utf8"
        content = captures[span.capture_id][field]
        if type(content) is not str or span.end > len(content) or content[span.start:span.end] != span.quote_utf8:
            raise ValueError("Lens basis span does not match exact Capture text")
        spans.append(span)
    candidate_ids = _canonical_ids(value["locality_candidate_ids"], "locality_candidate_ids", 4)
    if any(item not in candidates for item in candidate_ids):
        raise ValueError("Lens references unknown Locality")
    return RecallLens(value["lens_id"], value["future_query"], tuple(spans), candidate_ids, value["unresolved"])


def _canonical_ids(value: object, name: str, limit: int, require: bool = False) -> tuple[str, ...]:
    if type(value) is not list or len(value) > limit or (require and not value) or any(type(item) is not str or not item for item in value):
        raise ValueError(f"{name} must be a bounded string list")
    result = tuple(value)
    if tuple(sorted(set(result))) != result:
        raise ValueError(f"{name} must be canonical and unique")
    return result
