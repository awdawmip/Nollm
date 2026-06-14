# Packaging

V1 packaging remains simple. Release archives must use POSIX-style `/` path separators.

Valid archive entry:

```text
nollm/reference/python/nollm/cli.py
```

Invalid archive entry:

```text
nollm\reference\python\nollm\cli.py
```

Recommended packaging paths:

- Use the GitHub source zip.
- Use `git archive`.
- Use a Python zip creation script that writes archive names with `Path.as_posix()`.

If a helper script is added later, it must use only the Python standard library unless the project explicitly accepts a packaging dependency.

Packaging is not the project identity and does not introduce a runtime, database, MCP server, external LLM call, or dependency.

## Test Command

Use the project test command before packaging or upload:

```bash
python3 run_tests.py
```

The runner sets `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, runs every test file in deterministic order, and applies a hard timeout to each group so ambient pytest plugins or host subprocess behavior do not stall the canonical command indefinitely.

## Clean Tree Guard

Before packaging or uploading, run:

```bash
python3 scripts/check_package_hygiene.py ../..
```

The checker is a release hygiene guard only. It does not create archives and does not add runtime behavior.

It rejects:

- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `settings.json`
- generated `examples/openclaw/recalls/recall_*.json`
- generated `examples/openclaw/recalls/recall_*.md`
- local `audit.json` / `audit.md` outputs
- temporary archives

Keep committed fixtures such as `examples/audit_reports/openclaw_audit.json` and `examples/openclaw/recalls/sample_recall_digest.*`.

Top-level `examples/tool_requests/*.json` are safe against committed OpenClaw. Generated-output examples, including `examples/tool_requests/generated_output_examples/recall_scale_scan.json`, must be run against a temporary notebook copy or cleaned before packaging.

## Release Candidate Procedure

Run the V1 release checklist in `docs/V1_RELEASE_CHECKLIST.md`.

Prepare tag commands only after validation and project-owner authorization:

```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
```
