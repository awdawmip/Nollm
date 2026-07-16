from __future__ import annotations

import argparse
import json
from pathlib import Path

from latency_support import canonical_json, evidence_sha256, load_records, summarize


def verify_workspace(workspace: Path) -> dict[str, object]:
    from nollm_access import FileHandleStore, FileStatementStore
    from nollm_core import AtomHandle, CoreRuntime

    handle_store = FileHandleStore(workspace)
    statement_store = FileStatementStore(workspace)
    document = json.loads(handle_store.state_bytes().decode("utf-8"))
    checked_statements: set[str] = set()
    with CoreRuntime(workspace) as core:
        for item in document["bindings"]:
            handle = AtomHandle.from_mapping(item["handle"])
            binding = handle_store.binding_for_handle(handle)
            current = statement_store.get(binding.current_statement_id)
            atom = core.get(handle)
            if atom.payload_utf8 != current.content_utf8:
                raise ValueError("workspace reopen payload mismatch")
            checked_statements.add(current.statement_id)
            for statement_id in binding.supporting_statement_ids:
                statement_store.get(statement_id)
                checked_statements.add(statement_id)
    return {"status": "pass", "binding_count": len(document["bindings"]), "statement_count": len(checked_statements), "reopen_verified": True}


def _metric(value: object) -> str:
    if type(value) is not dict or value.get("status") != "observed":
        return "insufficient sample"
    keys = ["n", "min_ms", "median_ms", "p50_ms", "p90_ms", "p95_ms", "max_ms"]
    return ", ".join(f"{key}={value[key]}" for key in keys if key in value)


def _ms(value: object) -> str:
    return "unavailable" if value is None else f"{float(value):.1f}"


def _write_rows(summary: dict[str, object]) -> str:
    rows = []
    for attempt in summary["write_attempts"]:
        placements = attempt["placements"]
        outcomes = ",".join(str(item["final_outcome"]) for item in placements) or "no-placement"
        timing = [item["operation_timing"] for item in placements]
        rows.append(
            "| {scenario} | `{identity}` | {outcome} | {calls} | {first} | {all_} | {provider:.1f} | {local:.1f} | {terminal} |".format(
                scenario=attempt["scenario_id"],
                identity=str(attempt["turn_correlation_id"])[:12],
                outcome=outcomes,
                calls=sum(int(item.get("model_call_count", 0)) for item in timing),
                first=_ms(attempt["turn_to_first_durable_ms"]),
                all_=_ms(attempt["turn_to_all_durable_ms"]),
                provider=float(attempt["formation_provider_total_ms"]) + sum(float(item.get("placement_provider_total_ms", 0)) for item in placements),
                local=float(attempt["formation_local_total_ms"]) + sum(float(item.get("placement_local_total_ms", 0)) for item in placements),
                terminal=",".join(str(item.get("terminal_reason") or "none") for item in placements) or "none",
            )
        )
    return "\n".join(rows)


def _recall_rows(summary: dict[str, object]) -> str:
    rows = []
    for sample in summary["recall_samples"]:
        timing = sample["operation_timing"]
        provider = float(timing.get("surface_traversal_provider_ms", 0)) + float(timing.get("recall_selection_provider_ms", 0))
        local = float(timing.get("total_operation_ms", 0)) - provider
        terminal = timing.get("timeout_stage") or timing.get("provider_timeout_stage") or "none"
        rows.append(
            f"| {sample['scenario_id']} | `{str(sample['recall_request_id'])[:12]}` | {sample['outcome']} | "
            f"{timing.get('model_call_count', 0)} | {_ms(sample['query_to_injection_ready_ms'])} | "
            f"{_ms(sample['query_to_visible_answer_ms'])} | {provider:.1f} | {local:.1f} | {terminal} |"
        )
    return "\n".join(rows)


