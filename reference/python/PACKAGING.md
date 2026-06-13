# Packaging

Release archives must use POSIX-style `/` path separators.

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

## Clean Tree Guard

Before packaging or uploading, remove ignored local artifacts:

- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- generated `examples/openclaw/recalls/recall_*.json`
- generated `examples/openclaw/recalls/recall_*.md`
- local `audit.json` / `audit.md` outputs
- temporary archives

Keep committed fixtures such as `examples/audit_reports/openclaw_audit.json` and `examples/openclaw/recalls/sample_recall_digest.*`.
