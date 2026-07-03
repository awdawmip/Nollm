# DX2 Multi-Admission Assembly-to-Recall Delivery Receipt

- baseline commit: `7fb0149ed9b182c7a09b1c7ba9f42f5f12afe009`
- branch: `codex/dx2-multi-admission-assembly-recall-validation-rc1`
- implementation commit: recorded in final delivery response
- delivery head: recorded in final delivery response
- bundle filename: `nollm_dx2_multi_admission_assembly_recall_20260703.bundle`

## Scope

DX2 adds synthetic validation only. It changes DX2 fixtures, tests, validation
runner, validation report, protocol note, delivery receipt, and roadmap status.
No sealed production implementation is modified.

## Validation Commands

The fixed acceptance commands are:

```text
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q reference/python/tests/test_dx2_multi_admission_assembly_recall.py reference/python/tests/test_dx2_multi_admission_assembly_recall_report_regeneration.py reference/python/tests/test_ba1_batch_admission_coordinator.py reference/python/tests/test_df1_field_snapshot_assembly.py reference/python/tests/test_df1_dr1_recall_universe_contract.py reference/python/tests/test_dr1_01_closure.py reference/python/tests/test_dr1_coverage_and_gravity.py reference/python/tests/test_dr1_cross_module_contracts.py reference/python/tests/test_dr1_evidence_qualification.py reference/python/tests/test_dr1_exact_projection.py reference/python/tests/test_dr1_legacy_and_boundaries.py reference/python/tests/test_dr1_relative_time.py reference/python/tests/test_di1_integration_shell_boundaries.py reference/python/tests/test_di1_integration_shell_contract.py reference/python/tests/test_di1_integration_shell_determinism.py reference/python/tests/test_di1_integration_shell_public_view.py reference/python/tests/test_di1_integration_shell_read_only.py reference/python/tests/test_ci1_capture_ingress.py reference/python/tests/test_ci1_capture_visibility.py reference/python/tests/test_ci1_capture_policy.py
PYTHONDONTWRITEBYTECODE=1 python validation/dx2/run_dx2_multi_admission_assembly_recall.py --output docs/validation/DX2_MULTI_ADMISSION_ASSEMBLY_RECALL_BASELINE_REPORT.md
PYTHONDONTWRITEBYTECODE=1 python reference/python/scripts/check_package_hygiene.py
git diff --check 7fb0149ed9b182c7a09b1c7ba9f42f5f12afe009..HEAD
```

Actual command results are reported in the final delivery response after the
delivery head is committed and the worktree is clean.

## Validation Head

The report `validation_head` records the Git HEAD at report generation time. It
is normalized by the report regeneration regression because the same report
content is expected to regenerate from later delivery commits.

## Known Limitations

The A/B explicit finite assembly is single-gravity-chart. Sealed DF1 rejects one
snapshot spanning multiple gravity chart fingerprints, so DX2 validates a real
cross-chart VerifiedChartLink through D, an admitted control that is excluded
from the BA1 receipt admission IDs used by DF1.

Final bundle SHA-256 is intentionally not recorded here because the receipt and
bundle have a self-reference problem. The final response reports the bundle path
and SHA-256 from the actual generated bundle.
