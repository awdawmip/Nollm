# CAOLD Translation-Normalized Coverage, Physical Entry, And P1 Report

## Gate 0

Expected vector:

```text
C +10 | S 0 | T 0 | A +5 | H 0 | U 0 | O +5 | L +10 | D +5
```

Primary direction:

```text
translation-normalized Coverage
-> physical residual
-> explicit physical entry
-> P1 closure
```

Input evidence:

```text
Bundle: nollm_caold_translation_covariant_coverage_reuse_20260715_66684dc5.bundle
Bundle SHA-256: 2a56dad3164d468169d8ff27a4dd7512041956c5eaa6ba0f64ef5c94897213da
Input HEAD: 66684dc51339544ad4a846614ed31aa52c7ddc24
Branch: codex/caold-translation-normalized-coverage-physical-entry-p1-closure
Bundle verify: complete history
Input tree: clean
```

Protected workspace inventory:

```text
V3.7 workspace exists: yes
V3.8 workspace exists: yes
V3.8 cells=11 atoms=13 bindings=13 statement_files=20 bridges=0
physical distribution: layer0 cells=10 atoms=12; layer1 cells=1 atoms=1
chart_id=default only; phase=null only
coordinate range: q=-12..24; r=0..14
core SHA-256: 7f15148469f6d378bc710848fb4dac4e260d81ad362cbf86236ade5c8e3b7dcd
bindings SHA-256: 3784f10d7fb8e58ba2683504ed75baa19e4b9d272ab1095b0f61dfca73d71f08
```

Gate result:

```text
Actual modules affected: C/A/O/L/D governance only.
Actual progress: authority and audited baseline activated; implementation not yet credited.
Scope added: none.
Deviation above 5%: none.
Status: IN_PROGRESS.
```

## Gate 1

Expected vector and direction:

```text
L +10 is primary; C +10 waits for the mathematics contract.
translation-normalized Coverage -> physical residual -> explicit physical entry -> P1 closure
```

The input absolute-world Decimal80 path was reproduced at `q/r=+/-10^14`.
Across eight layer phases and both directions it produced `DivisionByZero`, no
positive overlap, Q16 normalization failure, and raw source-share mass as high
as 5. Q16 output could still report a forced total of 65536 for other invalid
raw partitions.

The selected contract is:

```text
q/r: signed 64-bit
physical layer: -64..64
chart_id: default only
phase: null only
span: adjacent physical layer
numeric frame: source-side normalized local coordinates
precision: independent Lab Oracle B Decimal96
```

Oracle B independently derives target fractional axial coordinates and clips
local polygons without importing Core or Oracle A. Oracle C uses partition
mass, radius-4/radius-6 support equality, and reciprocal intersection-area
invariants; it does not use Core as its truth source.

Gate 1 evidence:

```text
Oracle B unit tests: passed
Oracle A/B bounded report: 1296 samples, support mismatch=0, false negatives=0
Oracle A/B report SHA-256: 5b4f3655ca20820c472fb460faee6ed5b41f306a18bf74b5cc147e9a7503a88e
Oracle C: 96 samples, candidate mismatch=0, reciprocal mismatch=0
Oracle C max partition mass error: 3.164e-92
Oracle C report SHA-256: a90f12a0ae4aa37b6d80c166f9b2ee7b5a2006951de143ddd5ce4a3d1116c629
historical reusable asset hashes: 17 matched, 0 failures
```

Gate result:

```text
Actual modules affected: Lab and V3.8 governance.
Actual progress: L +10 contract evidence established; C remains uncredited until Gate 2.
Scope added: none.
Deviation above 5%: none.
Gate 2 authorized: yes.
```

## Gate 2

Expected vector and direction:

```text
C +10 and L +10 are the active work.
translation-normalized Coverage -> physical residual -> explicit physical entry -> P1 closure
```

