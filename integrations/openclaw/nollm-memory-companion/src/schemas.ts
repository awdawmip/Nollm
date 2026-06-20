import { Type } from "@sinclair/typebox";

export const ConfigSchema = Type.Object(
  {
    pythonCommand: Type.Optional(Type.String({ default: "python3" })),
    nollmRepoRoot: Type.String({
      description: "Required absolute path to the Nollm repository."
    }),
    workspaceRoot: Type.String({
      description: "Required absolute path to the OpenClaw workspace."
    }),
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

export const StatusInputSchema = Type.Object({}, { additionalProperties: false });

