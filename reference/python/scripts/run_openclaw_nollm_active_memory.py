from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from nollm.openclaw_active_memory_adapter import (
    ACTIVE_STATUS_SCHEMA,
    ACTIVE_PREPARE_INPUT_SCHEMA,
    ACTIVE_CAPTURE_SCHEMA,
    ACTIVE_TRIAL_REPORT_SCHEMA,
    active_capture,
    active_prepare,
    active_status,
    active_trial_report,
)


def _fail(code: str, message: str) -> dict[str, object]:
    return {
        "ok": False,
        "schema": "nollm.active_memory_error.v1",
        "error": {"code": code, "message": message, "retryable": False},
    }


def _identity_from_command(command: dict[str, Any]) -> dict[str, str]:
    """Build a deterministic identity dict from top-level hook fields."""
    raw = command.get("identity") or {}
    return {
        "agent_id": str(command.get("agent_id", raw.get("agent_id", ""))),
        "session_id": str(command.get("session_id", raw.get("session_id", ""))),
        "run_id": str(command.get("run_id", raw.get("run_id", ""))),
    }


def _print_json(data: dict[str, object]) -> None:
    """Write JSON to stdout as UTF-8 bytes.

    On Windows the console encoding is often GBK/cp936, which mangles or
    surrogates-valid UTF-8 coming from the Node.js host. Writing bytes
    directly keeps the JSON contract stable across transports.
    """
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Nollm active memory sidecar for OpenClaw.")
    parser.add_argument("--repo-root", default="../..")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--native-store-root", required=True)
    parser.add_argument("--trial-root", default=None)
    parser.add_argument("--config-json", default=None)
    args = parser.parse_args(argv)

    config: dict[str, object] = {}
    if args.config_json:
        try:
            config = json.loads(args.config_json)
        except json.JSONDecodeError as exc:
            _print_json(_fail("configuration_error", f"Invalid --config-json: {exc}"))
            return 2

    native_store_root = Path(args.native_store_root).resolve()
    trial_root = Path(args.trial_root).resolve() if args.trial_root else None

    # Read raw bytes and decode as UTF-8 explicitly. The Node.js host sends
    # UTF-8, but Windows Python defaults to the console code page (often GBK),
    # which would decode valid UTF-8 as garbage and produce surrogates.
    stdin_text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    if not stdin_text.strip():
        _print_json(_fail("invalid_command", "No JSON command on stdin."))
        return 2
    try:
        command = json.loads(stdin_text)
    except json.JSONDecodeError as exc:
        _print_json(_fail("invalid_command", f"stdin is not valid JSON: {exc}"))
        return 2

    if not isinstance(command, dict):
        _print_json(_fail("invalid_command", "stdin must be a JSON object."))
        return 2

    cmd = command.get("command")
    schema = command.get("schema", "")
    identity = _identity_from_command(command)
    trial_id = command.get("trial_id")

    result: dict[str, object]
    if cmd == "active-status":
        if schema != ACTIVE_STATUS_SCHEMA:
            result = _fail("schema_mismatch", f"Expected {ACTIVE_STATUS_SCHEMA}, got {schema}")
        else:
            result = active_status(native_store_root)
    elif cmd == "active-prepare":
        if schema != ACTIVE_PREPARE_INPUT_SCHEMA:
            result = _fail("schema_mismatch", f"Expected {ACTIVE_PREPARE_INPUT_SCHEMA}, got {schema}")
        else:
            query = command.get("query", "")
            budget = command.get("budget") or {}
            if not isinstance(budget, dict):
                budget = {}
            result = active_prepare(
                native_store_root,
                query,
                budget,
                trial_id=trial_id,
                identity=identity,
                trial_root=trial_root,
            )
    elif cmd == "active-capture":
        if schema != ACTIVE_CAPTURE_SCHEMA:
            result = _fail("schema_mismatch", f"Expected {ACTIVE_CAPTURE_SCHEMA}, got {schema}")
        else:
            messages = command.get("messages")
            success = command.get("success")
            if not isinstance(messages, list):
                result = _fail("invalid_event", "messages must be an array.")
                _print_json(result)
                return 1
            if not isinstance(success, bool):
                result = _fail("invalid_event", "success must be a boolean.")
                _print_json(result)
                return 1
            result = active_capture(
                native_store_root,
                messages,
                success,
                trial_id=trial_id,
                identity=identity,
                trial_root=trial_root,
            )
    elif cmd == "active-trial-report":
        if schema != ACTIVE_TRIAL_REPORT_SCHEMA:
            result = _fail("schema_mismatch", f"Expected {ACTIVE_TRIAL_REPORT_SCHEMA}, got {schema}")
        else:
            tid = command.get("trial_id") or trial_id
            if not tid:
                result = _fail("invalid_command", "trial_id required for active-trial-report")
            else:
                result = active_trial_report(native_store_root, str(tid), trial_root=trial_root)
    else:
        result = _fail("invalid_command", f"Unknown command: {cmd}")

    _print_json(result)
    return 0 if result.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
