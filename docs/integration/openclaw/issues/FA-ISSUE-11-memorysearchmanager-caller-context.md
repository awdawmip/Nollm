# FA-ISSUE-11: OpenClaw MemorySearchManager.readFile needs caller/session context for session-bound authorization

## Status
- **Discovered in**: F0-04 Real OpenClaw Loader Capture Contract Closure
- **Target commit**: `dc9c11be917ebdc711b956250aa80a8e5b47bea6`
- **Impact**: The Nollm compatibility facade cannot claim true session-bound ref authorization through the existing OpenClaw manager interface.

## Observation
The OpenClaw `MemorySearchManager.readFile()` contract accepted by the Nollm compatibility facade accepts only:

```text
{ relPath: string; from?: number; lines?: number }
```

There is no parameter for caller agent, session, run, or session key. The Nollm facade can bind issued refs to:

- process-local manager instance (via manager generation),
- agent id,
- field revision id,
- expiry timestamp,
- query hash.

Because `readFile()` does not receive caller/session context, the facade cannot verify that a ref issued in one session is being read by the same session. It can only verify that the ref is valid for the current manager/agent/revision.

## Why this matters
F0-03 originally described compatibility refs as "session-bound". That claim is not supportable through the `MemorySearchManager.readFile()` contract alone. Honest F0 documentation must describe the refs as process-local, manager-scoped, agent-scoped, and revision-bound, and must not claim session-level authorization.

## Request to upstream
1. Add an optional `callerContext` or `sessionKey` parameter to `MemorySearchManager.readFile()`, or attach caller/session context to the manager construction parameters.
2. Document whether the compatibility manager is expected to enforce per-session authorization, or only per-manager/per-agent authorization.
3. If per-session authorization is out of scope, document that callers of `readFile()` are responsible for their own session scoping and that the manager does not provide cross-session isolation.

## F0-04 handling
- The F0-04 compatibility facade is explicitly documented as manager-scoped (not session-bound).
- `search()` records `opts.sessionKey` as audit metadata only; it does not rely on it for authorization.
- `readFile()` continues to reject unissued, cross-manager, expired, and revision-mismatched refs.
