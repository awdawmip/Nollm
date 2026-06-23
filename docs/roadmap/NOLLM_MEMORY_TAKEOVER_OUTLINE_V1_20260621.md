# Nollm Memory Takeover Outline V1

Date: 2026-06-23

This outline tracks the route from legacy OpenClaw memory ownership to a
Nollm-native active memory provider.

## Stages

- MT0: route split and baseline freeze
- MT1: archive ingest foundation
- MT2: native dream ingress
- MT3: native recall runtime
- MT4: OpenClaw runtime takeover
  - F0-01 Functional Alpha: standalone `@nollm/openclaw-memory` active memory
    provider with synthetic deterministic alpha field, private recall/capture,
    and no legacy fallback.
  - F1 Native Ingress Alpha: promote F0 capture receipts to native shards under
    R14-safe capability storage.
  - F2+ production hardening: multi-user isolation, durable ingress queue,
    cross-platform evidence, supported CLI validation.
- MT5: geometry causality upgrade
- MT6: legacy shutdown
- MT7: long-run hardening

## Current position (post F0-01)

F0-01 proves that Nollm can occupy the OpenClaw active memory slot without
legacy memory tools, without reading/writing `MEMORY.md`/`DREAMS.md`, and
without exposing Nollm geometry tools to Primary. It uses a synthetic field and
receipt-only capture. It does not claim production cutover.

## Relationship to companion mode

`nollm-memory-companion` remains a historical/experimental tool plugin. It is
not the active memory route. The active route is `@nollm/openclaw-memory`
(plugin id `nollm`, kind `memory`).
