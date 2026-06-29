# DG2 Field Dynamics Delivery Receipt

## Identity

- task id: DG2
- title: Dream Geometry V2 - Deterministic Field Dynamics Foundation
- date: 2026-06-29
- branch: `feature/dg2-field-dynamics`
- base HEAD: `314f0d93ce04977588db933969ea71c216351a7b`
- final HEAD: the commit containing this receipt; exact object id is verified after commit by `git rev-parse HEAD` and bundle `list-heads`.
- commit subject: `DG2: implement deterministic field dynamics`

## Preflight

```text
git status --short -> clean
git rev-parse HEAD -> 314f0d93ce04977588db933969ea71c216351a7b
git merge-base --is-ancestor 314f0d93ce04977588db933969ea71c216351a7b HEAD -> ancestor: yes
git log -1 --oneline -> 314f0d93 DG1.2: correct relative phase recurrence
```

## Changed Files

- `docs/delivery/DG2_FIELD_DYNAMICS_DELIVERY_RECEIPT.md`
- `docs/field/DG2_FIELD_DYNAMICS_CONVENTIONS.md`
- `docs/field/DG2_FIELD_DYNAMICS_SCOPE.md`
- `docs/validation/DG2_FIELD_DYNAMICS_BASELINE_REPORT.md`
- `protocol/v2/DG2_FIELD_DYNAMICS_CONTRACT.md`
- `protocol/v2/INVARIANTS.md`
- `protocol/v2/MODULE_DEPENDENCY_RULES.md`
- `protocol/v2/OBJECT_OWNERSHIP.md`
- `reference/python/nollm/dream_geometry/field/__init__.py`
- `reference/python/nollm/dream_geometry/field/compaction.py`
- `reference/python/nollm/dream_geometry/field/cover.py`
- `reference/python/nollm/dream_geometry/field/gravity.py`
- `reference/python/nollm/dream_geometry/field/trace.py`
- `reference/python/nollm/dream_geometry/field/types.py`
- `reference/python/nollm/dream_geometry/protocol/__init__.py`
- `reference/python/nollm/dream_geometry/protocol/contracts.py`
- `reference/python/nollm/dream_geometry/validation/dg2_field_report.py`
- `reference/python/tests/fixtures/dg2_field/README.md`
- `reference/python/tests/test_dg2_compaction.py`
- `reference/python/tests/test_dg2_cover_lifecycle.py`
- `reference/python/tests/test_dg2_field_boundaries.py`
- `reference/python/tests/test_dg2_gravity_snapshot.py`
- `reference/python/tests/test_dg2_trace_propagation.py`

exception_paths: none.

## Frozen Paths Not Modified

- `reference/python/nollm/dream_geometry/geometry/`
- `reference/python/tests/test_dg1_*.py`
- V1 modules under `reference/python/nollm/*.py`
- OpenClaw / plugin / sidecar / runtime / native memory / CLI / JSON tool paths
- Field did not import or mutate Evidence, Cortex, Recall, Adapter, V1, OpenClaw, validation, network, subprocess, or filesystem APIs.

## Protocol Invariants

DG2 adds supplemental Python contract constant `DG2_FIELD_INVARIANTS` and protocol documentation for:

```text
I-V2-011 Field uses supplied DG1-confirmed directed coverage only.
I-V2-012 Propagation conserves parent mass after residual accounting.
I-V2-013 Trace and Cover preserve provenance.
I-V2-014 provisional_llm_generalization cannot become accepted/stable/crystallized by Field alone.
I-V2-015 Field cannot write, replace, or delete Evidence/Card/Ledger/original Trace inputs.
I-V2-016 Stable Cover requires versioned multi-support / anti-black-hole eligibility.
I-V2-017 Gravity Snapshot is internal Field state, not external anchor/index/query parameter.
I-V2-018 Trace compaction is lossless and reversible.
```

The existing DG0 `INVARIANTS` tuple remains `I-V2-001` through `I-V2-010`.

## API Summary

- Trace: `TraceSeed`, `GrowthTrace`, `TraceResidual`, `VerifiedChartLink`, `TracePropagationResult`, `seed_to_trace`, `propagate_trace`
- Cover: `CoverPolicy`, `CoarseCover`, `CoverEligibility`, `CrystallizationDecision`, `build_local_covers`, `evaluate_cover_eligibility`, `crystallize_cover`
- Gravity: `GravityPolicy`, `GravityContribution`, `GravitySnapshot`, `calculate_gravity_snapshot`
- Compaction: `TraceCompaction`, `compact_traces`, `expand_compaction`

