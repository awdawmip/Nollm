# NOLLM GRF3R2 Validation Report

## Gate A: Strict Query Identity Binding

GATE_A_PASS. `shard_id`, `placement_id`, and `admission_id` recall/replay
queries require exactly their matching typed identity. Missing, mismatched, or
multiple identity namespaces return a stable `ValueError` response before Core
recall. `source_window` and `explicit_cell` reject extraneous identity fields.

## Gate B: Place and Admit Separation

GATE_B_PASS. The Host `place` route calls `GRFFacade.place` and
`GRFAdmissionBridge.place`; it persists placement objects but returns
`admission_identity = null`. In the full E2E run, immediately after place,
`placement_record_count = 1` and `admission_record_count = 0`.

Host `admit` accepts `nollm_grf_admit_existing_placement_request` only with
matching evidence and placement identities. It reads the existing placement,
checks shard identity and source fallback refs, and writes one
`MinimalAdmissionRecord`. Afterwards, the same E2E workspace has
`placement_record_count = 1` and `admission_record_count = 1`.

## Gate C: Error Semantics

GATE_C_PASS. Unsupported capabilities produce a stable
`UnsupportedCapabilityError` Host response. Missing identity, mismatched
identity, missing placement, placement/shard mismatch, missing evidence, and
invalid request kind produce stable contract failure responses. The File
Adapter maps malformed mappings to `adapter_request_error` and unexpected
exceptions to `adapter_failure`, without paths, evidence contents, tracebacks,
or internal exception messages.

## Gate D: Full End-to-End

GATE_D_PASS. The File Adapter ran capture, place, admission-count check,
admit-existing-placement, shard recall, placement recall, admission replay,
and source fallback resolution. All three query forms selected the captured
shard; the resolved fallback content was `original source content`. Replay by
admission identity was deterministic with the equivalent shard/placement
recall result.

## Test Result and Limitations

The GRF component suite and scoped repository boundary suite pass. The terminal
skeletons remain declarative and do not participate in execution. This is a
file-first deterministic prototype boundary; it does not authorize a terminal
runtime, legacy provider, automatic admission, or GRF4 work.
