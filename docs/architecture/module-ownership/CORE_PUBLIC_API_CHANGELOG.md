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

## 2026-11-22: support pressure and geometric experiments

Added `IncomingCoverage`, `IncomingCoverageMember`,
`incoming_coverage_candidates` and `incoming_coverage`. These compute the complete
incoming native up footprint locally; they do not persist a reverse relation index.

Added `CoverageStencil`, `coverage_stencil_q40`, `coverage_sample_offsets_q40`,
`nearest_axial_q40` and `normalize_q16_weights` so Lab can reuse the admitted
integer stencil, tie rule and normalization through an explicit public surface.
The existing coverage outputs, state format and runtime operations are unchanged.
Lab variable-frame/twist arithmetic has its own experimental numeric contract.
