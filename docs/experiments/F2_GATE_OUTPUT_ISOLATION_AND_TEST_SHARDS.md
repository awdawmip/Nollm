# F2 Gate Output Isolation and Test Shards

F2 keeps internal gate runs from mutating tracked example fixtures by default.
Runtime reports are written under ignored `out/nollm_runtime/` paths unless an
explicit `--output` path is supplied.

Safe local gate runs from `reference/python`:

```bash
python scripts/run_nollm_local_gate.py --skip-pytest
python scripts/run_nollm_local_gate.py --include-pytest --pytest-timeout 5
```

Tracked example reports are refreshed only by explicit output commands:

```bash
python scripts/run_nollm_local_gate.py --skip-pytest --output ../../examples/openclaw_dream/local_gate_report.json
```

Deterministic test shards:

```bash
python scripts/run_nollm_test_shards.py --profile collect
python scripts/run_nollm_test_shards.py --profile dream --timeout 120
python scripts/run_nollm_test_shards.py --profile core --timeout 120
python scripts/run_nollm_test_shards.py --profile docs --timeout 120
python scripts/run_nollm_test_shards.py --profile full --timeout 120
```

Shard reports are written under `out/nollm_runtime/test_shards/` by default and
record status, return code, timeout state, duration, output tails, and missing
test files.

These runners are experimental internal infrastructure. They do not write
cards, confirm placement, create anchors, expand stable recall/tool behavior,
or introduce vector, graph, embedding, MCP, or external LLM behavior.
