# Nollm Current Status

Date: 2026-07-11

M1 establishes package-level Core/Access behavior. The active Core and Access
implementations are under `packages/`; Bare and Minimal distributions do not
reference the old GRF runtime.

Current verified boundaries:

- Core uses addressed Handles and explicit-cell bounded Recall.
- Access preserves original Evidence and maps externally supplied decisions.
- Snapshot and Trace bind directly to the new Core consistency boundary.
- Production boundary violations and production cycles are zero.
- Old GRF and OpenClaw implementations are migration assets outside active
  distributions.

OpenClaw Live and LLM corpora remain paused. M1 does not prove LLM placement
quality. History/Audit product behavior and physical GitHub splitting remain
deferred.
