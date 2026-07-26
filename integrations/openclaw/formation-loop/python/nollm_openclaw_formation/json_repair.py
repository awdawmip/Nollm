from __future__ import annotations

import hashlib
import json
import re


def repair_json_envelope(raw: str) -> tuple[str, dict[str, object]]:
    """Apply only format-level repairs and preserve every JSON string token."""
    if type(raw) is not str:
        raise json.JSONDecodeError("response must be text", "", 0)
    before_sha256 = hashlib.sha256(raw.encode("utf-8")).hexdigest()
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
        "after_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "string_values_unchanged": True,
        "fields_added": False,
        "fields_removed": False,
    }


def _unfence_single_json(text: str) -> str:
    lines = text.splitlines()
    if (
        len(lines) < 3
        or not re.fullmatch(r"```(?:json)?[ \t]*", lines[0], re.IGNORECASE)
        or lines[-1].strip() != "```"
    ):
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
