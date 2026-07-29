# V3.12 Field Encounter Asset Reallocation

Date: 2026-07-29

Vector:

```text
C0 | S0 | T0 | A+15 | H0 | U0 | O+15 | L+15 | D+5
```

This inventory classifies current behavior and state ownership rather than file
names. No listed implementation is removable until the unified replacement is
active and its equivalence tests pass.

| Asset | Current behavior/ownership | Classification | V3.12 destination |
| --- | --- | --- | --- |
| `packages/nollm-access/src/nollm_access/surface_navigation.py` | Access projection over public Core Surface, one physical entry, bounded Recall | `REUSE_SHARED` | Shared structural navigation beneath Field Encounter |
| `packages/nollm-access/src/nollm_access/surface_selection.py` | Separate Recall/Placement budgets over one Core Surface | `MOVE_TO_ENCOUNTER` | One operation-neutral Encounter policy; old constants remain migration input |
| `packages/nollm-access/src/nollm_access/cartography.py` | Prompt-bounded progressive Atlas pages, structural region identity, Local detail | `REUSE_SHARED` | Encounter root/region pages and finite Locality facts |
| `AccessMemoryLoop.build_progressive_atlas/open_progressive_region` | Complete progressive field projection with state-bound fingerprints | `REUSE_SHARED` | One root/page implementation for query, proposition, and mixed stimuli |
| `AccessMemoryLoop.local_detail_page/bounded_locality` | Current Statement projection after structural selection | `ADAPT_RECALL` | `EncounterFactCard` projection in the selected Locality |
| `AccessMemoryLoop.placement_candidates` | Existing/lateral/frontier candidates; split Placement envelope | `ADAPT_PLACEMENT` | Geometry input only; active selection moves to visible vacancy cards |
| `CoreRuntime.junction_candidates` | Geometry-only empty candidate ranking, capacity/boundary/free faces | `REUSE_SHARED` | Local, boundary, and neutral vacancy generation |
| `CoreRuntime.relation_group_junction_candidates` | Realized multi-group geometry candidates | `REUSE_SHARED` | `JUNCTION_VACANCY`; `all_groups_realized` remains mandatory |
| `packages/nollm-access/src/nollm_access/recall.py` | Canonical single consistent read from explicit entry cells | `REUSE_SHARED` | Fact contact readback after one selected entry |
| `packages/nollm-access/src/nollm_access/placement_contract.py` | LLM-owned reuse/revision/new decisions and provisional confirmation | `ADAPT_PLACEMENT` | Encounter effect resolver and exact fact/vacancy terminal binding |
| `packages/nollm-access/src/nollm_access/runtime.py` | Cross-store atomic mutation and rollback under Core/Access coordination | `REUSE_SHARED` | Conditional state-bound commit; stale must be zero-write |
| Statement, Handle, Evidence, provenance stores | Canonical persistent Access state and exact source mapping | `REUSE_SHARED` | Persistent state remains unchanged; operation pages/IDs are never persisted |
| `integrations/openclaw/formation-loop/python/.../main_agent_recall.py` | Main-run single-entry Recall-specific tool path | `ADAPT_RECALL` | Main agent uses the common `nollm_field_encounter` Wire |
| `integrations/openclaw/formation-loop/python/.../cartographer.py` | Writer then separate Cartographer semantics and Placement navigation | `ADAPT_PLACEMENT` | Formation continues in the same Host session into Field Encounter |
| `integrations/openclaw/formation-loop/python/.../memory_loop.py` | Split Recall traversal and apply orchestration | `MOVE_TO_ENCOUNTER` | One run-scoped Encounter operation store and terminal resolver |
| `integrations/openclaw/formation-loop/python/.../legacy_cartographer.py` | Explicit legacy parser/migration compatibility | `LEGACY_MIGRATION` | Offline migration reference only; never active fallback |
| `integrations/openclaw/formation-loop/python/.../adapter.py` and `bridge.py` | Python bridge and active Host command surface | `MOVE_TO_ENCOUNTER` | One strict Encounter command envelope |
| `integrations/openclaw/formation-loop/src/index.ts` | OpenClaw hook/tool registration and worker lifecycle | `MOVE_TO_ENCOUNTER` | Register one main-agent Encounter tool and one Writer session continuation |
| `integrations/openclaw/formation-loop/src/capture.ts` | Immutable Raw Capture and append-only absorption progress | `REUSE_SHARED` | Capture remains zero-semantic and unchanged |
| Capture state, Tool Evidence, continuation modules | Per-Capture exact evidence and retry state | `REUSE_SHARED` | Pending proposition provenance and retryable Encounter defer |
| Existing Recall/Cartography Python tests | Split-path conformance and historical regression | `LEGACY_MIGRATION` | Retained while unified tests prove equivalent required behavior |
| `lab/nollm-lab/**` | Deterministic geometry/provider fixtures and bounded evidence | `MOVE_TO_ENCOUNTER` | Query/write/mixed, vacancy, session-count, latency, and negative matrices |
| `distributions/nollm-openclaw/manifest.json` | Writer v4, Cartographer v2, Recall v1/v2 active profile | `MOVE_TO_ENCOUNTER` | V3.12 Encounter wires, budgets, single-session policy, legacy inactive truth |
| Frozen Provider evidence | Immutable prior capability observations | `UNRELATED` | Preserved unchanged; not relabeled as V3.12 Live evidence |

## Replacement Rules

- The active implementation uses the existing Core Surface and Core mutation
  runtime. No second Surface engine or semantic Core API is introduced.
- Query text and pending proposition text are bounded operation material only;
  Python does not use them to rank regions, facts, or vacancies.
- `EncounterFactCard` and `EncounterVacancyCard` are finite, state-bound,
  operation-local projections. Their IDs and paths are deletable.
- Existing split paths remain `LEGACY_MIGRATION` until the OpenClaw common Wire
  is active, automated matrices pass, and Distribution truth is updated.
- No asset is `REMOVE_AFTER_REPLACEMENT` at this Gate because active Host
  replacement and Provider evidence have not yet closed.

## Gate B Result

- Core production changes: none.
- New read/write mode: none.
- Second Surface: none.
- Independent Cartographer session: still present as migration input, not yet
  removed or claimed closed.
- Query/fact index: none.
- Single-entry: preserved.
- `AGENTS.md`: canonical empty file.
