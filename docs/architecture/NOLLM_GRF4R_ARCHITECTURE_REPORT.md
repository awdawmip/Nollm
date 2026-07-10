# NOLLM GRF4R Architecture Report

GRF Core remains inward-facing and host-independent. No module under
`reference/python/nollm/grf` imports integrations, adapters, terminals,
OpenClaw, or Codex. Hosts create only contract requests; adapters map and
translate; `GRFHostService` invokes `GRFFacade`; Core owns all evidence,
placement, admission, field, recall, ledger, and replay facts.

Geometry readiness remains bounded: runtime profiles use no polygon path, the
exact profile allows no runtime float, kernels are reusable and reconstruct
without error, and field indexes remain sparse. Evidence readiness includes
source fallback, file ledger events, deterministic replay, and explicit
failure classification.

The OpenClaw-like and Codex-like integrations are fixture hosts over
declarative capability skeletons. They are not native memory providers or
terminal runtimes.
