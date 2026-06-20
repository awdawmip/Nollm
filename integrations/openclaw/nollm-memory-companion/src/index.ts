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

const plugin = defineToolPlugin({
  id: "nollm-memory-companion",
  name: "Nollm Memory Companion",
  description:
    "Companion tools that delegate to the Nollm Python sidecar while OpenClaw memory-core remains the active owner.",
  activation: {
    onStartup: false
  },
  configSchema: ConfigSchema,
  tools: (tool) => [
    tool({
      name: "nollm_memory_search",
      label: "Nollm Memory Search",
      description:
        "Search Nollm companion memory sidecar results with source, provenance, geometry, gravity, and drift orientation.",
      parameters: SearchInputSchema,
      async execute(input: { query: string; limit?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const normalized = normalizeConfig(config);
        return await runSidecarCommand(
          config,
          "search",
          {
            query: input.query,
            limit: clampSearchLimit(input.limit ?? normalized.maxSearchResults, normalized.maxSearchResults)
          },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_memory_get",
      label: "Nollm Memory Get",
      description:
        "Retrieve exact source-backed Nollm sidecar content by candidate_id, memory_id, or shard_id before factual use.",
      parameters: GetInputSchema,
      async execute(input: { id: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(config, "get", { id: input.id }, context.signal);
      }
    }),
    tool({
      name: "nollm_memory_write_candidate",
      label: "Nollm Memory Write Candidate",
      optional: true,
      description:
        "Create a pending-review candidate only; this does not write durable OpenClaw memory or mutate MEMORY.md.",
      parameters: WriteCandidateInputSchema,
      async execute(input: { text: string; source: string; why?: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const result = await runSidecarCommand(
          config,
          "write-candidate",
          {
            text: input.text,
            source: input.source,
            why: input.why
          },
          context.signal
        );
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
    }),
    tool({
      name: "nollm_memory_status",
      label: "Nollm Memory Status",
      description:
        "Return Nollm sidecar counts, source roles, accepted ID forms, and forbidden-semantics flags without host secrets.",
      parameters: StatusInputSchema,
      async execute(_input: object, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(config, "status", {}, context.signal);
      }
    })
  ]
});

export default plugin;
