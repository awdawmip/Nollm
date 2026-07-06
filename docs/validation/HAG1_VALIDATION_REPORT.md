# HAG1 Validation Report

Baseline:

- Local main: `8bb324a3a5de46bebb6eadd217820627a971e2a0`
- Stale origin/main: `3b9ebc3492fb0fb1877b1e3cadeb20212a55911d`
- Prior evidence ref: `refs/nollm-delivery/tq1-c7r/8bb324a3a5de46bebb6eadd217820627a971e2a0`

Fixed gates run before commit:

```text
python -m pytest -q reference/python/tests/test_hag1_file_first_explicit_admission_gateway.py
36 passed
```

The task-pack wildcard command was resolved through PowerShell `Get-ChildItem` because Python/pytest received `test_cx2_*.py` literally when invoked from PowerShell:

```text
python -m pytest -q <fixed dependency file list with expanded cx2/ba1/da1/dx2 globs>
192 passed
```

Baseline evidence ref verification:

```text
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref --repo-root . --evidence-ref refs/nollm-delivery/tq1-c7r/8bb324a3a5de46bebb6eadd217820627a971e2a0 --expected-head 8bb324a3a5de46bebb6eadd217820627a971e2a0
status: verified
evidence_commit: a92c65b2f36c0fb50259e141adb9927a31edeec6
```
