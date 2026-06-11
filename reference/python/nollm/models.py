from __future__ import annotations

CARD_TYPES = {
    "fact",
    "decision",
    "definition",
    "constraint",
    "preference",
    "warning",
    "failure",
    "procedure",
    "question",
    "hypothesis",
    "evidence",
    "note",
}

CARD_DIRS = {
    "fact": "facts",
    "decision": "decisions",
    "definition": "definitions",
    "constraint": "constraints",
    "preference": "preferences",
    "warning": "warnings",
    "failure": "failures",
    "procedure": "procedures",
    "question": "questions",
    "hypothesis": "hypotheses",
    "evidence": "evidence",
    "note": "notes",
}

STATUSES = {"draft", "candidate", "confirmed", "superseded", "rejected", "archived"}
WRITE_STATUSES = {"draft", "candidate"}

TRUST_VALUES = {
    "human-approved",
    "source-backed",
    "llm-proposed",
    "unverified",
    "conflicted",
}

SOURCE_KINDS = {
    "user_statement",
    "human_decision",
    "project_file",
    "ledger_event",
    "external_reference",
    "llm_inference",
}

RECALL_KEYS = [
    "query_or_task",
    "memory_intent",
    "anchors_used",
    "cards_read",
    "recalled_points",
    "warnings",
    "do_not_assume",
    "source_addresses",
    "open_questions",
]

