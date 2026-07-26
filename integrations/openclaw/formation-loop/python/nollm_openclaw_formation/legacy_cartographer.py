from __future__ import annotations

import json

from .cartographer import (
    LEGACY_CONTEXTUAL_PROPOSITION_WRITER_SCHEMA_VERSION,
    LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION,
    _legacy_proposition,
)
from .errors import FormationAdapterError
from .json_repair import repair_json_envelope
from .writer_inputs import captures as _captures


def migrate_legacy_proposition_writer_result(
    raw_response: object,
    captures: object,
    request_id: object,
) -> dict[str, object]:
    """Convert historical Writer output only for explicit offline migration."""
    clean = _captures(captures)
    if type(raw_response) is not str or type(request_id) is not str or not request_id:
        raise FormationAdapterError(
            "invalid_writer_result", "Writer response and request_id are required"
        )
    try:
        repaired, diagnostics = repair_json_envelope(raw_response)
        value = json.loads(repaired)
    except json.JSONDecodeError as exc:
        raise FormationAdapterError("invalid_json", str(exc)) from exc
    if (
        type(value) is dict
        and value.get("schema_version")
        == LEGACY_CONTEXTUAL_PROPOSITION_WRITER_SCHEMA_VERSION
        and set(value) == {"schema_version", "outcome", "propositions", "defer_reason"}
        and value.get("outcome") in {"no_memory", "defer"}
    ):
        if value["propositions"] != [] or type(value["defer_reason"]) is not str or not value["defer_reason"]:
            raise FormationAdapterError(
                "invalid_writer_schema", "legacy terminal Writer outcome is invalid"
            )
        return {
            "outcome": "zero_new_propositions" if value["outcome"] == "no_memory" else "retryable_defer",
            "propositions": [],
            "reason_text": value["defer_reason"],
            "continuation": None,
            "migrated_from_version": LEGACY_CONTEXTUAL_PROPOSITION_WRITER_SCHEMA_VERSION,
            "legacy_outcome": value["outcome"],
            "provenance_precision": "legacy",
            "json_repair": diagnostics,
        }
    if (
        type(value) is not dict
        or value.get("schema_version") != LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION
        or value.get("outcome") != "plan"
        or type(value.get("propositions")) is not list
    ):
        raise FormationAdapterError(
            "invalid_writer_schema",
            "explicit migration requires legacy Writer v1 plan or v3 terminal result",
        )
    source_map = {item["capture_id"]: item for item in clean}
    propositions = [_legacy_proposition(item, source_map, source_map) for item in value["propositions"]]
    return {
        "outcome": "plan",
        "propositions": propositions,
        "defer_reason": None,
        "migrated_from_version": LEGACY_PROPOSITION_WRITER_SCHEMA_VERSION,
        "provenance_precision": "coarse",
        "json_repair": diagnostics,
    }
