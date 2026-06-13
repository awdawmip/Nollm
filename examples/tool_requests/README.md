# Tool Request Examples

Top-level `*.json` files in this directory are runnable examples.

Run them from `reference/python`:

```bash
python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/orient.json
python3 -m nollm.cli tool ../../examples/tool_requests/recall_scale_scan.json
```

Some examples mutate derived output. `recall_scale_scan.json` may create generated recall files under the target notebook's `recalls/` directory when run manually.

Tests execute mutating examples against temporary notebook copies. Generated `recall_*.json` and `recall_*.md` files are not source memory unless they are explicitly committed as example fixtures.

Files under `templates/` are templates and may contain placeholders. They are not expected to run as-is.
