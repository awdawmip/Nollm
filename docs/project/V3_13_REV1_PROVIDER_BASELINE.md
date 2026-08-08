# V3.13 Rev1 Provider/Host Baseline

Date: 2026-08-04

This is the modification-before-code baseline for V3.13 Rev1. It was run on
Windows 10 with PowerShell, Python for Windows, Node 24.17.0, OpenClaw
2026.6.11, and the isolated profile
`v313r1-provider-live-baseline-clean`.

## Provider and host

- Provider/model: `meituan/LongCat-2.0`
- Gateway: loopback-only isolated OpenClaw Gateway on port `19714`
- Statement, memory, capture, evidence, and session state: external `D:\Nollm\workspaces\v313r1-provider-live-baseline-clean`
- Main-agent session records: 43 at the final baseline snapshot
- Hidden dream-agent sessions: 1 observed; no zero claim is made
- Main visible requests with valid JSON output: 43
- Main Provider attempts: 43
- Main tool calls: 15, concentrated in the first natural write; later natural turns were still captured by the host hook

## Matrix

| Sample | Count | Result |
|---|---:|---|
| Relevant query | 10 | Provider `ok`; pending fallback made the initial captured statement visible |
| Explicit NONE query | 5 | Provider `ok`; no Nollm statement was intentionally requested |
| Write: new/reuse/revision | 12 | 8 new, 2 reuse, 2 revision; Provider `ok` |
| Mixed read/write | 8 | Provider `ok`; recalled W01-W08 and recorded M01-M08 |
| Restart | 2 | Both restored a healthy isolated Gateway; the first wrapper launch failed and was recovered with direct `node.exe` launch |
| Concurrency | 2 successful | Two independent `node.exe` agent processes returned Provider `ok` concurrently |

Additional concurrent argument-quoting failures are retained as raw evidence;
they are CLI launch failures, not Provider failures, and are excluded from the
successful concurrency count.

## Timing and integrity

- Main request wall time: p50 `8107 ms`, p95 `28234 ms`, max `34518 ms`
- Final prompt UTF-8 bytes: p50 `51`, p95 `101`, max `116` for the captured JSON sample set
- Valid Capture records: `43`
- Capture event states at the snapshot: `captured=43`, `processing=13`, `retryable_defer=11`
- Durable terminal commits observed: `0`
- Raw Capture byte-integrity failures: `0` among observed records
- Duplicate/orphan records: none observed in the raw capture/evidence inventory
- The initial write and subsequent writes were visible in host responses, but visibility is not treated as durable commit evidence

The background Proposition Writer repeatedly timed out or deferred on the
isolated live profile. This is recorded as the baseline Capture-to-commit
blocker; it is not converted into a fabricated admission result.

## Evidence

Raw JSON, restart health, capture state, and the derived summary are outside
the repository at:

`D:\Nollm\artifacts\V3_13_REV1_BASELINE`

The summary is `baseline-summary.json`. The implementation stage and the
post-stage comparison must use the same sample classes and keep this baseline
unchanged.
