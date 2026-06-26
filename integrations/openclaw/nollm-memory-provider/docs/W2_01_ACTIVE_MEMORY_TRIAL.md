# W2-01 Direct Active Memory Trial

Owner-authorized empirical cutover of the OpenClaw memory slot to the `nollm` native active memory provider.

Deliver:

- `integrations/openclaw/nollm-memory-provider/` as active memory-slot owner.
- `agent_turn_prepare` recall from the W1 native companion store into a bounded `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` deterministic explicit stable-sentence capture into the same native store.
- Local-only redacted trial metrics and a tested rollback path.
- No Primary-visible Nollm memory tools in active mode.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md`.

Acceptance:

- `plugins.slots.memory` resolves to `nollm`.
- Real Gateway restart/reload succeeds with `nollm` loaded.
- Synthetic identity/preference/release markers are captured and recalled across real turns.
- Duplicate statements deduplicate; secret-like statements are rejected.
- Legacy source hashes are preserved; rollback to `memory-core` is proven.
- Workspace `MEMORY.md` bootstrap is recorded as a measured confound, not a blocker or silent assumption.

## Status

Trial result: `PARTIAL`. Active slot ownership, capture, and most recalls succeeded. Identity recall was confounded by legacy `MEMORY.md` workspace bootstrap. See the local trial report in `.local-runs/active-memory-w2/`.
