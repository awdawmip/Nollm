# V1 Final Audit Checklist

This checklist records the expected V1 release-candidate audit commands and pass criteria.

Run commands from `reference/python` unless noted.

## Required Commands

```bash
python3 run_tests.py
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q
python3 -m nollm.cli validate ../../examples/openclaw
python3 -m nollm.cli audit ../../examples/openclaw
python3 -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
python3 scripts/check_package_hygiene.py ../..
```

Run safe top-level examples:

```bash
python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/orient.json
python3 -m nollm.cli tool ../../examples/tool_requests/inspect_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/review_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/annotations_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/ledger_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/history_openclaw_card.json
python3 -m nollm.cli tool ../../examples/tool_requests/read_openclaw_card.json
```

Run generated-output recall examples only against temporary notebook copies.

## Expected Pass Criteria

- Tests pass.
- OpenClaw validation prints `PASS`.
- Audit output is valid JSON.
- Audit-check reports `ok: true`, `matches: true`, and `drift_count: 0`.
- Safe tool examples return `ok: true`.
- Package hygiene reports `PASS package hygiene`.
- `examples/openclaw/recalls/` contains no generated `recall_*.json` or `recall_*.md`.
- No `.pytest_cache/`, `__pycache__/`, or `*.pyc` files remain.
- No temporary archives, local audit outputs, or `settings.json` are committed.

## Archive Verification

From the repository root:

```bash
git archive --format=zip --prefix=nollm/ -o ../nollm_v1.0.0_rc1_source.zip HEAD
```

Verify the archive:

- It is outside the source tree.
- It is not committed.
- All entry paths use `/`.
- Backslash entry count is zero.
- No cache, pyc, local settings, local audit, or generated recall artifacts are present.
- Required committed fixtures are present.

## Tag Readiness

Prepare but do not run without owner authorization:

```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```

Final V1 tag, later:

```bash
git tag v1.0.0
git push origin v1.0.0
```