Core now validates the complete address before calculation and supports the
explicit domain `q/r=signed-64`, physical layer `-64..64`, `chart_id=default`,
and `phase=null`. The production overlap path constructs source-centered local
polygons. Precision is derived from coordinate and layer digit counts with 72
guard digits and a Decimal96 minimum. It never constructs absolute-world
polygons.

Physical mass is validated before Q16. The expansion separately exposes raw
source mass, partition residual, candidate-window residual, threshold residual,
numeric error bound, ambiguity, Q16 sum, and Q16 rounding residual. Certified
positive overlaps remain in support; geometric zero overlaps never enter the
members. Unsupported addresses and uncertified physical mass fail before
propagation.

Gate 2 evidence:

```text
Core focused tests: 9 passed
Core complete test suite: 55 passed
bounded Core/Oracle A/Oracle B samples: 1296
large-coordinate Core/Oracle B samples: 64
support mismatch: 0
large-coordinate support mismatch: 0
positive weight on zero overlap: 0
max raw partition residual: 5.367e-92
max candidate-window residual: 0
max Core/Oracle B source-share error: 8e-96
max Q16 error: 1
cache-clear digest before/after: bfb09336abc05596a518d877e022a0f5dd87cba93baf250752b6820af2f0b58b
validation report SHA-256: 0159705ffe54c5223729137cd0a2f9a042c415a5ed45ee1e939a45daf239fe82
full validation elapsed: 427.934 seconds
```

Gate result:

```text
Actual modules affected: Core and Lab validation.
Actual progress: C +10 and L +10 are evidenced in the declared coordinate domain.
Scope added: none.
Deviation above 5%: none.
Gate 3 authorized: yes.
```

## Gate 3

Expected vector and direction:

```text
C +10 remains primary; A +5 begins adaptation.
physical residual -> truthful Surface projection -> explicit physical entry
```

Surface records now carry an immutable source-Cell-to-native-Atom occupancy
mapping. Every higher-order projection computes `native_atom_count` from that
mapping, and order summaries deduplicate the source mapping before totaling it.
No order uses `len(source_cells)` as an Atom count.

Each certified physical expansion contributes its physical and Q16 residual
once to a deterministic owner projection, so overlap fanout cannot multiply the
same residual. `SurfaceCellProjection` and `SurfaceOrderInfo` expose
`coverage_residual_q16`, `coverage_ambiguous_count`, and
`coverage_invalid_count`. Unsupported chart/phase/domain input fails through
the Core physical guard; no nearest-cell fallback is present.

Gate 3 focused evidence:

```text
adaptive Surface focused tests: 9 passed
Core complete test suite: 57 passed
multi-Atom same-Cell native count at orders 0..3: 2 at every order
single expansion order residual: equals physical expansion Q16 rounding residual
projection residual sum: equals order residual
certified ambiguity count: 0
certified invalid count: 0
```

Gate result:

```text
Actual modules affected: Core Surface and its tests.
Actual progress: C +10 Surface truth is evidenced; A remains pending Gate 4.
Scope added: none.
Deviation above 5%: none.
Gate 4 authorized after complete Core regression.
```

## Gate 4 Access

Order 0 Core projections now expose their already-computed physical source
memberships. Access does not recompute geometry. `PhysicalEntryCandidateView`
contains an operation-local candidate ID, exact `GeometryAddress`, native Atom
count, current Statement preview, truncation flag, membership Q16 weight, and
the source Surface candidate ID.

Physical candidates are finite and paged with the existing operation budget.
`select_entry` accepts only `PhysicalEntryPage`; selecting an Order 0 Surface
candidate directly is a type error. Multiple physical candidates require one
shown physical candidate ID. A single candidate is returned with
`resolved_singleton=true`. No candidate state is persisted.

Access evidence:

```text
Core/Access focused physical-entry tests: 7 passed
Access complete test suite: 77 passed, 8 existing deprecation warnings
multi-entry fixture candidate count: 2
invented physical-entry candidate: rejected
direct Surface-to-entry fallback: removed
operation-local state file: absent
```

