# V1 Release Checklist

Use this checklist before preparing a V1 release candidate.

## Validation

Run from `reference/python`:

```bash
python3 run_tests.py
python3 -m nollm.cli validate ../../examples/openclaw
python3 -m nollm.cli audit ../../examples/openclaw
python3 -m nollm.cli audit-check ../../examples/openclaw --against ../../examples/audit_reports/openclaw_audit.json
python3 scripts/check_package_hygiene.py ../..
```

Run safe top-level tool examples from `reference/python`:

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

## Fixture Hygiene

- Confirm `examples/openclaw/recalls/` contains no generated `recall_*.json` or `recall_*.md`.
- Run generated-output recall examples only against temporary notebook copies.
- Keep mutating tool examples under `examples/tool_requests/templates/`.
- Confirm committed fixtures remain present:
  - `examples/openclaw/recalls/sample_recall_digest.json`
  - `examples/openclaw/recalls/sample_recall_digest.md`
  - `examples/audit_reports/openclaw_audit.json`
  - `examples/tool_responses/*.json`

## Package Hygiene

- Confirm no `.pytest_cache/`, `__pycache__/`, or `*.pyc`.
- Confirm no `settings.json`.
- Confirm no temporary zip/tar archives.
- Confirm no local `audit.json`, `audit.md`, `*_audit.json`, or `*_audit.md` outputs outside committed fixtures.
- Confirm no machine-local absolute paths in committed fixtures.

## Release Readiness

- Review `docs/V1_KNOWN_LIMITATIONS.md`.
- Review `docs/V1_RELEASE_NOTES_DRAFT.md`.
- Create a Git checkpoint.
- Prepare tag commands, but do not tag until authorized:

```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```
