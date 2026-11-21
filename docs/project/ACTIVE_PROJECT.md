# Active Project Basis

Repository memory feedback cycle, 2026-11-18.

The V3.14 native OpenClaw memory-slot baseline and parity-preserving Q40 phase
kernel are merged on main through PR #4 at `e798a72b34f1d62725cc31163a4e5ee144656932`.
That task and branch reconciliation are completed. Its working branch was
archived; do not recreate it or restart V3.13/PR #1 from a historical taskbook.

The repository memory experiment may feed measured improvements into main.
Core selects results by physical geometry. Access resolves the resulting handles
to their canonical evidence. The Lab skill may reuse these native files across
sessions and must recheck Git evidence at the requested revision.

Develop changes on `experiment/repository-memory`, compare baseline and candidate
on the same inputs, and bring validated changes into main. Synchronize the
experiment from the accepted main tip before its next trial. Preserve unsuccessful
trials so later improvements can be compared against the original result.

Existing migration work also continues, including unfinished WIP. The user authorizes publication of all Nollm code
to `awdawmip/Nollm`, excluding secrets and personal data. Verify each batch by
source paths, exact bytes/hashes and fixed-commit remote readback; record existing
test outcomes or `NOT_RUN`. Passing all historical tests, completing real bridge
integration, receiving full Git history or all 60 historical ZIPs are not
prerequisites for accepting a verified code batch. Record remaining migration
gaps separately; batch acceptance does not establish functional readiness or full
migration. Canceled operations remain canceled. Actual access denials and platform
restrictions remain binding; this scope does not authorize bypassing them or
resuming canceled calls.

## Current exploratory development: Enterprise Math memory

The [Enterprise Math memory experiment](tasks/NOLLM_ENTERPRISE_MATH_MEMORY_EXPERIMENT_20261120.md)
defines the implementation basis for extending repository memory into a usable internal research component.
The user expanded the earlier understanding study into exploratory implementation and actual LLM use,
with no defensive code or redundant validation/hash machinery in this experiment.
Use its [Codex handoff](tasks/NOLLM_ENTERPRISE_MATH_MEMORY_CODEX_PROMPT_20261120.md)
for the task branch and functional acceptance. Existing understanding and evaluation material is reference.

PR #7 now ships the [research CLI and populated native field](../../lab/nollm-lab/repository_memory/enterprise_math/README.md).
Start a new TASK session with `memory.py em walk`. A cold reader derived a prefix-set rule, saved it,
and another reader used it on a different CRT baseline. The [development trials](../../lab/nollm-lab/repository_memory/enterprise_math/TRIAL.md)
include the direct-source and same-content lexical comparisons and the cost of forming and revising the field.

The current follow-up is the [research-value test and development task](tasks/NOLLM_RESEARCH_VALUE_TESTS_20261121.md),
with its [Codex prompt](tasks/NOLLM_RESEARCH_VALUE_CODEX_PROMPT_20261121.md).
The [2026-11-21 evidence](../../lab/nollm-lab/repository_memory/enterprise_math/value_trial_20261121/REPORT.md)
contains same-content source/flat/native readers and actual navigation scaling diagnostics.
Use the measured failures and explicit missing tests to choose the next useful work; the public development cases are not withheld evidence.

