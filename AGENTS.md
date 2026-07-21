# Nollm V3.11 Rev4 Contextual Relational Growth Rules

## Authority

- Read `docs/architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md` first.
- Active architecture amendment: `docs/architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_11_REV4_CONTEXTUAL_PROPOSITION_SHARED_RETRIEVAL_ENTRY_IDENTITY_20260721.md`.
- Active route: `docs/project/NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md`.
- Current task: `docs/project/tasks/NOLLM_A_O_L_D_RECALL_ENTRY_IDENTITY_CONTEXTUAL_WRITER_RELATIONAL_GROWTH_TASK_20260721.md`.
- `c40f8bf6a5be6184e5e56236c96d2817fed4bee5` is the immutable runtime-integrity input checkpoint. Its one-cell counterexample is invalid because fast Recall entry IDs collided.

## Current closure contract

- One MemoryStatement maps to one Atom, one Handle, and one Cell.
- One Capture or chat turn may produce zero, one, or multiple independent MemoryStatements.
- Multiple Statements from one Capture do not authorize multi-cell footprints.
- Trace sinks are observational only; reentrant Core mutation, import, or close during an operation must not commit.
- Public Junction candidate limits may not discard candidates before scoring.
- Access fatal rollback preserves structured diagnostics and poisons the affected runtime.
- Readback failure after commit is an indeterminate commit state, not a pre-commit failure.
- Corrupt Statement data is an item-level Recall error unless canonical state itself is unreadable.
- Live Evidence uses a run-scoped mutable path; freeze publishes immutable exact bytes only after the writer rotates or is disabled.
- Machine-detected facts and operator attestations are separate evidence fields.
- Every selectable Atlas entry is unique within its operation/page. Never deduplicate Atlas entries by a region-local entry ID.
- Writer receives bounded chronological narrative context separated from absorption sources; context-only Captures never re-enter absorption state.
- Absolute time or location normalization requires explicit Evidence provenance.
- Recall teaching distinguishes direct queries from broader shared-entry queries.
- Cartographer resolves plausible shared retrieval neighborhoods, not only regions that already contain the new answer.
- Entry queries, relation labels, Atlas paths, and narrative context remain operation-local and are not persisted.
- Keep one Statement, one Atom, one Handle, and one Cell. Core is not modified in Rev4.
- Do not add multi-cell, multi-entry Recall, Topic/Entity, vector, graph, embedding, or query/fact indexes in this task.

## V3.11 operation contract

- V3.11 teaches the LLM to simulate future Recall Lenses before choosing locality.
- Do not ask whether a complete fact is important enough to remember. `no_memory` is limited to no standalone proposition, empty/tool noise, or exact no-new-information cases.
- Recall Lenses are operation-local teaching artifacts. Do not persist axis IDs, future queries, query-to-entry or fact-to-entry mappings, contact candidate IDs, Lens text, or LLM reasoning.
- Reuse DC1 axis/ray concepts only as ephemeral Prompt and Lab references; do not restore Cortex Store, rule registry, receipts, or fixed ontology.
- A Dream Sculptor call may form Statements and plan Placement in one batch. It selects supplied Locality candidate IDs and never outputs coordinates.
- Core computes geometry-only Junction candidates from distance, boundary, occupancy, and free faces.
- Store one Statement as one Atom in one Junction Cell. Do not add multi-cell footprints, duplicated Atoms, automatic Bridge/Stitch, or multi-layer Placement.
- Natural multi-entry is observed only after field growth through independent single-entry Recalls. The Tokyo/date/weather fixture is an observation, not a global invariant.
- Writer/Reader/Critic self-play belongs in Lab; production common path remains one Dream Sculptor call.
- Close V3.10 scope, turn idempotency, drain, provenance, retry, and partial-outcome gaps before Junction growth.

## Foreground and background contract

