# Roadmap

## v0.1: Protocol Scaffold

- Define Core documents for cards, anchors, ledgers, recall digests, and memory addresses.
- Define statuses and LLM-facing actions before runtime implementation.
- Freeze protocol vocabulary for statuses, types, trust, sources, actions, and validation before P1 CLI work.
- Define Cortex guidance for prompts, anchor composition, and read/write policy.
- Provide a small example notebook.
- Keep all source of truth in Markdown, YAML, and JSONL.
- Align protocol language to Anchor is Field, not Folder and Recall is Scale Scan, not Tree Descent.

## v0.2: Validation And Tooling

- Add schema checks for anchors, aliases, cards, and ledger events.
- Add deterministic address validation.
- Add simple local inspection commands.
- Keep SQLite, if used, only as an optional audit projection.

## v0.3: Recall Workflow

- Formalize recall digest generation.
- Define conflict and supersession conventions.
- Keep active inspection deterministic without introducing passive human review queues.
- Preserve status transition history in the ledger.

## V4 Engineering Gravity Decision

The next experimental engineering direction is captured in:

- `NOLLM_PROJECT_SPEC_V4_ENGINEERING_GRAVITY_20260616.md`
- `docs/roadmap/NOLLM_ENGINEERING_ROADMAP_V4_20260616.md`
- `docs/engineering/NOLLM_MINIMUM_DATA_MODEL_20260616.md`
- `docs/experiments/NOLLM_MINIMAL_ABLATION_EXPERIMENT_PLAN_20260616.md`
- `docs/geometry/NOLLM_TRUE_TILING_ENGINEERING_REQUIREMENTS_20260616.md`
- `protocol/GRAVITY_WELL.md`
- `protocol/GRAVITY_MARK.md`
- `protocol/DRIFT_REPORT.md`
- `protocol/RETURN_VECTOR.md`

G0 only adds these decided documents. G1-G8 remain separate implementation tasks.
The V4 drafts do not expand the stable V1 recall/tool surface and do not make
`drift_class` a trust/status mapping.

## Dream Geometry V2 Route

The V2 amendment in `docs/architecture/NOLLM_GEOMETRY_ARCHITECTURE_AMENDMENT_V2_ATLAS_COVERAGE_KERNELS_20260629.md` supersedes older Anchor-oriented route language for new V2 work. V2 is parallel, not yet integrated, and does not replace V1 runtime during DG0.

