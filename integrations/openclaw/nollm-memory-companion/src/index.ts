import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import {
  ComposeDigestInputSchema,
  ConfigSchema,
  CommitCandidateInputSchema,
  DriftInputSchema,
  FocusInputSchema,
  GetInputSchema,
  OrientInputSchema,
  RecallInputSchema,
  ReadInputSchema,
  SearchInputSchema,
  StatusInputSchema,
  SurfaceInputSchema,
  WriteCandidateInputSchema
} from "./schemas.js";
import { clampSearchLimit, configurationRequiredStatus, normalizeConfig, runSidecarCommand } from "./sidecar.js";
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
      name: "nollm_orient",
      label: "Nollm Orient",
      description:
        "Begin a Cortex recall pass from bounded coarse Nollm dream-field surfaces, not aliases or raw source search.",
      parameters: OrientInputSchema,
      async execute(input: { query: string; limit?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const configRequired = configurationRequiredStatus(config);
        if (configRequired.ok === false) {
          return configRequired;
        }
        return await runSidecarCommand(config, "orient", { query: input.query, limit: input.limit ?? 3 }, context.signal);
      }
    }),
    tool({
      name: "nollm_surface",
      label: "Nollm Surface",
      description:
        "Inspect content-bearing coarse surface cells and bridge hints before focusing to finer Nollm dream shards.",
      parameters: SurfaceInputSchema,
      async execute(input: { surface_id: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(config, "surface", { surface_id: input.surface_id }, context.signal);
      }
    }),
    tool({
      name: "nollm_focus",
      label: "Nollm Focus",
      description:
        "Traverse by coverage and overlap to a sufficient scale without forcing raw source span descent.",
      parameters: FocusInputSchema,
      async execute(input: { query: string; surface_id: string; sufficient_scale?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "focus",
          {
            query: input.query,
            surface_id: input.surface_id,
            sufficient_scale: input.sufficient_scale ?? 2
          },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_drift",
      label: "Nollm Drift",
      description:
        "Inspect lateral and return links from a dream shard; drift labels are orientation only, never rejection or trust.",
      parameters: DriftInputSchema,
      async execute(input: { shard_id: string; query?: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "drift",
          { shard_id: input.shard_id, query: input.query ?? "" },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_read",
      label: "Nollm Read",
      description: "Read a Nollm dream shard by id; the recall unit is the dream shard, not a raw Markdown chunk.",
      parameters: ReadInputSchema,
      async execute(input: { shard_id: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(config, "read", { shard_id: input.shard_id }, context.signal);
      }
    }),
    tool({
      name: "nollm_compose_digest",
      label: "Nollm Compose Digest",
      description:
        "Compose a compact Nollm Recall Digest after orient/surface/focus/drift, returning NONE when the field lacks useful material.",
      parameters: ComposeDigestInputSchema,
      async execute(input: { query: string }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(config, "compose-digest", { query: input.query }, context.signal);
      }
    }),
    tool({
      name: "nollm_memory_recall",
      label: "Nollm Memory Recall",
      description:
        "Return an LLM-usable memory digest with direct evidence, lateral context, cautions, source provenance, and gravity orientation.",
      parameters: RecallInputSchema,
      async execute(input: { query: string; limit?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const configRequired = configurationRequiredStatus(config);
        if (configRequired.ok === false) {
          return configRequired;
        }
        const normalized = normalizeConfig(config);
        return await runSidecarCommand(
          config,
          "recall",
          {
            query: input.query,
            limit: clampSearchLimit(input.limit ?? normalized.maxSearchResults, normalized.maxSearchResults)
          },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_memory_search",
      label: "Nollm Memory Search",
      description:
        "Search Nollm companion memory sidecar results with source, provenance, geometry, gravity, and drift orientation.",
      parameters: SearchInputSchema,
      async execute(input: { query: string; limit?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const configRequired = configurationRequiredStatus(config);
        if (configRequired.ok === false) {
          return configRequired;
        }
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
      name: "nollm_memory_commit_candidate",
      label: "Nollm Memory Commit Candidate",
      optional: true,
      description:
        "Commit a staged Nollm pending candidate to a managed durable/daily memory section only after explicit user confirmation.",
      parameters: CommitCandidateInputSchema,
      async execute(
        input: {
          candidate_id: string;
          explicit_confirmation: boolean;
          target: "durable" | "daily";
          reason: string;
          source: string;
        },
        config: PluginConfig,
        context
      ) {
        context.signal?.throwIfAborted();
        if (input.explicit_confirmation !== true) {
          return {
            ok: false,
            error: {
              code: "commit_rejected",
              message: "nollm_memory_commit_candidate requires explicit_confirmation=true.",
              retryable: false
            }
          };
        }
        return await runSidecarCommand(
          config,
          "commit-candidate",
          {
            candidate_id: input.candidate_id,
            explicit_confirmation: input.explicit_confirmation,
            target: input.target,
            reason: input.reason,
            source: input.source
          },
          context.signal
        );
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
        const configRequired = configurationRequiredStatus(config);
        if (configRequired.ok === false) {
          return configRequired;
        }
        return await runSidecarCommand(config, "status", {}, context.signal);
      }
    })
  ]
});

export default plugin;
