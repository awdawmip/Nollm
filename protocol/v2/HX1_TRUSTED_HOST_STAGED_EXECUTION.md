# HX1 Trusted Host Staged Execution

HX1 defines a trusted internal host bridge from a validated CX2 `CortexActionPlan` to real staged execution.

Inputs:

- `CortexActionPlan`: declaration-only plan.
- `HostPlanBindings`: host explicit one-shot bindings for opaque capture, candidate, admission, query, workset, and DG6 refs.
- `HostExecutionContext`: explicit finite work-root and fixed execution policies.

Stages:

1. Preflight validates CX2, binding exactness, work-root isolation, and no unsupported DG6 influence.
2. Capture calls CI1 `CaptureIngress` only for declared capture refs.
3. Admission calls BA1 and DA1 only for declared promotion/admission refs.
4. Assembly calls DF1 only for `ExplicitAssembly.admission_ids`.
5. Projection calls DG6 verification-only compaction and expansion checks.
6. Recall calls DR1 and DI1 against the finite DF1 universe.

State separation:

- Capture success is not admission success.
- Admission success is not inclusion in this assembly.
- For `mixed_explicit`, same-call admission receipt ids must exactly equal `ExplicitAssembly.admission_ids` in order.
- Admitted-but-unassembled controls, such as D in validation, must be pre-existing host setup and not same-call hidden admissions.
- DG6 projection is not recall input.
- Recall miss is not global memory absence.

Receipt reopen:

- `execution_input_fingerprint` binds the normalized plan, explicit host bindings, and execution context.
- Reusing a plan id with changed bindings, query refs, policies, context, or DG6 refs fails closed with `HX1_REOPEN_MISMATCH`.

HX1 is not OpenClaw integration, an external API, a daemon, automatic memory, automatic admission, semantic search, vector search, cache, database, network, LLM/NLP, or global discovery.
