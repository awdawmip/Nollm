# Distribution Matrix

Distributions assemble public module packages. They contain no domain or
product logic.

| Distribution | Runtime modules | Optional | Development only |
| --- | --- | --- | --- |
| `nollm-bare` | Core | None | None |
| `nollm-minimal` | Core, Snapshot, minimal Access API | None | None |
| `nollm-openclaw` | Core, Snapshot, Access, OpenClaw | None | None |
| `nollm-debug` | OpenClaw composition plus Trace | Inspectors | Selected Lab tools |
| `nollm-audited` | OpenClaw composition plus Trace and Audit | External source-store connector | None |

Trace and Audit are optional observers of public contracts. Disabling either
does not alter Core correctness or its current-state result.
