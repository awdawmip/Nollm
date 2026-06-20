# OCP3 Live OpenClaw E2E Evaluation Runbook

This runbook reproduces the OCP3 live evaluation shape without committing raw runtime evidence.

## Preconditions

- OpenClaw CLI installed and logged in.
- Gateway service available locally.
- Current branch: `feature/openclaw-nollm-memory`.
- Run from the repository root.

## Steps

1. Create a run directory:

```powershell
$runId = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = "out\nollm_runtime\openclaw_live_eval\$runId"
New-Item -ItemType Directory -Force -Path "$runDir\workspace\memory"
```

2. Create the controlled corpus:

- `workspace/MEMORY.md`
- `workspace/DREAMS.md`
- `workspace/memory/2026-06-20.md`

Use the exact Atlas/Tessa/Mira corpus from the OCP3 task.

3. Capture environment evidence:

```powershell
openclaw --version
node --version
python --version
openclaw status --all
openclaw gateway status --json
openclaw health --verbose --json
openclaw plugins inspect memory-core --runtime --json
openclaw plugins inspect nollm-memory-companion --runtime --json
```

4. Install or refresh Nollm companion:

```powershell
python reference/python/scripts/install_openclaw_nollm_companion.py `
  --apply `
  --workspace "$runDir\workspace" `
  --repo-root . `
  --report-path "$runDir\installer_apply.json"
```

5. Create or refresh an isolated agent:

```powershell
openclaw agents add ocp3-nollm-eval `
  --workspace "$runDir\workspace" `
  --model kimi/kimi-for-coding `
  --non-interactive `
  --json
```

6. If remote embeddings fail, patch only the evaluation agent:

```json
{
  "agents": {
    "list": [
      { "id": "main" },
      {
        "id": "ocp3-nollm-eval",
        "name": "ocp3-nollm-eval",
        "workspace": "<runDir>/workspace",
        "agentDir": "C:/Users/Administrator/.openclaw/agents/ocp3-nollm-eval/agent",
        "model": "kimi/kimi-for-coding",
        "memorySearch": { "provider": "none", "fallback": "none" }
      }
    ]
  }
}
```

Then run:

```powershell
openclaw config patch --file <patch.json>
openclaw gateway restart
openclaw memory index --agent ocp3-nollm-eval --force --verbose
```

7. Run the agent matrix with `openclaw agent --agent ocp3-nollm-eval --json --timeout 180`.

Use Nollm disabled for baseline and enabled for the Nollm condition:

```powershell
openclaw plugins disable nollm-memory-companion
openclaw gateway restart

openclaw plugins enable nollm-memory-companion
openclaw gateway restart
```

8. For T7 only, run installer with `--enable-write-candidate` against a copied write-safety workspace. After T7, rerun installer without that flag to restore read-only default.

9. Generate:

- `agent_turn_summary.json`
- `scoring_report.json`
- `evidence_manifest.json`

Keep these under `out/nollm_runtime/openclaw_live_eval/<run_id>/`.

## Expected Result

- Baseline uses `memory-core` tools.
- Explicit Nollm T5 uses `nollm_memory_search` and `nollm_memory_get`.
- T7 uses `nollm_memory_write_candidate` and leaves durable source files unchanged.
- `value_hypothesis` is supported only when explicit Nollm tool use is proven.
