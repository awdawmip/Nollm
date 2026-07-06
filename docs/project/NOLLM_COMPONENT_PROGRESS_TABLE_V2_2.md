# Nollm Component Progress Table V2.2

| Component | Layer | Status | Notes |
| --- | --- | --- | --- |
| V2 layer constitution | L0 | V2L0 in progress | Establishes active Core-to-Terminal dependency direction. |
| Evidence identity kernels | L1 | accepted components present | Preserve evidence identity and projection boundaries. |
| Geometry and field services | L2 | accepted components present | Deterministic domain services only. |
| DG5 | L2 validation | sealed / validation | Evidence-preserving trace compaction; does not replace original evidence or facts. |
| DG6 | L2 validation | sealed / validation | Isolated verification-only snapshot-compaction projection; does not enter core recall or fact path. |
| DG7 | L2 validation | sealed / validation | Explicit reference-runtime positive verification; not production runtime, daemon, network service, or terminal integration. |
| Historical Engineering RC hash manifest | historical validation | C3 rebaseline | Only `reference/python/tests/test_geometry.py` canonical `size_bytes` / `sha256` was rebaselined because the complete TQ1 matrix still collects the historical RC artifact integrity suite. This does not make Engineering RC a current V2 runtime. |
| Capture / Admission / Assembly workflows | L3 | accepted components present | Core workflows; no terminal or adapter ownership of facts. |
| HX1 | L4 | accepted asset | Trusted host staged execution bridge and preflight binding. |
| CX2 | L4 | accepted asset | External cortex conformance and public envelope boundary. |
| HCG1 | L5 | accepted | File Capture Adapter. |
| HAG1-C1R | L5 | accepted, unpromoted | File Admission Adapter candidate at `0e0d21c1747d3113b5c19d39e920eb60bf5e3c5f`. |
| OpenClaw | L5/L6 future | frozen migration asset | Not current runtime and not Core dependency. |
| V1 / MT1 / pre-V2 prototypes | historical | retired | Preserved for audit and migration reference only. |

Local main baseline for this table is
`8bb324a3a5de46bebb6eadd217820627a971e2a0`; each delivery machine must recheck
local and remote refs before promotion or publication.

V2L0 remains a candidate until C3 evidence and acceptance audit are complete.
HAG1-C1R remains accepted and unpromoted.