- The visible path durably publishes exact user and assistant bytes before returning from the delivery Hook.
- Capture performs zero Provider, Python bridge, Surface, and Core calls.
- OpenClaw owns immutable Capture and append-only state events; Access does not persist raw conversation Capture.
- Formation, Placement, confirmation, and Admission run only through the recoverable background worker.
- Pending read-your-writes is bounded by scope, time, count, and characters and has no query/topic/source index.
- Admission is complete only after Statement, HandleBinding, and Core Atom reopen verification.
- Mechanical singleton Recall uses zero hidden calls; common admitted Recall uses at most one entry-selection call and no second Statement-selection agent.
- "Conversation becomes remembered" means Statement + current HandleBinding + Core Atom are durably committed and readable after reopen.
- Formation output alone is not remembered memory.
- "Recall ready" means the hidden injection payload is ready for the main agent.
- "Visible recall latency" ends when the correlated main-agent `message_sent` event is observed.
- Use monotonic clocks for durations inside one process.
- Use epoch timestamps only for cross-process/cross-hook correlation; never subtract unrelated monotonic clocks.
- Existing `formation_ms` is semantically cumulative and must not be used as pure Formation provider latency.
- Separate queue wait, prompt build, provider wait, parsing, Surface, Core, persistence, confirmation, and main-agent time.
- Do not optimize the system in the same task unless a measurement defect itself blocks truthful timing.
- Do not add a Trace product, telemetry service, database, daemon, persistent correlation index, or hidden-reasoning storage.
- Timing evidence must contain hashes/IDs and durations, not full conversations unless already required by the existing Live evidence contract.
- Measurement overhead must be quantified and disabled by default outside debug validation mode.
- Report warm, cold, dense, hidden-preview, NONE, multi-Statement, reuse, revision, defer, and failure samples separately.
- No latency threshold may be promoted to a permanent architecture invariant from one Provider or one workstation.

## Hard physical contract

- Adjacent physical-layer rotation increment is 22.5 degrees.
- `theta(L) = L * 22.5 degrees mod 60 degrees`.
- `beta = 2^(1/4)`; adjacent-layer density ratio is `sqrt(2)`.
- Increasing physical layer index means finer cells.
- Physical Memory Layer and Aggregation Order are separate identity domains.
- Coverage approximation may not alter these constants.

## Approximation contract

- Production Coverage is a bounded structural approximation, not exact physical area measurement.
- Exact polygon/Decimal code belongs in Lab/Oracle and must not run per Surface cell in the chat path.
- Default production method: deterministic equal-area hex quadrature with fixed-point transforms and nearest target-cell assignment.
- A residue atlas may be added only as a derived acceleration of the same quadrature contract.
- Approximation quality is measured by weighted mass errors and total variation, not exact support equality.
- Default Gate targets:
  - `missed_mass_p99 <= 0.02`
  - `false_mass_p99 <= 0.02`
  - `total_variation_p95 <= 0.05`
  - `partition_mass_error == 0` after integer normalization
  - `max_fanout <= 8`
  - no target outside the certified local radius
  - dominant-target agreement >= 0.95
- Small support differences below the declared relation threshold are allowed.
- Approximation policy must be selected from broad, deterministic, exact-Oracle calibration rather than a hand-picked fixture set.
- The storage/transport radius and active writable radius are separate contracts. Writes must remain closed under configured Recall Coverage depth.

## Reuse before rebuild

- Reuse the historical chart/hex/polygon/Coverage assets as Lab Oracle and benchmark inputs.
- Do not copy product, relation-index, Field, Recall or Evidence code from legacy paths into Core.
- Record provenance for any ported math routine.

## Operational domain

- Mathematical coordinates remain conceptually unbounded.
- Active product profile uses `max(|q|,|r|,|q+r|) <= 2^31-1`.
- Do not spend the active task on signed-64 closure, arbitrary-precision Wire or all-plane exact certification.
- Node/JSON integer transport must reject values outside the active domain.

## Surface and Recall

- Surface Orders are computed lazily, finest to coarser, stopping at the first order satisfying budget.
- `page()` and descent may not rebuild all Orders.
- Cache only derived address/residue Coverage and Surface pages; caches must be deletable.
- One traversal selects one final physical entry.
- Natural reachability from multiple entries is an observation, not an invariant or persisted fact-to-entry mapping.
- No `select_entries`, Cursor, Topic/Source route, graph/vector/embedding or Python semantic placement.
- Current Placement policy remains physical layer 0; no Stitch or multi-layer semantic Placement in this task.

## Active write and traversal policy

- Core storage validity and Access/OpenClaw active semantic write policy are different contracts.
- Active semantic Placement remains `default_dream_v1/default/layer0/phase=null` and active writable radius only.
- Surface prompts must be generated from state-derived `legal_actions`; never advertise impossible actions.
- Invalid model navigation is recoverable only through a bounded operation-local correction loop with zero state mutation.
- Mechanical singleton physical-entry resolution is allowed only when the total visible candidate universe contains exactly one entry; otherwise the LLM selects one visible candidate.
- Existing failed P1 Statement/Evidence must be reused when valid; do not create duplicate facts merely to retry Placement.
- Provider latency and model failures must be reported separately from Surface/Core timing.
- No Stitch, multi-layer semantic Placement, Cursor, semantic route, graph/vector/embedding, exact polygon production path, or persistent traversal state.
- Final delivery commit must be included in the ownership manifest before bundle creation.

