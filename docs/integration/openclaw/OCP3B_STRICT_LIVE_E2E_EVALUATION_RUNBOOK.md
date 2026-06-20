# OCP3b Strict Live E2E Evaluation Runbook

This runbook records the strict OpenClaw live E2E procedure used for OCP3b.

## Preconditions

- Use branch `feature/openclaw-nollm-memory`.
- Keep `memory-core` as the selected OpenClaw memory slot.
- Keep Nollm as a companion tool plugin only.
- Use an isolated controlled workspace, not production user memory.
- Do not allow direct `read` to substitute for memory retrieval.

## Environment Capture

Run and save sanitized output:

```powershell
openclaw --version
node --version
python --version
openclaw config file
openclaw config validate
openclaw gateway status --deep --require-rpc --json
openclaw plugins inspect memory-core --runtime --json
openclaw plugins inspect nollm-memory-companion --runtime --json
```

Discover log syntax with:

```powershell
openclaw logs --help
```

## Controlled Corpus

Create a runtime workspace under ignored `out/` with:

- `MEMORY.md`: authoritative Atlas owner and rollback credential.
- `memory/YYYY-MM-DD.md`: supporting daily context and explicit negative fact.
- `DREAMS.md`: speculative Mira Chen lateral note that is not ownership evidence.
- `AGENTS.md`: local instruction to use memory tools and avoid inference.

Record SHA-256 hashes before any scored run.

## Agent Controls

Create two read-only evaluation agents:

- `ocp3b-baseline`: `memory_search`, `memory_get` only.
- `ocp3b-nollm`: memory-core tools plus `nollm_memory_search`, `nollm_memory_get`, and `nollm_memory_status`.

Both agents must use:

- same workspace;
- same model;
- `contextInjection: "never"`;
- `bootstrapMaxChars: 1`;
- `bootstrapTotalMaxChars: 1`;
- direct tool deny list containing `read`, `exec`, `process`, `edit`, `write`, `apply_patch`, `web_search`, and `web_fetch`;
- fresh sessions for each scored turn.

Validate and restart:

```powershell
openclaw config validate
openclaw gateway restart
openclaw memory index --agent ocp3b-baseline --force --verbose
openclaw memory index --agent ocp3b-nollm --force --verbose
```

## Scored Matrix

Run fresh Gateway agent turns:

- B1: durable Atlas owner and credential.
- B2: daily supporting context.
- B3: speculative DREAMS item classification.
- B4: negative query answered as not recorded.
- N1-N4: same classes with memory-core first and Nollm enrichment.
- N5: explicit Nollm calibration requiring Nollm search/get.
- N6: autonomous adoption with Nollm tools available but unnamed.
- N7: write safety in a copied workspace with `nollm_memory_write_candidate` enabled.

Reject any scored retrieval turn that calls `read`, lacks memory-core tool calls, or has workspace context injection.

## Evidence Package

Commit a sanitized package under:

```text
docs/integration/openclaw/evidence/ocp3b_<run_id>/
```

The package must include the manifest, config proof, runtime plugin inspect summary, source hashes, agent turn summary, tool trace JSONL, scoring report, and bounded log excerpt.

Validate with:

```powershell
python reference/python/scripts/validate_ocp3b_live_e2e_evidence.py docs/integration/openclaw/evidence/ocp3b_<run_id>
```

Only conclude `value_hypothesis: supported` when a valid baseline, valid Nollm trace, safety, correctness, and measurable added value are all backed by committed evidence.
