# HISTORICAL_INVALID_FOR_CONTENT_ADMISSION

This package is quarantined historical evidence. It rejects secret-shaped input,
uses stable-sentence promotion, and suppresses transient facts such as weather;
those policies violate the current content-neutral memory contract. It must not
be installed, activated, copied, or migrated into Capture, Formation, Admission,
or Recall. Its executable entry point fails closed.

# @nollm/openclaw-memory

Historical Nollm active memory provider for the closed OpenClaw W2-01 trial.

This package is **not** the historical `nollm-memory-companion`. The companion
remains an experimental tool surface that delegates to legacy `memory-core`.
This provider is the active memory-slot implementation selected by:

```json5
plugins.slots.memory = "nollm"
```

## Scope

- Single-user, local, Windows-native active memory trial.
- Private `agent_turn_prepare` recall from the W1 native companion store into `NOLLM_MEMORY_CONTEXT_V1`.
- Deterministic `agent_end` capture of explicit stable user sentences into the same native store.
- No Primary-visible memory tools and no Nollm geometry/navigation tools.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

## Non-goals

- Production multi-user cutover.
- Real historical memory migration.
- R14 capability-storage hardening.
- Finished Cortex geometry recall.

See `docs/integration/openclaw/NOLLM_OPENCLAW_RUNTIME_PLUGIN_READINESS_REVIEW.md`
and the local W2-01 trial report for runtime proof, known recall boundaries, and
rollback procedure.

## W2-01 status

- Active slot `plugins.slots.memory = "nollm"` is selected by OpenClaw Gateway.
- `agent_turn_prepare` calls the native sidecar `active-prepare` and injects a
  bounded `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` calls `active-capture` with a deterministic, narrow promotion policy.
- Rollback to `memory-core` is tested and documented.
- Legacy `MEMORY.md` / `memory/*.md` / `DREAMS.md` are preserved as observed
  confounds; the provider itself does not read or write them.

## W2-03 target-bound trial controller

`reference/python/scripts/run_openclaw_nollm_active_trial.py` is the W2-03
execution controller for the local active-memory trial. It is target-bound:

- `--openclaw-bin`, `--config`, `--workspace`, `--repo-root`, `--python-executable`,
  and `--out` must be absolute paths.
- OpenClaw commands always use the explicit `--openclaw-bin` plus
  `OPENCLAW_CONFIG_PATH`; there is no bare `openclaw` PATH fallback.
- `plan` and `diagnose` run before live mutation. `diagnose` writes a private
  diagnostic capsule and a redacted share zip.
- `apply` snapshots the current config, writes a staged config, validates it
  through the target OpenClaw binary, then atomically replaces the target config.
- Live mutation failures trigger automatic rollback from the private snapshot.
- `trial` uses the W2-03 markers `MIST-COPPER-81`, `PINE-EMBER-92`, and
  `RIVER-ONYX-03`; duplicate trial events are receipt-gated so replay does not
  inflate capture metrics.
- Raw logs, config backups, and full traces remain local-private. Sanitized
  evidence is published separately on an orphan evidence branch.

## W2-03R main-agent cutover

W2-03R targets the actual user-facing OpenClaw agent through
`--target-agent-id`; it must not create a parallel trial agent and call that a
main-agent cutover.

- `trialId` is controller-provided and passed unchanged to prepare/capture.
- `agent_turn_prepare` injects a memory persistence rule: the model must not
  claim a current-turn fact has already been permanently remembered unless that
  fact is already present in returned Nollm context.
- Capture receipts use claim/commit recovery so committed replay does not call
  remember again and does not inflate normal capture metrics.
- Short temporal reports such as `昆明今天下雨了。` are not promoted and must not
  become a location identity.
- Explicit temporal notes may be stored as notes with source
  `active_turn_explicit_v1`; they must not be rewritten into identity/location.
