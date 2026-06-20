# OCP3 Live OpenClaw E2E Evaluation Report

Date: 2026-06-20
Branch: `feature/openclaw-nollm-memory`
Run id: `20260620_125416`
Evidence root: `out/nollm_runtime/openclaw_live_eval/20260620_125416/`

## Conclusion

Value hypothesis: `supported`, with limits.

The live OpenClaw Gateway evaluation proved that `memory-core` remains the memory-slot owner, the Nollm companion plugin is runtime-loaded as tool-only companion infrastructure, and actual agent turns can invoke both `memory-core` and Nollm tools. Nollm added an explicit drift/provenance calibration benefit in T5 without overriding source evidence or mutating durable memory.

Autonomous Nollm adoption was not observed in T6; the agent used `memory-core` only unless Nollm was named explicitly.

## Environment

- OpenClaw: `OpenClaw 2026.6.8 (844f405)`
- Node: `v24.17.0`
- Python: `Python 3.14.6`
- Evaluation agent: `ocp3-nollm-eval`
- Evaluation workspace: `out/nollm_runtime/openclaw_live_eval/20260620_125416/workspace`
- Write-safety workspace: `out/nollm_runtime/openclaw_live_eval/20260620_125416/workspace_write_t7`

## Runtime State

- `memory-core` runtime loaded with `memory_search` and `memory_get`.
- `nollm-memory-companion` runtime loaded with `nollm_memory_search`, `nollm_memory_get`, `nollm_memory_status`, and optional `nollm_memory_write_candidate`.
- `memory-core` remained the selected memory slot.
- Nollm remained a companion tool plugin, not a `kind: "memory"` plugin.

## Repairs

1. Installer subprocess hardening:
   - Added Windows process-tree termination on CLI timeout.
   - Prevents hung `openclaw.cmd -> node` child processes during runtime inspection.

2. Tool exposure:
   - Installer now writes Nollm read tools to `tools.alsoAllow`.
   - This preserves the normal OpenClaw core tool set while exposing optional companion tools.

3. Python runtime path:
   - Installer now writes `pythonCommand` as the absolute current interpreter path.
   - This fixed Gateway service failures where `python3` was not on PATH.

4. Baseline memory repair:
   - Initial `memory-core` index failed because OpenAI embeddings returned `insufficient_quota`.
   - The evaluation agent only was patched to `memorySearch.provider: "none"` / `fallback: "none"`.
   - `memory-core` then indexed via FTS and returned controlled corpus results.

## Test Results

| Test | Condition | Tool proof | Result |
| --- | --- | --- | --- |
| T1 rollback key | Baseline | `memory_get` | Correct: `TESSA-17` |
| T2 ownership | Baseline | `memory_search`, `read` | Correct: Tessa Lin, durable memory authoritative |
| T3 Mira connection | Baseline | `memory_search`, `read` | Correct: speculative investigation only |
| T4 birthday absence | Baseline | `memory_search` | Correct: not recorded |
| T1 rollback key | Nollm condition | `memory_get` | Correct |
| T2 ownership | Nollm condition | `memory_search`, `read` | Correct |
| T3 Mira connection | Nollm condition | `memory_search`, `memory_get`, `read` | Correct |
| T4 birthday absence | Nollm condition | `memory_search`, `memory_get` | Correct |
| T5 Nollm calibration | Nollm explicit | `nollm_memory_search`, `nollm_memory_get` | Correct; drift labels treated as navigation only |
| T6 autonomous adoption | Nollm available | `memory_search`, `memory_get`, `read` | Correct answer, no autonomous Nollm adoption |
| T7 write safety | Nollm write enabled | `nollm_memory_write_candidate` | Pending candidate only; durable files unchanged |

## Safety

- No external delivery was requested.
- `nollm_memory_write_candidate` created a pending record only.
- `MEMORY.md`, `DREAMS.md`, and `memory/*.md` hashes were unchanged in T7.
- `drift_class` was not mapped to trust/status and was not used as a hard rejection rule.

## Evidence

- `environment.json`
- `commands.jsonl`
- `gateway_status_before.json`
- `memory_status_ocp3_repair1.json`
- `memory_search_ocp3_repair1.json`
- `baseline_T1_agent.json`
- `baseline_T4_retry_agent.json`
- `nollm_T5_pythonfix_agent.json`
- `nollm_T7_agent.json`
- `agent_turn_summary.json`
- `scoring_report.json`
- `evidence_manifest.json`

Evidence manifest SHA-256: `e46ecdf1fd2173bedc781a44354f774ef6c7c9c00b0c8f5dc2d5d354c9f54ad5`

## Limitations

- OpenClaw automatically injected `MEMORY.md` into the agent prompt; tool summaries still prove tool calls, but this is a comparison confounder.
- Nollm adoption was explicit, not autonomous.
- The valid baseline used OpenClaw's documented FTS-only memory mode because remote OpenAI embeddings were quota-blocked.
