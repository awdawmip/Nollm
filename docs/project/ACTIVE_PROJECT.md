# Active Project Basis

- Highest principle: [NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md](../architecture/NOLLM_FIRST_PRINCIPLES_AND_ANTI_DRIFT_20260711.md)
- Active architecture: [V3.8 Translation-Covariant Physical Coverage](../architecture/NOLLM_ARCHITECTURE_BOOK_V3_8_TRANSLATION_COVARIANT_PHYSICAL_COVERAGE_20260714.md)
- Active route: [V3.8 Coverage Reuse Route](NOLLM_ROUTE_BOOK_V3_8_TRANSLATION_COVARIANT_COVERAGE_REUSE_20260714.md)
- Current status: [NOLLM_CURRENT_STATUS.md](NOLLM_CURRENT_STATUS.md)
- Module ledger: [NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md](NOLLM_CURRENT_STATUS_MODULE_PROGRESS_LEDGER.md)
- Current task: [Translation-Normalized Coverage And P1 Closure](tasks/NOLLM_C_A_O_L_D_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_RESIDUAL_ENTRY_AND_P1_CLOSURE_TASK_20260715.md)

Current state:

```text
TRANSLATION_NORMALIZED_PHYSICAL_COVERAGE_SINGLE_ENTRY_P1_VALIDATED
```

Input checkpoint:

```text
66684dc51339544ad4a846614ed31aa52c7ddc24
```

`66684dc5` is retained as evidence for:

```text
historical geometry reuse and two bounded-window Oracles；
complete-address Coverage inputs and physical/Surface address separation；
Order 0..8 Surface API and cross-layer kernel path；
controlled single-entry cross-layer Recall；
truthful IN_PROGRESS delivery when P1 did not write。
```

It is not active evidence for:

```text
large-coordinate translation-normalized Coverage；
explicit physical residuals；
LLM-selected unique physical entry；
P1 Formation-to-restart-Recall closure。
```

Those input-checkpoint gaps are closed by the current branch at implementation
HEAD `9296869281cf3d7d8a68fcf00a4628e75f5915c8`. The active evidence is recorded
in `docs/project/CAOLD_TRANSLATION_NORMALIZED_COVERAGE_PHYSICAL_ENTRY_P1_REPORT.md`.

Current declared boundary:

```text
signed-64 q/r; physical layer -64..64; chart_id=default; phase=null;
source-centered Coverage; explicit physical residual;
one Host-selected physical entry; P1 write and restart Recall.
```

Gate 7 records 1818 tracked files, 1818 ownership rows, zero unclassified
files, zero production boundary violations, zero production cycles, and a
complete post-Manifest regression pass. Final delivery identity is supplied by
the immutable commit, tag, and verified bundle. No follow-on capability is
authorized by this status file.

The next candidate is PB-scale performance research, but it requires a new,
separately approved taskbook. It is not opened by this closure.

V3.7 and its completion Tag remain historical. They do not override V3.8.
