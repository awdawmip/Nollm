from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


CAPTURE_KEYS = {"capture_id", "user_utf8", "assistant_utf8", "captured_epoch_ms", "timezone_offset_minutes"}
TOOL_EVIDENCE_KEYS = {"tool_evidence_id", "tool_result_utf8", "observed_epoch_ms"}


def _required_text(name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise TypeError(f"{name} must be a non-empty string")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class EvidenceQuoteRef:
    evidence_ref_id: str
    capture_id: str
    role: str
    quote_utf8: str
    occurrence_hint: int | None = None
    left_context_utf8: str | None = None
    right_context_utf8: str | None = None

    def __post_init__(self) -> None:
        _required_text("evidence_ref_id", self.evidence_ref_id)
        _required_text("capture_id", self.capture_id)
        if self.role not in {"user", "assistant", "tool"}:
            raise ValueError("role must be user, assistant, or tool")
        _required_text("quote_utf8", self.quote_utf8)
        if self.occurrence_hint is not None and (type(self.occurrence_hint) is not int or self.occurrence_hint < 0):
            raise TypeError("occurrence_hint must be null or a non-negative integer")
        for name, value in (("left_context_utf8", self.left_context_utf8), ("right_context_utf8", self.right_context_utf8)):
            if value is not None and (type(value) is not str or not value):
                raise TypeError(f"{name} must be null or non-empty text")

    @classmethod
    def from_mapping(cls, value: object) -> "EvidenceQuoteRef":
        required = {"evidence_ref_id", "role", "quote_utf8"}
        optional = {"occurrence_hint", "left_context_utf8", "right_context_utf8"}
        identities = {"capture_id", "tool_evidence_id"} & set(value) if type(value) is dict else set()
        if type(value) is not dict or not required <= set(value) or len(identities) != 1 or set(value) - required - optional - identities:
            raise ValueError("EvidenceQuoteRef mapping has invalid fields")
        identity = value[next(iter(identities))]
        if value["role"] == "tool" and identities != {"tool_evidence_id"}:
            raise ValueError("tool Evidence refs require tool_evidence_id")
        if value["role"] != "tool" and identities != {"capture_id"}:
            raise ValueError("Capture Evidence refs require capture_id")
        return cls(
            value["evidence_ref_id"], identity, value["role"], value["quote_utf8"],
            value.get("occurrence_hint"), value.get("left_context_utf8"), value.get("right_context_utf8"),
        )

    def to_mapping(self) -> dict[str, object]:
        value: dict[str, object] = {
            "evidence_ref_id": self.evidence_ref_id,
            "role": self.role,
            "quote_utf8": self.quote_utf8,
        }
        value["tool_evidence_id" if self.role == "tool" else "capture_id"] = self.capture_id
        if self.occurrence_hint is not None:
            value["occurrence_hint"] = self.occurrence_hint
        if self.left_context_utf8 is not None:
            value["left_context_utf8"] = self.left_context_utf8
        if self.right_context_utf8 is not None:
            value["right_context_utf8"] = self.right_context_utf8
        return value


@dataclass(frozen=True)
class ExactEvidenceSpan:
    evidence_ref_id: str
    capture_id: str
    role: str
    start: int
    end: int
    quote_utf8: str
    quote_sha256: str
    capture_sha256: str

    def __post_init__(self) -> None:
        _required_text("evidence_ref_id", self.evidence_ref_id)
        _required_text("capture_id", self.capture_id)
        if self.role not in {"user", "assistant", "tool"}:
            raise ValueError("role must be user, assistant, or tool")
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start < self.end:
            raise TypeError("span offsets must satisfy 0 <= start < end")
        _required_text("quote_utf8", self.quote_utf8)
        if any(type(value) is not str or len(value) != 64 for value in (self.quote_sha256, self.capture_sha256)):
            raise TypeError("span digests must be SHA-256 text")

    def to_mapping(self) -> dict[str, object]:
        value = {
            "evidence_ref_id": self.evidence_ref_id,
            "role": self.role,
            "start": self.start,
            "end": self.end,
            "quote_utf8": self.quote_utf8,
            "quote_sha256": self.quote_sha256,
            "capture_sha256": self.capture_sha256,
        }
        value["tool_evidence_id" if self.role == "tool" else "capture_id"] = self.capture_id
        return value

    @classmethod
    def from_mapping(cls, value: object) -> "ExactEvidenceSpan":
        common = {"evidence_ref_id", "role", "start", "end", "quote_utf8", "quote_sha256", "capture_sha256"}
        identities = {"capture_id", "tool_evidence_id"} & set(value) if type(value) is dict else set()
        if type(value) is not dict or set(value) != common | identities or len(identities) != 1:
            raise ValueError("ExactEvidenceSpan mapping must have exact fields")
        identity = value[next(iter(identities))]
        return cls(*(value[key] for key in ("evidence_ref_id",)), identity, *(value[key] for key in ("role", "start", "end", "quote_utf8", "quote_sha256", "capture_sha256")))


def resolve_evidence_quote_refs(refs: object, captures: object) -> tuple[ExactEvidenceSpan, ...]:
    if type(refs) is not list or not refs:
        raise TypeError("Evidence quote refs must be a non-empty list")
    if type(captures) is not list or not captures:
        raise TypeError("Captures must be a non-empty list")
    capture_map: dict[str, dict[str, object]] = {}
    for capture in captures:
        keys = set(capture) if type(capture) is dict else set()
        if type(capture) is not dict or (keys != CAPTURE_KEYS and keys != TOOL_EVIDENCE_KEYS):
            raise ValueError("Evidence mapping must have exact Capture or Tool Evidence fields")
        is_tool = keys == TOOL_EVIDENCE_KEYS
        capture_id = _required_text("evidence identity", capture["tool_evidence_id" if is_tool else "capture_id"])
        if capture_id in capture_map:
            raise ValueError("Evidence identities must be unique")
        if is_tool:
            if type(capture["tool_result_utf8"]) is not str or type(capture["observed_epoch_ms"]) is not int:
                raise TypeError("Tool Evidence content and time fields are invalid")
            capture_map[capture_id] = {"kind": "tool", "content": capture["tool_result_utf8"], "raw": capture}
        else:
            if any(type(capture[key]) is not str for key in ("user_utf8", "assistant_utf8")):
                raise TypeError("Capture role text must be strings")
            if type(capture["captured_epoch_ms"]) is not int or type(capture["timezone_offset_minutes"]) is not int:
                raise TypeError("Capture time fields must be integers")
            capture_map[capture_id] = {"kind": "capture", "content": capture, "raw": capture}
    parsed = tuple(EvidenceQuoteRef.from_mapping(value) for value in refs)
    if len({item.evidence_ref_id for item in parsed}) != len(parsed):
        raise ValueError("Evidence ref IDs must be unique")
    return tuple(_resolve_quote(ref, capture_map) for ref in parsed)


def _resolve_quote(ref: EvidenceQuoteRef, captures: dict[str, dict[str, object]]) -> ExactEvidenceSpan:
    try:
        capture = captures[ref.capture_id]
    except KeyError as exc:
        raise ValueError("Evidence quote names an unavailable Capture") from exc
    if capture["kind"] == "tool" and ref.role != "tool":
        raise ValueError("Tool Evidence quote has the wrong role")
    if capture["kind"] == "capture" and ref.role == "tool":
        raise ValueError("Capture quote has the wrong role")
    content = capture["content"] if ref.role == "tool" else capture["content"][f"{ref.role}_utf8"]
    starts: list[int] = []
    cursor = 0
    while True:
        found = content.find(ref.quote_utf8, cursor)
        if found < 0:
            break
        starts.append(found)
        cursor = found + 1
    if ref.left_context_utf8 is not None:
        starts = [start for start in starts if content[:start].endswith(ref.left_context_utf8)]
    if ref.right_context_utf8 is not None:
        starts = [start for start in starts if content[start + len(ref.quote_utf8):].startswith(ref.right_context_utf8)]
    if not starts:
        raise ValueError("evidence_quote_not_found")
    if ref.occurrence_hint is not None:
        if ref.occurrence_hint >= len(starts):
            raise ValueError("evidence_quote_occurrence_unavailable")
        starts = [starts[ref.occurrence_hint]]
    if len(starts) != 1:
        raise ValueError("evidence_quote_ambiguous")
    start = starts[0]
    end = start + len(ref.quote_utf8)
    return ExactEvidenceSpan(
        ref.evidence_ref_id,
        ref.capture_id,
        ref.role,
        start,
        end,
        ref.quote_utf8,
        sha256(ref.quote_utf8.encode("utf-8")).hexdigest(),
        sha256(_canonical(capture["raw"])).hexdigest(),
    )
