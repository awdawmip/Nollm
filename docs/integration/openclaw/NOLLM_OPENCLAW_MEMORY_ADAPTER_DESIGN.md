# Nollm OpenClaw Memory Adapter Design

Date: 2026-06-23

This document is the design baseline for Nollm's OpenClaw integration after
F0-01.

## Position

Nollm now provides an **active memory provider** for OpenClaw:

```text
Nollm Core / Cortex
        |
        v
@nollm/openclaw-memory  (kind: memory, id: nollm)
        |
        v
OpenClaw active memory slot
        |
        v
private recall + private capture
        |
        v
Primary receives NOLLM_MEMORY_CONTEXT_V1 only
```

This is the intended takeover route. The historical companion mode
(`nollm-memory-companion`) remains available as an experimental tool surface but
is no longer the path to owning the memory slot.

For the active provider:

- `MEMORY.md`, `DREAMS.md`, and `memory/*.md` are not read or written.
- `memory_search`, `memory_get`, `memory_store`, `memory_recall` are not exposed
  to Primary.
- Nollm geometry/navigation tools are not exposed to Primary.
- Do not map `drift_class` to trust/status; drift_class is orientation metadata only.
- Recall is private through `agent_turn_prepare`.
- Capture is receipt-only through `agent_end`.

## Modes

Mode A (historical): companion tool mode. Nollm-specific geometry navigation
tools sit beside OpenClaw `memory-core`. This mode is preserved for experiments
but is not the active-memory route.

Mode B (current, F0-01): active memory-slot provider mode. Nollm owns the
`plugins.slots.memory` selection and injects context directly.

## Mapping

In the active provider, OpenClaw memory operations map as follows:

```text
agent_turn_prepare
  -> Nollm private recall (Python sidecar prepare)
  -> bounded NOLLM_MEMORY_CONTEXT_V1 envelope
  -> injected before Primary system prompt

agent_end
  -> Nollm private capture (Python sidecar capture)
  -> receipt written under nollmDataRoot
  -> state: captured_pending_native_ingress
```

## Sidecar layout (F0)

Nollm-owned state lives outside the OpenClaw workspace:

```text
{nollmDataRoot}/
  functional-alpha/
    capture-receipts/
      <receipt_id>.json
```

No sidecar metadata is placed beside OpenClaw memory files.

## Non-goals

The active provider does not:

- implement finished Cortex geometry recall in F0;
- migrate historical `MEMORY.md` / `DREAMS.md`;
- write legacy markdown files;
- expose Primary-visible memory tools;
- claim production cutover.

## F0-02 updates

The following Functional Alpha closure items were addressed in F0-02:

- **Context validation**: sidecar prepare results are schema-validated before
  injection. A secondary maxFacts/maxCharacters budget is enforced in the
  TypeScript layer, truncating or rejecting oversized results.
- **Runtime identity**: agent_id, session_id, and run_id are extracted from the
  hook context, not from the plugin registration id. Unsupported agent ids are
  explicitly rejected.
- **Latest user text**: the provider extracts the most recent user message,
  supporting both string and text-block-array content. Assistant messages are
  never misidentified as user queries.
- **Opaque compatibility references**: search results issue process-local,
  manager-scoped, agent-scoped, revision-bound nollm://compat/v1/<nonce> refs.
  readFile only accepts refs issued by the same manager instance. These refs
  are explicitly not session-bound: the upstream `MemorySearchManager.readFile()`
  contract does not accept caller/session context, so true cross-session
  authorization cannot be enforced through this compatibility facade
  (see `FA-ISSUE-11`). Unissued, cross-manager, expired, and revision-mismatched
  refs are rejected. Compatibility score is ordering-only, not vector similarity
  or trust.
- **Idempotent capture**: receipt identity is based on stable facts
  (agent_id, session_id, run_id, event_hash, field_revision_id), not
  request_id or Date.now(). Same event produces same receipt with reused=true.
  Content collision with different event hash fails closed.
- **Secret redaction**: capture receipts store only content hashes and
  structural metadata in receipt_only mode. Recursive redaction handles
  nested objects and string-embedded credentials.
- **Segment-aware legacy path rejection**: nollmDataRoot is validated using
  path segments, not substrings. Paths ending in memory, MEMORY.md, DREAMS.md,
  or legacy_workspace are rejected on both POSIX and Windows.
- **Host integration harness**: the harness uses NOLLM_OPENCLAW_CHECKOUT
  instead of hardcoded paths, verifies Node engine compatibility, and performs
  actual plugin loading tests (H1-H8) rather than relying on direct SDK import.


## F0-04 updates

The following Functional Alpha closure items were addressed in F0-04:

- **Real OpenClaw loader integration**: the harness provisions a fixed upstream
  checkout (`dc9c11be917ebdc711b956250aa80a8e5b47bea6`), creates an isolated
  OpenClaw profile selecting `plugins.slots.memory = "nollm"`, and attempts to
  load the local plugin through public OpenClaw entry points only. The target
  commit does not export a public local-memory-plugin loader seam, so the host
  proof is recorded as `target_limitation: OPENCLAW_LOADER_LOCAL_MEMORY_PLUGIN_LIMITATION`
  rather than substituted with a mock proof (see `FA-ISSUE-10`).
- **Canonical capture identity authority**: Python is the sole canonical
  identity authority. TypeScript forwards a strict `nollm.provider.capture.v2`
  event without an `event_hash`; Python validates strict input, computes the
  canonical event hash, and returns the canonical `receipt_id`.
- **Atomic receipt publish**: receipts are created with an atomic no-clobber
  `O_CREAT | O_EXCL` open. Duplicate canonical events fall through to a reuse
  path; corrupt existing receipts are moved to a `quarantine/` directory and
  never overwritten.
- **Compatibility scope honesty**: the compatibility facade is explicitly
  manager-scoped, not session-bound, because the upstream
  `MemorySearchManager.readFile()` contract lacks caller/session context (see
  `FA-ISSUE-11`).
- **Fixture containment parity**: TypeScript and Python both canonicalize
  fixture paths with `realpath`/`resolve()` and reject symlink escapes.
- **Auto-generated evidence**: command records, artifact hashes, upstream
  commit, and remote state are generated from actual execution output, not
  hand-written counts.

See `docs/integration/openclaw/F0_NOLLM_MEMORY_PROVIDER_ALPHA.md` and
`docs/issues/FUNCTIONAL_ALPHA_OPEN_ISSUES.md` for the full contract and known
limitations.
