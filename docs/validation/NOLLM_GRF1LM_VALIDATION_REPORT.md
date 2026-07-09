# NOLLM GRF1-LM Validation Report

## Gate L

GATE_L_PASSED

- GRFFacade exposes capture/admit/recall/replay/validate.
- CLI emits exactly one JSON object.
- Errors are stable JSON and do not leak absolute paths.
- Facade does not import HCG/HAG/HX/OCA.
- Capture/admit/recall chain round-trips through file store.
- Replay recall equals in-memory recall.
- No embedding/global search/object semantic edge path exists.

## Gate M

GATE_M_PASSED

- HCG-like capture JSON imports into GRF capture request without HCG import.
- OCA-like input imports without OpenClaw import.
- V2 DreamShard-like input imports without placement inference.
- Host/request/message IDs never become GRF evidence identity unless explicitly provided as shard_id.
- Importer is import-only and does not call legacy runtime.
- Unknown unsupported semantics are ignored or rejected explicitly, not silently treated as placement/admission.