- DG0: Module boundaries and constitution.
- DG1: Pure Geometry Kernel and coverage-kernel validation.
- DG2: Field Dynamics with traces, covers, and internal gravity.
- DE1: Memory Substrate / Epistemic Core for Dream Shards, externally supplied interpretations, revision threads, usage state, and ledger history.
- DC1: Accepted and sealed Cortex Compiler Foundation at `19d516681301ee9213b7591fd36f9775ebb5207e`.
- DR1: Recall Resolver Foundation is the next permitted phase; it must consume sealed DE1/DC1/DG1/DG2 structures without reopening them.
- DX1: End-to-End Synthetic Memory Cycle Validation is accepted and sealed after DX1.1R final witness record closure; it remains validation-only and does not authorize runtime, OpenClaw, real memory, global window admission, LLM/NLP, or performance work.
- DA1: Memory Admission / Write Orchestrator Foundation is accepted and sealed after DA1.1S RFC3339 Offset Range Closure at implementation commit `184e0da635543389539237c250a754b25ba59b24`. It adds deterministic host-supplied write-side preflight, ordered DE1/DC1/AdmissionRecord commit, idempotent retry, strict replay records, and read-only replay for a narrow AdmissionRecord. It does not authorize LLM/NLP, automatic placement, Query, Recall, DI1, OpenClaw, runtime, global Field persistence, database, cache, network, concurrency, or further DA1.x work.
- DF1: Finite Field Snapshot Assembly is accepted and sealed after DF1.1 assembly replay kernel closure at implementation commit `06ced9dcb7820fbc1cc39ffbdef5ce551d4af537`. It adds a read-only, in-memory assembly layer for explicit host-supplied finite AdmissionRecord sets, requires real DA1 replay, validates DE1/DC1/DG1/DG2 bindings, derives immutable FiniteFieldSnapshot values, builds placement-derived `K_down`, and exposes a DR1-compatible RecallUniverse view. It does not authorize DF1.2/DF1.x, discovery, persistence, Query, recall execution, runtime, OpenClaw, database, cache, LLM/NLP, embeddings, anchors, policy downgrades, conflicting coverage sources, or multi-gravity-chart assembly.
- CI1: Capture Ingress / Deferred Admission Foundation is accepted and sealed after CI1.1 capture state closure. It adds a separate lightweight Capture Lane for host-supplied CaptureRequest objects, DE1-public DreamShard persistence, current-turn-only ephemeral visibility, explicit physical visibility windows, optional deferred admission candidates, idempotent CaptureReceipt replay, and local-failure candidate publication closure. CI1 is independent of GrowthProposal, PlacementPlan, geometry, field, admission replay, assembly, recall, adapters, runtime, OpenClaw, database/cache/network, LLM/NLP, embeddings, semantic search, global discovery, automatic admission, real memory integration, global transaction, crash recovery, background cleanup, or DE1 rollback.
- CX1: Capture / Deferred / Visibility Synthetic Validation is accepted and sealed after synthetic validation of real CI1 CaptureIngress, CapturePolicy, CaptureVisibility, CaptureStateStore, and DE1 public MemorySubstrateStore interactions. It validates ephemeral, captured, deferred, persistent_explicit, retry/reopen, local failure closure, explicit physical visibility, and formal path isolation. CX1 is validation-only and does not authorize CX1.1/CX1.x, production implementation changes, LLM/NLP, GrowthProposal, DA1 admission, geometry, field, DF1 assembly, recall, global discovery, cache, runtime, OpenClaw, CLI, network, database, or real memory integration.
- BA1: Batch Admission Coordinator is accepted and sealed at baseline `1def9e0d4d2b0deb2ab2ad9db74f6d01d4a3dbf7`. BA1-C1 closes duplicate promotion decision, compiled proposal, and placement plan identity preflight plus structured lower-layer preflight normalization. BA1 coordinates only host-explicit DeferredAdmissionCandidate selections into independent DA1 requests after all-member zero-write preflight. It does not select candidates, generate proposals or placements, mutate CI1 candidate state, persist batch state, assemble FieldSnapshots, execute recall, or authorize runtime work.
- RC1: DF1-to-DR1 RecallUniverse contract closure is accepted and sealed at baseline `7fb0149ed9b182c7a09b1c7ba9f42f5f12afe009`. RC1-C1 full support-trace binding closure keeps DF1 `FiniteFieldSnapshot.coarse_covers` as the DG2 local `CellRef` view while binding `RecallUniverse.covers` to same-call replayed `HexCell` values only when every declared support trace exists and matches the cover identity.
- DX2: Multi-Admission Assembly-to-Recall Synthetic Validation is accepted and sealed at baseline `5e5110a0b1c4f08e9b5cce1b4864f7d403a35cee`. It validates CI1 capture/deferred input, BA1 host-explicit A/B admission, DA1 replay, DF1 explicit finite assembly, DR1 recall, and DI1 public envelope boundaries without modifying sealed production implementation.
- GPR1: Geometry Profile / Parameter-Regime Synthetic Validation is accepted and sealed after GPR1-C1 multilayer coverage diagnostic closure. It samples each legal base layer in the finite 0..16 window for coverage metrics without selecting a new production profile or modifying sealed production geometry.
- GVR1: Finite Translation-Variation / Coverage-Robustness Synthetic Validation is accepted and sealed. It validates finite source translation sensitivity for engineering baseline B without changing production geometry or runtime paths.
- GAT1: Finite Chart-Atlas Transition / Groupoid Synthetic Validation is accepted and sealed at baseline `7c3ef9d3a83f87a0dccfa7e9018692be9cdc69af`.
- GSC1: Finite Sparse-Shard / Scale-Coverage Synthetic Validation is accepted and sealed at baseline `f850599995e75b0a5c74fa9267202958a6369bdd`.
- GCM1: Finite Sparse-Collision / Trace-Compaction Non-Conflation Synthetic Validation is accepted and sealed at baseline `2ce5c13f48c2478010acb73c4a612678e7830b10`.
- GRA1: Finite Rotation-Scale Resonance / Phase-Drift Separation Synthetic Validation is accepted and sealed at baseline `1c9b1f0498051cd62b66cfad2fa05a6071778ab3`.
- GRC1: Finite Resonance-Conditioned Coverage / Non-Hierarchy Synthetic Validation is accepted and sealed at baseline `39b673fbba829f1c3285e9496b5af9c9890bf0af`.
- GKD1: Finite Bidirectional Coverage-Kernel / Directional Non-Inversion Synthetic Validation is accepted and sealed at baseline `f2629ba08aeec0a7179e640536a35dd720ab28a1`.
- GKC1: Finite Directed-Kernel Composition / Non-Identity Synthetic Validation is accepted and sealed at baseline `c98d8d96412551ff96ca4e4c4a9dcbc70f2497df`.
- GEO1: Finite Geometry Evidence Consolidation / Production-Freeze Gate is accepted on main at `b16133fdc7599dc2e4a91e6bfd66438ffa61bfe2` with GEO1-C1 canonical evidence hash and accepted-baseline anchor closure completed.
- DG5: Evidence-preserving trace compaction capability is accepted at `5e91504d0f3961be9631856a8853a58ca6bd1921` as a finite, view-only CompressionPlan / CompactedTraceView with lossless expansion.
- DG6: Isolated snapshot compaction adapter is accepted at `47eca074045cede79d19b897ff4cae48dca23ab6` after DG6-C2 replay trace identity preflight closure.
- DG7: Explicit reference runtime positive verification is implemented and accepted at `5275d4d6bcb49d2c405296872f331eb6a579b7e1` after DG7-C1 explicit assembly declaration binding and delivery evidence closure.
- CX2: External Cortex Integration / Conformance Pack is accepted at `3b9ebc3492fb0fb1877b1e3cadeb20212a55911d` as a validation-only declaration protocol, prompt/policy pack, synthetic fixture validator, and reproducible conformance report.
- HX1: Trusted Host Staged Plan Execution Bridge adds an internal host-controlled bridge from validated CX2 plans plus explicit host bindings to real CI1 capture, BA1/DA1 admission, DF1 finite assembly, optional DG6 verification-only projection, and DR1/DI1 read-only recall. HX1-C1 closes exact mixed stage binding, fail-closed receipt reopen by `execution_input_fingerprint`, structured host binding errors, and pre-existing admitted-but-unassembled controls. HX1-C2 closes nested host-input preflight before fingerprint/work-root/stages, execution context semantic validation, and explicit DG6 enablement semantics. HX1-C3 closes canonical nested preflight for placement plans, DreamShards, and query probes; binds canonical DreamShard payloads into reopen identity; rejects undeclared DG6 bindings; and rejects repository-root descendant work roots. HX1-C4 makes work-root containment independent of caller cwd by protecting the HX1 source repository root from the module path plus any caller-cwd repository root, while preserving external owned temporary roots. It is not OpenClaw, runtime, external API, daemon, automatic memory, global discovery, cache, database, network, LLM/NLP, embedding, semantic search, or automatic placement.
- TQ1: Bounded Complete Test Matrix / Delivery Output Convention adds a repository test delivery gate driven by a clean git commit, real pytest collection, deterministic node-id shard assignment, a plan-owned ignored-runtime fixture snapshot, matrix-owned detached worktree execution, external receipts under `C:\Users\chaos\nollm_test_runs`, and delivery bundle placement under `C:\Users\chaos`. It does not modify production Nollm modules or introduce runtime, OpenClaw, network, LLM/NLP, cache, database, daemon, global discovery, or automatic admission behavior.

