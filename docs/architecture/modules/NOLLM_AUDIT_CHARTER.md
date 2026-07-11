# Nollm Audit Charter

Purpose: optional host/user/session, source-handle, model/prompt, Access-decision, and Core-command-result records.

- Persistent state: append-only audit records and reports.
- Temporary state: correlation and report buffers.
- Public API: record/query/report over Access and optional Trace contracts.
- Forbidden API: Core dependency, mutation authority, fact/truth adjudication.
- Dependencies: Access contracts and optional Trace contracts.
- Failure: report loss is observable but cannot affect Core correctness.
- Distributions: audited only by default.
- Future repository: `nollm-audit`.
- Current sources: ledgers, delivery records, and model-run evidence require later split/classification.
