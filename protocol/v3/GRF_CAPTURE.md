# GRF Capture Prototype

GRF capture is an explicit file-first prototype boundary for raw evidence.

- `GRFCaptureRequest` is host-supplied and finite.
- Capture writes an `EvidenceShardRecord` only.
- Capture does not place, admit, recall, embed, summarize, or create semantic edges.
- Reopening the same `capture_id` with the same content bytes is idempotent.
- Reopening the same `capture_id` with different content is rejected without overwrite.

This protocol page is prototype documentation for GRF validation only. It is not an HCG/HAG/HX replacement and does not bind OpenClaw runtime.
