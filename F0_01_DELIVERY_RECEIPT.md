# F0-01 OpenClaw Memory Provider Functional Alpha — Delivery Receipt

Date (UTC): 06/24/2026 03:29:51.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

## Bundle

| Item | Value |
| --- | --- |
| Filename | nollm_f0_01_openclaw_memory_provider_functional_alpha_20260623T192915Z_review.bundle |
| Path | C:\Users\Administrator\Documents\Codex\2026-06-22\codex-resume-019eb778-55fc-7e41-ae6b-2\nollm_f0_01_openclaw_memory_provider_functional_alpha_20260623T192915Z_review.bundle |
| SHA-256 | F7E72F26864294B621F3837C0266BFF11D558F9A8C390B434C1F93C77930E31E |
| Size | 893695 bytes |

## Git refs in bundle

| Ref | SHA |
| --- | --- |
| feature/nollm-openclaw-memory-f0-01 | e8b3c587a48e75bfebe14ef59ec0362d899ffb8c |
| evidence/f0-01-openclaw-memory-provider-20260623 | 7e370eb42eb54168a6d70483ca798f5f55814441 |

## Repository checks

- git bundle verify: OK
- git diff --check: OK (no output)
- git fsck --full: completed with dangling commits from deleted scratch branches only; no corruption in bundled refs

## Upstream baseline

| Property | Value |
| --- | --- |
| Repository | https://github.com/openclaw/openclaw |
| Commit | dc9c11be917ebdc711b956250aa80a8e5b47bea6 |
| Declared version | 2026.6.9 |

## Environment

| Property | Value |
| --- | --- |
| OS | Windows |
| Node | v24.17.0 |
| npm | 11.13.0 |
| Python | Python 3.14.6 |
| Shell | PowerShell |

## Commands run and results

### TypeScript provider tests

`powershell
cd integrations/openclaw/nollm-memory-provider
npm test
`

Result: exit code 0, 24/24 tests passed.

### Python alpha core tests

`powershell
$env:PYTHONPATH=\"C:\\Users\\chaos\\nollm\\reference\\python\"
python -m pytest reference/python/tests/test_openclaw_memory_provider_alpha.py -x -q
`

Result: exit code 0, 12 passed.

### Fixed OpenClaw integration harness

`powershell
cd integrations/openclaw/nollm-memory-provider
node scripts/integration-harness.mjs
`

Result: exit code 0.

Harness step summary:

- verify_upstream_commit: OK (dc9c11be917ebdc711b956250aa80a8e5b47bea6)
- node_modules_present: OK
- isolated_openclaw_profile: OK
- openclaw_build: OK (openclaw.mjs present)
- provider_build: OK
- openclaw_plugins_build: expected failure (tool-only CLI)
- openclaw_plugins_validate: expected failure (tool-only CLI)
- direct_sdk_load: OK (id=nollm, kind=memory, register=function, configSchema=object)

## Known Functional Alpha limitations

Documented in docs/issues/FUNCTIONAL_ALPHA_OPEN_ISSUES.md:

- FA-ISSUE-01: OpenClaw MemoryPluginRuntime backend discriminant is not extensible beyond builtin/qmd.
- FA-ISSUE-02: agent_end is fire-and-forget on persistent Gateway paths.
- FA-ISSUE-03: F0 uses deterministic keyword selection, not finished Cortex geometry recall.
- FA-ISSUE-04: R14 capability storage and archive transaction closure remain blockers for real migration.
- FA-ISSUE-05: Windows handle-equivalence and POSIX descriptor evidence are not complete.
- FA-ISSUE-06: Compatibility score is ordering-only and must not be read as vector relevance/trust.
- FA-ISSUE-07: No multi-agent sharing, multi-user isolation, or untrusted workspace support.
- FA-ISSUE-08: No native shard promotion from capture receipt until F1 Native Ingress Alpha.
- FA-ISSUE-09: OpenClaw CLI plugins build/validate only accepts defineToolPlugin entries, rejecting the correct memory plugin.

## What was not claimed

- Production memory takeover.
- Historical MEMORY.md / DREAMS.md migration.
- R14 capability-storage hardening.
- Finished Cortex geometry recall.
- Multi-user / untrusted workspace support.

## Notes

The evidence orphan branch contains only minimal synthetic evidence files:
README.md, upstream_baseline.json, commands_and_results.md,
functional_alpha_run.json, tool_surface_assertion.json,
legacy_access_assertion.json, artifact_hashes.json.

No real user memories, OpenClaw workspace, node_modules, build cache, or secrets
are included in the evidence branch or the bundle.
