# DR1.1T Evidence Aggregation Closure Receipt

Date: 2026-07-01

Branch: `feature/dr1-01t-evidence-aggregation-closure`

Base commit: `122001246f27412e9c0a30fb3ec094c3f9d217a6`

## Scope

Closed DR1.1T evidence aggregation and seed-family identity gaps only.

Implemented:

- seed budget now counts exact-match seed families, not individual physical covers;
- family identity is based on support traces, support shards, and matched required axes;
- all covers in a selected seed family may produce executable route candidates before global route dedup;
- final evidence identity is `origin_shard_id`, not `(cover_id, shard_id)`;
- one DreamShard evidence unit keeps one maximum-mass route per axis, with stable route-key tie-break;
- distinct required axes in one DreamShard may accumulate into one evidence unit;
- final multi-axis gate is rechecked after route and axis dedup, with `DR1_INSUFFICIENT_POST_DEDUP_AXIS_MATCH`;
- `RecallResultItem.cover_id` remains deterministic representative provenance and `cover_ids` records all winning cover provenance.

Preserved:

- exact query atom projection and runtime relative-time span binding;
- K_up target must be `Cover.support_cell`;
- K_down target must return to exact `Trace.cell`;
- `path_mass = trace.mass * K_up * K_down`, without renormalization;
- strict finite `RecallUniverse` validation, VerifiedChartLink handling, global traversal accounting, primary/context partition, and Gravity true-tie behavior;
- read-only finite-universe Recall boundary with no LLM, runtime, OpenClaw, CLI, adapter, network, database, cache, or history writes.

Excluded:

- NLP, embeddings, semantic search, anchor lookup, LLM calls;
- global Universe discovery, window admission, indexes, or route search;
- Geometry, Field, Evidence, Cortex, OpenClaw, adapter, runtime, memory, or database implementation edits;
- DR1.2 or any additional DR1.x continuation.

## Changed Paths

- `reference/python/nollm/dream_geometry/recall/**`
- `reference/python/nollm/dream_geometry/validation/dr1_*`
- `reference/python/tests/test_dr1_*`
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
  - evidence: `61 passed in 15.25s`
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q <expanded tests/test_dg0_*.py test_dg1_*.py test_dg2_*.py test_de1_*.py test_dc1_*.py test_dr1_*.py>`
  - result: pass
  - evidence: `228 passed in 16.09s`
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
  - evidence: `1113 passed, 183 subtests passed in 580.40s (0:09:40)`
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

DR1.1T closes evidence aggregation.

After this closure, DR1 is sealed as `Accepted and sealed - Recall Resolver Foundation`.

Do not continue DR1.2 or any other DR1.x work.
