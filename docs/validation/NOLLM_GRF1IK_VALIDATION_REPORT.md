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
