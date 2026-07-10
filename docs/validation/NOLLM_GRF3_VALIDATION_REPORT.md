# NOLLM GRF3 Validation Report

## Gate A

GATE_A_PASS. `GRFFacade` exposes capture, place, admit, recall, replay, and
validate operations. GRF Core imports no adapter or terminal package. Replay
is asserted equal to recall for the same contract request.

## Gate B

GATE_B_PASS. `GRFHostRequest` and `GRFHostResponse` use `grf_host_v1`.
`CapabilityRegistry` rejects unsupported operations. The host request,
evidence, placement, and admission namespaces have distinct validation rules.

## Gate C and D

GATE_C_PASS. `GRFFileAdapter` maps only JSON contract payloads and translates
invalid adapter input. It owns no GRF store or field mutation. GATE_D_PASS:
OpenClaw and Codex contain declaration-only V2 skeletons, isolated from legacy
assets.

## Gate E

Contract tests execute capture, place, admit, recall, replay, validate,
wrong-identity rejection, invalid capability rejection, missing-source
handling, and adapter malformed-input recovery. Recall and replay preserve the
same selected result and source fallback reference.

Metrics are measured in nanoseconds at the Core and adapter boundaries and
returned in responses as `core_latency_ns` and `adapter_latency_ns`.
