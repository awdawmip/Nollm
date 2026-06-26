from __future__ import annotations

import re
import unicodedata
from typing import Any

CJK_STOP_CHARS = {
    "的", "是", "我", "你", "他", "她", "它", "这", "那", "什", "么", "怎",
    "请", "记", "忆", "一", "下", "吗", "呢", "了", "在", "和", "或", "与",
    "就", "都", "不", "有", "没", "为", "对", "给", "说", "问", "查", "询",
    "回", "忆", "用", "把", "被", "让", "向", "到", "从", "上", "下", "中",
    "里", "外", "前", "后", "会", "能", "可", "要", "想", "看", "听", "来",
    "去", "过", "也", "很", "最", "更", "太", "还", "只", "又", "再", "但",
    "而", "因", "所", "如", "果", "虽", "然", "个", "条", "次", "种",
}

IDENTITY_QUERY_ALIASES = ["我叫什么", "我的名字", "我是谁", "我姓名", "我叫", "名字是什么", "我名字", "姓名"]
PREFERENCE_QUERY_ALIASES = ["我偏好什么", "我喜欢怎样回答", "我偏好", "我的偏好", "我喜欢什么", "偏好", "喜欢"]
PROJECT_DECISION_QUERY_ALIASES = ["项目", "发版", "发布", "决策", "release", "launch", "decision", "project"]

FACET_MARKERS: dict[str, list[str]] = {
    "identity_name": ["叫", "名字", "姓名", "name"],
    "identity_code": ["身份代号", "用户代号", "identity code"],
    "preference_color_or_label": ["标签", "颜色", "色彩", "color", "label"],
    "preference_response_style": ["回答", "简洁", "详细", "长", "短", "风格", "style"],
    "project_release": ["发版", "发布", "上线", "release", "launch"],
    "project_decision": ["决定", "决策", "会议", "开会", "decision"],
    "generic_test_code": ["测试代号", "测试码", "marker", "code", "identifier"],
}

GENERIC_CJK_TOKENS = {"代号", "项目", "偏好", "测试"}
GENERIC_LATIN_RE = re.compile(r"^(?:\d+|w\d+|t\d+)$", re.IGNORECASE)
BROAD_MARKERS = ["哪些", "有什么", "都有什么", "全部", "所有", "一切", "列举", "列表"]


def _normalize_recall_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    normalized_chars = []
    for char in text:
        cat = unicodedata.category(char)
        if cat.startswith("L") or cat.startswith("N") or char.isspace():
            normalized_chars.append(char)
        else:
            normalized_chars.append(" ")
    return " ".join("".join(normalized_chars).split())


def _latin_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _cjk_ngrams(text: str) -> set[str]:
    normalized = _normalize_recall_text(text)
    # Drop generic tokens so cross-token bigrams (e.g. "试代") are not created.
    for token in sorted(GENERIC_CJK_TOKENS, key=len, reverse=True):
        normalized = normalized.replace(token, " ")
    chars = [c for c in normalized if not c.isascii() and not c.isspace()]
    ngrams: set[str] = set()
    for i in range(len(chars) - 1):
        ngrams.add(chars[i] + chars[i + 1])
    return ngrams


def _is_stop_ngram(ngram: str) -> bool:
    return all(char in CJK_STOP_CHARS for char in ngram)


def analyze_facets(text: str) -> set[str]:
    """Return the deterministic facets present in *text*."""
    norm = _normalize_recall_text(text)
    facets: set[str] = set()
    for facet, markers in FACET_MARKERS.items():
        if any(marker in norm for marker in markers):
            facets.add(facet)
    return facets


def is_generic_latin_token(token: str) -> bool:
    return bool(GENERIC_LATIN_RE.match(token))


def is_generic_cjk_ngram(ngram: str) -> bool:
    return ngram in GENERIC_CJK_TOKENS


def _query_intents(query: str) -> set[str]:
    normalized = _normalize_recall_text(query)
    intents: set[str] = set()
    if any(alias in normalized for alias in IDENTITY_QUERY_ALIASES):
        intents.add("identity")
    if any(alias in normalized for alias in PREFERENCE_QUERY_ALIASES):
        intents.add("preference")
    if any(alias in normalized for alias in PROJECT_DECISION_QUERY_ALIASES):
        intents.add("project_decision")
    return intents


def _kind_intent_match(kind: str, intents: set[str]) -> bool:
    if "identity" in intents and kind == "identity":
        return True
    if "preference" in intents and kind == "preference":
        return True
    if "project_decision" in intents and kind in {"project", "decision"}:
        return True
    return False


def classify_query(query: str, query_facets: set[str]) -> str:
    """Classify a recall query as 'broad' or 'specific'."""
    normalized = _normalize_recall_text(query)
    if any(marker in normalized for marker in BROAD_MARKERS):
        return "broad"
    if not query_facets:
        return "broad"
    return "specific"


def _discriminative_latin_overlap(query_tokens: set[str], record_text: str) -> set[str]:
    record_tokens = _latin_tokens(record_text)
    return {token for token in (query_tokens & record_tokens) if not is_generic_latin_token(token)}


