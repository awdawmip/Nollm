# GRF1-FH Validation Report

## Gate F

```text
GATE_F_PASSED
- GRF storage layout implemented;
- canonical JSON stable across roundtrip;
- all persisted objects have schema_version;
- ids determine paths and path traversal is rejected;
- duplicate same-byte write is idempotent;
- duplicate different-byte write is rejected;
- exact runtime objects preserve integers and do not serialize floats.
```

## Gate G

```text
GATE_G_PASSED
- append-only ledger implemented;
- every durable GRF object write has ledger event when recorded_at is supplied;
- object hash matches canonical bytes;
- different-byte rewrite rejected without overwrite;
- relation field rebuilt from files;
- replayed recall matches in-memory recall on selected_shards and path classes;
- rejected stitch records reload and suppress repeated false-friend acceptance;
- RecallDigest is derived and source objects remain authoritative.
```

## Gate H

```text
GATE_H_PASSED
- expanded synthetic datasets created: concentrated=20, scattered=24, false_decoys=18;
- local Cognee-style baselines retained without actual Cognee run;
- N5_grf_file_replay added;
- polygon_runtime_call_count = 0;
- runtime_float_operation_count = 0 for eisenstein_exact_v1;
- average_kernel_fanout = 3/1 and max_kernel_fanout = 7;
- false_stitch_rate reported;
- relation_storage_size does not scale as pairwise O(N^2) for GRF variants;
- N5 replay_selected_shard_delta = 0;
- N5 replay_path_class_delta = 0.
```

Expanded validation metrics:

```text
dataset_items = 62
B0_lexical: recall_correctness=245/251, source_faithfulness=245/453, false_stitch_rate=8/453, relation_storage_size=453
B1_vector_like_hashed_bow: recall_correctness=118/251, source_faithfulness=118/149, false_stitch_rate=2/149, relation_storage_size=149
B2_explicit_graph: recall_correctness=251/251, source_faithfulness=251/253, false_stitch_rate=0/253, relation_storage_size=253
N0_evidence_only: recall_correctness=0/251, missed_stitch_rate=251/251, relation_storage_size=0
N1_geometry_mark_only: recall_correctness=8/251, relation_storage_size=8, ledger_event_count=11, object_file_count=8
N2_grf_coverage_propagation: recall_correctness=24/251, relation_storage_size=24, ledger_event_count=27, object_file_count=24
N3_grf_plus_stitching: recall_correctness=42/251, source_faithfulness=42/42, false_stitch_rate=0/42, relation_storage_size=42
N4_grf_coverage_report_visible: recall_correctness=42/251, source_faithfulness=42/42, false_stitch_rate=0/42, relation_storage_size=42
N5_grf_file_replay: recall_correctness=42/251, replay_selected_shard_delta=0, replay_path_class_delta=0, ledger_event_count=45, object_file_count=42
context_token_cost_estimate = 358
```

Storage layout summary:

```text
workspace/grfs contains evidence, patches, placements, admissions, recalls,
relation_fields, ledger.jsonl, and manifests. Object files are canonical JSON.
```

Ledger semantics:

```text
append-only JSONL;
object_written for durable writes;
object_reopened_same_bytes for same-byte reopen when recorded;
object_write_rejected_different_bytes for rejected rewrite without overwrite;
relation_field_rebuilt and recall_digest_written for derived replay actions.
```

Replay equality summary:

```text
RelationField reloads placement records and bridge kernels from files.
Replay recall matches in-memory selected_shards and path classes in tests.
Rejected stitch proposals reload as anti-stitch evidence.
```

Limitations / failure cases:

```text
1. B0 lexical has false stitch risk on same-name entities.
2. B1 deterministic token overlap misses many expected relations.
3. N0 evidence-only has no relation-field recall and misses all stitch pairs.
4. N1 geometry mark only has low recall on dispersed facts.
5. N3/N5 prototype relation budget intentionally stores only bounded relations.
6. Fixtures remain synthetic and small.
7. File store is prototype JSON files, not production concurrency control.
```

Next recommended task:

```text
GRF1-I: integration with capture/admission workflow or larger benchmark.
```
