# M1 Starting State

Recorded: 2026-07-11

```text
branch: codex/m1-core-handle-access-command-extraction
baseline HEAD: f62c21a72e416f80b9f4baf6eaa613c91257fc81
status: clean
production findings: 9
production cycles: 1
migration dependencies: 44
```

Baseline checks reproduced:

```text
ownership manifest check: tracked=1328 unclassified=0 unchanged
ownership manifest valid: tracked=1328 rows=1328
module boundaries: production=9 baseline=9 new_production=0 resolved=0
production_cycles=1 new_cycles=0 migration=44
```

M0C1 commits `8a596b7f`, `3f589460`, `ce2a944d`, and `f62c21a7`
are present. The paused checkpoint `95d8dd4d` and preserved corpus results remain
in history. M1 performs no reset, remote-ref mutation, corpus execution, model
call, or OpenClaw Live activation.
