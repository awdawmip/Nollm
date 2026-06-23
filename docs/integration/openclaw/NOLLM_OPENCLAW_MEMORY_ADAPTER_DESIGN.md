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

See `docs/integration/openclaw/F0_NOLLM_MEMORY_PROVIDER_ALPHA.md` and
`docs/issues/FUNCTIONAL_ALPHA_OPEN_ISSUES.md` for the full contract and known
limitations.
