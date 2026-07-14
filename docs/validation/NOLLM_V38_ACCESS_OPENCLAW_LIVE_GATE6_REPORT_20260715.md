# Nollm V3.8 Access/OpenClaw Live Gate 6 Report

**Date**: 2026-07-15
**Branch**: `codex/caold-translation-covariant-physical-coverage-reuse`
**Input HEAD**: `ac8ebaa44cda35e1d2f73e0bfc95055bae425a86`
**Result**: `IN_PROGRESS`

## Controlled Migration

The V3.7 workspace remains unchanged at:

```text
C:\Users\Administrator\.openclaw\memory\nollm-caold-rotated-physical-field-v1
```

The migration tool created a separate V3.8 workspace at:

```text
C:\Users\Administrator\.openclaw\memory\nollm-caold-translation-covariant-v1
```

The migration changed only the Core geometry registry identity. It retained all
GeometryAddress values and copied Access bindings and MemoryStatement files
byte-for-byte. The source and target statement-tree digest is:

```text
c7d1cd681f1b9af74dd277ea6bb53c801568aa865f3d79a6c24da9f6f3a06c30
```

The migration receipt SHA-256 is:

```text
87659f09ae70a3737529d925e5bf18891482519fa69064409f3e4def0cf511f2
```

## Plugin And Gateway

The plugin is version `0.8.0`, uses Surface Wire `single-entry-v3-path`, and
requires geometry contract
`nollm_translation_covariant_physical_coverage_v1`. Gateway health and plugin
inspection succeeded after restart. The restart command timed out while waiting
for its own readiness response, but the replacement Gateway process was healthy
and loaded the plugin from this worktree.

Selected Recall paths are exposed only as observational metadata. Every path is
bound to a selected statement and carries `path_is_not_truth_proof=true`.

## Live Results

| Run | Session | Result | Evidence SHA-256 |
|---|---|---|---|
| R1 | `caold-v38-r1-20260715` | Alpha facts recalled; hidden injection | `4a8f6bd9f14e64e9ec18ba921423f76a1f66b239f48bda42cad4e57df7e89567` |
| R2 | `caold-v38-r2-20260715` | visitor desk and cafe facts recalled; hidden injection | `0cd1b65dc031f8b76298bd484bdcc5dfa25433fd5e0bcd8427543932861d4480` |
| R3 | `caold-v38-r3-20260715` | unrelated question produced `completed_none` | `f0f4fcb1b930dfab4f8553cf3e5d926ee0cfe0b47eb2de6ed173f5e6db328baf` |
| controlled cross-layer | `caold-v38-cross-layer-20260715` | layer-0 entry selected only the layer-1 target and returned `TC-3817` | `385d5fa4f86931852de996b2370d672adf85fe75613a89804b36d8246f528faf` |

The controlled fixture SHA-256 is:

```text
2f549fd7c50d2ec4cd2948ba47f708a107caa937c371f8c498905ce0b9fa07ee
```

The fixture contains no bridge or lateral relation. Its required Core path is
`coverage_down`. The successful Live run selected the explicit entry at layer 0
and the target at layer 1. A later run after adding the observational
`selected_paths` event field returned `completed_none`; therefore no path-bearing
Live event is claimed. The Gate 5 deterministic fixture remains the direct path
witness.

## Incomplete P1

P1 was attempted twice:

```text
caold-v38-p1-20260715
caold-v38-p1-retry-20260715
```

Both attempts produced a unique Formation statement but did not reach
`placement_apply` within five minutes. No HandleBinding or Core placement was
written. The attempts were not retried further and no evidence was fabricated.

Consequently Gate 6 is not fully closed. This delivery must use:

```text
CAOLD_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_REUSE_IN_PROGRESS_AT_<HEAD>
```
