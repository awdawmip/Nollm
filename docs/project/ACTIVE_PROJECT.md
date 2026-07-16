# Active Project Basis

- Highest principle: [NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md](../architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)
- Active project book: [V3.4 Core Function Priority](NOLLM_PROJECT_BOOK_V3_4_CORE_FUNCTION_PRIORITY_20260713.md)
- Active architecture: [V3.9 Bounded Approximate Hex Coverage](../architecture/NOLLM_ARCHITECTURE_AMENDMENT_V3_9_BOUNDED_APPROXIMATE_HEX_COVERAGE_20260715.md)
- Active route: [V3.9 Fast Structural Geometry](NOLLM_ROUTE_BOOK_V3_9_FAST_STRUCTURAL_GEOMETRY_20260715.md)
- Current task: [Real Memory Commit And Recall Latency Baseline](tasks/NOLLM_A_O_L_D_REAL_MEMORY_COMMIT_AND_RECALL_LATENCY_BASELINE_TASK_20260716.md)
- Input checkpoint: `26bd0ae68470ef8d1396014884e305cc1c3ab7ef`
- Gate 0 checkpoint: `b16ca3bf979ca054341531b9df92388fc02b805f`
- Evidence/report checkpoint: `71ba080bf8d2ec196ced294c1392d0f02027ac3d`
- Report: [AOLD Real Memory Commit Recall Latency Baseline Report](AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_REPORT.md)

Current state:

```text
AOLD_REAL_MEMORY_COMMIT_RECALL_LATENCY_BASELINE_IN_PROGRESS
```

The task measured the existing layer-0 Formation, durable Placement, and hidden Recall injection path in 12 write host turns and 12 Recall host turns. The frozen evidence has 110 records and SHA-256 `6d3203649b07acc89a760ebc41cddbf38551bdddba5565b45f3f5ea78d0948fb`. The result remains IN_PROGRESS because the OpenClaw CLI host exposed `agent_end` rather than the required `message_sent`, leaving 0 formally correlated durable write turns and 0 visible-answer Recall correlations. No optimization is authorized by this baseline task.
