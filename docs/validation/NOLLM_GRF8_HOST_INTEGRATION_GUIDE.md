# GRF8 Host Integration

Hosts use the shared `grf_host_v2` facade/runtime contract for `capture`,
`capture_source`, `place`, `admit`, `recall`, `replay`, `source_get`,
`revise`, and `retire`. The File Host, Codex fixture, and OpenClaw fixture are
adapters: they map host requests and persist request ownership only. They do
not alter Core geometry or own evidence truth.

Run the complete fixture lifecycle on Windows with:

```powershell
$env:PYTHONPATH = ".;reference/python"
python experiments/grf/run_grf8_host_integration.py
```

Each fixture captures evidence, places and admits it, recalls its admission,
obtains its original source, ingests and revises a file, retires that source,
restarts the adapter, and replays the original admission. The runner reports
each capability separately and fails if any host differs from the contract.
