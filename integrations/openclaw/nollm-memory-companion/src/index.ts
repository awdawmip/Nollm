import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import {
  ConfigSchema,
  GetInputSchema,
  SearchInputSchema,
  StatusInputSchema,
  WriteCandidateInputSchema
} from "./schemas.js";
import { clampSearchLimit, normalizeConfig, runSidecarCommand } from "./sidecar.js";
import type { PluginConfig } from "./types.js";

export const plugin = defineToolPlugin({
  id: "nollm-memory-companion",
  configSchema: ConfigSchema,
  tools: [
    {
      name: "nollm_memory_search",
      description:
        "Search Nollm companion memory sidecar results with source, provenance, geometry, gravity, and drift orientation.",
      inputSchema: SearchInputSchema,
      async execute(input: { query: string; limit?: number }, context: { config: PluginConfig }) {
        const normalized = normalizeConfig(context.config);
        return await runSidecarCommand(context.config, "search", {
          query: input.query,
          limit: clampSearchLimit(input.limit ?? normalized.maxSearchResults, normalized.maxSearchResults)
        });
      }
    },
    {
      name: "nollm_memory_get",
      description:
        "Retrieve exact source-backed Nollm sidecar content by candidate_id, memory_id, or shard_id before factual use.",
      inputSchema: GetInputSchema,
      async execute(input: { id: string }, context: { config: PluginConfig }) {
        return await runSidecarCommand(context.config, "get", { id: input.id });
      }
    },
    {
      name: "nollm_memory_write_candidate",
      optional: true,
      description:
        "Create a pending-review candidate only; this does not write durable OpenClaw memory or mutate MEMORY.md.",
      inputSchema: WriteCandidateInputSchema,
      async execute(input: { text: string; source: string; why?: string }, context: { config: PluginConfig }) {
        const result = await runSidecarCommand(context.config, "write-candidate", {
          text: input.text,
          source: input.source,
          why: input.why
        });
        if (result.ok === false) {
          return result;
        }
        return {
          ...result,
          pending_review: true,
          durable_write: false,
          target_files_mutated: false,
          notice: "Pending candidate only; no durable OpenClaw memory file was written."
        };
      }
    },
    {
      name: "nollm_memory_status",
      description:
        "Return Nollm sidecar counts, source roles, accepted ID forms, and forbidden-semantics flags without host secrets.",
      inputSchema: StatusInputSchema,
      async execute(_input: Record<string, never>, context: { config: PluginConfig }) {
        return await runSidecarCommand(context.config, "status");
      }
    }
  ]
});

export default plugin;