## Semantic placement and revision policy

- Placement action semantics are LLM-owned but must be precisely defined.
- `reuse` means the new Statement is materially the same current fact.
- `revision_current` is destructive to the current Handle binding and is allowed only for the same subject or referent, the same proposition slot, and a new value that supersedes the current value.
- Similar wording, the same field label, the same document type, or the same locality is not enough for revision.
- Different subjects with analogous attributes must remain distinct current facts.
- Additive facts about the same subject use `new_local` or another non-destructive action, not `revision_current`.
- Every `revision_current` decision is provisional until one bounded real-LLM confirmation succeeds.
- Rejected revision confirmation causes zero mutation and excludes that revision target for the operation-local retry.
- Python and Core must not infer subject identity or proposition equality by keywords, hashes, regexes, embeddings, or fixed scores.
- The V5 BX-3917/CR-7159 binding is a known semantic repair target; repair only in a non-destructive V6 copy using public Access operations.
- Dense Live must be formed from normal conversation, not direct Store injection or forced Cell addresses.
- Freeze Live evidence before writing the report; do not append to a hashed evidence file afterward.
- No Stitch, multi-layer semantic Placement, persistent Surface cache, semantic route, graph/vector/embedding, or PB validation.

## Gate discipline

- Gate 1 calibrates approximate Coverage against exact Oracle on bounded fixtures.
- Gate 2 replaces production Decimal/polygon Coverage.
- Gate 3 implements lazy Surface and proves the small-field runtime target.
- Only then run OpenClaw regression/P1.
- Incomplete work must still be committed with clean tree and one full-history Bundle.
- Update architecture, route, status, ledger, task report and final Manifest in Git.
- Do not describe a capability as sealed, permanently complete, or permanently 100 percent complete.
- `dd95606` is a prototype checkpoint, not validated Lens-to-geometry causality.
- A resolved Recall Lens must causally constrain the geometry relation groups.
- Do not accept a primary/contact choice unrelated to Lens Atlas paths.
- Core Junction must score all relation groups symmetrically enough to make contacts observable.
- Do not enumerate only around the first group or truncate candidates before geometry scoring.
- Locality Atlas must be derived from bounded multi-scale Surface, not stable-coordinate prefixes.
- Synthetic hand-built wire tests are conformance tests, not LLM self-play.
- Multi-entry observations require independent single-entry queries and unrelated occupied negative controls.
- The Tokyo/date/weather field must use arms of length at least two, not a center-plus-neighbor star.
- Persist raw validated Sculptor evidence at runtime; do not rely only on post-hoc log recovery.
- Do not add Lens persistence, Topic/Entity indexes, fact-to-entry maps, vectors, graphs or multi-cell Atoms.
- An Atlas is active only when its coverage certificate shows zero uncovered occupied Cells.
- Never even-sample or stable-key-sample Surface projections and call the result field-complete.
- Choose the finest Surface Order whose entire non-empty projection set fits the Atlas budget.
- If no supported Order fits, return explicit Atlas overflow and defer; do not sample.
- A resolved Lens is not geometrically realized until the selected Junction is within contact_radius of every relation group.
- Access must never apply an all_groups_realized=false Junction.
- Core must not expose active candidates outside max_radius.
- Provider Writer/Reader validation must use one causal workspace: apply Writer, reopen, then Reader.
- Do not preseed the Reader target independently of Writer.
- Counterfactual and Reader must use the same final field and RecallBudget.
- Synthetic direct seeds are conformance only, not Provider long-arm evidence.
- Preserve one Statement/Atom/Cell and operation-local Lens.
- f9f01f5 is a field-complete Atlas and realized-Junction checkpoint, not a relation-entry Reader proof.
- A causal Reader success requires a non-empty path from a relation entry; selecting the target Cell directly is a separate control.
- Do not use occupied stable-key prefixes as the production Recall universe.
- A complete Atlas must be Prompt-bounded through progressive full pages, not one huge serialized field.
- Writer sees Capture only and forms Statements plus future Recall Lenses.
- Cartographer sees Lenses and operation-local Atlas pages and maps them to geometry.
- An independent complete proposition may create a relation-neutral seed when no Lens resolves.
- Do not force unrelated facts to attach to existing Localities.
- Atlas representatives are navigation hints; exact reuse/revision requires bounded local detail.
- Common batch uses one Writer call and one Cartographer session; do not recreate a session for every Lens.
- No single Writer/Cartographer Prompt may exceed the active byte budget.
- Preserve Core realized-Junction code unchanged unless a real regression is found.
