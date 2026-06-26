import type {
  MemoryPluginRuntime,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawConfig } from "openclaw/plugin-sdk/plugin-entry";
import type { NormalizedConfig } from "./types.js";

export function createNollmCompatibilityRuntime(
  _config: NormalizedConfig
): MemoryPluginRuntime {
  const runtime: MemoryPluginRuntime = {
    async getMemorySearchManager(_params: {
      cfg: OpenClawConfig;
      agentId: string;
      purpose?: "default" | "status" | "cli";
    }) {
      return {
        manager: null,
        error: "nollm compatibility runtime disabled in active W2 config",
      };
    },

    resolveMemoryBackendConfig(_params: {
      cfg: OpenClawConfig;
      agentId: string;
    }) {
      return {
        backend: "builtin",
        provider: "nollm",
        custom: {
          backendKind: "nollm",
          compatibilityShim: false,
          activeMode: true,
        },
      } as unknown as ReturnType<MemoryPluginRuntime["resolveMemoryBackendConfig"]>;
    },
  };

  return runtime;
}
