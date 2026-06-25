# P0-01 Evidence Branch Protocol

This document records the live-run protocol and the required contents of the
orphan evidence branch for P0-01.

## Evidence branch name

    evidence/p0-01-windows-live-preflight-<UTC_TIMESTAMP>

## Required contents

The evidence branch is an orphan branch and must contain only:

    README.md
    synthetic_preflight_report.json
    synthetic_preflight_report.md
    test_commands_and_results.md
    artifact_hashes.json
    remote_push_receipt.json

It must **not** contain:

- The real Windows live preflight report.
- Real workspace/config/state paths or content.
- Real chat transcript content or MEMORY.md content.
- Tokens, secrets, or credentials.
- The OpenClaw checkout, node_modules, venv, cache, or build artifacts.

## Synthetic report rules

- Use the same schema as the live report:
  `nollm.windows_openclaw_preflight.v1`.
- Use placeholder paths such as `%USERPROFILE%/.openclaw` and
  `C:/OpenClaw/example`.
- Mark safety fields exactly as the live report does (`read_only`, all
  mutation booleans `false`).
- Keep the same 12-section Markdown report structure.
- Do not include any real hostname, username, or filesystem metadata.

## Live-run protocol

1. Create a temporary output directory outside the repository.
2. Run `windows-live-preflight.ps1` with `-OpenClawCommand openclaw`.
3. Verify the JSON report has no bare backslashes.
4. Verify the Markdown report has no bare backslashes.
5. Verify neither report contains Bearer tokens, `sk-...`, `ghp_...`,
   `github_pat_...`, or `xox...` patterns.
6. Verify the Markdown report has 12 sections in the required order.
7. Verify safety fields are all `false` / `read_only`.
8. Do not commit the live report to Git or include it in the bundle.

## Push status

After committing, attempt:

    git remote get-url origin
    git push -u origin feature/nollm-p0-windows-live-preflight
    git push -u origin evidence/p0-01-windows-live-preflight-<UTC>
    git ls-remote --heads origin <project-branch>
    git ls-remote --heads origin <evidence-branch>

If `origin` is not configured, record `remote_status = pending_not_configured`
and do not claim the commits are on GitHub.
