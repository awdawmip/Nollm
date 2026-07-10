# GRF Host Contract V1

`grf_host_v2` is the current versioned boundary between a host adapter and GRF
Core. `grf_host_v1` remains supported with `supported_deprecated` status. Both
versions preserve the same typed identity and capability semantics.

Each request contains a distinct runtime-validated `HostRequestID`, optional
`EvidenceIdentity` (`shard:`), `PlacementIdentity` (`placement:`), and
`AdmissionIdentity` (`admission:`). A host request identifier cannot occupy
any identity namespace. Capture and validate cannot predeclare a GRF identity;
place and admit require evidence identity and cannot predeclare output
placement or admission identities. Host `place` emits a placement only; Host
`admit` requires both evidence and placement identity and accepts the existing
placement only. Supported capabilities are `capture`, `place`, `admit`,
`recall`, `replay`, and `validate`.

For recall and replay, `shard_id`, `placement_id`, and `admission_id` entry
modes require exactly the matching identity and no other identity namespace.
The currently untyped entry modes (`explicit_cell`, `source_window`,
`island_id`, and `patch_id`) require all identity fields to be null.

Adapters may map JSON, declare configuration, and translate errors. They may
not write evidence, alter placements or fields, or edit recall results; all
such operations are mediated by `GRFHostService` and `GRFFacade`.
