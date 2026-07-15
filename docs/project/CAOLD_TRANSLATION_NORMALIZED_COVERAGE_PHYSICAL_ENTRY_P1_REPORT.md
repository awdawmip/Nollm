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
