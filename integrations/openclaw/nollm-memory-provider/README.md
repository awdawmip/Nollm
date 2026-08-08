# @nollm/openclaw-memory

V3.14 beta of the official OpenClaw memory-slot integration.

## Current status

Implemented offline:

- `kind: memory` plugin identity
- `MemoryPluginCapability` with Nollm prompt and no MEMORY.md flush
- host-scoped `memory_search` / `memory_get` tool factories
- progressive Unified Field Encounter transport through the existing development bridge
- ClawHub-oriented package metadata

Not yet closed:

- packaged platform sidecar
- automatic capture/Formation migration
- clean ClawHub install/update/uninstall
- Windows Provider Live

Development mode may set `pythonExecutable`, `nollmRepoRoot`, and `memoryWorkspace`. Public releases must not require those fields.
