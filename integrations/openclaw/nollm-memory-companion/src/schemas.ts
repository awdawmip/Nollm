import { Type } from "typebox";

export const ConfigSchema = Type.Object(
  {
    pythonCommand: Type.Optional(Type.String({
      default: "python",
      description: "Deprecated. Use pythonExecutable instead."
    })),
    pythonExecutable: Type.Optional(Type.String({
      description: "Absolute path to the Python executable. Required on Windows; recommended everywhere."
    })),
    pythonArgs: Type.Optional(Type.Array(Type.String(), {
      default: [],
      description: "Additional arguments passed to pythonExecutable before the sidecar script."
    })),
    nollmRepoRoot: Type.Optional(Type.String({
      description: "Optional at install time; required absolute path to the Nollm repository before tool use."
    })),
    workspaceRoot: Type.Optional(Type.String({
      description: "Optional at install time; required absolute path to the OpenClaw workspace before tool use."
    })),
    sidecarScript: Type.Optional(
      Type.String({
        description: "Optional absolute path under nollmRepoRoot."
      })
    ),
    sidecarOutDir: Type.Optional(
      Type.String({
        description: "Optional absolute path under workspaceRoot."
      })
    ),
    commandTimeoutMs: Type.Optional(Type.Integer({ default: 15000, minimum: 1000, maximum: 60000 })),
    maxSearchResults: Type.Optional(Type.Integer({ default: 5, minimum: 1, maximum: 20 }))
  },
  { additionalProperties: false }
);

export const StatusInputSchema = Type.Object({}, { additionalProperties: false });

export const FieldOverviewInputSchema = Type.Object(
  {
    field_id: Type.Optional(Type.String({ minLength: 1 })),
    limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 100 }))
  },
  { additionalProperties: false }
);

export const OpenWellInputSchema = Type.Object(
  {
    entry_shard_id: Type.String({ minLength: 1 }),
    entry_task: Type.String({ minLength: 1 }),
    anchor_vector: Type.Record(Type.String({ minLength: 1 }), Type.Number({ minimum: 0 })),
    revision_id: Type.Optional(Type.String({ minLength: 1 })),
    ttl_seconds: Type.Optional(Type.Integer({ minimum: 1, maximum: 86400 }))
  },
  { additionalProperties: false }
);

export const SurfaceInputSchema = Type.Object(
  {
    well_id: Type.String({ minLength: 1 }),
    center_shard_id: Type.String({ minLength: 1 }),
    radius: Type.Optional(Type.Integer({ minimum: 0, maximum: 12 })),
    target_scale: Type.Optional(Type.Union([Type.Literal("coarse"), Type.Literal("bridge"), Type.Literal("fine"), Type.Integer({ minimum: 0, maximum: 12 })]))
  },
  { additionalProperties: false }
);

export const FocusInputSchema = Type.Object(
  {
    well_id: Type.String({ minLength: 1 }),
    target_shard_id: Type.String({ minLength: 1 }),
    target_scale: Type.Optional(Type.Union([Type.Literal("coarse"), Type.Literal("bridge"), Type.Literal("fine"), Type.Integer({ minimum: 0, maximum: 12 })]))
  },
  { additionalProperties: false }
);

export const DriftInputSchema = Type.Object(
  {
    well_id: Type.String({ minLength: 1 }),
    current_shard_id: Type.String({ minLength: 1 }),
    chosen_shard_id: Type.Optional(Type.String({ minLength: 1 })),
    radius: Type.Optional(Type.Integer({ minimum: 0, maximum: 12 }))
  },
  { additionalProperties: false }
);

export const ReadInputSchema = Type.Object(
  {
    well_id: Type.String({ minLength: 1 }),
    shard_id: Type.String({ minLength: 1 })
  },
  { additionalProperties: false }
);

export const RecallTraceInputSchema = Type.Object(
  {
    well_id: Type.String({ minLength: 1 }),
    path: Type.Array(Type.String({ minLength: 1 }), { minItems: 1 })
  },
  { additionalProperties: false }
);