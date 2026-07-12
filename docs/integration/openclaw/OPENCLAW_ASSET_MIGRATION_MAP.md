# OpenClaw Asset Migration Map

| Asset | Classification | AOLD use |
| --- | --- | --- |
| `integrations/openclaw/formation-loop` | ACTIVE | Explicit Statement Formation tool and strict Access bridge |
| `nollm-memory-provider` | LEGACY_REFERENCE | Uninstalled from host; not imported or revived |
| `nollm-memory-companion` | LEGACY_REFERENCE | Uninstalled from host; no tool reused |
| `grf-adapter` | LEGACY_REFERENCE | Uninstalled from host; no Placement/Recall capability reused |
| `lab/nollm-lab/statement_formation` | LEGACY_REFERENCE / parser regression | Deterministic contracts only; not model-quality evidence |
| `lab/nollm-lab/openclaw_formation` | ACTIVE_VALIDATION | Real calls, reviews, prompts, failures, metrics |

The active dependency is OpenClaw Runtime -> Formation adapter -> public `nollm_access` Formation contract. There is no Core write, Geometry address, Placement, Recall, native memory store, lexical search, or automatic promotion path.
