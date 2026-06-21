# MT1 Archive Ingest And Cutover Foundation Plan

MT1 creates a verifiable legacy-memory migration chain.

Required gates:

- archive bytes match source bytes
- manifest hash verifies
- source span coverage is complete
- imported shards carry archive provenance
- duplicate import is idempotent
- staging failure does not publish a field revision
- source files remain byte-identical
- importer works after source workspace is unavailable

MT1 does not implement MT2 ingress, MT3 recall runtime, MT4 runtime takeover, or MT5 geometry causality upgrade.
