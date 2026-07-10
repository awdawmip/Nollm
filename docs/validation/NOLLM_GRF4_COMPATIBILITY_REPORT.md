# NOLLM GRF4 Compatibility Report

`grf_host_v1` remains the contract version for File, declared OpenClaw V2, and
declared Codex adapters. Capability declarations match the supported set:
`capture`, `place`, `admit`, `recall`, `replay`, and `validate`.

The Host Contract continues to enforce typed evidence, placement, and
admission identities. The GRF3R2 separation remains intact: Host place creates
only placement state; Host admit consumes an existing placement. Replay remains
deterministic and resolves the original source fallback.

GATE_A_PASS. Core import-firewall tests continue to prove no terminal or
adapter dependency. Legacy OpenClaw provider assets remain isolated and were
not started or modified.
