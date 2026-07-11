# M1 Distribution Matrix

Distributions assemble package public APIs and contain no runtime logic.

| Distribution | Runtime | Status |
| --- | --- | --- |
| `nollm-bare` | Core | Active addressed Core API |
| `nollm-minimal` | Core, Snapshot, Access | Active minimal Evidence-to-Recall path |
| `nollm-debug` | Minimal plus Trace | Active; inspectors/Lab tools remain development-only |
| `nollm-audited` | Minimal, Trace, Audit skeleton | Composition only; Audit is not productized |
| `nollm-openclaw` | Minimal plus adapter migration asset | Live activation paused pending future E2E |

No active distribution references `reference/python/nollm/grf` or uses
`GRFFacade` as its runtime entrypoint. Trace and Audit do not alter Core
correctness.
