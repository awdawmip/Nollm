# Nollm Execution Policy

Nollm delivery uses one project branch plus one synthetic orphan evidence branch in a Git bundle. Raw diagnostics, config backups, raw Gateway logs, and raw runtime transcripts stay private and local by default.

Sanitized diagnostic capsules are separate share artifacts. They may include redacted command shapes, bounded logs, traceback text, runtime versions, and outcome summaries, but must not include raw transcripts, real memory text, secrets, full session or run identifiers, private config backups, or full home paths.

If `origin` is absent, delivery records `remote_status = pending_not_configured`. If `origin` is present, delivery pushes the project and evidence branches and verifies both refs with `git ls-remote`.

Integration failures block only the affected live validation, cutover, or release. They do not block unrelated Nollm Core, native-store, recall, documentation, or focused unit-test work.

Hard stops require immediate rollback or stop: unintended legacy-file mutation, wrong target configuration mutation, failed rollback, secret exposure, or an unavailable Gateway after cutover.
