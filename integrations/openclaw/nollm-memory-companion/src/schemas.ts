import { Type } from "typebox";

export const ConfigSchema = Type.Object(
  {
    pythonCommand: Type.Optional(Type.String({ default: "python3" })),
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

export const SearchInputSchema = Type.Object(
  {
    query: Type.String({ minLength: 1 }),
    limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 20 }))
  },
  { additionalProperties: false }
);

export const RecallInputSchema = Type.Object(
  {
    query: Type.String({ minLength: 1 }),
    limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 20 }))
  },
  { additionalProperties: false }
);

export const GetInputSchema = Type.Object(
  {
    id: Type.String({ minLength: 1 })
  },
  { additionalProperties: false }
);

export const WriteCandidateInputSchema = Type.Object(
  {
    text: Type.String({ minLength: 1 }),
    source: Type.String({ minLength: 1 }),
    why: Type.Optional(Type.String({ maxLength: 240 }))
  },
  { additionalProperties: false }
);

export const CommitCandidateInputSchema = Type.Object(
  {
    candidate_id: Type.String({ minLength: 1 }),
    explicit_confirmation: Type.Boolean(),
    target: Type.Union([Type.Literal("durable"), Type.Literal("daily")]),
    reason: Type.String({ minLength: 1, maxLength: 500 }),
    source: Type.String({ minLength: 1, maxLength: 240 })
  },
  { additionalProperties: false }
);

export const StatusInputSchema = Type.Object({}, { additionalProperties: false });

export const OrientInputSchema = Type.Object(
  {
    query: Type.String({ minLength: 1 }),
    limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 10 }))
  },
  { additionalProperties: false }
);

export const SurfaceInputSchema = Type.Object(
  {
    surface_id: Type.String({ minLength: 1 })
  },
  { additionalProperties: false }
);

export const FocusInputSchema = Type.Object(
  {
    query: Type.String({ minLength: 1 }),
    surface_id: Type.String({ minLength: 1 }),
    sufficient_scale: Type.Optional(Type.Integer({ minimum: 1, maximum: 3 }))
  },
  { additionalProperties: false }
);

export const DriftInputSchema = Type.Object(
  {
    shard_id: Type.String({ minLength: 1 }),
    query: Type.Optional(Type.String())
  },
  { additionalProperties: false }
);

export const ReadInputSchema = Type.Object(
  {
    shard_id: Type.String({ minLength: 1 })
  },
  { additionalProperties: false }
);

export const ComposeDigestInputSchema = Type.Object(
  {
    query: Type.String({ minLength: 1 })
  },
  { additionalProperties: false }
);
