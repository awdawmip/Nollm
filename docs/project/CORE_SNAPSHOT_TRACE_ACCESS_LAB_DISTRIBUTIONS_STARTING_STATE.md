# Core / Snapshot / Trace / Access / Lab / Distributions Starting State

## Input

- Bundle: `nollm_m1c8_workspace_callback_bound_store_runtime_config_20260711_c040915e.bundle`
- SHA-256: `627b5624325832fa9c15a69c67b54a849ee093d3fef1f41f1574fd38c0412337`
- Input HEAD: `c040915e6f548ab661998dca51b155f76aa74970`
- Work branch: `codex/core-snapshot-trace-access-lab-distributions-boundary-reallocation`
- Environment: Windows, PowerShell, Python for Windows, Git for Windows; `zstandard` available.

Bundle verify, list-heads, complete-history status, detached input identity, clean initial worktree, and connectivity fsck passed.

## Expected Vector

```text
CORE +10% | SNAPSHOT +5% | TRACE +5% | ACCESS +5% |
LAB +10% | DISTRIBUTIONS +5% | HISTORY/AUDIT/OPENCLAW 0%
```

Charter review did not require a task-start adjustment. Starting estimates remain Core 65%, Snapshot 45%, Trace 35%, Access 55%, Lab 40%, Distributions 35%, History/Audit 10%, and OpenClaw 25%. Confidence is medium-high for Core/Access, medium for Snapshot/Lab/Distributions, and medium-low for Trace because its implementation test surface was initially one test.

## Reproduced Input Gates

```text
manifest = 1453 / 1453; unclassified = 0
production violations = 0; production cycles = []
Core = 56 passed
Snapshot = 5 passed
Trace = 1 passed
Access = 51 passed
M0 = 18 passed
architecture / forbidden / hygiene = 8 passed
GRF = 112 passed
geometry parity = 9 / 9
M1-C8 minimal E2E = passed
```

## Withdrawn Routes And Limits

The active task withdraws capability issuance, callback attack isolation, shadow Store defenses, dynamic template compilation in Core, and public Store/fault-hook contracts. It does not authorize relation indexes, graph/vector/embedding, Python semantic Placement, OpenClaw Live, models, corpora, PB scale, History/Audit productization, or remote repository work.

This starting state is a traceable capability baseline, not a sealed or final conclusion.
