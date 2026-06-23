import type {
  MemoryPluginRuntime,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawConfig } from "openclaw/plugin-sdk/plugin-entry";
import { runSidecarCommand } from "./sidecar.js";
import type { NormalizedConfig } from "./types.js";

export function createNollmCompatibilityRuntime(
  config: NormalizedConfig
): MemoryPluginRuntime {
  const runtime: MemoryPluginRuntime = {
    async getMemorySearchManager(params: {
      cfg: OpenClawConfig;
      agentId: string;
      purpose?: "default" | "status" | "cli";
    }) {
      const result = await runSidecarCommand(config, "status", {});
      if (!result.ok) {
        return { manager: null, error: result.error.message };
      }

      return {
        manager: {
          async search(query, opts) {
            const prepareResult = await runSidecarCommand(config, "prepare", {
              request_id: `compat-search-${Date.now()}`,
              agent_id: params.agentId,
              session_id: "compat",
              run_id: `compat-${Date.now()}`,
              messages: [{ role: "user", content: query }],
              budget: {
                max_facts: opts?.maxResults ?? config.maxFacts,
                max_characters: config.maxCharacters,
              },
            });
            if (!prepareResult.ok) {
              return [];
            }
            const ctx = (
              prepareResult as unknown as {
                context: {
                  facts: Array<{
                    shard_id: string;
                    claim: string;
                    source_refs: string[];
                  }>;
                };
              }
            ).context;
            return ctx.facts.map((fact, index) => ({
              path: fact.source_refs[0] ?? `nollm://compat/${index}`,
              startLine: index + 1,
              endLine: index + 1,
              score: 1.0,
              snippet: fact.claim.slice(0, 240),
              source: "memory" as const,
            }));
          },

          async readFile(params) {
            if (
              !params.relPath.startsWith("nollm://") ||
              params.relPath.includes("..")
            ) {
              throw new Error("nollm_compat_ref_rejected");
            }
            return {
              text: "opaque Nollm compatibility reference",
              path: params.relPath,
            };
          },

          status() {
            return {
              backend: "builtin",
              provider: "nollm",
              custom: {
                backendKind: "nollm",
                compatibilityShim: true,
              },
            };
          },

          probeEmbeddingAvailability: async () => ({
            ok: false,
            checked: true,
            error: "not implemented in Functional Alpha",
          }),

          probeVectorAvailability: async () => false,

          probeVectorStoreAvailability: async () => false,

          getCachedEmbeddingAvailability: () => null,
        },
        error: undefined,
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
          compatibilityShim: true,
        },
      } as unknown as ReturnType<MemoryPluginRuntime["resolveMemoryBackendConfig"]>;
    },
  };

  return runtime;
}
