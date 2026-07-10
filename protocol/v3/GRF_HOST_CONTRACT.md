# GRF Host Contract V1

`grf_host_v1` is a versioned boundary between a host adapter and GRF Core.

Each request contains a distinct runtime-validated `HostRequestID`, optional
`EvidenceIdentity` (`shard:`), `PlacementIdentity` (`placement:`), and
`AdmissionIdentity` (`admission:`). A host request identifier cannot occupy
any identity namespace. Capture and validate cannot predeclare a GRF identity;
place and admit require evidence identity and cannot predeclare output
placement or admission identities. Supported capabilities are `capture`,
`place`, `admit`, `recall`, `replay`, and `validate`.

Adapters may map JSON, declare configuration, and translate errors. They may
not write evidence, alter placements or fields, or edit recall results; all
such operations are mediated by `GRFHostService` and `GRFFacade`.
