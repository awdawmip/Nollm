# HAG1 Validation Report

Baseline:

- Local main: `8bb324a3a5de46bebb6eadd217820627a971e2a0`
- Stale origin/main: `3b9ebc3492fb0fb1877b1e3cadeb20212a55911d`
- HAG1 baseline evidence ref: `refs/nollm-delivery/tq1-c7r/5b9ecdf363269401eb04e97956bd646561bf1090`

Fixed gates run before commit:

```text
python -m pytest -q reference/python/tests/test_hag1_file_first_explicit_admission_gateway.py
45 passed
```

The task-pack wildcard command was resolved through PowerShell `Get-ChildItem` because Python/pytest received `test_cx2_*.py` literally when invoked from PowerShell:

```text
python -m pytest -q <fixed dependency file list with expanded cx2/ba1/da1/dx2 globs>
192 passed
```

C1R targeted coverage includes actual CI1/DE1 shard identity, deterministic CX2 projection metadata, legacy shard alias rejection before evidence read, candidate/declaration mismatch rejection before evidence read, evidence identity mismatch rejection, projection collision rejection, and closed/mismatched/multi-source window rejection before candidate/evidence/HX1 calls.

Baseline evidence ref verification command for C1R:

```text
python reference/python/scripts/package_nollm_tq1_delivery_evidence.py verify-ref --repo-root . --evidence-ref refs/nollm-delivery/tq1-c7r/5b9ecdf363269401eb04e97956bd646561bf1090 --expected-head 5b9ecdf363269401eb04e97956bd646561bf1090
```

Final C1R matrix and bundle values are recorded after final code commit and evidence packaging.
