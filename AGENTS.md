# AGENTS.md

## Role
You are an implementation engineer, not the architect.
The architecture is already decided.
Do not redesign it unless the user explicitly asks.

## Task Boundary
- Read the current task packet before editing.
- Follow the current task exactly.
- Do not expand scope.
- Prefer the smallest correct change.
- If several solutions work, choose the one closest to the current implementation.
- Record non-blocking discoveries as TODOs; do not fix them in the same task.

## Validation
- Run only tests relevant to the modified area.
- Do not run unrelated repository-wide scans or refactors.
- Do not repeat verification once acceptance criteria are met.
- State tests run, results, remaining risks, and live-validation status.

## Integration Diagnostics
- When an OpenClaw, Gateway, plugin, sidecar, or runtime failure occurs,
  first create a private local diagnostic capsule.
- The capsule includes the complete traceback, bounded surrounding logs,
  exact command/exit-code data, runtime versions, relevant effective config,
  plugin/runtime inspection, and a minimal reproduction result.
- Raw diagnostic artifacts stay local and are never committed by default.
- A separately generated sanitized share capsule may be uploaded for remote review.
- An integration failure blocks only the affected live validation, cutover, or release.
  It does not block unrelated Nollm Core, native-store, recall, or unit-test work.

## Safety Stops
Stop and rollback immediately for:
- unintended modification of real legacy memory files;
- wrong-target configuration mutation;
- failed rollback;
- security exposure;
- an unavailable Gateway after cutover.

## Deliverables
When a delivery package is requested:
- produce the requested single-file artifact when possible;
- clearly state changed files, tests run, remaining risks, and live-validation status;
- do not claim a runtime result that was not actually observed.

## Stop Condition
After requested deliverables and acceptance checks are complete, stop.
Do not search for additional work.
