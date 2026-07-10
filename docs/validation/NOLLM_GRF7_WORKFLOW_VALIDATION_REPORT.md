# NOLLM GRF7 Workflow Validation Report

Gate I executes coding, research, document, and long-running-agent fixtures.
Each compares lexical, vector-like, explicit graph, graph+vector, and GRF
implementations. Baselines remain experiment-local and are not imported into
Core.

GRF returns the exact source-backed item for all four workflows, reduces each
100-item context to one result, reports 0/1 false relations, and retains a
replayable fallback. It does not maintain pairwise object edges. The report
does not claim general quality beyond these deterministic fixtures.

Raw: `experiments/grf/results/GRF7_WORKFLOW_RAW.json`.

`GATE_I_PASS`.
