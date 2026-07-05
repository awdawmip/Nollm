# HX1 Delivery Receipt

HX1 adds a trusted internal staged execution bridge under `reference/python/nollm/dream_geometry/host_execution`.

Delivered behavior:

- CX2 plan validation plus exact host binding preflight.
- Nested host public value preflight before fingerprinting, work-root creation, or staged execution.
- Canonical preflight for AdmissionPlacementPlan, DreamShard, and CompiledQueryProbe values before fingerprinting.
- Context semantic validation for batch ids, finite set id, timestamp, and DG6 enablement.
- Source-module repository root and caller-cwd repository root descendant work-root rejection.
- CI1 capture execution with explicit capture bindings.
- BA1/DA1 admission for explicit candidates and requests.
- DF1 finite explicit assembly with admitted-but-unassembled exclusion.
- DG6 verification-only projection non-influence check.
- DG6 projection gated by explicit plan declaration, exact binding, and enabled context.
- DR1/DI1 read-only recall over the finite universe.
- Structured completed, partial, and rejected receipts.
- Same plan, same bindings, same context, and same owned work-root idempotent receipt reopen.
- Fail-closed reopen when a plan id is reused with different effective inputs.
- Complete canonical DreamShard payload binding in reopen identity.
- Exact same-call mixed admission ids equal explicit assembly ids.
- Pre-existing admitted-but-unassembled D control rather than same-call hidden admission.
- No-DG6 plans can complete with DG6 disabled and no projection id.
- Undeclared DG6 host bindings are rejected instead of becoming implicit projection work.
- Work-root containment is independent of caller cwd and uses pathlib-only `.git` ancestor detection.

Not delivered:

- OpenClaw, runtime, external API, daemon, network, database, cache, session, LLM/NLP, embeddings, semantic search, global discovery, automatic admission, or automatic placement.
