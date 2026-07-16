from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from latency_support import COMMIT_SCHEMA, RECALL_SCHEMA, canonical_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--mode", choices=("write", "recall"), required=True)
    parser.add_argument("--receipt", type=Path, action="append", required=True)
    args = parser.parse_args()
    schema = COMMIT_SCHEMA if args.mode == "write" else RECALL_SCHEMA
    existing = set()
    if args.evidence.exists():
        for line in args.evidence.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record.get("event_type") == "host_turn_receipt":
                existing.add((record.get("schema_version"), record.get("session_key_sha256")))
    appended = 0
    with args.evidence.open("a", encoding="utf-8", newline="\n") as stream:
        for receipt_path in args.receipt:
            for line in receipt_path.read_text(encoding="utf-8").splitlines():
                receipt = json.loads(line)
                session_id = receipt["session_id"]
                session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
                identity = (schema, session_hash)
                if identity in existing:
                    continue
                if receipt.get("exit_code") != 0:
                    raise ValueError("only successful Host turn receipts may be imported")
                record = {
                    "schema_version": schema,
                    "event_epoch_ms": receipt["returned_epoch_ms"],
                    "scenario_id": receipt["scenario_id"],
                    "validation_run_id": "aold-latency-20260716",
                    "event_type": "host_turn_receipt",
                    "session_key_sha256": session_hash,
                    "host_exit_code": receipt["exit_code"],
                    "host_started_epoch_ms": receipt["started_epoch_ms"],
                    "host_returned_epoch_ms": receipt["returned_epoch_ms"],
                    "host_command_duration_ms": receipt["returned_epoch_ms"] - receipt["started_epoch_ms"],
                    "stdout_bytes": receipt["stdout_bytes"],
                    "stderr_bytes": receipt["stderr_bytes"],
                }
                stream.write(canonical_json(record))
                existing.add(identity)
                appended += 1
    print(json.dumps({"status": "pass", "mode": args.mode, "appended": appended}, separators=(",", ":")))


if __name__ == "__main__":
    main()