W2/OpenClaw runtime work is historical background for this route, not the current V2 mainline and not a DG0 prerequisite.

## MT1-R9 Trust Boundary Correction

MT1-R9 is a breaking archive/publication trust-boundary correction for the reference Python ingest path. It introduces archive manifest v3 `sources[]`, policy-derived source identity/state, SafeRoot-contained MT1 I/O, retired flat field writers, publish-journal-backed HEAD activation, repeated `_rN` recovery batches, and structured public failures. R1-R8 MT1 active artifacts require rearchive/reimport and are not a stable migration foundation.

## Non-Goals

- No model runtime.
- No agent orchestration.
- No vector database.
- No embedding dependency.
- No automatic ontology engine.
- Stable V1 Core/tool surfaces do not perform geometry recall or automatic runtime placement.
- D-series reference modules may contain experimental pure geometry, placement candidate records, and deterministic diagnostics.

## Nollm V1 Route Lock

Nollm V1 Core exposes explicit filesystem-backed objects, deterministic validation, audit projections, and tool surfaces.

Nollm V1 Core does not compose context, rank semantics, infer truth, or perform autonomous memory management.

Core:

- explicit object read/write surfaces
- validation
- deterministic audit/audit-check
- scale-scan recall digest
- active inspection metadata
- annotation ledger
- ledger/history inspection
- tool bridge

Cortex / LLM:

- context composition
- deciding what to read next
- interpreting recall
- deciding how to use annotations/history
- proposing writes
- resolving ambiguity

## V1 Allowed Surface

V1 CLI commands:

- `validate`
- `orient`
- `recall`
- `read`
- `inspect`
- `review`
- `annotate`
- `annotations`
- `ledger`
- `history`
- `audit`
- `audit-check`
- `tool`

Stable V1 tool actions:

- `nollm.validate`
- `nollm.orient`
- `nollm.recall`
- `nollm.read_card`
- `nollm.inspect`
- `nollm.review`
- `nollm.annotate`
- `nollm.annotations`
- `nollm.ledger`
- `nollm.history`
- `nollm.audit`

