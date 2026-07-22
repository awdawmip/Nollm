import pytest

from nollm_access import resolve_evidence_quote_refs


def capture(user: str, assistant: str = "") -> dict[str, object]:
    return {
        "capture_id": "capture-one",
        "user_utf8": user,
        "assistant_utf8": assistant,
        "captured_epoch_ms": 1,
        "timezone_offset_minutes": 480,
    }


def ref(quote: str, **extra: object) -> dict[str, object]:
    return {"evidence_ref_id": "e1", "capture_id": "capture-one", "role": "user", "quote_utf8": quote, **extra}


@pytest.mark.parametrize("text,quote", [
    ("中文证据", "中文"),
    ("東京の天気", "東京"),
    ("English evidence", "evidence"),
    ("status 🙂 ready", "🙂"),
    ("line one\nline two", "one\nline"),
])
def test_quote_resolver_uses_exact_python_codepoint_offsets(text, quote):
    span = resolve_evidence_quote_refs([ref(quote)], [capture(text)])[0]
    assert text[span.start:span.end] == quote
    assert len(span.quote_sha256) == len(span.capture_sha256) == 64


def test_repeated_quote_requires_occurrence_or_exact_context():
    value = capture("left repeat middle repeat right")
    with pytest.raises(ValueError, match="evidence_quote_ambiguous"):
        resolve_evidence_quote_refs([ref("repeat")], [value])
    second = resolve_evidence_quote_refs([ref("repeat", occurrence_hint=1)], [value])[0]
    assert second.start == value["user_utf8"].rindex("repeat")
    first = resolve_evidence_quote_refs([ref("repeat", left_context_utf8="left ", right_context_utf8=" middle")], [value])[0]
    assert first.start == value["user_utf8"].index("repeat")


def test_same_quote_across_roles_is_role_bound():
    value = capture("same", "same")
    refs = [ref("same"), {"evidence_ref_id": "e2", "capture_id": "capture-one", "role": "assistant", "quote_utf8": "same"}]
    spans = resolve_evidence_quote_refs(refs, [value])
    assert [item.role for item in spans] == ["user", "assistant"]


def test_quote_resolver_rejects_empty_missing_ambiguous_normalized_and_duplicate_refs():
    value = capture("caf\u00e9 repeated repeated")
    with pytest.raises(TypeError, match="quote_utf8"):
        resolve_evidence_quote_refs([ref("")], [value])
    with pytest.raises(ValueError, match="not_found"):
        resolve_evidence_quote_refs([ref("missing")], [value])
    with pytest.raises(ValueError, match="not_found"):
        resolve_evidence_quote_refs([ref("cafe\u0301")], [value])
    with pytest.raises(ValueError, match="unique"):
        resolve_evidence_quote_refs([ref("caf\u00e9"), ref("caf\u00e9")], [value])


def test_quote_resolver_handles_long_capture_without_normalization():
    text = "x" * 100_000 + " exact tail "
    span = resolve_evidence_quote_refs([ref(" exact tail ")], [capture(text)])[0]
    assert span.start == 100_000
    assert span.end == len(text)
