# NOLLM GRF7 Real Host Runtime Report

Gate G runs File, OpenClaw, and Codex lifecycle fixtures through real queues,
`GRFHostRequest` parsing, Adapter dispatch, and Core operations. They execute
100,000 mixed requests: 20K each capture/place/admit/recall/replay, with 1,000
timeouts, 100 adapter failures, 1,100 retries, and 100 session restarts.

All requests eventually succeed. Retry is idempotent, restart replay is
deterministic, duplicate Evidence and namespace collisions are zero, and the
Adapter event log is not durable truth. These are lifecycle fixtures, not
claims of connection to external OpenClaw or Codex processes.

Raw: `experiments/grf/results/GRF7_HOST_RUNTIME_RAW.json`.

`GATE_G_PASS`.
