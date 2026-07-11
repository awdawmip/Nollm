# Core Public API Changelog

This task binds the active Core public surface to `CORE_PUBLIC_API_ALLOWLIST.json`.

Removed from public Core ownership:

- `CellStore`, `FileCoreStateStore`
- `CoreClientLease`, `CoreTransaction`
- `ConsistentStatePort`
- `CoverageTemplateCompiler`, `CompilerMetadata`
- `NullTraceSink`, `safe_emit`, legacy `TraceEvent`

Replacements:

- Snapshot owns `ConsistentStatePort` and composes through `CoreRuntime.export_state_bytes()` / `import_state_bytes()`.
- Trace owns Null, Memory, JSONL, Metrics, Composite sinks and inspection.
- Lab owns template compilation and generates the canonical Core runtime artifact.
- Access owns trusted local composition and rollback without Core-issued capabilities.

This is a capability baseline change, not a sealed or final API declaration.
