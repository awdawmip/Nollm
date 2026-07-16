from __future__ import annotations

import argparse
import json
from pathlib import Path

from latency_support import canonical_json, evidence_sha256, load_records, summarize


def _metric(value: object) -> str:
    if type(value) is not dict or value.get("status") != "observed":
        return "insufficient sample"
    keys = ["n", "min_ms", "median_ms", "p50_ms", "p90_ms", "p95_ms", "max_ms"]
    return ", ".join(f"{key}={value[key]}" for key in keys if key in value)


def render_report(summary: dict[str, object], evidence: Path) -> str:
    write = summary["write_latency"]
    recall = summary["recall_latency"]
    return f"""# AOLD Real Memory Commit And Recall Latency Baseline Report

Status: `AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

This report measures the existing layer-0 memory loop. It does not establish a permanent SLA and does not authorize optimization.

## Evidence

- Evidence: `{evidence.as_posix()}`
- Records: {summary['record_count']}
- SHA-256: `{summary['evidence_sha256']}`
- Write turns: {summary['write_turn_count']}
- Durable-memory turns: {summary['durable_memory_turn_count']}
- Recall queries: {summary['recall_query_count']}
- Visible-answer correlations: {summary['visible_answer_correlated_count']}
- NONE recalls: {summary['none_recall_count']}

## Commit Latency

- Turn to first durable: {_metric(write['turn_to_first_durable'])}
- Turn to all durable: {_metric(write['turn_to_all_durable'])}

## Recall Latency

- Query to injection ready: {_metric(recall['query_to_injection_ready'])}
- Query to visible answer: {_metric(recall['query_to_visible_answer'])}
- Query to NONE terminal: {_metric(recall['query_to_none_terminal'])}

## Limits

Provider, cold/warm, dense hidden-preview, multi-Statement, revision, reuse, defer, and NONE cohorts remain `insufficient sample` unless the frozen Evidence contains the required independent Live samples. Formation output is not durable memory, injection readiness is not a visible answer, and unmatched run IDs are never inferred.

No optimization was performed in this task. Candidate optimization priority must be derived from the final observed Provider/local/main-agent shares rather than assumed here.
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    records = load_records(args.evidence)
    summary = summarize(records)
    summary["evidence_sha256"] = evidence_sha256(args.evidence)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(canonical_json(summary), encoding="utf-8", newline="\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary, args.evidence), encoding="utf-8", newline="\n")
    print(json.dumps({"status": "pass", "records": len(records), "summary": str(args.summary), "report": str(args.report)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
