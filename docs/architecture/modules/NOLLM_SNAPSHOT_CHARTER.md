# Nollm Snapshot Charter

Purpose: create, restore, clone, verify, and structurally diff Core state.

- Persistent state: versioned snapshot artifacts and structural metadata.
- Temporary state: consistent-read sessions and verification buffers.
- Public API: create/restore/clone/verify/structural-diff through Core Snapshot Port.
- Forbidden API: truth, history semantics, retention policy, audit authority.
- Dependencies: Core public Snapshot Port only; never Core private implementation.
- Failure: may fail an explicit snapshot operation, never alter Core correctness.
- Distributions: minimal, OpenClaw, debug, audited.
- Future repository: `nollm-snapshot`.
- Current sources: GRF serialization/replay/snapshot helpers marked `SPLIT` or `MOVE`.