## Invariant-To-Test Map

- Mass and residual accounting: `test_dg2_trace_propagation.py::test_dg2_t1_single_hop_conserves_mass_with_residual`
- Supplied DG1 coverage and cross-chart link discipline: `test_dg2_t4_*`, `test_dg2_t5_*`, `test_dg2_t6_*`, `test_dg2_t7_*`
- Provenance and deterministic IDs: `test_dg2_t9_*`, cover support list tests, compaction tests
- Provisional cannot upgrade: `test_dg2_t8_*`, `test_dg2_c4_*`
- Anti-black-hole cover eligibility: `test_dg2_c2_*`, `test_dg2_c3_*`, `test_dg2_c5_*`
- Gravity internal monotonicity and penalties: `test_dg2_gravity_snapshot.py`
- Lossless compaction: `test_dg2_compaction.py`
- Boundary imports and no external selector language: `test_dg2_field_boundaries.py`

## Validation Evidence

### DG0 + DG1 + DG2 Directed Suite

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_dg0_v2_module_boundaries.py tests/test_dg0_v2_protocol_contracts.py tests/test_dg0_v2_dependency_firewall.py tests/test_dg1_hex_coordinates.py tests/test_dg1_local_charts.py tests/test_dg1_polygon_overlap.py tests/test_dg1_coverage_kernels.py tests/test_dg1_partition_discipline.py tests/test_dg1_chart_transforms.py tests/test_dg1_anti_resonance_metrics.py tests/test_dg1_purity_and_dependencies.py tests/test_dg2_trace_propagation.py tests/test_dg2_cover_lifecycle.py tests/test_dg2_gravity_snapshot.py tests/test_dg2_compaction.py tests/test_dg2_field_boundaries.py
```

Result:

```text
126 passed in 7.02s
```

### Package Hygiene Script Test

Command:

```powershell
cd reference/python
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python3 -m pytest -q tests/test_package_hygiene_script.py
```

Result:

```text
4 passed in 2.64s
```

### Package Hygiene

Command:

```powershell
cd reference/python
python3 scripts/check_package_hygiene.py ../..
```

Result:

```text
PASS package hygiene
```

### Full Suite

Command:

```powershell
cd reference/python
python3 run_tests.py
```

Result:

```text
1011 passed, 183 subtests passed in 347.07s (0:05:47)
```

### DG2 Baseline Report

Command:

```powershell
cd reference/python
python3 -m nollm.dream_geometry.validation.dg2_field_report --output ..\..\docs\validation\DG2_FIELD_DYNAMICS_BASELINE_REPORT.md
```

Result:

```text
exit code 0
observed runtime under 1 second
output: docs/validation/DG2_FIELD_DYNAMICS_BASELINE_REPORT.md
```

## Push And Bundle Evidence

These operations are performed after the final commit exists and are recorded in the final delivery response.

Planned push command:

```powershell
git push -u origin feature/dg2-field-dynamics
```

Planned bundle commands:

```powershell
git bundle create ../nollm_dg2_field_dynamics_20260629.bundle HEAD
git bundle verify ../nollm_dg2_field_dynamics_20260629.bundle
git bundle list-heads ../nollm_dg2_field_dynamics_20260629.bundle
```

Bundle path:

```text
C:\Users\chaos\nollm_dg2_field_dynamics_20260629.bundle
```

## Non-Blocking Debt

- GravityPolicy weights are deterministic baseline values, not production-calibrated weights.
- DG2 does not implement multi-cell covers, cluster merge/split, placement, chart gluing, or energy optimization.
- DG2 does not implement revision/time filtering.
- DG2 does not implement query-side K_down, Recall Resolver, or Cortex compiler.
- DG2 does not implement real authorization or ledger persistence.
- DG1 full baseline report remains comparatively slow; DG2 report uses only small synthetic fixtures.
- Future sandbox hardening remains outside DG2.

## Explicitly Not Implemented

DG3 Cortex compiler contracts, DG4 Query Probe / Recall Resolver, DG5 revision / compression extensions / scale experiments, DG6 adapter integration, and DG7 runtime verification are not implemented here.

## Boundary Statement

DG2 did not connect to LLMs, OpenClaw, runtime, true memory, adapter, CLI, JSON tool, real Evidence, real ledger, network, subprocess, database, or third-party dependencies.
