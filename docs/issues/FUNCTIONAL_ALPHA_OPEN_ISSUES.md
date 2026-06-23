# Functional Alpha Open Issues

This file contains public-issue seeds discovered during F0-01 OpenClaw Native
Memory Provider Functional Alpha. They are intentionally written so they can be
copied into a GitHub/GitLab issue tracker with minimal editing.

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
The OpenClaw host discriminates memory backends using `backend: "builtin" | "qmd"`. A third-party provider such as Nollm must either lie about being `builtin` or fail type checks.

**Why it matters**
The memory-slot contract is clean (`kind: "memory"`, `registerMemoryCapability`), but the runtime status/config discriminant cannot truthfully report a non-built-in provider id. This forces compatibility shims.

**Scope / non-scope**
- In scope: host interface extensibility for memory provider ids.
- Out of scope: changing Nollm to be a built-in backend; that would be a fork.

**Acceptance evidence**
A memory provider can return `backend: "nollm"` (or an extensible provider id) without type/runtime rejection, and OpenClaw host callers continue to work.

**Suggested labels**
`upstream`, `openclaw`, `memory-provider`, `api-contract`

**Blocks Functional Alpha?** No. F0 uses `backend: "builtin"` with `custom.backendKind: "nollm"` and documents the shim.

**Blocks production cutover?** Yes. The shim must not survive production claims.

---

## FA-ISSUE-02: agent_end is fire-and-forget on persistent Gateway paths

**Current behavior**
`agent_end` is invoked after the primary reply is delivered. If the process or Gateway restarts before the capture receipt is durably queued, the receipt may be lost.

**Why it matters**
F0 capture receipts are the input boundary for F1 native ingress. Losing them silently would break durable memory evolution.

**Scope / non-scope**
- In scope: a durable ingress queue/recovery contract.
- Out of scope: implementing the full queue in F0.

**Acceptance evidence**
A documented recovery path exists; tests demonstrate idempotent receipt recovery after simulated restart.

**Suggested labels**
`reliability`, `memory-provider`, `f1-ingress`

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
`recall`, `cortex`, `f1`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-04: R14 capability storage and archive transaction closure remain blockers for real memory migration

**Current behavior**
F0 stores capture receipts only. It does not promote receipts to native shards, migrate historical archives, or complete R14 capability-storage hardening.

**Why it matters**
Real user memory migration requires SafeRoot V3, capability storage, and archive transaction closure.

**Scope / non-scope**
- In scope: completing R14 as a separate track.
- Out of scope: doing R14 inside F0.

**Acceptance evidence**
R14 delivery receipt exists and a migration path from receipt to native shard is defined.

**Suggested labels**
`r14`, `capability-storage`, `archive`, `migration`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-05: Windows handle-equivalence and POSIX descriptor evidence are not complete production evidence

**Current behavior**
F0 tests run on Windows. POSIX descriptor-level evidence is not part of this bundle.

**Why it matters**
Cross-platform hardening requires equivalent evidence on POSIX.

**Scope / non-scope**
- In scope: running the same matrix on Linux/macOS.
- Out of scope: platform-specific kernel guarantees.

**Acceptance evidence**
Same provider tests and harness pass on a POSIX runner.

**Suggested labels**
`portability`, `windows`, `posix`, `testing`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Partially.

---

## FA-ISSUE-06: Compatibility score is ordering-only and must not be read as vector relevance/trust

**Current behavior**
The compatibility runtime returns `score: 1.0` for all matched facts because F0 does not implement semantic ranking.

**Why it matters**
Callers may misinterpret the score as relevance or confidence.

**Scope / non-scope**
- In scope: returning meaningful bounded scores or removing the score where not applicable.
- Out of scope: building a vector relevance engine in F0.

**Acceptance evidence**
Tests or documentation clarify that F0 scores are ordering placeholders.

**Suggested labels**
`compatibility`, `scoring`, `documentation`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-07: No multi-agent sharing, multi-user isolation, or untrusted workspace support

**Current behavior**
F0 is single-user, local, and uses one synthetic alpha field.

**Why it matters**
Production deployments require isolation boundaries.

**Scope / non-scope**
- In scope: designing per-agent/per-user data roots and access controls.
- Out of scope: implementing them in F0.

**Acceptance evidence**
Design doc and tests demonstrate per-user field separation.

**Suggested labels**
`security`, `isolation`, `multi-user`, `f2`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-08: No native shard promotion from capture receipt until F1 Native Ingress Alpha

**Current behavior**
Capture receipts are written with `state: "captured_pending_native_ingress"` but are not promoted to native shards.

**Why it matters**
Receipts alone are not durable memory. They need an ingress pipeline.

**Scope / non-scope**
- In scope: F1 native ingress alpha.
- Out of scope: automatic promotion in F0.

**Acceptance evidence**
F1 tests promote a receipt to a native shard without legacy-file writes.

**Suggested labels**
`ingress`, `f1`, `native-shard`

**Blocks Functional Alpha?** No.

**Blocks production cutover?** Yes.

---

## FA-ISSUE-09: OpenClaw CLI plugins build/validate only accepts defineToolPlugin entries

**Current behavior**
At commit `dc9c11be917ebdc711b956250aa80a8e5b47bea6` (`2026.6.9`), `openclaw plugins build` and `openclaw plugins validate --entry <path>` hard-code `loadToolPlugin()` and reject entries that use `definePluginEntry({ kind: "memory" })` with:

```text
plugin entry does not expose defineToolPlugin metadata: ./dist/index.js
```

**Why it matters**
The Nollm provider is a correct memory-slot plugin per the OpenClaw SDK, but the CLI authoring commands cannot validate it. This limits the integration verification surface.

**Scope / non-scope**
- In scope: upstream CLI support for `definePluginEntry` of any kind.
- Out of scope: converting Nollm to a tool plugin; that would violate the
  memory-slot design.

**Acceptance evidence**
`openclaw plugins build --entry ./dist/index.js` and `openclaw plugins validate --entry ./dist/index.js` succeed for a `kind: "memory"` provider.

**Suggested labels**
`upstream`, `openclaw`, `cli`, `memory-provider`

**Blocks Functional Alpha?** No. The integration harness uses a direct SDK load test as the alternative verification and records the CLI limitation.

**Blocks production cutover?** Yes. Production packaging should rely on supported CLI validation.
