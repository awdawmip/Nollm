 # Nollm F0-04 Real OpenClaw Loader Capture Contract Closure
 ## Delivery Receipt

 **Date**: 2026-06-25
 **Project branch**: `feature/nollm-openclaw-memory-f0-04-20260625T060048Z`
 **Evidence branch**: `evidence/f0-04-openclaw-memory-provider-20260625T060048Z`
 **Review input**: `nollm_f0_03_openclaw_memory_provider_host_truth_protocol_closure_20260624T094500Z_review.bundle`

 ---

 ## Delivered bundle

 ```text
 nollm_f0_04_real_openclaw_loader_capture_contract_closure_20260625T060351Z_review.bundle
 ```

 - SHA-256: `33CB9B5A79BA2B7F7A5E24D1C4933359AFAA70BB4BF775415C8BC968548B317D`
 - Size: 958555 bytes

 ## Bundle verification

 ```text
 git bundle verify: PASS
 git fsck --full --no-reflogs: PASS
 ```

 Bundle refs:

 ```text
 refs/heads/feature/nollm-openclaw-memory-f0-04-20260625T060048Z 820b0e7e94081b42c1c26380bfd5f3ac75de5646
 refs/heads/evidence/f0-04-openclaw-memory-provider-20260625T060048Z 02053e2266a12791b965e6f6e48d9cc990f6b884
 ```

 ## Test results

 | Suite | Command | Result |
 |---|---|---|
 | TypeScript provider tests | `npm test` | 64 passed, 0 failed |
 | Python provider tests | `python -m pytest tests/test_openclaw_memory_provider_alpha.py tests/test_openclaw_memory_adapter_docs.py tests/test_native_field.py -v` | 34 passed, 0 failed |

 ## Real OpenClaw loader integration

 The integration harness was run against fixed upstream commit `dc9c11be917ebdc711b956250aa80a8e5b47bea6`.

 **Result**: `target_limitation` — `OPENCLAW_LOADER_LOCAL_MEMORY_PLUGIN_LIMITATION`.

 `loadOpenClawPlugins` is not exported from any checked public OpenClaw entry point:
 - `openclaw/package-main`
 - `openclaw/plugin-sdk/index`
 - `openclaw/plugin-sdk/plugin-runtime`
 - `openclaw/plugin-sdk/plugin-entry`

 No mock, internal-chunk, or hand-rolled registry proof was substituted. The honest F0-04 result is that real host loader integration is blocked by the missing upstream public seam. Upstream issue seeds:
 - `docs/integration/openclaw/issues/FA-ISSUE-10-loader-local-memory-plugin.md`
 - `docs/integration/openclaw/issues/FA-ISSUE-11-memorysearchmanager-caller-context.md`

 - `docs/integration/openclaw/issues/FA-ISSUE-11-memorysearchmanager-caller-context.md`

 ## Provisioning note

 The harness provisions a fresh checkout of the fixed upstream commit. On this run, `npm ci` failed because the upstream `package-lock.json` is out of sync with `package.json`; dependencies were installed with `npm install` so the build and loader-discovery steps could execute. This is recorded in the harness output as `npm_ci: skipped, reason: node_modules present`.

## Remote status

 `origin` is not configured.

 ```text
 git remote get-url origin: error: No such remote 'origin'
 git push origin feature/...: fatal: 'origin' does not appear to be a git repository
 git push origin evidence/...: fatal: 'origin' does not appear to be a git repository
 ```

 ## Project branch commits

 ```text
 820b0e7 f0-04-08 evidence: include new artifacts in evidence generation
 49437e3 f0-04-05 compat: state manager-scoped ref semantics and add FA-ISSUE-11
 bf2464a f0-04-07 tests: capture race, identity fallback, incomplete identity skip
 4ceb5ff f0-04-04 capture: Python canonical v2 authority, TS no duplicate authority, atomic O_EXCL receipt publish, identity fail-close and event fallback
 ea8002b f0-04-08b evidence: resolve npm/python .cmd shims on Windows
 ```

 ## F0-04 contract gaps closed in this delivery

 - **D4 capture identity authority**: TypeScript no longer computes or caches its own `event_hash`; it forwards the strict v2 event to the Python sidecar and accepts the returned canonical `receipt_id`. Python validates strict input (messages list, boolean success, non-empty agent/session/run), computes the canonical event hash including `field_id` and `field_revision_id`, and returns the canonical receipt.
 - **D5 atomic receipt publish**: Python creates receipt files with `O_CREAT | O_EXCL` for no-clobber atomic publish; duplicate events fall through to a reuse path, and corrupt existing receipts are quarantined rather than overwritten.
 - **D3 durable identity fail-close**: `agent_end` now rejects capture when `sessionId` or `runId` is missing; `agent_turn_prepare` already rejected incomplete identity. `resolveNollmTurnIdentity` uses `event.runId` and `event.sessionId` as fallbacks when the hook context is missing them.
 - **D6 compatibility scope honesty**: the adapter design document now explicitly describes compatibility refs as process-local, manager-scoped, agent-scoped, and revision-bound—not session-bound—and upstream issue `FA-ISSUE-11` documents the missing `MemorySearchManager.readFile()` caller/session context.
 - **D7 TS/Python fixture parity**: both sides already canonicalize fixture paths with `realpath`/`resolve()`; the new test matrix covers symlink escape, missing file, and inside-root acceptance.
 - **D8 auto-generated evidence**: `generate-f0-04-evidence.mjs` records actual command argv, exit code, stdout/stderr SHA-256, parsed test counts, harness result, artifact hashes, and remote push state.

 ## Delivery label

 `local-bundle-complete / remote-push-pending-not-configured`

 ## Scope confirmation

 The following remain out of scope as required:
 - legacy MEMORY.md recall fallback
 - companion deletion
 - Primary-visible Nollm geometry tools
 - real memory migration
 - production cutover
 - R14 full SafeRoot rewrite
 - OpenClaw checkout/node_modules vendoring
 - fake host success claim
 The integration harness was run against fixed upstream commit `dc9c11be917ebdc711b956250aa80a8e5b47bea6`.

 **Result**: `target_limitation` — `OPENCLAW_LOADER_LOCAL_MEMORY_PLUGIN_LIMITATION`.

 `loadOpenClawPlugins` is not exported from any checked public OpenClaw entry point:
 - `openclaw/plugin-sdk/plugin-entry`

 No mock, internal-chunk, or hand-rolled registry proof was substituted. The honest F0-04 result is that real host loader integration is blocked by the missing upstream public seam. Upstream issue seeds:
