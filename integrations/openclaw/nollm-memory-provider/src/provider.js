import { normalizeConfig } from "./config.js";
import { NollmBridgeRuntime } from "./bridge-runtime.js";
import { MemoryOperationRegistry, createMemoryGetFactory, createMemorySearchFactory } from "./memory-tools.js";

export function buildNollmMemoryPrompt(params = {}) {
  const tools = params.availableTools instanceof Set ? params.availableTools : new Set(params.availableTools ?? []);
  if (!tools.has("memory_search") || !tools.has("memory_get")) return [];
  return [
    "Nollm owns long-term memory for this OpenClaw agent.",
    "Use memory_search when prior user facts or decisions may matter. The tool may require repeated calls through one geometry Surface and one Locality before it returns results.",
    "Use memory_get only with a nollm:// path returned by memory_search.",
    "If memory_search returns no results, do not claim to remember. Geometry paths are navigation evidence, not truth proof."
  ];
}

export function createNollmProvider(api) {
  const config = normalizeConfig(api.pluginConfig ?? {}, (value) => api.resolvePath?.(value) ?? value);
  const bridge = new NollmBridgeRuntime(config);
  const registry = new MemoryOperationRegistry({ ttlMs: config.operationTtlMs });

  api.registerMemoryCapability({
    promptBuilder: buildNollmMemoryPrompt,
    flushPlanResolver: () => null,
    publicArtifacts: { async listArtifacts() { return []; } }
  });

  api.registerTool(createMemorySearchFactory({ bridge, registry, config }), { names: ["memory_search"] });
  api.registerTool(createMemoryGetFactory({ bridge, config }), { names: ["memory_get"] });

  api.registerService?.({
    id: "nollm-memory-runtime",
    start() {
      if (!bridge.available) {
        api.logger.warn("Nollm memory slot is installed but no packaged runtime is available; memory_search/get fail open until runtime installation completes.");
      }
      if (config.autoCapture) {
        api.logger.warn("Nollm autoCapture is requested but the Formation Loop writer has not yet been migrated into the publishable memory-slot package.");
      }
    }
  });

  return { config, bridge, registry };
}