OpenClaw Wire adaptation remains pending before Gate 4 can close.

## Gate 4 OpenClaw

The OpenClaw traversal Wire is now
`nollm_openclaw_translation_normalized_surface_traversal_v1`. An Order 0
Surface decision can only open physical entries. Final selection occurs on a
separate `nollm_openclaw_single_physical_entry_recall_v1` page and accepts one
visible `physical-entry:*` ID. Recall and Placement share this exact boundary.

Physical traversal state contains only operation-local Surface state, source
Surface address, source candidate ID, and page position. Every continuation
reopens current Core/Access truth. No entry hint, query mapping, or session state
is persisted. OpenClaw imports only Access; it does not import Core.

Distribution identity is now:

```text
plugin version: 0.9.0
geometry contract: nollm_translation_normalized_physical_coverage_v1
coordinate domain: nollm_signed64_default_chart_null_phase_v1
physical residual schema: nollm_physical_coverage_residual_v1
Surface Wire: nollm_openclaw_translation_normalized_surface_traversal_v1
physical-entry Wire: nollm_openclaw_single_physical_entry_recall_v1
```

Gate 4 evidence:

```text
OpenClaw Python tests: 37 passed
OpenClaw Node 24 tests: 19 passed
TypeScript build: passed
OpenClaw Python direct Core imports: 0
invented physical-entry candidate: rejected
Surface candidate direct select_entry: rejected
select_entries production action: absent
```

Gate result:

```text
Actual modules affected: Access, OpenClaw, and distribution contract metadata.
Actual progress: A +5 and O +5 explicit physical-entry boundary evidenced.
Scope added: none.
Deviation above 5%: none.
Gate 5 authorized after the final focused assertion rerun.
```

## Gate 5

The synthetic cross-layer fixture has no Bridge and does not allow lateral
substitution in its direct control request. With Coverage disabled, only the
entry Statement is returned. With `coverage_down` enabled, the adjacent-layer
Statement is returned with path `("coverage_down",)`; a far physical target is
not returned.

The same fixture is projected into an Order 0 Surface Cell containing at least
two physical candidates. Access explicitly selects the source-layer physical
candidate and performs one-entry Recall. Cache deletion and runtime reopen
produce the same statement/path sequence. A second fixture at
`q=10^14,r=-10^14` proves `coverage_up` Recall and reopen inside the declared
signed-64 domain.

Gate 5 evidence:

```text
cross-layer focused tests: 2 passed
entry count per Recall request: 1
multi-physical candidate count: >=2
Coverage disabled cross-layer hit: absent
Coverage enabled cross-layer path: coverage_down
large-coordinate path: coverage_up
Bridge fixture count: 0
wrong far candidate hit: absent
cache-clear/reopen statement-path sequence: identical
```

Gate result:

```text
Actual modules affected: Access/Lab-style synthetic tests and report only.
Actual progress: C/A/O/L single physical-entry composition is evidenced.
Scope added: none.
Deviation above 5%: none.
Gate 6 authorized: yes.
```

## Gate 6

Expected vector and direction:

```text
O +5 is primary; A/C/D support the timed write and reopen loop.
explicit physical entry -> P1 write -> Gateway restart -> new-session Recall
```

The accepted V3.8 workspace was migrated non-destructively into a new V3.9
workspace. Migration changed only the Core geometry registry from v4 to v5.
The source workspace remained in place. Statement-tree and HandleBinding bytes
are identical across source and target.

```text
source: C:\Users\Administrator\.openclaw\memory\nollm-caold-translation-covariant-v1
target: C:\Users\Administrator\.openclaw\memory\nollm-caold-translation-normalized-v1-migrated
cells=11 atoms=13 bindings=13 statement_files=20 bridges=0
Statement tree SHA-256: 110dfd287d99e573018db9fcf807baf792b9e258aa8c1cf71ca64a31086f2222
HandleBinding SHA-256: 3784f10d7fb8e58ba2683504ed75baa19e4b9d272ab1095b0f61dfca73d71f08
migration receipt SHA-256: 5cc8b0a403f53a3aed390a24d2538693d571ad20179ff650eaf27b51190ecf92
```

