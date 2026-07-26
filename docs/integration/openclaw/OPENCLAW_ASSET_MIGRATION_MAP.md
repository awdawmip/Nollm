# OpenClaw Asset Migration Map

| Asset | Classification | AOLD use |
| --- | --- | --- |
| `integrations/openclaw/formation-loop` | ACTIVE | Capture, Tool Evidence, content-neutral Writer, Cartographer, Access apply, and progressive Recall |
| `formation-loop/adapter.py` | OFFLINE_MIGRATION | Legacy Formation contract; `public_api=none`; imported only by `legacy_bridge.py` |
| `formation-loop/dream_adapter.py` | OFFLINE_MIGRATION | Legacy Dream JSON contract; `public_api=none`; imported only by `legacy_bridge.py` |
| `formation-loop/sculptor.py` | OFFLINE_MIGRATION | Legacy Dream Sculptor; `public_api=none`; imported only by `legacy_bridge.py` |
| `nollm-memory-provider` | HISTORICAL_INVALID | Uninstalled; `public_api=none`; not imported or revived |
| `nollm-memory-companion` | EXPORT_ONLY_REFERENCE | Uninstalled; `public_api=none`; no Formation import |
| `grf-adapter` | OFFLINE_MIGRATION | Uninstalled; `public_api=none`; no active Placement/Recall import |
| `lab/nollm-lab/statement_formation` | LEGACY_REFERENCE / parser regression | Deterministic contracts only; not model-quality evidence |
| `lab/nollm-lab/openclaw_formation` | ACTIVE_VALIDATION | Real calls, reviews, prompts, failures, metrics |

The active dependency is OpenClaw Runtime -> durable Capture/Tool Evidence -> content-neutral Writer/Cartographer -> public `nollm_access` contracts. Legacy Formation modules are reachable only through `legacy_bridge.py` with `offline_migration=true`.
