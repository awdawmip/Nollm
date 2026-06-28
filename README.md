# Nollm W2-03R Sanitized Evidence

This orphan branch contains structured sanitized evidence only.

Project branch: feature/nollm-main-agent-active-cutover-transactional-closure
Project commit: 7b3d64586b7b605d78652fa2081241540f929857
Evidence branch: evidence/w2-03r-main-agent-active-cutover-20260628T094800Z

Result summary:

- AGENTS baseline restored from W2-02 parent before implementation.
- Target agent: main.
- Config binding probe: PASS.
- Provider build and local install route: PASS.
- Apply: PASS.
- Runtime assertion: PASS; observed tool catalog is session_status only.
- Main-agent live trial: PASS for SUNSET-MICA-41, WILLOW-EMBER-52, AURORA-SLATE-63.
- Temporal report no-save check: PASS.
- Local replay check: PASS.
- Rollback and reapply: PASS.
- Legacy source hash unchanged checks: PASS.
- W2-03 evidence: quarantined for redaction failure, not for share.

See evidence/w2-03r-summary.json.
