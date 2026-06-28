from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


OPERATION_ID_RE = re.compile(r"^w2-05-[0-9]{8}T[0-9]{6}Z-[a-f0-9]{12}$")
TRIAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
TURN_RECEIPT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{31,127}$")

FORBIDDEN_STATES = {
    "planned",
    "prepared",
    "runtime_asserted",
    "trial_running",
    "succeeded",
    "failed_quarantined",
    "diagnostics_collected",
    "manual_repair_required",
    "human_resolved_repaired",
    "human_resolved_discarded",
    "blocked_pre_mutation",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_segment(value: str, pattern: re.Pattern[str], name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    if value != unicodedata.normalize("NFKC", value):
        raise ValueError(f"{name} contains non-canonical unicode")
    if value.strip() != value or not value:
        raise ValueError(f"{name} must not be empty or padded")
    if value in {".", ".."}:
        raise ValueError(f"{name} must not be a dot segment")
    if any(ch in value for ch in ("/", "\\", "\x00")):
        raise ValueError(f"{name} must not contain path separators or NUL")
    if any(ord(ch) < 32 or ord(ch) == 127 or ch.isspace() for ch in value):
        raise ValueError(f"{name} must not contain control characters or whitespace")
    if not pattern.fullmatch(value):
        raise ValueError(f"{name} has invalid format")
    return value


def validate_operation_id(value: str) -> str:
    return validate_segment(value, OPERATION_ID_RE, "operation_id")


def validate_trial_id(value: str) -> str:
    return validate_segment(value, TRIAL_ID_RE, "trial_id")


def validate_turn_receipt_id(value: str) -> str:
    return validate_segment(value, TURN_RECEIPT_ID_RE, "turn_receipt_id")


def safe_join_under_root(approved_root: Path | str, child: str) -> Path:
    child = validate_segment(child, re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,255}$"), "child")
    root = Path(approved_root).resolve(strict=True)
    candidate = (root / child).resolve(strict=False)
    if candidate == root or root not in candidate.parents:
        raise ValueError("candidate path escapes approved root")
    return candidate


def new_operation_id() -> str:
    suffix = hashlib.sha256(os.urandom(32)).hexdigest()[:12]
    return f"w2-05-{stamp()}-{suffix}"


def operation_root(out_root: Path | str, operation_id: str) -> Path:
    validate_operation_id(operation_id)
    root = Path(out_root).resolve()
    operations = root / "operations"
    operations.mkdir(parents=True, exist_ok=True)
    return safe_join_under_root(operations, operation_id)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def append_ledger(op_root: Path, state: str, reason: str, details: dict[str, Any] | None = None) -> None:
    if state not in FORBIDDEN_STATES:
        raise ValueError(f"unknown W2-05 state: {state}")
    record = {
        "schema": "nollm.w2_05.operation_ledger_event.v1",
        "timestamp": now_iso(),
        "state": state,
        "reason": reason,
        "details": details or {},
    }
    with (op_root / "operation-ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def create_operation(out_root: Path | str, operation_id: str | None, binding: dict[str, Any]) -> dict[str, Any]:
    op_id = validate_operation_id(operation_id) if operation_id else new_operation_id()
    op_root = operation_root(out_root, op_id)
    if op_root.exists():
        raise ValueError(f"operation already exists: {op_id}")
    for subdir in (
        "private/openclaw",
        "private/workspace",
        "private/native-store",
        "private/active-trials",
        "private/provider",
        "logs",
        "receipts",
        "diagnostics/sanitized",
    ):
        (op_root / subdir).mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema": "nollm.w2_05.operation_manifest.v1",
        "operation_id": op_id,
        "created_at": now_iso(),
        "state": "planned",
        "binding": binding,
        "isolation": {
            "config": "operation-private",
            "workspace": "operation-private",
            "native_store": "operation-private",
            "active_trials": "operation-private",
            "provider_payload": "operation-private",
            "logs_receipts_diagnostics": "operation-private",
            "shared_mutation_allowed": False,
        },
    }
    write_json(op_root / "operation.json", manifest)
    append_ledger(op_root, "planned", "operation_created")
    return {"operation_id": op_id, "operation_root": str(op_root), "manifest": manifest}


def set_operation_state(op_root: Path, state: str, reason: str, details: dict[str, Any] | None = None) -> None:
    manifest_path = op_root / "operation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["state"] = state
    manifest["updated_at"] = now_iso()
    manifest["state_reason"] = reason
    write_json(manifest_path, manifest)
    append_ledger(op_root, state, reason, details)


def quarantine_operation(op_root: Path, reason: str, details: dict[str, Any] | None = None) -> None:
    (op_root / "QUARANTINED").write_text(reason + "\n", encoding="utf-8")
    write_json(op_root / "diagnostics" / "sanitized" / "manual-repair-handoff.json", {
        "schema": "nollm.w2_05.manual_repair_handoff.v1",
        "created_at": now_iso(),
        "reason": reason,
        "details": details or {},
        "automatic_retry_or_repair": False,
    })
    set_operation_state(op_root, "failed_quarantined", reason, details)
    set_operation_state(op_root, "diagnostics_collected", "sanitized_diagnostics_available", {})
    set_operation_state(op_root, "manual_repair_required", "human_resolution_required", {})
