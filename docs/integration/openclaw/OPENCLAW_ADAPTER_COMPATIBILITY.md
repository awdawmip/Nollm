# OpenClaw Adapter Compatibility

This document records the upstream baseline and compatibility decisions for
Nollm's OpenClaw integration.

## Upstream baseline

| Property | Value |
| --- | --- |
| Repository | `https://github.com/openclaw/openclaw` |
| Commit | `dc9c11be917ebdc711b956250aa80a8e5b47bea6` |
| Declared version | `2026.6.9` |
| Node engine | `>=22.19.0` |

This commit is the initial adapter target for F0-01. It is recorded in the
delivery receipt and integration harness output. If a different commit is
required, it must be updated deliberately, not silently.

## Memory-slot contract

OpenClaw exposes the following seams used by the Nollm provider:

- `plugins.slots.memory` -> single active memory provider selection.
- `api.registerMemoryCapability(...)` -> memory runtime / prompt builder / flush plan.
- `api.on("agent_turn_prepare", ...)` -> private recall injection.
- `api.on("agent_end", ...)` -> capture receipt enqueue.
- `before_compaction` / `after_compaction` -> reserved for F1 checkpoint seam.

F0 implements the first four. Compaction hooks are registered only if the host
supports them; they are no-ops in F0.

## Backend discriminant shim

OpenClaw's host discriminant for memory runtime status and backend config only
accepts `backend: "builtin" | "qmd"`. Because Nollm is neither, the
compatibility runtime returns:

```json
{
  "backend": "builtin",
  "provider": "nollm",
  "custom": {
    "backendKind": "nollm",
    "compatibilityShim": true
  }
}
```

This is a host-interface workaround. It does **not** mean Nollm uses SQLite,
vector search, or the built-in memory implementation. It is documented as
`FA-ISSUE-01`.

## CLI limitation

At the target commit, `openclaw plugins build --entry <path>` and `openclaw
plugins validate --entry <path>` call `loadToolPlugin()` and reject entries that
use `definePluginEntry({ kind: "memory" })`:

```text
plugin entry does not expose defineToolPlugin metadata: ./dist/index.js
```

The Nollm provider is intentionally a memory plugin, not a tool plugin, so this
is an upstream limitation. The integration harness runs the CLI commands,
records their failure, and then performs a direct SDK load test as the
alternative verification. See `FA-ISSUE-09`.

## Companion vs provider

Two packages coexist:

| Package | Plugin id | Kind | Role |
| --- | --- | --- | --- |
| `@nollm/openclaw-memory-companion` | `nollm-memory-companion` | tool | Historical/experimental companion surface that exposes geometry navigation tools and delegates to legacy `memory-core`. |
| `@nollm/openclaw-memory` | `nollm` | memory | Functional Alpha active memory provider. |

The companion is **not** the active memory route. The provider is **not** a
tool wrapper. They must not be confused.

## Verification

The integration harness in
`integrations/openclaw/nollm-memory-provider/scripts/integration-harness.mjs`
verifies:

1. exact upstream commit;
2. OpenClaw build presence;
3. provider TypeScript build;
4. direct SDK load with `id === "nollm"` and `kind === "memory"`;
5. `openclaw plugins build/validate` are executed and their failure is
   attributed to the known CLI limitation.

No model credentials are required.