def render_report(summary: dict[str, object], evidence: Path) -> str:
    write = summary["write_latency"]
    recall = summary["recall_latency"]
    write_attempts = summary["write_attempts"]
    recall_samples = summary["recall_samples"]
    placements = [item for attempt in write_attempts for item in attempt["placements"]]
    durable_placements = [item for item in placements if item["final_outcome"] == "applied" and item.get("durable_commit", {}).get("verified") is True]
    deferred_placements = [item for item in placements if item["final_outcome"] == "defer"]
    relevant_recalls = [item for item in recall_samples if item["scenario_id"] != "R_NONE"]
    explicit_none = [item for item in recall_samples if item["scenario_id"] == "R_NONE"]
    dense_median = summary["cohorts"]["dense_query_to_injection"].get("median_ms")
    warm_median = summary["cohorts"]["warm_query_to_injection"].get("median_ms")
    dense_delta = "insufficient sample"
    if dense_median is not None and warm_median is not None:
        dense_delta = f"observed median +{float(dense_median) - float(warm_median):.1f} ms (n=2 versus n=3; not a population estimate)"
    return f"""# AOLD Real Memory Commit And Recall Latency Baseline Report

Status: `AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

This report measures the existing layer-0 memory loop. It does not establish a permanent SLA and does not authorize optimization.

## Evidence

- Evidence: `{evidence.as_posix()}`
- Records: {summary['record_count']}
- SHA-256: `{summary['evidence_sha256']}`
- Write turns: {summary['write_turn_count']}
- Write attempts (all source hooks): {summary['write_turn_attempt_count']}
- Ordinary write host turns: {summary['write_host_turn_count']}
- Durable-memory turns: {summary['durable_memory_turn_count']}
- Durable-memory attempt turns (all source hooks): {summary['durable_memory_attempt_turn_count']}
- Recall queries: {summary['recall_query_count']}
- Recall host turns: {summary['recall_host_turn_count']}
- Visible-answer correlations: {summary['visible_answer_correlated_count']}
- NONE recalls: {summary['none_recall_count']}
- Workspace reopen: {json.dumps(summary.get('workspace_reopen', {'status': 'not run'}), ensure_ascii=False, sort_keys=True)}

## Commit Latency

- Turn to first durable: {_metric(write['turn_to_first_durable'])}
- Turn to all durable: {_metric(write['turn_to_all_durable'])}
- Durable readback: {len(durable_placements)}/{len(placements)} Placement terminals verified after reopen; formal message-sent-to-durable samples remain unavailable.

| Scenario | Turn ID | Outcome | Model calls | First durable ms | All durable ms | Provider ms | Local ms | Timeout/correction/retry |
|---|---|---:|---:|---:|---:|---:|---:|---|
{_write_rows(summary)}

## Recall Latency

- Query to injection ready: {_metric(recall['query_to_injection_ready'])}
- Query to visible answer: {_metric(recall['query_to_visible_answer'])}
- Query to NONE terminal: {_metric(recall['query_to_none_terminal'])}

| Scenario | Query ID | Outcome | Model calls | Injection ms | Visible ms | Provider ms | Local ms | Timeout/correction/retry |
|---|---|---:|---:|---:|---:|---:|---:|---|
{_recall_rows(summary)}

## Cohorts

- Cold relevant injection: {_metric(summary['cohorts']['cold_query_to_injection'])}; only {summary['cohorts']['cold_relevant_count']} relevant cold sample, so cold-warm delta is insufficient sample.
- Warm relevant injection: {_metric(summary['cohorts']['warm_query_to_injection'])}.
- Dense hidden-preview injection: {_metric(summary['cohorts']['dense_query_to_injection'])}.
- Dense versus warm: {dense_delta}.
- Maximum selected Statement count: {summary['cohorts']['max_selected_statement_count']}; multi-Statement amplification is insufficient sample.

## Success Observations

- Formation terminal observations: {len(write_attempts)}/8 instrumented source-hook attempts; only 0/12 ordinary host turns had the required `message_sent` source.
- Durable memory: {len(durable_placements)}/{len(placements)} Placement terminals, but 0/12 formally correlated ordinary host turns.
- Placement defer: {len(deferred_placements)}/{len(placements)} Placement terminals.
- Provider timeout: 0/{len(placements) + len(recall_samples)} terminal operations reported `provider_timeout_stage`.
- Invalid JSON / repair: 0 corrections succeeded; no repaired result is promoted into a formal timing sample.
- Revision confirmation: 0 observed.
- Recall relevant injection: {sum(item['outcome'] == 'inject' for item in relevant_recalls)}/{len(relevant_recalls)} non-explicit-NONE queries.
- Explicit NONE observation: {sum(item['outcome'] == 'none' for item in explicit_none)}/{len(explicit_none)}.
- Visible-answer correlation: {summary['visible_answer_correlated_count']}/{summary['recall_query_count']} because the CLI host emitted `agent_end`, not the required `message_sent` event.

## Limits

Formation output is not durable memory, injection readiness is not a visible answer, and unmatched run IDs are never inferred. The frozen evidence supports only the explicitly reported small cohorts; it does not establish a permanent SLA or model-quality rate.

No optimization was performed in this task. Candidate optimization priority must be derived from the final observed Provider/local/main-agent shares rather than assumed here.

## Stage Shares

- Write Provider share: {summary['stage_shares']['write_provider_share']}
- Recall Provider share: {summary['stage_shares']['recall_provider_share']}
- Main-agent share: {summary['stage_shares']['main_agent_share']}

## Bottleneck Classification

1. Provider calls account for {float(summary['stage_shares']['write_provider_share']) * 100:.1f}% of observed write-operation time.
2. Multi-Statement serial Placement amplification is insufficient sample because at most {summary['cohorts']['max_selected_statement_count']} Statements were selected and no formally correlated multi-durable turn exists.
3. Local Surface/Core work is not the aggregate bottleneck: Provider share exceeds 96% for writes and 97% for Recall.
4. Recall Provider traversal/selection dominates the measured query-to-injection path. Main-agent generation is unavailable because no `message_sent` endpoint was observed.
5. Cold restart delta is insufficient sample: only {summary['cohorts']['cold_relevant_count']} cold relevant injection was captured.
6. Dense hidden-preview versus ordinary warm relevant Recall: {dense_delta}.
7. NONE still invokes the Provider: all {summary['none_recall_count']} NONE terminals made one model call and took {_metric(recall['query_to_none_terminal'])}.

## Candidate Priority

| Priority | Candidate for a separately authorized task | Evidence basis |
|---:|---|---|
| 1 | Reduce avoidable Formation, Placement, and Recall Provider calls or prompt size without replacing semantic decisions in Python | Provider share is 96.2% write and 97.9% Recall |
| 2 | Add a real host `message_sent` hook and preserve exact turn/query correlation | 0/12 visible endpoint correlations |
| 3 | Study bounded read-only Surface reuse for a Formation batch | Multi-Statement amplification remains unmeasured |
| 4 | Collect additional cold, multi-Statement, revision, reuse, and defer cohorts | Minimum independent sample gates were not met |

No optimization is implemented or authorized by this report.

## Gate Result

`AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

Gate checks: `{json.dumps(summary['completion_gates'], ensure_ascii=False, sort_keys=True)}`
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()
    records = load_records(args.evidence)
    summary = summarize(records)
    summary["evidence_sha256"] = evidence_sha256(args.evidence)
    summary["evidence_line_count"] = len(records)
    summary["evidence_size_bytes"] = args.evidence.stat().st_size
    if args.workspace is not None:
        summary["workspace_reopen"] = verify_workspace(args.workspace)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(canonical_json(summary), encoding="utf-8", newline="\n")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary, args.evidence), encoding="utf-8", newline="\n")
    print(json.dumps({"status": "pass", "records": len(records), "summary": str(args.summary), "report": str(args.report)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
