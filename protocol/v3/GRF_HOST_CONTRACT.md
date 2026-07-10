# GRF Host Contract V1

`grf_host_v1` is a versioned boundary between a host adapter and GRF Core.

Each request contains a distinct `host_request_id`, optional
`evidence_identity` (`shard:`), `placement_identity` (`placement:`), and
`admission_identity` (`admission:`). A host request identifier cannot occupy
any identity namespace. Supported capabilities are `capture`, `place`,
`admit`, `recall`, `replay`, and `validate`.

Adapters may map JSON, declare configuration, and translate errors. They may
not write evidence, alter placements or fields, or edit recall results; all
such operations are mediated by `GRFHostService` and `GRFFacade`.
