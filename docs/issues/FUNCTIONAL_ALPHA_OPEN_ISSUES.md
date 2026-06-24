# Functional Alpha Open Issues

This file contains public-issue seeds discovered during F0-01 and F0-02 OpenClaw
Native Memory Provider Functional Alpha. They are intentionally written so they
can be copied into a GitHub/GitLab issue tracker with minimal editing.

Each entry includes:

- current behavior
- why it matters
- scope / non-scope
- acceptance evidence
- suggested labels
- does it block Functional Alpha?
- does it block production cutover?

---

## FA-ISSUE-01: OpenClaw MemoryPluginRuntime backend discriminant is not extensible beyond builtin/qmd

**Current behavior**
The OpenClaw host discriminates memory backends using backend builtin or qmd. A third-party provider such as Nollm must either lie about being builtin or fail type checks.

**Why it matters**
The memory-slot contract is clean (kind: memory, registerMemoryCapability), but the runtime status/config discriminant cannot truthfully report a non-built-in provider id. This forces compatibility shims.

**Scope / non-scope**
- In scope: host interface extensibility for memory provider ids.
- Out of scope: changing Nollm to be a built-in backend; that would be a fork.

**Acceptance evidence**
A memory provider can return backend nollm (or an extensible provider id) without type/runtime rejection, and OpenClaw host callers continue to work.

**Suggested labels**
upstream, openclaw, memory-provider, api-contract

**Blocks Functional Alpha?** No. F0 uses backend builtin with custom.backendKind nollm and documents the shim.

**Blocks production cutover?** Yes. The shim must not survive production claims.

---

## F0-02 Resolution Summary

The following F0-01 issues were resolved in F0-02:

- B1 (Evidence/bundle mismatch): Fixed. Evidence branch now uses the same project head as the feature branch.
- B3 (Not actual host integration): Improved. Integration harness now uses NOLLM_OPENCLAW_CHECKOUT env var, verifies Node engine, and performs actual host loading via plugin registry.
- B4 (Compat readFile not ref-bound): Fixed. NollmCompatibilityReferenceRegistry issues and validates opaque refs bound to agent/revision.
- B5 (agent_turn_prepare wrong user text): Fixed. extractLatestUserText scans from the end for role=user messages.
- B6 (Runtime identity hardcoded): Fixed. resolveNollmTurnIdentity uses ctx.agentId/sessionId/runId with allowAgentIds config.
- B7 (No sidecar schema/budget validation): Fixed. validatePrepareResult and validateContextEnvelope enforce schema and secondary budget.
- B8 (Non-idempotent capture): Fixed. Receipt identity based on stable facts (agent/session/run/event_hash), not Date.now().
- B9 (Secret leakage in capture): Fixed. Recursive redaction, receipt_only stores only content_hash/length, not raw content.
- B10 (Legacy path bypass): Fixed. Segment-aware validation in both TS and Python.
- B11 (Regression tests): Fixed. Adapter docs test updated, load_field_head returns None for missing root.

FA-ISSUE-09 remains partially open: the CLI build/validate still rejects memory plugins, but the integration harness now uses actual host registry loading to prove slot selection and hook execution.

---

## FA-ISSUE-02: agent_end is fire-and-forget on persistent Gateway paths

**Current behavior**
agent_end is invoked after the primary reply is delivered. If the process or Gateway restarts before the capture receipt is durably queued, the receipt may be lost.

**Why it matters**
F0 capture receipts are the input boundary for F1 native ingress. Losing them silently would break durable memory evolution.

**Scope / non-scope**
- In scope: a durable ingress queue/recovery contract.
- Out of scope: implementing the full queue in F0.

**Acceptance evidence**
A documented recovery path exists; tests demonstrate idempotent receipt recovery after simulated restart.

**Suggested labels**
reliability, memory-provider, f1-ingress

**Blocks Functional Alpha?** No. F0 writes receipts to the local filesystem and documents the limitation.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-03: F0 uses deterministic keyword selection, not finished Cortex geometry recall

**Current behavior**
Recall is implemented as simple keyword/token overlap against the synthetic alpha field.

**Why it matters**
This proves the end-to-end slot plumbing but is not the eventual Cortex geometry recall.

**Scope / non-scope**
- In scope: replacing keyword recall with native field/scale-scan recall.
- Out of scope: turning the provider into a general semantic search engine.

**Acceptance evidence**
Native recall returns field/revision-bound facts with explicit absences and no fabricated matches.

**Suggested labels**
recall, cortex, memory-provider