Internal or experimental tool actions that remain available but are not the V1 external surface: `nollm.surface`, `nollm.focus`, `nollm.write_card`, `nollm.update_status`, and `nollm.read_card` legacy `card_id_or_address` input compatibility. They must preserve the same Core boundaries and must not introduce new V1 concepts.

Compatibility labels:

- `review` remains compatibility naming for active inspection.
- `inspect` is preferred.
- `read_card` is explicit single-card read.
- context composition is not a Core action.

## V1 Explicit Non-Goals

- No SQLite runtime.
- No database-backed recall.
- No embedding/vector search.
- No graph database.
- No MCP server.
- No external LLM calls.
- No geometry recall.
- No polygon-overlap-driven V1 recall.
- No automatic card placement.
- No automatic anchor creation.
- No automatic status approval.
- No autonomous memory rewriting.
- No semantic completeness scoring.
- No truth scoring.
- No passive human review inbox.
- No mandatory human approval gate.
- No tree descent.
- No parent/children hierarchy.
- No automatic context composition.
- No deterministic context bundle.
- No neighbor/related-card ranking.

## V1 Known Limitations

These limitations do not block V1.

- Unicode/mojibake terminology guard remains deferred.
- No GitHub Actions yet.
- No formal CONTRIBUTING.md yet.
- No public AGENTS.example.md yet.
- Packaging remains simple.
- Generated-output recall examples are isolated and should be run against temp notebooks.
- SQLite audit projection remains future research, not V1 runtime.
- MCP remains future consideration, not V1.

## F0-01: OpenClaw Native Memory Provider Functional Alpha

A short milestone between MT1 archive ingest and later native recall runtime:

- Add @nollm/openclaw-memory as a standalone kind: \"memory\" plugin.
- Keep
ollm-memory-companion as historical/experimental companion surface.
- Implement private gent_turn_prepare recall and gent_end capture receipt.
- Use a synthetic deterministic alpha field.
- Disable legacy memory fallback.
- Validate against a fixed OpenClaw commit without model credentials.
- Document known limitations as public issue seeds.

F0 does **not**:

- complete R14 SafeRoot / capability storage;
- migrate real MEMORY.md / DREAMS.md history;
- implement finished Cortex geometry recall;
- claim production memory takeover.

The next milestone after F0 is F1 Native Ingress Alpha, which promotes capture
receipts to native shards under R14-safe storage.

## W1-01: OpenClaw Native Companion Memory MVP

A short milestone that adds explicit native remember/recall/get tools to the
existing `nollm-memory-companion` package while keeping `memory-core` active:

- Deterministic Nollm-owned store under `.nollm-memory/native-companion-v1/`.
- `nollm_memory_remember`, `nollm_memory_recall`, `nollm_memory_get` exposed as
  strict OpenClaw tool-plugin tools.
- Secret-like input guard, canonical deduplication by `(scope, kind, text)`,
  and Chinese identity/preference query aliases.
- Python sidecar commands `native-remember`, `native-recall`, `native-get`.
- Updated skill guidance for explicit user identity/preference remember/recall.
- Windows live smoke with a synthetic marker, legacy source hashes unchanged.

W1-01 does **not**:

- replace `memory-core` or claim the OpenClaw memory slot;
- write or migrate `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- call a real LLM or use embeddings;
- automatically capture every conversation turn;
- implement R14 capability-storage hardening.
## W2-01: OpenClaw Direct Active Memory Cutover

Owner-authorized empirical trial that makes the `nollm` provider the active
OpenClaw memory-slot owner (`plugins.slots.memory = "nollm"`).

- Convert `integrations/openclaw/nollm-memory-provider/` from F0 alpha fixture
  mode to a Windows-safe native active memory provider.
- Reuse the W1 native companion store (`native-companion-v1/`).
- `agent_turn_prepare` recalls from the native store into a bounded
  `NOLLM_MEMORY_CONTEXT_V1` envelope.
- `agent_end` deterministically auto-captures explicit stable user sentences
  (remember directives, identity, preference, project/release decisions).
- No Primary-visible Nollm memory tools in active mode.
- No read/write of `MEMORY.md`, `DREAMS.md`, or `memory/*.md` by the provider.
- Local-only redacted trial metrics; tested rollback to `memory-core`.
- Record legacy `MEMORY.md` workspace bootstrap as a measured confound.

W2-01 result: `PARTIAL`. Active slot ownership, capture, and most recalls
succeeded; identity recall was confounded by legacy `MEMORY.md` bootstrap.

W2-01 does **not**:

- claim exclusive prompt memory ownership while workspace bootstrap may exist;
- clean up or tombstone `MEMORY.md`, `DREAMS.md`, or `memory/*.md`;
- wait for W1-04 generic exact-match cleanup or F0 harness closure;
- use embeddings, vector DB, SQLite recall, or external LLM calls;
- expose manual Nollm memory tools to Primary while active.
