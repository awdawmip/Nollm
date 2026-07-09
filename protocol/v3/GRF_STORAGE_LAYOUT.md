# GRF Storage Layout

GRF1-FH stores replayable prototype objects under a workspace-local `grfs/`
root. Tests use temporary workspaces.

```text
grfs/evidence/islands
grfs/patches/local_patches
grfs/patches/stitch/proposals
grfs/patches/stitch/records
grfs/patches/stitch/rejections
grfs/patches/stitch/bridges
grfs/placements/candidates
grfs/placements/decisions
grfs/placements/records
grfs/placements/rejections
grfs/admissions/minimal_records
grfs/recalls/digests
grfs/recalls/coverage_reports
grfs/relation_fields/indexes
grfs/ledger.jsonl
grfs/manifests
```

Object paths derive only from object id. Path traversal is rejected. Duplicate
writes with identical canonical bytes are idempotent; duplicate writes with
different canonical bytes fail without overwriting.
