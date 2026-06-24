import type {
  MemoryPluginRuntime,
} from "openclaw/plugin-sdk/memory-core-host-runtime-core";
import type { OpenClawConfig } from "openclaw/plugin-sdk/plugin-entry";
import { runSidecarCommand } from "./sidecar.js";
import { NollmCompatibilityReferenceRegistry } from "./compat-registry.js";
import { validatePrepareResult } from "./context-validation.js";
import { createHash } from "node:crypto";
import type { NormalizedConfig } from "./types.js";

const REF_PREFIX = "nollm://compat/v1/";

export function createNollmCompatibilityRuntime(
  config: NormalizedConfig
): MemoryPluginRuntime {
  const registry = new NollmCompatibilityReferenceRegistry();
  let managerGeneration = 0;

  const runtime: MemoryPluginRuntime = {
    async getMemorySearchManager(params: {
      cfg: OpenClawConfig;
      agentId: string;
      purpose?: "default" | "status" | "cli";
    }) {
      managerGeneration++;
      const currentGeneration = managerGeneration;
      const sessionId = "compat";

      const statusResult = await runSidecarCommand(config, "status", {});
      if (!statusResult.ok) {
        return { manager: null, error: statusResult.error.message };
      }

      return {
        manager: {
          async search(query: string, opts?: { maxResults?: number }) {
            const prepareResult = await runSidecarCommand(config, "prepare", {
              request_id: `compat-search-${Date.now()}`,
              agent_id: params.agentId,
              session_id: sessionId,
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

            const validated = validatePrepareResult(prepareResult, {
              maxFacts: config.maxFacts,
              maxCharacters: config.maxCharacters,
              maxContextCharacters: config.maxContextCharacters,
            });

            if (!validated.ok) {
              return [];
            }

            const raw = validated as unknown as {
              context: {
                field_id: string;
                field_revision_id: string;
                facts: Array<{
                  shard_id: string;
                  claim: string;
                  source_refs: string[];
                }>;
              };
            };
            const ctx = raw.context;
            const queryHash = createHash("sha256").update(query).digest("hex");

            return ctx.facts.map((fact) => {
              const ref = registry.issueRef({
                agentId: params.agentId,
                sessionId,
                managerGeneration: currentGeneration,
                fieldId: ctx.field_id,
                fieldRevisionId: ctx.field_revision_id,
                shardId: fact.shard_id,
                boundedExcerpt: fact.claim.slice(0, 240),
                queryHash,
              });
              return {
                path: ref,
                startLine: 1,
                endLine: 1,
                score: 1.0,
                snippet: fact.claim.slice(0, 240),
                source: "memory" as const,
              };
            });
          },

          async readFile(readParams: { relPath: string; from?: number; lines?: number }) {
            if (!readParams.relPath.startsWith(REF_PREFIX)) {
              throw new Error("nollm_compat_ref_rejected");
            }

            const statusRes = await runSidecarCommand(config, "status", {});
            let fieldRevisionId = "unknown";
            if (statusRes.ok) {
              const s = statusRes as unknown as { field_revision_id?: string; context?: { field_revision_id?: string } };
              if (s.field_revision_id) {
                fieldRevisionId = s.field_revision_id;
              } else if (s.context?.field_revision_id) {
                fieldRevisionId = s.context.field_revision_id;
              }
            }

            const resolved = registry.resolveRef(readParams.relPath, {
              agentId: params.agentId,
              sessionId,
              managerGeneration: currentGeneration,
              fieldRevisionId,
            });

            if (!resolved) {
              throw new Error("nollm_compat_ref_rejected");
            }
            return {
              text: resolved.excerpt,
              path: readParams.relPath,
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
