# Nollm Execution Policy

Nollm delivery uses one project branch plus one synthetic orphan evidence branch in a Git bundle. Raw diagnostics, config backups, raw Gateway logs, and raw runtime transcripts stay private and local by default.

Sanitized diagnostic capsules are separate share artifacts. For W2-03R and later public evidence, they must be structured JSON/Markdown only: no zip files, raw logs, traceback windows, raw transcripts, real memory text, secrets, full session or run identifiers, private config backups, host names, absolute paths, or full home paths.

If `origin` is absent, delivery records `remote_status = pending_not_configured`. If `origin` is present, delivery pushes the project and evidence branches and verifies both refs with `git ls-remote`.

Integration failures block only the affected live validation, cutover, or release. They do not block unrelated Nollm Core, native-store, recall, documentation, or focused unit-test work.

Hard stops require immediate rollback or stop: unintended legacy-file mutation, wrong target configuration mutation, failed rollback, secret exposure, or an unavailable Gateway after cutover.

W2-03 evidence is quarantined for redaction failure and must not be reused as publishable runtime proof. W2-03R evidence must be a new orphan branch with strict content gates.
