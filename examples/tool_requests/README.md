# Tool Request Examples

Top-level `*.json` files in this directory are runnable examples.

Run them from `reference/python`:

```bash
python3 -m nollm.cli tool ../../examples/tool_requests/audit_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/annotations_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/ledger_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/history_openclaw_card.json
python3 -m nollm.cli tool ../../examples/tool_requests/inspect_openclaw.json
python3 -m nollm.cli tool ../../examples/tool_requests/orient.json
python3 -m nollm.cli tool ../../examples/tool_requests/read_openclaw_card.json
python3 -m nollm.cli tool ../../examples/tool_requests/review_openclaw.json
```

Top-level examples are safe against committed OpenClaw: they are read-only or non-mutating and do not create generated recall files.

Generated-output examples live under `generated_output_examples/`. `generated_output_examples/recall_scale_scan.json` calls `nollm.recall` and may create generated recall files under the target notebook's `recalls/` directory when run manually. Run it against a temporary notebook copy or clean generated `recall_*.json` and `recall_*.md` files before committing.

Files under `templates/` are templates and may contain placeholders. Mutating examples belong there unless a test explicitly runs them against a temporary notebook fixture.