The [independent intake audit](../../lab/nollm-lab/repository_memory/enterprise_math/intake_audit_20261121/REPORT.md) records a real new R284CO understanding saved to the live field and reused by two fresh readers. It also rechecks navigation and adds a thin native link readback for the paired backend/gateway candidate in [em-research-mcp #112](https://github.com/awdawmip/em-research-mcp/pull/112). Candidate maintenance tests and the current live v23 are recorded separately.

## Governing and inherited sources

- Highest principle: [NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md](../architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)
- Inherited architecture, subject to the V3.14 mainline and current amendments: [V3.13 Rev1 Direct Encounter Activation](../architecture/NOLLM_ARCHITECTURE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_DEFERRED_NEURAL_ADAPTER_20260804.md)
- Inherited route, not the current execution dispatch: [V3.13 Rev1 Direct Encounter Activation](NOLLM_ROUTE_BOOK_V3_13_REV1_DIRECT_ENCOUNTER_ACTIVATION_20260804.md)
- Historical task; Live restrictions apply to Live acceptance, not current code-preservation dispatch: [A-O-L-D Direct Encounter Activation, Provider Live and GitHub Delivery](tasks/NOLLM_A_O_L_D_DIRECT_ENCOUNTER_ACTIVATION_PROVIDER_LIVE_GITHUB_EXECUTION_TASK_20260804.md)
- Content-neutral authority: [Memory Eligibility Decision](../architecture/NOLLM_CONTENT_NEUTRALITY_AND_MEMORY_ELIGIBILITY_DECISION_20260723.md)
- Current status: [NOLLM_CURRENT_STATUS.md](NOLLM_CURRENT_STATUS.md)
- Inherited module capability ledger: [NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md](NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md)
- Preserved V3.13 execution evidence, not current V3.14 Live: [V3_13_REV1_DIRECT_ACTIVATION_REPORT.md](V3_13_REV1_DIRECT_ACTIVATION_REPORT.md)
- Active repository asset policy: [NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md](NOLLM_ACTIVE_REPOSITORY_ASSET_POLICY.md)
- Lifecycle authority: [ACTIVE_ASSET_LIFECYCLE_PLAN.json](../architecture/module-ownership/ACTIVE_ASSET_LIFECYCLE_PLAN.json)
- Boundary report: [MODULE_BOUNDARY_REPORT.json](../architecture/module-ownership/MODULE_BOUNDARY_REPORT.json)
- Preserved V3.12 capability record: [AOLD_UNIFIED_FIELD_ENCOUNTER_REPORT.md](AOLD_UNIFIED_FIELD_ENCOUNTER_REPORT.md)
- Current mathematical unit, derivation, executable gates and limitations: [Ideal overlap enclosures](../architecture/CERTIFIED_OVERLAP.md)

## Retained production kernel contract

`parity_preserving_q40_phase_kernel_v1` factors the admitted 96-sample algorithm
into two directional stencils and counted relative footprints. With S=2^40,
`cq=2*S*bq+pq`, `cr=2*S*br+pr`, retain residues in [0,2*S) and restore the even
anchor `(2*bq,2*br)` before absolute storage checks. Half-to-even rounding and cube
repair are equivariant under even translations, not arbitrary integer ones.
Direction, both residues and sample multiplicities remain in the carrier.

All sample counts, targets, Q16 weights, contract IDs, boundaries and canonical
state identity remain unchanged. All four bounded caches are disposable. The
implementation is exactly equivalent to the predecessor's bounded approximation;
it is not exact real-area Coverage and is not eight translation templates.
PR #4 records the completed 394-test and ownership/asset admission. Its original
implementation derivation remains in Git history and the PR; it is not restarted.

## Retained Lab unit and functional admission gates

Lab computes source-share enclosures using outward-rounded algebraic radicals
and exact rational inner/outer half-plane clipping. Candidate completeness comes
from geometric coordinate bounds, not production hits. Uncertain support remains
uncertain; precision/candidate exhaustion fails explicitly. The existing fixture
generator, Decimal cross-check and production phase kernel are consumed unchanged.

Required before admission: arithmetic/analytic golden tests; reciprocal and
large-coordinate checks; frozen broad cross-check and exact per-request error
bounds; current offline package/governance matrix; no production dependency on
Lab; no Core/Access/Host/state-byte changes. Generated evidence stays outside Git.
Passing these gates validates this Lab capability, not a production replacement.

Next, use measured errors and actual cost to decide which production improvement
is useful. Any changed coverage outputs require an explicit contract and migration
gate. Do not increase sample count, change normalization, drop small overlaps or
activate a real-area evaluator by stealth. A full phase-region atlas is not yet
built. The ideal eight-layer identity is not a shortcut through rounded Q40 steps.

## Unchanged boundaries

Evidence remains the fact source; Core is deterministic and semantic-blind;
Access and the real LLM/Host own semantics. Unified Field Encounter uses one
physical entry. Physical Memory Layer is not Aggregation Order. Native exclusive
memory-slot tools remain the OpenClaw integration direction. Packaging, automatic
capture/Formation migration, current-version compatibility, Windows Provider Live,
public ClawHub release and measured memory quality remain independently unclosed.
The four cold branches and existing archive tags are preserved, not reactivated.


