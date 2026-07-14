# CAOLD Real Revision Loop Report

Date: 2026-07-14

## Status

`REAL_OPENCLAW_REVISION_LOOP_VALIDATED` for the bounded Windows/OpenClaw
scenario authorized by `NOLLM_CAOLD_REAL_REVISION_LOOP_TASK_20260713.md`.
This does not claim general semantic accuracy, long-term stability, release
readiness, security completion, or cross-provider portability.

## Access Boundary

- `AccessMemoryLoop` owns the Core lifecycle, Statement and Handle stores,
  bounded local Recall, Placement application, revision atomicity, and public
  cursor address mappings.
- The OpenClaw Python adapter imports `nollm_access` and has zero direct
  `nollm_core` imports in production or tests.
- Placement receives one new Statement, a finite cursor, finite local context,
  available Handles, and the allowed action schema. No Python semantic rule,
  global discovery, topic/entity index, graph, vector, or embedding was added.

## Initial And Revised Fact

- Initial Statement: `dream:7746cec189b0ba3edf885fdae7ab9b6457207d509b1bf509cbcca2d0133b5e87`.
- Initial Handle local atom ID: the same `dream:7746...5e87` identity.
- GeometryAddress: profile `eisenstein_exact_v1`, chart `default`, layer `0`,
  q `0`, r `0`, phase `null`.
- Initial Placement action: `new`; Core write count `1`.
- Natural correction Statement:
  `dream:88d6531a716181cf40791fc76d6e1809126dd3a0b145f928fb27a9eeacee34e3`.
- The real Placement LLM selected `revision_current`, reused the initial
  Handle, and performed one Core write.
- The final recovery Statement is
  `dream:006e69c2adff365553be0c3e0df54cb2044fc90488b05e5ef1ed032eed34b1e5`.
  It records that the controlled Friday proposal is void and Thursday 15:00
  remains current. The same Handle and GeometryAddress remain active.

## Atomic Failure And Recovery

A controlled `FileHandleStore.revise_current` failure was injected after the
natural correction. The binding remained on `dream:88d653...34e3`, the failed
proposal was absent from the StatementStore, Recall still returned only the
old current, and no orphan was left. Restoring the store method allowed a
subsequent revision. A later natural OpenClaw turn then revised that temporary
proposal to `dream:006e69...b1e5`, proving continued chat and successful
recovery without clearing data or disabling the plugin.

## Recall And Controls

- Session C selected only `dream:88d653...34e3`; the superseded Tuesday
  Statement ID was not selected or injected. The visible answer was Thursday
  at 15:00 and did not expose Nollm, Geometry, tools, or internal memory.
- After the recovery and another real Gateway restart, a fresh session selected
  only `dream:006e69...b1e5` and answered `Every Thursday at 3 PM` in Chinese.
- Equivalent duplicate Statement `dream:585ca4...dbf9` produced `reuse`, the
  original Handle, and `core_write_count=0`. It became supporting evidence and
  did not create a second current binding.
- Similar but distinct technical-review Statement `dream:5faf5c...5f9c`
  produced `new`, one Core write, and an independent current Handle.
- An unrelated arithmetic turn had no Recall injection (`promptChars=32`, the
  original prompt length). Formation returned `defer` with zero writes.

Final bindings contain exactly two current facts: the project meeting's final
Thursday revision and the separate Tuesday technical review. Superseded
Statement files may remain as immutable evidence but are not reachable as
current facts through the active project-meeting Handle.

## Restart, Plugin, And Data State

The Scheduled Task Gateway was stopped and started more than twice during the
scenario. The final restart reported a new start time, a successful
connectivity probe, and `0.0.0.0:18789` listening. The `nollm-formation` plugin
remains installed and enabled. The isolated v5 workspace and all earlier Nollm
workspaces were preserved; no Statement, Core, Handle, Cursor, or prior
OpenClaw data was cleared.

## Automated Evidence

- Access and OpenClaw Python tests: `94 passed`.
- Core, Snapshot, and Trace tests: `49 passed`.
- OpenClaw Node tests: `15 passed`.
- OpenClaw direct `nollm_core` imports: `0`.
- Ownership manifest: `1764` tracked, `unclassified=0`.
- Module boundary gate: `production=0`, `production_cycles=0`.

## Actual Vector And Completion

```text
CORE +5% | SNAPSHOT 0% | TRACE 0% | ACCESS +10% |
HISTORY 0% | AUDIT 0% | OPENCLAW +10% |
LAB +5% | DISTRIBUTIONS +5%
```

| Module | Actual | Lifecycle |
| --- | ---: | --- |
| CORE | 90% | `CAPABILITY_VALIDATED` |
| SNAPSHOT | 50% | `IMPLEMENTED` |
| TRACE | 40% | `IMPLEMENTED` |
| ACCESS | 100% | `CAPABILITY_VALIDATED` |
| HISTORY | 10% | `PROPOSED` |
| AUDIT | 10% | `PROPOSED` |
| OPENCLAW | 80% | `CAPABILITY_VALIDATED` |
| LAB | 85% | `IMPLEMENTED` |
| DISTRIBUTIONS | 65% | `IMPLEMENTED` |

