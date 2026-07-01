# DR1.1S Global Traversal Accounting Closure Receipt

Date: 2026-07-01

Branch: `feature/dr1-01s-global-traversal-accounting-closure`

Base commit: `bf9ccc24d6e4c20dcfa2dd6278e5fd95a9d029a0`

## Scope

Closed DR1.1S global traversal accounting gaps only.

Implemented:

- `max_seed_covers` now applies after structural covers become exact-match seed candidates;
- unrelated stable covers can be diagnosed but do not consume seed budget;
- exact seed truncation returns `budget_exhausted` with `DR1_BUDGET_MAX_SEED_COVERS`;
- executable routes are collected for selected seeds, then deduplicated digest-globally by `(origin_shard_id, axis, trace-cell)`;
- duplicate route identities keep the maximum `path_mass`, with stable route-key tie-break;
- selected route cells, layers, chart fingerprints, and direct cross-chart coverage edges are budgeted digest-globally;
- repeated use of the same direct cross-chart edge by multiple traces or axes counts once;
- result items and `route_refs` are built only from globally deduplicated selected routes.

Preserved:

- K_up must target `Cover.support_cell`;
- K_down must return to exact `Trace.cell`;
- `path_mass = trace.mass * K_up * K_down`, without renormalization;
- strict finite `RecallUniverse` coverage/source/context validation;
- primary/context partition before result limiting;
- gravity tie-break only inside same tier and equal core-score epsilon;
- read-only Recall boundaries with no cache, runtime, OpenClaw, CLI, adapter, network, database, or history writes.

Excluded:

- NLP, embeddings, semantic search, anchor lookup, LLM calls;
- global Universe discovery, window admission, indexes, or route search;
- Geometry, Field, Evidence, Cortex, OpenClaw, adapter, runtime, memory, or database implementation edits;
- DR1.2 or any additional DR1.x continuation.

## Changed Paths

- `reference/python/nollm/dream_geometry/recall/**`
- `reference/python/nollm/dream_geometry/validation/dr1_*`
- `reference/python/tests/test_dr1_*`
- `reference/python/tests/fixtures/dr1_recall/**`
- `protocol/v2/RECALL_RESOLVER.md`
- `protocol/v2/INVARIANTS.md`
- `docs/validation/DR1_*`
- `docs/delivery/DR1_*`

Sealed implementation path diff:

- `reference/python/nollm/dream_geometry/geometry/**`: none
- `reference/python/nollm/dream_geometry/field/**`: none
- `reference/python/nollm/dream_geometry/evidence/**`: none
- `reference/python/nollm/dream_geometry/cortex/**`: none

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q <expanded tests/test_dr1_*.py> tests/test_dg0_v2_dependency_firewall.py tests/test_dg0_v2_module_boundaries.py tests/test_dg0_v2_protocol_contracts.py`
  - result: pass
  - evidence: `57 passed in 7.83s`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q <expanded tests/test_dg0_*.py test_dg1_*.py test_dg2_*.py test_de1_*.py test_dc1_*.py test_dr1_*.py>`
  - result: pass
  - evidence: `224 passed in 9.68s`
- `PYTHONDONTWRITEBYTECODE=1 python scripts/check_package_hygiene.py ../..`
  - result: `PASS package hygiene`
- `PYTHONDONTWRITEBYTECODE=1 python -m nollm.dream_geometry.validation.dr1_recall_report`
  - result: pass
  - output: `docs/validation/DR1_RECALL_RESOLVER_BASELINE_REPORT.md`
- `git diff --check`
  - result: pass
  - note: Git reported a CRLF normalization warning for `docs/validation/DR1_RECALL_RESOLVER_BASELINE_REPORT.md`; no whitespace errors.
- `PYTHONDONTWRITEBYTECODE=1 python3 run_tests.py`
  - result: pass
  - evidence: `1109 passed, 183 subtests passed in 337.52s (0:05:37)`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli validate ../../examples/openclaw`
  - result: `PASS`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli audit ../../examples/openclaw`
  - result: pass, `validation.pass=true`, `issue_count=0`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json`
  - result: pass, `"ok": true`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli tool ../../examples/tool_requests/orient.json`
  - result: pass, `"ok": true`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json`
  - result: not runnable because the top-level request file is absent.
  - evidence: `FileNotFoundError: ../../examples/tool_requests/recall_scale_scan.json`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json`
  - result: best-effort pass, `"ok": true`
  - generated `recall_20260701_000001.json` and `recall_20260701_000001.md` were deleted after verification; `examples/openclaw/recalls/` again contains only committed sample files.

Commit, push attempt, and bundle verification are recorded in the final handoff.

## Seal

DR1.1S closes global traversal accounting.

After this closure, DR1 is sealed as `Accepted and sealed - Recall Resolver Foundation`.

Do not continue DR1.2 or any other DR1.x work.
