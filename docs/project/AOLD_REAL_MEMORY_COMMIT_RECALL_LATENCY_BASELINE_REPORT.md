# AOLD Real Memory Commit And Recall Latency Baseline Report

Status: `AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS`

This report measures the existing layer-0 memory loop. It does not establish a permanent SLA and does not authorize optimization.

## Evidence

- Evidence: `validation/aold_real_memory_commit_recall_latency_20260716.jsonl`
- Records: 110
- SHA-256: `6d3203649b07acc89a760ebc41cddbf38551bdddba5565b45f3f5ea78d0948fb`
- Write turns: 0
- Write attempts (all source hooks): 8
- Ordinary write host turns: 12
- Durable-memory turns: 0
- Durable-memory attempt turns (all source hooks): 3
- Recall queries: 12
- Recall host turns: 12
- Visible-answer correlations: 0
- NONE recalls: 4
- Workspace reopen: {"binding_count": 34, "reopen_verified": true, "statement_count": 37, "status": "pass"}

## Commit Latency

- Turn to first durable: insufficient sample
- Turn to all durable: insufficient sample
- Durable readback: 3/6 Placement terminals verified after reopen; formal message-sent-to-durable samples remain unavailable.

| Scenario | Turn ID | Outcome | Model calls | First durable ms | All durable ms | Provider ms | Local ms | Timeout/correction/retry |
|---|---|---:|---:|---:|---:|---:|---:|---|
| W_NEW_MULTI | `0826c7c7ba78` | defer,defer | 4 | unavailable | unavailable | 346360.2 | 6352.1 | placement_prompt,placement_prompt |
| W_ADDITIVE | `0c796034e0a0` | no-placement | 0 | unavailable | unavailable | 19979.7 | 3527.3 | none |
| W_NEW_MULTI | `1bf0fffad1d0` | applied | 2 | unavailable | unavailable | 107998.5 | 6648.8 | none |
| W_NEW_SINGLE | `29b6e257a33e` | defer | 1 | unavailable | unavailable | 57737.4 | 5355.1 | placement_prompt |
| W_REUSE | `2bc2d984f6c4` | applied | 4 | unavailable | unavailable | 243851.8 | 6085.2 | none |
| W_NO_MEMORY | `772cb2c117ee` | no-placement | 0 | unavailable | unavailable | 35034.9 | 3051.5 | none |
| W_COLD_AFTER_RESTART | `aa9356bddeae` | no-placement | 0 | unavailable | unavailable | 36818.6 | 3310.6 | none |
| W_NEW_SINGLE | `d82a9978a677` | applied | 3 | unavailable | unavailable | 285179.7 | 9828.9 | none |

## Recall Latency

- Query to injection ready: n=8, min_ms=52311.952, median_ms=111642.123, p50_ms=111642.123, p90_ms=168840.253, p95_ms=not statistically meaningful, max_ms=168840.253
- Query to visible answer: insufficient sample
- Query to NONE terminal: n=4, min_ms=27268.415, median_ms=34382.526, max_ms=57636.666

| Scenario | Query ID | Outcome | Model calls | Injection ms | Visible ms | Provider ms | Local ms | Timeout/correction/retry |
|---|---|---:|---:|---:|---:|---:|---:|---|
| R_NONE | `recall-135d7` | none | 1 | unavailable | unavailable | 32369.9 | 2012.6 | none |
| R_RELEVANT_WARM | `recall-4fbcd` | inject | 3 | 156674.4 | unavailable | 154371.0 | 2303.3 | none |
| R_DENSE_HIDDEN_PREVIEW | `recall-54653` | inject | 3 | 168840.3 | unavailable | 166753.4 | 2086.9 | none |
| R_RELEVANT_COLD | `recall-5596e` | none | 1 | unavailable | unavailable | 25241.9 | 2026.5 | none |
| R_RELEVANT_WARM | `recall-6e9d5` | none | 1 | unavailable | unavailable | 54637.5 | 798.3 | none |
| R_NONE | `recall-6fb6e` | none | 1 | unavailable | unavailable | 55915.8 | 1720.9 | none |
| R_RELEVANT_WARM | `recall-74e13` | inject | 2 | 114694.3 | unavailable | 112284.1 | 2410.2 | none |
| R_REPEATED_TOPIC | `recall-a64af` | inject | 2 | 99355.2 | unavailable | 97350.8 | 2004.4 | none |
| R_DENSE_HIDDEN_PREVIEW | `recall-ea469` | inject | 3 | 164285.2 | unavailable | 162672.6 | 1612.6 | none |
| R_MULTI_FACT | `recall-f508f` | inject | 3 | 75742.5 | unavailable | 74207.9 | 1534.6 | none |
| R_RELEVANT_COLD | `recall-f7181` | inject | 2 | 52312.0 | unavailable | 49824.2 | 2487.7 | none |
| R_RELEVANT_WARM | `recall-f8df8` | inject | 3 | 111642.1 | unavailable | 109364.8 | 2277.4 | none |

