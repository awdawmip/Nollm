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
