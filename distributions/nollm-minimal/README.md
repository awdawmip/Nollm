# nollm-minimal

Minimal composes `CoreRuntime`, `SnapshotService`, `AccessRuntime`,
`FileEvidenceStore`, and `FileHandleStore` with `trace=None`.

Composition: active Core, Snapshot, and Access package APIs with NullTrace and
FileEvidenceStore defaults. Legacy GRF is not a runtime dependency.
