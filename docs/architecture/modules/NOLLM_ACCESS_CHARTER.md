# Nollm Access Charter

Purpose: form statements, decide placement/recall entry, format recall, and own source/user/session/product policy.

- Persistent state: Core handles, policy configuration, optional current/history references.
- Temporary state: bounded candidate context and pending decisions.
- Dense-locality views expose finite Statement previews and truthful occupancy count/band fields. Access does not reinterpret them as physical or semantic density.
- Public API: reuse/new/revision/stitch/defer/forget mappings to Core public commands.
- Dream formation: a real Host LLM may rewrite, split, merge, or defer bounded temporary `ConversationMaterial`; Access validates only schema, exact types, canonical ordering, identity, and character/count budgets.
- Persistent semantic contract: `StatementStore` stores canonical `MemoryStatement` bytes. `EvidenceStore` and exact-span Formation remain compatibility/migration assets and new compatibility writes use the statement schema.
- Formation boundary: Access does not make semantic decisions, choose placement, persist conversation material, or write Formation results implicitly.
- Forbidden API: direct Core private access, geometry invariants, external relation indexes, Python semantic fallback.
- Dependencies: Core public API and optional Snapshot public API.
- Failure: trusted exclusive composition uses public Core state bytes for ordinary local rollback; direct concurrent Store mutation is unsupported.
- Binding contract: `HandleBinding` is strict canonical persistent state; `AccessRuntime` and `FileHandleStore` share one trusted process-local composition lock for each canonical Access/Core workspace pair.
- Supported fault model: ordinary file-write failures roll back Core and binding bytes; private write monkeypatching is test/Lab-only and is not a public capability.
- Distributions: minimal API, OpenClaw, debug, audited.
- Future repository: `nollm-access`.
- Current sources: capture/admission/evidence/source/placement/facade and protocol assets marked `SPLIT`.
