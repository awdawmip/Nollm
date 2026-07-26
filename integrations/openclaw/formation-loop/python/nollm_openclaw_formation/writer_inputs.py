from __future__ import annotations

from pathlib import Path

from .errors import FormationAdapterError


def workspace(value: object) -> Path:
    if type(value) is not str or not value:
        raise FormationAdapterError("invalid_workspace", "memory workspace is required")
    return Path(value)


def captures(value: object) -> list[dict[str, object]]:
    base = {
        "capture_id",
        "user_utf8",
        "assistant_utf8",
        "captured_epoch_ms",
        "timezone_offset_minutes",
    }
    legacy_directive = {
        "user_role_mode",
        "assistant_role_mode",
        "memory_tool_actions",
        "recalled_statement_ids",
    }
    origin = {
        "assistant_origin_kind",
        "memory_tool_actions",
        "recalled_statement_ids",
    }
    if type(value) is not list or not value or len(value) > 16:
        raise FormationAdapterError(
            "invalid_writer_captures", "Captures must be a bounded non-empty list"
        )
    clean = []
    for item in value:
        if (
            type(item) is not dict
            or frozenset(item)
            not in {frozenset(base), frozenset(base | legacy_directive), frozenset(base | origin)}
            or type(item["capture_id"]) is not str
            or not item["capture_id"]
            or type(item["user_utf8"]) is not str
            or type(item["assistant_utf8"]) is not str
            or type(item["captured_epoch_ms"]) is not int
            or type(item["timezone_offset_minutes"]) is not int
            or not -840 <= item["timezone_offset_minutes"] <= 840
        ):
            raise FormationAdapterError(
                "invalid_writer_captures", "Capture fields are invalid"
            )
        if legacy_directive <= set(item):
            if item["user_role_mode"] != "source" or item["assistant_role_mode"] not in {
                "source",
                "context_only",
                "memory_derived",
            }:
                raise FormationAdapterError(
                    "invalid_writer_captures", "Capture role modes are invalid"
                )
        if origin <= set(item) and item["assistant_origin_kind"] not in {
            "assistant",
            "model_inference",
            "recalled_memory",
            "tool",
        }:
            raise FormationAdapterError(
                "invalid_writer_captures", "Capture assistant origin is invalid"
            )
        if legacy_directive <= set(item) or origin <= set(item):
            actions = item["memory_tool_actions"]
            recalled = item["recalled_statement_ids"]
            if (
                type(actions) is not list
                or actions != sorted(set(actions))
                or any(
                    action not in {"surface", "open_region", "recall", "expand", "none"}
                    for action in actions
                )
            ):
                raise FormationAdapterError(
                    "invalid_writer_captures", "Capture memory actions are invalid"
                )
            if (
                type(recalled) is not list
                or recalled != sorted(set(recalled))
                or any(type(statement_id) is not str or not statement_id for statement_id in recalled)
            ):
                raise FormationAdapterError(
                    "invalid_writer_captures", "Capture recalled Statement IDs are invalid"
                )
        clean.append(item)
    ids = [item["capture_id"] for item in clean]
    if ids != sorted(ids) and len(ids) > 1:
        clean = sorted(clean, key=lambda item: item["capture_id"])
        ids = [item["capture_id"] for item in clean]
    if len(ids) != len(set(ids)):
        raise FormationAdapterError(
            "invalid_writer_captures", "Capture IDs must be unique"
        )
    return clean
