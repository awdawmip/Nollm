from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_PATH = "validation/aold_contextual_relational_growth_20260721.jsonl"
SUMMARY_PATH = "validation/aold_contextual_relational_growth_summary_20260721.json"


def _git_blob(revision: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout


def verify_payloads(evidence_bytes: bytes, summary_bytes: bytes) -> dict[str, object]:
    if not evidence_bytes.endswith(b"\n") or len(evidence_bytes.splitlines()) != 1:
        raise ValueError("contextual growth Evidence must be one newline-terminated JSONL record")
    record = json.loads(evidence_bytes)
    summary = json.loads(summary_bytes)
    canonical_evidence = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    canonical_summary = json.dumps(
        summary, ensure_ascii=False, indent=2, sort_keys=True,
    ).encode("utf-8") + b"\n"
    checks = {
        "evidence_canonical": evidence_bytes == canonical_evidence,
        "summary_canonical": summary_bytes == canonical_summary,
        "schema_current": (
            record.get("schema_version") == "nollm_v311r4_contextual_live_validation_v1"
            and summary.get("schema_version") == "nollm_v311r4_contextual_live_summary_v1"
        ),
        "completion_bound": (
            summary.get("validated_revision") == "75383c6f3cc0358d8dcc430cd09c02252edb947b"
            and summary.get("completion_status") == "CONTEXTUAL_WRITER_SHARED_RETRIEVAL_GROWTH_VALIDATED"
        ),
        "evidence_hash_bound": summary.get("evidence_sha256") == sha256(evidence_bytes).hexdigest(),
        "evidence_size_bound": summary.get("evidence_utf8_bytes") == len(evidence_bytes),
        "checks_identical": summary.get("checks") == record.get("checks"),
        "all_gates_passed": (
            record.get("passed") is True
            and summary.get("passed") is True
            and all(value is True for value in record.get("checks", {}).values())
        ),
        "nine_identities": (
            len(record.get("captures", [])) == 9
            and len(record.get("statements", [])) == 9
            and summary.get("capture_count") == 9
            and summary.get("statement_count") == 9
            and summary.get("occupied_cell_count") == 9
            and summary.get("placement_count") == 9
        ),
        "read_zero_write": (
            record.get("state_before_sha256") == record.get("state_after_sha256")
            and summary.get("read_zero_write") is True
        ),
        "controlled_capture_budget": (
            summary.get("capture_sample_count") == 150
            and float(summary.get("capture_p95_ms", float("inf"))) <= 100.0
        ),
        "live_capture_observation_preserved": (
            summary.get("live_capture_observed_sample_count") == 9
            and summary.get("live_capture_observed_p95_ms") == record.get("live_capture_observed_p95_ms")
        ),
    }
    return {
        "schema_version": "nollm_v311r4_contextual_evidence_verifier_v1",
        "evidence_sha256": sha256(evidence_bytes).hexdigest(),
        "evidence_utf8_bytes": len(evidence_bytes),
        "checks": checks,
        "passed": all(checks.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--revision", default="HEAD")
    args = parser.parse_args()
    revision = subprocess.run(
        ["git", "rev-parse", args.revision], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    result = verify_payloads(_git_blob(revision, EVIDENCE_PATH), _git_blob(revision, SUMMARY_PATH))
    result["revision"] = revision
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
