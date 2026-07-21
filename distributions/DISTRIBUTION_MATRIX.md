# M1 Distribution Matrix

Distributions assemble package public APIs and contain no runtime logic.

| Distribution | Runtime | Status |
| --- | --- | --- |
| `nollm-bare` | Core | Active addressed Core API |
| `nollm-minimal` | Core, Snapshot, Access | Active minimal Evidence-to-Recall path |
| `nollm-debug` | Minimal plus Trace | Active; TraceInspector, geometry generator, and capability validator are selected development tools |
| `nollm-audited` | Minimal, Trace, Audit skeleton | Composition only; Audit is not productized |
| `nollm-openclaw` | Minimal plus active Access-only adapter | Rev4 collision-free Reader and contextual Writer are active; v6 relational growth remains IN_PROGRESS |

No active distribution references `reference/python/nollm/grf` or uses
`GRFFacade` as its runtime entrypoint. Trace and Audit do not alter Core
correctness.

The OpenClaw adapter is an active Windows Host integration, not a Core runtime
dependency. Its mutable Evidence path is run-scoped and disabled or rotated
before an immutable frozen artifact is published.
