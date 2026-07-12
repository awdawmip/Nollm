# Dream Agent Compatibility Migration Report

Date: 2026-07-12

V3.3 replaces active exact-span Formation with LLM-produced bounded
`DreamMemoryDraft` values. Active Access APIs no longer require source spans,
and new durable writes use `FileStatementStore` with schema
`nollm_access_statement_v1`.

The old `EvidenceStore` API remains as a warning-emitting compatibility wrapper.
Files with schema `nollm_access_evidence_v1` remain readable and can be reopened
through the new Store. New writes never emit the legacy schema. Existing
`AccessRuntime` capture methods remain available and delegate through the
compatible path.

The previous visible `nollm_form_statement` main-agent tool and global Host
allow-list entries were removed during installation cleanup. The plugin now
registers hooks only. No migration path writes Core state, performs Placement
or Recall, preserves full conversation transcripts, or infers semantics in
Python.

Package tests cover legacy workspace reopen, new canonical writes, public
runtime compatibility, and wrong-type rejection before writes.
