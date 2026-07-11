# Nollm Current Status

Date: 2026-07-11

M1 establishes package-level Core/Access behavior. The active Core and Access
implementations are under `packages/`; Bare and Minimal distributions do not
reference the old GRF runtime.

Current verified boundaries after the public-boundary reallocation candidate:

- Core uses addressed Handles and explicit-cell bounded Recall.
- Access preserves original Evidence and maps externally supplied decisions.
- Snapshot owns its Protocol and composes through atomic Core state bytes.
- Trace owns sink, file, metrics, and inspector implementations; Core retains only the immutable event port.
- Lab owns canonical geometry template generation; Core loads the generated artifact.
- Access uses a trusted local composition contract without Core-issued security capabilities.
- Production boundary violations and production cycles are zero.
- Old GRF and OpenClaw implementations are migration assets outside active
  distributions.

OpenClaw Live and LLM corpora remain paused. M1 does not prove LLM placement
quality. History/Audit product behavior and physical GitHub splitting remain
deferred.
