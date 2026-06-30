# DC1 Cortex Compiler Delivery Receipt

## Scope

- Task: DC1 Cortex Compiler Foundation.
- Branch: `feature/dc1-cortex-compiler-foundation`.
- Starting HEAD: `c2a28c25cb472a8911c8bd8367a27351c6606aec`.
- Ending HEAD: the commit containing this receipt.
- Exception paths: none.

## Sealed Commit Checks

Executed before implementation:

| check | result |
|---|---|
| `git status --short` | clean |
| `git rev-parse HEAD` | `c2a28c25cb472a8911c8bd8367a27351c6606aec` |
| `git merge-base --is-ancestor c2a28c25cb472a8911c8bd8367a27351c6606aec HEAD` | pass |
| `git merge-base --is-ancestor 74b00a93b93abd22aadf08988a9d5947992f6e22 HEAD` | pass |
| `git merge-base --is-ancestor 314f0d93ce04977588db933969ea71c216351a7b HEAD` | pass |
| `git log -1 --oneline` | `c2a28c25 DE1.1R: close interpretation subject domain` |

## Changed Paths

- `reference/python/nollm/dream_geometry/cortex/`
- `reference/python/nollm/dream_geometry/protocol/contracts.py`
- `reference/python/nollm/dream_geometry/protocol/dependency_rules.py`
- `reference/python/nollm/dream_geometry/validation/dc1_cortex_report.py`
- `reference/python/tests/test_dc1_cortex_compiler.py`
- `reference/python/tests/test_dg0_v2_dependency_firewall.py`
- `protocol/v2/DC1_CORTEX_COMPILER_CONTRACT.md`
- `protocol/v2/DC1_CORTEX_COMPILER_CONVENTIONS.md`
- `protocol/v2/INVARIANTS.md`
- `protocol/v2/OBJECT_OWNERSHIP.md`
- `protocol/v2/MODULE_DEPENDENCY_RULES.md`
- `docs/cortex/DC1_CORTEX_COMPILER_SCOPE.md`
- `docs/cortex/DC1_CORTEX_COMPILER_CONVENTIONS.md`
- `docs/validation/DC1_CORTEX_COMPILER_BASELINE_REPORT.md`
- `docs/delivery/DC1_CORTEX_COMPILER_DELIVERY_RECEIPT.md`
- `ROADMAP.md`

Sealed DG1 Geometry, DG2 Field, and DE1 Evidence implementation paths were not modified.

## Validation

| command | result |
|---|---|
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_dc1_cortex_compiler.py` | `6 passed` |
| PowerShell-expanded `tests/test_dg0_* tests/test_dg1_* tests/test_dg2_* tests/test_de1_* tests/test_dc1_*` | `181 passed` |
| `python3 run_tests.py` | `1066 passed, 183 subtests passed in 364.74s` |
| `python3 -m nollm.cli validate ../../examples/openclaw` | `PASS` |
| `python3 -m nollm.cli audit ../../examples/openclaw` | passed, validation issue count `0` |
| `python3 -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json` | passed, drift count `0` |
| `python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json` | passed |
| `python3 -m nollm.cli tool ../../examples/tool_requests/orient.json` | passed |
| `python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json` | not run: file is not present at the documented top-level path |
| `python3 -m nollm.cli tool ../../examples/tool_requests/generated_output_examples/recall_scale_scan.json` | passed; generated recall artifacts were deleted afterward |
| `python -m nollm.dream_geometry.validation.dc1_cortex_report --output ../../docs/validation/DC1_CORTEX_COMPILER_BASELINE_REPORT.md` | passed |
| `python scripts/check_package_hygiene.py ../..` with `PYTHONDONTWRITEBYTECODE=1` | `PASS package hygiene` |
| `git diff --check` | passed; PowerShell reported only a CRLF normalization warning for `ROADMAP.md` |

## Bundle

Final bundle is generated outside the repository after the commit containing this receipt. The exact `git bundle verify`, `git bundle list-heads`, and SHA-256 are reported with the final delivery output.

## Explicit Exclusions

DC1 does not implement or claim:

- LLM calls, natural-language parsing, entity recognition, keyword search, embeddings, or vector search;
- rule truth or authority validation;
- Geometry placement, Field trace/cover/gravity mutation, Recall resolver behavior, or runtime integration;
- OpenClaw, CLI/tool registration, HTTP, subprocess, SQLite, database, cache, security signature, authentication, or anti-tamper guarantees.
