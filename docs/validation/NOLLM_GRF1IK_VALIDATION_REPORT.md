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
