# Nollm Access Charter

Purpose: form statements, decide placement/recall entry, format recall, and own source/user/session/product policy.

- Persistent state: Core handles, policy configuration, optional current/history references.
- Temporary state: bounded candidate context and pending decisions.
- Public API: reuse/new/revision/stitch/defer/forget mappings to Core public commands.
- Forbidden API: direct Core private access, geometry invariants, external relation indexes, Python semantic fallback.
- Dependencies: Core public API and optional Snapshot public API.
- Failure: trusted exclusive composition uses public Core state bytes for ordinary local rollback; direct concurrent Store mutation is unsupported.
- Distributions: minimal API, OpenClaw, debug, audited.
- Future repository: `nollm-access`.
- Current sources: capture/admission/evidence/source/placement/facade and protocol assets marked `SPLIT`.
