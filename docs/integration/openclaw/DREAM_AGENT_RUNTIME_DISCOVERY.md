# Dream Agent Runtime Discovery

Date: 2026-07-12

## Host

- Windows 10/11, PowerShell, Python for Windows, Git for Windows.
- OpenClaw `2026.6.11` with the real Gateway lifecycle.
- Live model: `meituan/LongCat-2.0`.
- Plugin id: `nollm-formation`, plugin version `0.3.0`.

## Lifecycle Truth

The Host exposes `before_agent_run`, `message_received`, `llm_output`,
`message_sent`, and `agent_end`. Channel delivery uses `message_sent`. The
2026.6.11 CLI/Gateway path is labeled `webchat` but does not emit
`message_sent`, so the adapter uses `agent_end` as the closest official
post-reply lifecycle event for that path. Live evidence records
`main_reply_delivered_at < dream_started_at` for all 45 runs.

The hook schedules work without awaiting the subagent. Every live spawn used
`deliver=false`; no announce or second assistant message was observed. Failed
Dream parsing remained fail-open and did not change the main-chat exit status.

## Model And Tool Binding

`modelMode=inherit` omits a model override and therefore uses the Host session
model and credentials. `modelMode=dedicated` passes the configured model after
`allowedModels` validation. The dedicated agent has an empty workspace, denies
message/session delegation tools, and allows only `read`. OpenClaw 2026.6.11
requires at least one callable tool for model preflight under its minimal
profile; live transcripts showed zero tool calls.

The plugin does not call provider HTTP endpoints and does not expose a
Formation tool to the main agent. Production defaults disable debug trace and
subagent transcript persistence.

## Limits

The Gateway fallback is tied to observed OpenClaw 2026.6.11 lifecycle behavior
and should be rechecked when the Host adds a true WebChat delivery hook. This
stage did not validate other operating systems or providers.
