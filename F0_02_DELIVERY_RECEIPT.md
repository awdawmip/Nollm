# F0-02 OpenClaw Memory Provider Functional Alpha Closure - Delivery Receipt

Date (UTC): 2026-06-24T03:25:14Z

## Bundle

| Item | Value |
| --- | --- |
| Filename | nollm_f0_02_openclaw_memory_provider_functional_alpha_closure_20260624T032514Z_review.bundle |
| Path | C:\Users\Administrator\Documents\Codex\2026-06-22\codex-resume-019eb778-55fc-7e41-ae6b-2\nollm_f0_02_openclaw_memory_provider_functional_alpha_closure_20260624T032514Z_review.bundle |
| SHA-256 | 68502BEB666FEA405EF09BDEC4AF341FA310AC82E6ADFB4719E390DF5A017F8F |
| Size | 914793 bytes |

## Git refs in bundle

| Ref | SHA |
| --- | --- |
| feature/nollm-openclaw-memory-f0-02 | fb8b56d905f704cb7eb00fde0e0721a4ce20bbe1 |
| evidence/f0-02-openclaw-memory-provider-20260624 | 5e36727395ab95f3ae6d1c744beefb0b83c588d3 |

## Repository checks

- git bundle verify: OK (exactly 2 refs)
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

`cd integrations/openclaw/nollm-memory-provider && npm test`

Result: exit code 0, 54/54 tests passed.

### Python alpha core tests

`="reference\python"; python -m pytest reference/python/tests/test_openclaw_memory_provider_alpha.py -x -q`

Result: exit code 0, 25 passed.

### Integration harness

`="<path>"; cd integrations/openclaw/nollm-memory-provider && node scripts/integration-harness.mjs`

Result: exit code 0.

Harness step summary:

- verify_upstream_commit: OK
- node_modules_present: OK
- isolated_openclaw_profile: OK
- openclaw_build: OK
- provider_build: OK
- openclaw_plugins_build: expected failure (tool-only CLI, FA-ISSUE-09)
- openclaw_plugins_validate: expected failure (tool-only CLI, FA-ISSUE-09)
- host_integration_load: OK (H1-H8 all pass)

## Remote push status

No git remote is configured on this repository. Remote push was not possible. This is documented honestly in evidence/remote_push_receipt.json. No remote or auth failure is reported as success.

## What was fixed in F0-02

- D1: Context validation boundary with secondary prompt budget enforcement
- D2: Latest-user text extraction and runtime identity (agentId/sessionId/runId from ctx, not api.id)
- D3: Opaque revision-bound compatibility references via NollmCompatibilityReferenceRegistry
- D4: Idempotent capture receipts with stable identity (no Date.now/request_id in receipt_id), recursive secret redaction, metadata-only receipt_only mode
- D5: Segment-aware legacy path rejection (TS and Python) replacing substring matching
- D6: Integration harness rewritten with NOLLM_OPENCLAW_CHECKOUT env var, Node engine gate, H1-H8 host loading checks
- D7: Adapter docs test oracle updated, load_field_head missing-root returns None

## Known limitations

- FA-ISSUE-09: OpenClaw CLI plugins build/validate only accepts defineToolPlugin entries, rejecting correct memory plugin (FA-ISSUE-09)
- No git remote configured; remote push not performed
- Compat refs are process-local and expire on restart in Functional Alpha
- No production cutover, historical memory migration, or R14 completion claimed