**Blocks Functional Alpha?** No. Keyword recall is sufficient for F0.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-04: R14 capability storage and archive transaction closure remain blockers for real migration

**Current behavior**
F0 capture receipts are metadata-only. Real migration requires R14 capability-storage and archive transaction closure.

**Why it matters**
Without R14 closure, capture receipts cannot be promoted into durable memory shards with provenance, source-span binding, and archive integrity.

**Scope / non-scope**
- In scope: R14 capability-storage and archive transaction closure.
- Out of scope: F0 Functional Alpha scope.

**Acceptance evidence**
Capture receipts can be promoted to published field revisions with full R14 integrity.

**Suggested labels**
r14, capability-storage, archive, migration

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-05: Windows handle-equivalence and POSIX descriptor evidence are not complete

**Current behavior**
F0 tests on Windows. POSIX descriptor-based path-safety evidence is not part of the F0 test matrix.

**Why it matters**
Cross-platform path safety (symlink rejection, handle-equivalence) matters for production but is not required for F0 single-platform alpha.

**Scope / non-scope**
- In scope: POSIX descriptor evidence and cross-platform path tests.
- Out of scope: Windows-specific handle equivalence beyond F0 needs.

**Acceptance evidence**
Tests pass on both Windows and POSIX with equivalent path-safety guarantees.

**Suggested labels**
cross-platform, path-safety, posix

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-06: Compatibility score is ordering-only and must not be read as vector relevance/trust

**Current behavior**
The compatibility manager returns a deterministic score of 1.0 for all matched facts.

**Why it matters**
This score represents deterministic compatibility ordering only. It must not be interpreted as vector similarity, truth confidence, or trust level.

**Scope / non-scope**
- In scope: documentation and README clarity about score semantics.
- Out of scope: implementing real vector relevance in F0.

**Acceptance evidence**
README and code comments explicitly state that score is ordering-only.

**Suggested labels**
compatibility, score, documentation

**Blocks Functional Alpha?** No. F0-02 documents this in README and code.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-07: No multi-agent sharing, multi-user isolation, or untrusted workspace support

**Current behavior**
F0 supports a single agent (main) in a single-user local workspace. Multi-agent memory sharing, multi-user isolation, and untrusted workspace isolation are not implemented.

**Why it matters**
Production deployments may need multi-agent and multi-user memory isolation.

**Scope / non-scope**
- In scope: multi-agent and multi-user isolation design.
- Out of scope: implementing multi-agent in F0.

**Acceptance evidence**
A design exists for multi-agent memory isolation with per-agent field scoping.

**Suggested labels**
multi-agent, multi-user, isolation

**Blocks Functional Alpha?** No. F0-02 rejects unsupported agent ids when allowAgentIds is configured.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-08: No native shard promotion from capture receipt until F1 Native Ingress Alpha

**Current behavior**
F0 capture receipts are metadata-only (content hashes, structural metadata). No raw message body is stored by default. Promotion to native shards requires F1.

**Why it matters**
F0-02 improved capture to be receipt-only with no raw body secrets. F1 will introduce the secure ingestion path for real raw-event archive.

**Scope / non-scope**
- In scope: F1 native ingress with secure raw-event archive.
- Out of scope: raw-event archive in F0.

**Acceptance evidence**
F1 can promote F0 capture receipts into published field revisions.

**Suggested labels**
f1-ingress, capture, shard-promotion

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-09: OpenClaw CLI plugins build/validate only accepts defineToolPlugin entries (PARTIALLY RESOLVED in F0-02)

**Current behavior**
The OpenClaw CLI plugins build/validate at commit dc9c11b only accepts entries that expose defineToolPlugin metadata. The Nollm provider correctly uses definePluginEntry with kind memory per the memory-slot contract, so the CLI rejects it.

**Why it matters**
The CLI cannot validate memory-slot plugins. However, F0-02 replaces CLI validation with actual host registry/hook execution proof (H1-H8) using the real plugin loader. The CLI limitation is recorded honestly and does not mask a host integration failure.

**Scope / non-scope**
- In scope: CLI support for memory-slot plugin validation.
- Out of scope: changing the provider to use defineToolPlugin.

**Acceptance evidence**
CLI build/validate result is recorded honestly. Host integration H1-H8 passes independently.

**Suggested labels**
upstream, openclaw, cli, memory-provider

**Blocks Functional Alpha?** No. F0-02 uses host loading instead of CLI validation.

**Blocks production cutover?** No, as long as host loading evidence is maintained.