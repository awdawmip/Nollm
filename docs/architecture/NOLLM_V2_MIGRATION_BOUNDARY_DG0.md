# Nollm V2 Migration Boundary DG0

Status: DG0 migration boundary. This document classifies existing modules without migrating, replacing, deleting, or runtime-integrating them.

## Existing Module Classification

| Existing path | DG0 classification | Principle |
| --- | --- | --- |
| `reference/python/nollm/geometry.py` | later-adapt | D1 pure geometry concepts may inform DG1, but DG0 does not import or wrap it. |
| `reference/python/nollm/coverage.py` | do-not-reuse-without-review | Existing coverage is tied to current native publication behavior and must not become V2 coverage kernel by name reuse. |
| `reference/python/nollm/chart_gluing.py` | later-adapt | May inform future transform validation, but V2 groupoid rules require independent tests first. |
| `reference/python/nollm/gravity.py` | do-not-reuse-without-review | V2 gravity is internal Field potential, not an exposed anchor or selector. |
| `reference/python/nollm/dream_placement.py` | do-not-reuse-without-review | Placement is not authorized in DG0; later use requires explicit DG task. |
| `reference/python/nollm/dream_shard.py` | later-adapt | Evidence concepts may map to Dream Shard, but no data migration occurs in DG0. |
| `reference/python/nollm/recall.py` | retain-as-legacy | Existing recall remains V1 legacy scale scan and is not replaced by V2. |
| `reference/python/nollm/cortex.py` | retain-as-legacy | Existing Cortex guidance remains V1 behavior; V2 compiler fixtures are future DG3 work. |
| `reference/python/nollm/openclaw_*.py` | retain-as-legacy | OpenClaw paths are frozen legacy/runtime paths for DG0. |
| `reference/python/nollm/native_field.py` | retain-as-legacy | Native memory/publication state is not read, written, or migrated in DG0. |
| `integrations/openclaw/` | retain-as-legacy | No plugin, sidecar, provider, install, trial, or rollback operation is authorized in DG0. |

## No-Migration List

DG0 does not migrate cards, anchors, native stores, ledgers, recall digests, OpenClaw memory, sidecar configuration, plugin settings, trial artifacts, rollback files, or historical `MEMORY.md` / `DREAMS.md` content.

DG0 does not replace V1 imports with V2 imports. DG0 does not connect V2 to CLI, JSON tools, OpenClaw, agent runtime, or memory write paths.

## Gates Before V2 May Touch V1

- DG1 must verify pure chart, transform, and directed coverage-kernel behavior without runtime.
- DG2 must verify Trace, Cover, and internal gravity without external visibility.
- DG3 must validate Cortex proposal fixtures without fact confirmation.
- DG4 must prove Query Probe recall on synthetic evidence without OpenClaw.
- DG6 must define adapter isolation and receipts before any external shell exists.
- DG7 must provide positive runtime evidence only after DG0-DG6 pass.

## Legacy Anchor Principle

Legacy `anchor_fields`, `anchors_used`, and related labels are history and diagnostics only. They may help explain old data or migration candidates, but they must not become V2 external recall selectors, query parameters, or visible gravity wells.

## W2 And OpenClaw Freeze

W2/OpenClaw provider, plugin, sidecar, active memory, trial, rollback, and native memory paths remain frozen for DG0. No operation in DG0 is allowed to fix, test, deploy, enable, or modify them.