The first empty-workspace attempt reached `placement_apply` and failed with
`new_local requires a selected locality`; it wrote no Statement or Handle. A
migrated-workspace attempt exposed an invalid Wire prompt that offered
`open_physical_entries` at Order 1. The validator rejected it. The prompt now
exposes only actions legal for its current order. A second Host defect stopped
Recall at the physical-entry page; Recall now continues through the same
explicit physical-entry state as Placement. Neither fix weakens candidate
validation or introduces a Python-selected entry.

The final P1 used ordinary natural chat and the real inherited
`meituan/LongCat-2.0` model. Formation produced
`dream:09adbf112797b51f45925c8b429c21a64c6ae6e90ebba9bf2e0e51e8ed1775a1`.
The model selected an Order 0 Surface Cell, explicitly selected its one shown
physical entry at `layer=0,q=-12,r=9`, then selected a supplied lateral
locality. Access applied `new_local` at `layer=0,q=-13,r=9`, persisted the
Statement, bound its real AtomHandle, and reported one Core write.

Successful operation timing:

```text
formation_ms=16918
surface_build_ms=70623
surface_order_count=1
surface_projection_count=10
surface_page_count=2
placement_prompt_build_ms=70381
placement_subagent_ms=103359
physical_entry_resolution_ms=310
decision_validation_ms=10
statement_persist_ms=2
placement_apply_ms=9
handle_bind_ms=0
total_operation_ms=247409
timeout_stage=null
```

The Gateway restart CLI waited past its own 120-second command window, but an
independent status probe confirmed the replacement process was running,
write-capable, and connected on OpenClaw `2026.6.11`. Plugin inspection showed
version `0.9.0` loaded from this worktree. A new Session selected the exact new
Statement through the physical entry at `layer=0,q=-13,r=9`, injected it with
`visible_message_count=0`, and the main agent answered `QN-7426`.

Live regressions:

```text
R1: completed; hidden Alpha release-window injection; correct visible answer
R2: completed on bounded retry; entry=(layer0,q7,r0); local visitor facts plus lateral cafe fact
R3: completed_none for 17*19; visible answer 323
P1: Formation -> Surface -> physical entry -> PlacementDecision -> Access apply -> HandleBinding -> Core write
Restart Recall: selected only dream:09adbf...; visible answer QN-7426
Cursor/entry hint: absent
OpenClaw direct Core import: absent
```

The external JSONL contains 156 canonical JSON lines at evidence-finalization
time. Its SHA-256 is
`a55de22d03d2855e0fc7328280df36be683437837b83bb2fd982e93dc6dd022c`.
It records earlier failed attempts as well as the successful closure; failures
were not overwritten.

Gate result:

```text
Actual modules affected: OpenClaw, Access timing, Lab migration, and distribution composition.
Actual progress: O +5 and A/C/D support are evidenced; P1 and restart Recall closed.
Scope added: none; migration and timing are Gate 6 work.
Deviation above 5%: none.
Gate 7 authorized: yes.
Implementation HEAD before authority/Manifest closure: 9296869281cf3d7d8a68fcf00a4628e75f5915c8
```

## Gate 7 Pre-Manifest Record

Actual task vector:

```text
CORE +10% | SNAPSHOT 0% | TRACE 0% | ACCESS +5% |
HISTORY 0% | AUDIT 0% | OPENCLAW +5% |
LAB +10% | DISTRIBUTIONS +5%
```

No Snapshot, public Trace, History, Audit, Stitch, multi-entry placement,
semantic index, vector, embedding, or persistent Surface cache scope was added.

Known limitations:

