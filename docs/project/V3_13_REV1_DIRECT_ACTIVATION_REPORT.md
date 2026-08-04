# V3.13 Rev1 Direct Encounter Activation Execution Report

Date: 2026-08-04
Branch: `codex/aold-v313r1-direct-activation`
Report preparation tip: `845771893ee763d56a703ddb4a1f802ec42005bd`

## Authority and scope

The V3.13 Rev1 architecture, route, and execution task are the only active
authority. The implementation is limited to direct exact-text projection from
`FieldEncounterResult` to the current `Statement` during the current Host run.

No `MemoryActivationPacket`, formal Model Adapter module, activation epoch,
semantic index, derived activation cache, Core change, or additional Provider
call was introduced. Existing legacy paths remain present unless live coverage
proves them removable.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| 0-1 authority/baseline | PASS | clean branch, empty `AGENTS.md`, V3.13 docs and lifecycle registration |
| 2 Provider baseline | PASS | `D:\Nollm\artifacts\V3_13_REV1_BASELINE` |
| 3-4 direct activation/offline closure | PASS | targeted OpenClaw Python tests: 25 passed; Node tests cover direct activation |
| 5 real Direct Activation Live | NOT CLOSED | real Host/Provider probe returned `run_scope_unavailable` |
| 6 limited legacy exit | PASS WITH ZERO DELETIONS | one shared renderer documented; no path met `REMOVABLE_AFTER_LIVE` |
| 7 complete regression | PASS | Core/Snapshot/Trace/Access/OpenClaw/M0/GRF/Node and governance checks below |
| 8 report/status | THIS CHECKPOINT | this report and status ledger update |

## Provider baseline and post-stage comparison

Provider/model was `meituan/LongCat-2.0`, using an isolated Windows OpenClaw
Gateway and external state under `D:\Nollm\workspaces`. The pre-code matrix
contained relevant queries `10`, explicit NONE `5`, writes `12` (8 new, 2
reuse, 2 revision), mixed `8`, restarts `2`, and successful concurrency `2`.

| Metric | Baseline | Post-stage |
|---|---:|---:|
| valid Provider outputs / attempts | 43 / 43 | 38 / 38 |
| request wall p50 / p95 / max | 8107 / 28234 / 34518 ms | 10410 / 32000 / 37737 ms |
| final prompt UTF-8 bytes p50 / p95 / max | 51 / 101 / 116 | 56 / 106 / 116 |
| tool calls | 15 | 26 |
| direct activation responses | not applicable pre-stage | 0 in standard matrix |
| total observed Capture records | 43 | 81 |
| Capture states at snapshot | captured 43; processing 13; retryable 11 | captured 81; processing 25; retryable 22 |
| durable terminal commits in snapshot | 0 | none observed |

Baseline raw evidence reported zero byte-integrity failures and no duplicate or
orphan records in the observed Capture/evidence inventory. The post-stage
standard matrix retained raw JSON and did not produce a terminal Field
Encounter commit; it therefore cannot be used to claim durable Direct
Activation visibility.

## Real Host finding

The standard post-stage matrix initially did not expose
`nollm_field_encounter` to the main agent, so it produced zero direct
activation responses. In the isolated profile only, the tool was then added to
the main-agent allowlist and became visible in the Provider system prompt.

An explicit read-only probe made three tool calls over `31517 ms`. Each call
returned `run_scope_unavailable`. The OpenClaw `before_tool_call` context did
not supply a bindable run scope, so the tool could not reach the current
Statement projection. This is a real Host/plugin conformance blocker, not an
environment-unavailable exemption. The probe is retained at
`D:\Nollm\artifacts\V3_13_REV1_POST\direct-probe`.

The background Writer remained in `processing`/`retryable_defer` for the live
sample and produced no durable terminal Statement. Consequently the following
hard conditions are not claimed: one-entry live traversal, NONE exclusion,
query non-mutation through the live tool, direct activation query visibility,
or live zero duplicate/orphan proof.

## Offline and regression evidence

- The direct renderer reads current Statement values in returned handle order,
  applies fixed bounds, and keeps the result operation-local. Targeted offline
  activation tests passed: `25 passed`.
- Core: `88 passed`; Snapshot: `7 passed`; Trace: `3 passed`.
- Access: `150 passed`, with 8 existing deprecation warnings.
- OpenClaw Python: `96 passed`.
- M0: `45 passed`; hygiene/language/forbidden tests: `8 passed`.
- GRF: `112 passed`.
- Node: `npm ci` passed; `66` tests ran with `64 passed`, `2 skipped`, `0
  failed`; `npm run plugin:check` passed.
- Forbidden production scan found `0` matches for Packet, model-adapter,
  activation-epoch, model-identity, or Prefix/KV activation symbols.
- Ownership manifest: `843/843`, unclassified `0`; production boundary
  violations `0`; active-tree violations `0`; `compileall` exit `0`;
  `git diff --check` exit `0`; `git fsck --full` exit `0`.
- Root `AGENTS.md`: `0` bytes, SHA-256
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, Git
  empty-blob object `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391`.

## Delivery decision

The branch is pushed through the governance checkpoint at `84577189`. The
current implementation is offline-validated, but Direct Activation Live is
**not accepted as closed** because the real Host run-scope contract is missing.
No production path was deleted and main was not advanced on the basis of this
incomplete live gate. A final full-history bundle and the draft GitHub delivery
record must preserve this fail-closed status.

The current live evidence does not independently expose p50/p95/max timings
for local rendering or Capture-to-commit; only Provider request wall time and
prompt-byte measurements above are reported. Those unmeasured dimensions are
not fabricated.

## Evidence locations

- Baseline: `D:\Nollm\artifacts\V3_13_REV1_BASELINE`
- Post-stage: `D:\Nollm\artifacts\V3_13_REV1_POST`
- Final regression logs: `D:\Nollm\artifacts\V3_13_REV1_FINAL`
- Shared renderer/path map: `docs/architecture/module-ownership/DIRECT_ACTIVATION_PATH_MAP.md`
