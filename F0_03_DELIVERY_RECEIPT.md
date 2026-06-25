# F0-03 OpenClaw Memory Provider Host Truth Protocol Closure - Delivery Receipt

Date (UTC): 2026-06-24T09:50:00Z

## Bundle

| Item | Value |
| --- | --- |
| Filename | nollm_f0_03_openclaw_memory_provider_host_truth_protocol_closure_20260624T094500Z_review.bundle |
| Path | C:\Users\Administrator\Documents\Codex\2026-06-22\codex-resume-019eb778-55fc-7e41-ae6b-2\nollm_f0_03_openclaw_memory_provider_host_truth_protocol_closure_20260624T094500Z_review.bundle |
| SHA-256 | 07FDA74F2A0C512DDB63BEF959CC50BD24BE832F16E6C6D334EEE71853F4BFB6 |
| Size | 922723 bytes |

## Git refs in bundle

| Ref | SHA |
| --- | --- |
| feature/nollm-openclaw-memory-f0-03 | 395ae33522e159e5b00649d0c90e0ba7ddcc438e |
| evidence/f0-03-openclaw-memory-provider-20260624 | f6c678f25e01b26f300ce24e62f0e61d92a95ac1 |

## Repository checks

- git bundle verify: OK (exactly 2 refs)
- git diff --check: OK (no output)
- git fsck --full: completed with dangling objects from deleted scratch branches only; no corruption in bundled refs

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

## Test results

### TypeScript provider tests

cd integrations/openclaw/nollm-memory-provider && npm test

Result: 54/54 passed.

### Python alpha core tests

cd C:\Users\chaos\nollm && python -m pytest reference/python/tests/test_openclaw_memory_provider_alpha.py -x -q

Result: 25 passed.

### Host integration harness

cd integrations/openclaw/nollm-memory-provider && node scripts/host-integration-check.mjs

Result: all H1-H10 checks passed.

H1: plugin manifest declares kind=memory, id=nollm
H2: getMemoryCapabilityRegistration().pluginId === "nollm" (real OpenClaw API)
H3: memory-core not active (our runtime is registered)
H4: promptBuilder and flushPlanResolver are functions
H5: agent_turn_prepare hook executes via real OpenClaw hook runner
H6: agent_end hook executes via real OpenClaw hook runner
H7: no prohibited tools registered
H8: no model credentials required
H9: idempotent end behavior verified
H10: real OpenClaw plugin-sdk/memory-core APIs used, not mockApi

## F0-03 changes

### D1: Real OpenClaw host harness
- Replaced mockApi-based host loading with real OpenClaw plugin-sdk/memory-core APIs
- host-integration-check.mjs imports from openclaw/plugin-sdk/plugin-runtime and memory-core-host-runtime-core
- Uses initializeGlobalHookRunner, getGlobalHookRunner, getMemoryCapabilityRegistration, registerMemoryCapability, clearMemoryPluginState
- Exercises agent_turn_prepare and agent_end through real hook dispatcher

### D2: Total context budget
- Added maxContextCharacters config field for total rendered context budget
- validateContextEnvelope now limits warnings, boundaries, explicit_absences lengths
- Total formatted context (including header) is checked against maxContextCharacters
- Fresh facts trimmed to zero converts to freshness=none with explicit absence

### D3: Canonical capture identity
- Capture identity includes agent_id, session_id, run_id, success, canonical messages digest, field_revision_id
- success=true vs false produces distinct receipt identities
- Missing agent/session/run/success rejected
- Idempotent replay returns reused=true
- Receipt no longer stores request_id

### D4: Compatibility ref session binding
- Registry entries now bind agentId, sessionId, managerGeneration, fieldRevisionId, shardId, expiry
- readFile rejects cross-session replay
- search() validates sidecar output via validatePrepareResult before issuing refs

### D5: Python/TypeScript config parity
- Python ProviderConfig.from_payload now checks fixture containment (alphaFixturePath under nollmRepoRoot)
- Both sides enforce: absolute paths, fixture containment, segment-aware legacy path rejection

### D6: Evidence and remote
- Artifact hashes are real SHA-256 values (24/24 valid, no MISSING)
- Remote push honestly recorded as not_configured (no origin remote)
- Command evidence generated from real execution

## Known limitations

- FA-ISSUE-09: OpenClaw CLI plugins build/validate only accepts defineToolPlugin entries, rejecting correct memory plugin (upstream limitation, not provider bug)
- Remote push: git repository has no configured origin remote; push not attempted
- Node engine warning: OpenClaw requires Node >=22.19.0; test environment has Node 24.17.0 (satisfies requirement)

## What was not claimed

- Production memory takeover
- Historical MEMORY.md / DREAMS.md migration
- R14 capability-storage hardening
- Finished Cortex geometry recall
- Multi-user / untrusted workspace support
- Real user data processing