```text
q/r is signed 64-bit and physical layer is -64..64.
Only chart_id=default and phase=null are supported by active physical Coverage.
OpenClaw provider latency was high; successful end-to-end operations took minutes.
The main Host also has an older non-Nollm project file; exact unique-code Recall proved Nollm injection without deleting it.
Cross-platform portability was not validated in this Windows-first stage.
Multi-physical-layer semantic Placement, Stitch, persistent Surface cache, and PB scale remain paused.
```

## Gate 7 Regression Record

The pre-Manifest regression pass used Python 3.14.6 and Node 24.17.0. Package
tests used package-minimal `PYTHONPATH` values because this independent clone
does not install editable monorepo packages. The two attempted aggregate
pytest commands exceeded their command-wide time limits and returned no usable
suite evidence; every suite below was then rerun independently to a conclusive
exit code.

| Suite | Result |
|---|---:|
| `packages/nollm-core/tests` | 57 passed |
| `packages/nollm-snapshot/tests` | 7 passed |
| `packages/nollm-trace/tests` | 3 passed |
| `packages/nollm-access/tests` | 78 passed, 8 deprecation warnings |
| `integrations/openclaw/formation-loop/tests` | 37 passed |
| `reference/python/tests/m0` | 45 passed |
| DG1 focused geometry tests | 46 passed |
| normalized migration and Decimal Oracle | 6 passed |
| OpenClaw Node tests | 19 passed |
| OpenClaw `plugin:check` | passed |
| reusable geometry assets | 17 matched, 0 failures |
| V3.8 authority and no-shortcut check | passed |
| `git diff --check` | passed |

External runner evidence is under
`C:\Users\chaos\nollm_caold_translation_normalized_gate7_outputs`:

```text
translation_normalized.json a90f12a0ae4aa37b6d80c166f9b2ee7b5a2006951de143ddd5ce4a3d1116c629
gvr1.json 06d01f464a871c9847f58c2165326e10330987f034d9bc2ecbbccdb6b2868cb0
gra1.json 8f16323a76f71dd15490f5cbf9cff3358020eb3386d1f3405e4264de6592304d
grc1.json cc3ffed1f1b84d3f8e7ce553be46e8f0cfca05fcd6d3bad1c1dc74bd7d38cb04
gkd1.json f424a2f9bfd2cd414ba67754263dbdd8bde1246c8fe5f3545f5084eea9218276
gpr1.json 09c128dff42a5ea89ad2981f65226d3e736e498343f744a5f6688d7ff24d71f6
```

The independent normalized Oracle C report passed 96 samples, all eight
phases and both directions, large-coordinate stress, radius-4/radius-6 support
identity, reciprocal intersection, and partition mass. Candidate and
reciprocal mismatch counts are zero; maximum partition mass error is
`3.164e-92`.

Post-report Gate 7 checks established:

```text
Git tracked files=1818
ownership Manifest rows=1818
unclassified=0
production boundary violations=0
production cycles=[]
OpenClaw direct nollm_core imports=0
production Cursor/cluster_anchor/select_entries=0
```

The complete post-Manifest regression repeated every package suite, focused
suite, external runner, governance tool, Node test, and plugin check listed
above. Counts were unchanged, all six external runner hashes were byte-for-byte
identical to the pre-Manifest pass, and `git diff --check` passed. Manifest
generation/check/validation and tracked-row equality are repeated after the
delivery commit as required by Gate 7.

The final legal
tag has form
`TRANSLATION_NORMALIZED_PHYSICAL_COVERAGE_SINGLE_ENTRY_P1_VALIDATED_AT_<FINAL_HEAD>`.
The complete-history bundle has form
`nollm_caold_translation_normalized_coverage_physical_entry_p1_20260715_<shorthead>.bundle`.
Its final SHA-256 is necessarily external delivery evidence: embedding that
hash in a tracked report included by the same bundle would make the bundle
hash self-referential. The exact final HEAD, tag, bundle filename, and bundle
SHA-256 are therefore reported with the verified delivery artifact.
