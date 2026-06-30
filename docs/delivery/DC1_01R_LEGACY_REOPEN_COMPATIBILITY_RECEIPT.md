# DC1.1R Legacy Reopen Compatibility Receipt

## Scope

- Task: DC1.1R Legacy Reopen Compatibility Closure.
- Branch: `feature/dc1-01r-legacy-reopen-compatibility`.
- Starting HEAD: `6bb7075eced614cad688c03af74714b8b3e22b61`.
- Ending HEAD: the commit containing this receipt.
- Exception paths: none.

## Ancestor Checks

Executed before implementation:

| check | result |
|---|---|
| `git status --short` | clean |
| `git rev-parse HEAD` | `6bb7075eced614cad688c03af74714b8b3e22b61` |
| `git merge-base --is-ancestor 6bb7075eced614cad688c03af74714b8b3e22b61 HEAD` | pass |
| `git merge-base --is-ancestor 3654c67cf065646e2c3a0c2247f4c73da26597e7 HEAD` | pass |
| `git merge-base --is-ancestor c2a28c25cb472a8911c8bd8367a27351c6606aec HEAD` | pass |
| `git merge-base --is-ancestor 74b00a93b93abd22aadf08988a9d5947992f6e22 HEAD` | pass |
| `git merge-base --is-ancestor 314f0d93ce04977588db933969ea71c216351a7b HEAD` | pass |

## Changed Paths

- `reference/python/nollm/dream_geometry/cortex/`
- `reference/python/nollm/dream_geometry/validation/dc1_cortex_report.py`
- `reference/python/tests/test_dc1_cortex_compiler.py`
- `reference/python/tests/fixtures/dc1_legacy/README.md`
- `protocol/v2/DC1_CORTEX_COMPILER_CONTRACT.md`
- `protocol/v2/DC1_CORTEX_COMPILER_CONVENTIONS.md`
- `docs/cortex/DC1_CORTEX_COMPILER_SCOPE.md`
- `docs/cortex/DC1_CORTEX_COMPILER_CONVENTIONS.md`
- `docs/validation/DC1_CORTEX_COMPILER_BASELINE_REPORT.md`
- `docs/delivery/DC1_01R_LEGACY_REOPEN_COMPATIBILITY_RECEIPT.md`
- `ROADMAP.md`

Sealed DG1 Geometry, DG2 Field, and DE1 Evidence implementation paths were not modified.

## Legacy Fixture Provenance

The legacy fixture is a synthetic frozen DC1 artifact shape matching the
pre-DC1.1 compiler contract at `3654c67cf065646e2c3a0c2247f4c73da26597e7`.
It omits `possible_conflict_refs`, preserves the raw old receipt
`input_snapshot`, includes old budget values, and includes same-rule label
variance that is read-only legacy state. The fixture is documented under
`reference/python/tests/fixtures/dc1_legacy/README.md`.

## Validator Boundaries

- Current `compile_growth()` remains strict: `possible_conflict_refs` is
  required, Growth budget caps are `8/48/16`, and same `rule_id` identity
  variance is rejected.
- Legacy reopen applies only when both proposal and receipt snapshot omit
  `possible_conflict_refs`, raw submitted fingerprint still matches the raw
  input snapshot, and the old proposal satisfies legacy structural bounds.
- Legacy admission is in-memory metadata: `legacy_dc1_read_only`. It is not
  written back and is not a current acceptance.

## Validation

| command | result |
|---|---|
| `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_dc1_cortex_compiler.py` | `11 passed` |
| PowerShell-expanded `tests/test_dg0_* tests/test_dg1_* tests/test_dg2_* tests/test_de1_* tests/test_dc1_*` | `186 passed` |
| `python3 run_tests.py` | `1071 passed, 183 subtests passed in 342.91s` |
| `python3 -m nollm.cli validate ../../examples/openclaw` | `PASS` |
| `python3 -m nollm.cli audit ../../examples/openclaw` | passed, validation issue count `0` |
| `python -m nollm.dream_geometry.validation.dc1_cortex_report --output ../../docs/validation/DC1_CORTEX_COMPILER_BASELINE_REPORT.md` | passed |
| `python scripts/check_package_hygiene.py ../..` with `PYTHONDONTWRITEBYTECODE=1` | `PASS package hygiene` |
| `git diff --check` | passed; PowerShell reported CRLF normalization warnings for `ROADMAP.md` and `docs/validation/DC1_CORTEX_COMPILER_BASELINE_REPORT.md` |

## Bundle

Final bundle is generated outside the repository after the commit containing this receipt. The exact `git bundle verify`, `git bundle list-heads`, and SHA-256 are reported with the final delivery output.

## Explicit Exclusions

DC1.1R does not implement or claim:

- LLM calls, natural-language parsing, entity recognition, time calculation, rule truth, or rule authority validation;
- conflict adjudication;
- Geometry placement, Field trace/cover/gravity mutation, Recall resolver behavior, or runtime integration;
- OpenClaw, CLI/tool registration, HTTP, subprocess, SQLite, database, cache, security signature, authentication, migration, auto-upgrade, or anti-tamper guarantees.
