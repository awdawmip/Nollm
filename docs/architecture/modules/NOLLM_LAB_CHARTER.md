# Nollm Lab Charter

Purpose: corpora, gold labels, validation, benchmarks, stress/migration tests, visualization, failure injection, and baselines.

- Persistent state: datasets, reproducible results, benchmark baselines.
- Temporary state: test workspaces and generated measurements.
- Public API: development commands only; no production runtime API.
- Forbidden API: import by any production module or distribution business logic.
- Dependencies: may use all public module APIs.
- Failure: never affects production Core correctness.
- Distributions: selected tools only in debug; otherwise development-only.
- Future repository: `nollm-lab`.
- Current sources: experiments, tests, validation, examples, migration tools, benchmarks, canonical geometry template compiler/generator, and Core capability validator.
- Asset classes: `ACTIVE_LIBRARY`, `ACTIVE_TOOL`, `ACTIVE_FIXTURE`, `ACTIVE_TEST`, `ACTIVE_VALIDATION`, `ACTIVE_REPOSITORY_TOOL`, `LEGACY_REGRESSION`, `LEGACY_REFERENCE`, and `HISTORICAL_RESULT`.
- `ACTIVE` means a current consumer or explicit gate exists; it does not follow from placement under a Lab-owned directory.
- Active libraries, tools, validations, and repository tools use package-root public contracts and import without side effects. Active tests use their declared package or governance suite.
- Legacy regressions run only through an explicit compatibility gate and do not count as current product capability. References and historical results are preserved but not executed by active gates.
- Dream Agent assets provide versioned Prompt/Schema, bounded real background-run observations, and truthful assistant/human review labels. Exact-span assets are legacy parser/schema regression only.
- Dream runtime truth validation recomputes visible main replies, Hook phase and duration, child model resolution, terminal timing, duplicate suppression, and fallback use from controlled raw Host evidence. Its check mode is read-only and does not call a model.
- DC1 axis/ray duality, Evidence basis discipline, relative-time fixtures, and growth/query duality are `REUSE_AS_PROMPT_AND_LAB_REFERENCE` assets for V3.11 Recall Lens evaluation. DC1 stores, receipts, fixed axes, and durable proposals remain reference-only.
- Writer/Reader/Critic cycle validation compares actual Handle reachability through public Access/Core Recall; natural-language self-evaluation is not acceptance evidence.
