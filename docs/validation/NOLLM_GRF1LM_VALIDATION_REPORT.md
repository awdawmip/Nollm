# NOLLM GRF1-LM Validation Report

## Gate L

GATE_L_PASSED

- GRFFacade exposes capture/admit/recall/replay/validate.
- CLI emits exactly one JSON object.
- Errors are stable JSON and do not leak absolute paths.
- Facade does not import HCG/HAG/HX/OCA.
- Capture/admit/recall chain round-trips through file store.
- Replay recall equals in-memory recall.
- No embedding/global search/object semantic edge path exists.

## Gate M

GATE_M_PASSED

- HCG-like capture JSON imports into GRF capture request without HCG import.
- OCA-like input imports without OpenClaw import.
- V2 DreamShard-like input imports without placement inference.
- Host/request/message IDs never become GRF evidence identity unless explicitly provided as shard_id.
- Importer is import-only and does not call legacy runtime.
- Unknown unsupported semantics are ignored or rejected explicitly, not silently treated as placement/admission.

## Gate N

GATE_N_PASSED

- Dataset generator emits dataset_items >= 1000 with seed grf1lm_scale_seed_v1.
- N7 facade replay path uses public GRFFacade.
- Source_resolution_success_rate = 1.0.
- Replay deltas = 0.
- Relation storage remains below explicit graph baseline.
- No runtime polygon / no exact runtime float.
- false_stitch_rate and missed_stitch_rate are reported.
- Local baselines remain Cognee-style, not actual Cognee run.

Scale validation metrics are emitted by `python experiments/grf/run_mini_validation.py` and include:

- dataset_items
- explicit_graph_relation_storage_size
- grf_relation_storage_size
- relation_storage_vs_explicit_graph_ratio
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
- elapsed_wall_ms_capture
- elapsed_wall_ms_admit
- elapsed_wall_ms_recall

Known limitations:

- Scale fixtures are deterministic synthetic data, not production captures.
- Local baselines are Cognee-style, not actual Cognee runs.
- N7 validates recall/replay equality on a fixed selected sample after full capture/admit.
- GRFFacade is a prototype orchestration surface, not a daemon or runtime service.
- Import boundary maps stable subsets only; unsupported legacy semantics are ignored or rejected explicitly.
- Placement scoring remains validation_fixture_policy, not production placement quality.
