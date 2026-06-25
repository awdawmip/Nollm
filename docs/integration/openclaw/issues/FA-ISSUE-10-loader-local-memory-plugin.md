# FA-ISSUE-10: OpenClaw target commit lacks a public loader seam for local memory plugins

## Status
- **Discovered in**: F0-04 Real OpenClaw Loader Capture Contract Closure
- **Target commit**: `dc9c11be917ebdc711b956250aa80a8e5b47bea6`
- **Impact**: Blocks F0-04 host proof H1-H10 from running through the actual OpenClaw plugin loader.

## Observation
The OpenClaw distribution at the target commit contains a real `loadOpenClawPlugins(options)` function, but it is located in an internal chunk (`dist/loader-*.js`) and is **not exported** from any public entry point:

- `openclaw` package main (`dist/index.js`) — does not export it.
- `openclaw/plugin-sdk/plugin-runtime` — does not export it.
- `openclaw/plugin-sdk/index` — does not export it.

It is only accessible by importing the internal `loader-*.js` chunk by file name, which is a build artifact hash and not a stable public API.

## Attempted usage
F0-04 `host-integration-check.mjs` attempted to import `loadOpenClawPlugins` from the internal chunk and call it with an isolated OpenClaw config:

```json
{
  "plugins": {
    "enabled": true,
    "slots": { "memory": "nollm" },
    "entries": {
      "nollm": { "enabled": true, "config": { ... } },
      "memory-core": { "enabled": false },
      "active-memory": { "enabled": false }
    },
    "load": { "paths": ["/path/to/nollm-memory-provider"] }
  }
}
```

The loader either fails to discover the local plugin or fails to activate it as the memory slot. The exact exception is recorded in `out/f0-04-integration-harness.json` under `steps.host_integration_load`.

## Why this blocks F0-04
Task D1 explicitly requires:

> F0-04 host test 中禁止：手写 realApi object、直接调用 def.register(realApi)、手动 initializeGlobalHookRunner。必须根据 fixed target commit 的真实 loader/config API，在 repo 外临时 checkout 加载 local Nollm plugin。

Because the target commit does not expose a stable public API for loading a local memory-slot plugin, the F0-04 host proof cannot be completed without relying on internal build artifacts or manually reconstructed host internals.

## Request to upstream
1. Export a stable public function (e.g., `loadOpenClawPlugins`) from `openclaw/plugin-sdk` or the main `openclaw` entry.
2. Document the expected `options` shape for loading a local plugin into a specific slot (`plugins.slots.memory`).
3. Provide a supported way to pass plugin load paths or built plugin directories so that third-party memory providers can be discovered and activated.


## F0-04 harness discovery result

The F0-04 host-integration-check.mjs checked the following public OpenClaw entry points for a loadOpenClawPlugins export:

- openclaw/package-main
- openclaw/plugin-sdk/index
- openclaw/plugin-sdk/plugin-runtime
- openclaw/plugin-sdk/plugin-entry

All checked public entries either did not expose the file or did not export loadOpenClawPlugins. The function is only present in an internal build-artifact chunk (dist/loader-*.js), which is not a stable public seam. The exact discovery log and exported names are recorded in out/f0-04-integration-harness.json under steps.host_integration_load.target_limitation.discoveryLog.
## Workaround in F0-04
If the loader cannot be made to work, F0-04 records `target_limitation: OPENCLAW_LOADER_LOCAL_MEMORY_PLUGIN_LIMITATION` and does not claim Functional Alpha pass.