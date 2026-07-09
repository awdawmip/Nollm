# GRF Replay

GRF replay reloads file-first objects, rebuilds a RelationField, reruns a
structured QueryProbe, and compares digest content.

Replay equality for GRF1-FH checks:

```text
selected_shards
coverage path classes
source_fallback_ref presence
rejected stitch records
```

RecallDigest and CoverageReport are derived read artifacts. They may be written
for audit, but deleting them must not delete or modify source GRF objects.
