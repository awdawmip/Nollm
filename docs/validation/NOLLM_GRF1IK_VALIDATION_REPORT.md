# NOLLM GRF1-IK Validation Report

## Gate I

GATE_I_PASSED

- Object IDs are protocol IDs, not path filenames.
- Colon/slash/question-mark IDs are path-safe through SHA-256 object filename encoding.
- EvidenceShardRecord stores original content and content_sha256.
- SourceWindowRecord persisted and reloadable.
- Capture writes evidence only, no placement/admission.
- Same-byte capture reopen is idempotent.
- Different-byte capture is rejected without overwrite.
- Ledger records durable evidence writes when recorded_at is supplied.

## Gate J

GATE_J_PASSED

- GRFAdmissionBridge is explicit and deterministic.
- Capture does not imply admission.
- Admitted records have source_fallback_refs.
- Rejected placement preserves evidence.
- Recall source fallback resolves to original content.
- Relation field reload from files preserves recall selected_shards/path classes.
- No embedding/global search/object semantic edge path exists.

## Gate K

GATE_K_PASSED

- Dataset sizes: concentrated_facts=60, scattered_facts=80, false_stitch_decoys=60, total=200.
- False-friend families include Apple company/fruit, Java language/island/coffee, Mercury planet/element/messenger.
- N6_grf_capture_file_replay uses GRFCaptureRequest, EvidenceShardRecord, SourceWindowRecord, GRFAdmissionBridge, file store reload, GRF recall, and source fallback resolution.
- Hard conditions checked: dataset_items >= 200, runtime_float_operation_count=0, polygon_runtime_call_count=0, N6 source_resolution_success_rate=1.0, N6 replay deltas=0.
- Local baselines are Cognee-style, not actual Cognee run.
- GRFAdmissionBridge is prototype validation code, not a production HCG/HAG replacement.

Gate K metrics are emitted by `python experiments/grf/run_mini_validation.py`:

- dataset_items
- relation_storage_size
- object_file_count
- ledger_event_count
- average_kernel_fanout
- max_kernel_fanout
- runtime_float_operation_count
- polygon_runtime_call_count
- false_stitch_rate
- missed_stitch_rate
- recall_correctness
- source_faithfulness
- context_token_cost_estimate
- storage_growth_vs_items
- relation_storage_vs_explicit_graph_ratio
- captured_shard_count
- admitted_shard_count
- source_resolution_success_rate
- capture_reopen_idempotency_checks
- rejected_rewrite_checks
- replay_selected_shard_delta
- replay_path_class_delta

Known limitations and failure cases:

- Synthetic fixtures are small compared with production corpora.
- Local baselines are deterministic Cognee-style comparisons, not an actual Cognee run.
- GRFAdmissionBridge uses validation_fixture_policy and does not replace HCG/HAG.
- Rejected false-friend cases are fixture-policy rejections, not learned semantic discrimination.
- Source fallback is direct ID lookup only; missing shards surface explicit missing_source.
- The file store prototype does not model production concurrency or durable compaction.
