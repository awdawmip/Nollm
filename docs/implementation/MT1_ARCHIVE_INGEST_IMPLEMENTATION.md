# MT1 Archive Ingest Implementation

Status: implementation note.

MT1 adds a deterministic archive and import path:

```text
legacy files -> archive snapshot -> source spans -> extraction -> staged import -> native field revision
```

Runtime data must be written under `NOLLM_MEMORY_ROOT`, outside this repository and outside OpenClaw live memory files.

MT1 intentionally does not implement runtime takeover, native turn ingress, or active recall.
