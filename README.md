# Nollm W2-03 Target-Bound Active Trial Evidence

Project branch: eature/nollm-target-bound-active-trial-diagnostics
Project commit: $commit
Evidence branch: $branch

This orphan branch contains sanitized evidence only. Raw OpenClaw logs, private config backups, full traceback windows, full trial transcripts, and legacy memory file contents are intentionally excluded.

## Result

- Target-bound plan: PASS.
- diagnose: PASS; sanitized zip committed under rtifacts/.
- pply: PASS; no automatic rollback was needed.
- ssert-runtime: PASS; active memory slot is 
ollm and trial agent deny set is complete.
- Live marker trial: PASS for MIST-COPPER-81, PINE-EMBER-92, RIVER-ONYX-03; weather no-match did not leak markers.
- Rollback: PASS.
- Reapply: PASS; final local OpenClaw state restored to W2-03 active trial config.
- Legacy sources unchanged: PASS.

## Tests

- Python focused tests: 67 passed in 6.63s.
- Provider npm tests with absolute python.exe: 98 passed, 0 failed.

See vidence/w2-03-summary.json for artifact hashes and structured results.
