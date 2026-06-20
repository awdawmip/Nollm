import { defineToolPlugin } from "openclaw/plugin-sdk/tool-plugin";
import {
  ConfigSchema,
  DriftInputSchema,
  FieldOverviewInputSchema,
  FocusInputSchema,
  GetInputSchema,
  OpenWellInputSchema,
  RecallInputSchema,
  ReadInputSchema,
  RecallTraceInputSchema,
  SearchInputSchema,
  StatusInputSchema,
  SurfaceInputSchema
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
      name: "nollm_field_overview",
      label: "Nollm Field Overview",
      description:
        "Return a bounded coarse dream-field map. Core does not choose a semantic entry or compute query scores.",
      parameters: FieldOverviewInputSchema,
      async execute(input: { field_id?: string; limit?: number }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        const configRequired = configurationRequiredStatus(config);
        if (configRequired.ok === false) {
          return configRequired;
        }
        return await runSidecarCommand(
          config,
          "field-overview",
          { field_id: input.field_id, limit: input.limit ?? 20 },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_open_well",
      label: "Nollm Open Well",
      description:
        "Open an ephemeral Gravity Well from a Cortex-selected entry shard and explicit non-negative anchor vector.",
      parameters: OpenWellInputSchema,
      async execute(
        input: { entry_shard_id: string; entry_task: string; anchor_vector: Record<string, number> },
        config: PluginConfig,
        context
      ) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "open-well",
          {
            entry_shard_id: input.entry_shard_id,
            entry_task: input.entry_task,
            anchor_vector: JSON.stringify(input.anchor_vector)
          },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_surface",
      label: "Nollm Surface",
      description:
        "Inspect content-bearing coarse surface cells and bridge hints before focusing to finer Nollm dream shards.",
      parameters: SurfaceInputSchema,
      async execute(
        input: { well_id: string; center_shard_id: string; radius?: number; target_scale?: string | number },
        config: PluginConfig,
        context
      ) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "surface",
          {
            well_id: input.well_id,
            center_shard_id: input.center_shard_id,
            radius: input.radius ?? 1,
            target_scale: input.target_scale
          },
          context.signal
        );
      }
    }),
    tool({
      name: "nollm_focus",
      label: "Nollm Focus",
      description:
        "Traverse by coverage and overlap to a sufficient scale without forcing raw source span descent.",
      parameters: FocusInputSchema,
      async execute(
        input: { well_id: string; target_shard_id: string; target_scale?: string | number },
        config: PluginConfig,
        context
      ) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "focus",
          {
            well_id: input.well_id,
            target_shard_id: input.target_shard_id,
            target_scale: input.target_scale
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
      async execute(
        input: { well_id: string; current_shard_id: string; chosen_shard_id?: string; radius?: number },
        config: PluginConfig,
        context
      ) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "drift",
          {
            well_id: input.well_id,
            current_shard_id: input.current_shard_id,
            chosen_shard_id: input.chosen_shard_id,
            radius: input.radius ?? 1
          },
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
      name: "nollm_recall_trace",
      label: "Nollm Recall Trace",
      description:
        "Finalize a deterministic structural trace for a Cortex-selected shard path. It returns no prose recall digest.",
      parameters: RecallTraceInputSchema,
      async execute(input: { well_id: string; path: string[] }, config: PluginConfig, context) {
        context.signal?.throwIfAborted();
        return await runSidecarCommand(
          config,
          "recall-trace",
          { well_id: input.well_id, path: JSON.stringify(input.path) },
          context.signal
        );
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