def _discriminative_cjk_overlap(query_ngrams: set[str], record_text: str) -> set[str]:
    record_ngrams = _cjk_ngrams(record_text)
    overlap = query_ngrams & record_ngrams
    return {ngram for ngram in overlap if not _is_stop_ngram(ngram) and not is_generic_cjk_ngram(ngram)}


def _evaluate_record(
    query_analysis: dict[str, Any],
    record: dict[str, Any],
    is_broad: bool,
    unique_test_code: bool,
) -> dict[str, Any] | None:
    query_text = query_analysis["normalized_text"]
    record_text = _normalize_recall_text(record.get("text", ""))
    query_facets = query_analysis["facets"]
    record_facets = analyze_facets(record_text)

    exact_substring = bool(query_text and (query_text in record_text or record_text in query_text))
    latin_overlap = _discriminative_latin_overlap(query_analysis["latin_tokens"], record_text)
    cjk_overlap = _discriminative_cjk_overlap(query_analysis["cjk_ngrams"], record_text)

    shared_facets = query_facets & record_facets
    has_test_code_facet = "generic_test_code" in shared_facets
    non_generic_shared_facets = shared_facets - {"generic_test_code"}
    exact_facet_match = bool(non_generic_shared_facets)

    kind = record.get("kind", "")
    kind_intent_match = _kind_intent_match(kind, query_analysis["intents"])

    has_evidence = exact_substring or bool(latin_overlap) or bool(cjk_overlap) or exact_facet_match

    admitted = False
    mode = ""
    generic_test_code_admitted = False
    matched_terms: list[str] = []
    matched_facets: list[str] = []

    if exact_substring:
        matched_terms.append(query_text if len(query_text) <= len(record_text) else record_text)
    matched_terms.extend(sorted(latin_overlap))
    matched_terms.extend(sorted(cjk_overlap)[:4])
    if exact_facet_match:
        matched_facets.extend(sorted(non_generic_shared_facets))
        matched_terms.extend(f"facet={f}" for f in sorted(non_generic_shared_facets))
    if has_test_code_facet:
        matched_facets.append("generic_test_code")
        matched_terms.append("test_code_marker")

    if is_broad:
        if has_evidence:
            admitted = True
            mode = "exact" if exact_substring else ("facet" if exact_facet_match else "lexical")
        elif kind_intent_match:
            admitted = True
            mode = "broad_collection"
            matched_terms.append(f"kind={kind}")
        elif has_test_code_facet and unique_test_code:
            admitted = True
            mode = "broad_collection"
            generic_test_code_admitted = True
    else:
        if has_evidence:
            admitted = True
            mode = "exact" if exact_substring else ("facet" if exact_facet_match else "lexical")
        elif has_test_code_facet and unique_test_code:
            admitted = True
            mode = "facet"
            generic_test_code_admitted = True

    if not admitted:
        return None

    score = (
        1 if exact_substring else 0,
        1 if exact_facet_match else 0,
        len(latin_overlap),
        len(cjk_overlap),
        1 if kind_intent_match else 0,
        record.get("created_at", ""),
        record.get("memory_id", ""),
    )

    return {
        "mode": mode,
        "matched_terms": matched_terms[:8],
        "matched_facets": matched_facets,
        "score": score,
        "generic_test_code_admitted": generic_test_code_admitted,
    }


def build_query_analysis(query: str) -> dict[str, Any]:
    return {
        "normalized_text": _normalize_recall_text(query),
        "latin_tokens": _latin_tokens(query),
        "cjk_ngrams": _cjk_ngrams(query),
        "facets": analyze_facets(query),
        "intents": _query_intents(query),
    }


def rank_candidates(
    query: str, records: list[dict[str, Any]]
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], dict[str, Any] | None]:
    """
    Score and rank *records* against *query*.
    Returns (scored_records, ambiguity_info_or_None).
    """
    query_analysis = build_query_analysis(query)
    query_facets = query_analysis["facets"]
    is_broad = classify_query(query, query_facets) == "broad"

    test_code_records = [
        r for r in records if "generic_test_code" in analyze_facets(_normalize_recall_text(r.get("text", "")))
    ]
    unique_test_code = len(test_code_records) == 1
    ambiguous_test_code = len(test_code_records) > 1 and "generic_test_code" in query_facets

    scored: list[tuple[dict[str, Any], dict[str, Any]]] = []
    any_generic_test_code_admitted = False
    for record in records:
        match = _evaluate_record(query_analysis, record, is_broad, unique_test_code)
        if match is None:
            continue
        scored.append((record, match))
        if match.get("generic_test_code_admitted"):
            any_generic_test_code_admitted = True

    ambiguity: dict[str, Any] | None = None
    if ambiguous_test_code and not any_generic_test_code_admitted and not scored:
        ambiguity = {"code": "native_memory_query_ambiguous", "candidate_count": len(test_code_records)}

    scored.sort(key=lambda item: item[1]["score"], reverse=True)
    return scored, ambiguity
