# DG6 Isolated Snapshot Compaction Adapter

DG6 is a read-only adapter from an explicit DF1 `FiniteFieldSnapshot` to a DG5 view-only compaction projection.

The adapter validates the DF1 snapshot fingerprint with `stable_fingerprint(snapshot_fingerprint_payload(snapshot))`, derives the trace manifest only from `snapshot.replayed_traces`, calls DG5 planning and view building, and returns an immutable in-memory `SnapshotCompactionProjection`.

DG6 does not accept caller-provided compression plans, compacted views, trace indexes, extra traces, recall universes, runtime handles, storage paths, or cache keys.

DG6 does not modify Evidence, Capture, Cortex, Admission, Assembly, Field, Compression, Recall, Integration, Geometry, CLI, OpenClaw, network, database, cache, LLM, NLP, embeddings, or semantic search.

Failures are exposed as structured `DG6AdapterError.reason_code` values.

Malformed projection manifest shapes, including non-tuple source trace fields, non-string trace ids, malformed fingerprint pairs, or fingerprint ids that do not match source trace ids, fail closed with DG6 structured reason codes. Malformed replayed trace enum fields surfaced by DG5 planning or view construction are translated at the DG6 boundary as invalid snapshot input. These translations do not change valid projection identity or DG5 bound-plan semantics.