## Cohorts

- Cold relevant injection: n=1, min_ms=52311.952, median_ms=52311.952, max_ms=52311.952; only 1 relevant cold sample, so cold-warm delta is insufficient sample.
- Warm relevant injection: n=3, min_ms=111642.123, median_ms=114694.3, max_ms=156674.361.
- Dense hidden-preview injection: n=2, min_ms=164285.202, median_ms=164285.202, max_ms=168840.253.
- Dense versus warm: observed median +49590.9 ms (n=2 versus n=3; not a population estimate).
- Maximum selected Statement count: 2; multi-Statement amplification is insufficient sample.

## Success Observations

- Formation terminal observations: 8/8 instrumented source-hook attempts; only 0/12 ordinary host turns had the required `message_sent` source.
- Durable memory: 3/6 Placement terminals, but 0/12 formally correlated ordinary host turns.
- Placement defer: 3/6 Placement terminals.
- Provider timeout: 0/18 terminal operations reported `provider_timeout_stage`.
- Invalid JSON / repair: 0 corrections succeeded; no repaired result is promoted into a formal timing sample.
- Revision confirmation: 0 observed.
- Recall relevant injection: 8/10 non-explicit-NONE queries.
- Explicit NONE observation: 2/2.
- Visible-answer correlation: 0/12 because the CLI host emitted `agent_end`, not the required `message_sent` event.

## Limits

Formation output is not durable memory, injection readiness is not a visible answer, and unmatched run IDs are never inferred. The frozen evidence supports only the explicitly reported small cohorts; it does not establish a permanent SLA or model-quality rate.

No optimization was performed in this task. Candidate optimization priority must be derived from the final observed Provider/local/main-agent shares rather than assumed here.

## Stage Shares

- Write Provider share: 0.9624850629653754
- Recall Provider share: 0.9791862183628287
- Main-agent share: insufficient sample: message_sent not observed

## Bottleneck Classification

1. Provider calls account for 96.2% of observed write-operation time.
2. Multi-Statement serial Placement amplification is insufficient sample because at most 2 Statements were selected and no formally correlated multi-durable turn exists.
3. Local Surface/Core work is not the aggregate bottleneck: Provider share exceeds 96% for writes and 97% for Recall.
4. Recall Provider traversal/selection dominates the measured query-to-injection path. Main-agent generation is unavailable because no `message_sent` endpoint was observed.
5. Cold restart delta is insufficient sample: only 1 cold relevant injection was captured.
6. Dense hidden-preview versus ordinary warm relevant Recall: observed median +49590.9 ms (n=2 versus n=3; not a population estimate).
7. NONE still invokes the Provider: all 4 NONE terminals made one model call and took n=4, min_ms=27268.415, median_ms=34382.526, max_ms=57636.666.

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

Gate checks: `{"cold_relevant_at_least_2": false, "dense_hidden_preview_at_least_2": true, "durable_memory_turns_at_least_8": false, "explicit_none_at_least_2": true, "formal_message_sent_write_turns_at_least_12": false, "query_to_injection_evidence": true, "query_to_visible_evidence": false, "recall_queries_at_least_12": true, "timing_semantics_corrected": true, "write_host_turns_at_least_12": true}`
