import fs from "node:fs";
import path from "node:path";
import { Type } from "typebox";
import type { NormalizedConfig, PluginConfig, SidecarResult } from "./types.js";

export const ConfigSchema = Type.Object(
  {
    pythonCommand: Type.Optional(Type.String({ default: "python3" })),
    nollmRepoRoot: Type.String({
      description: "Absolute path to the Nollm repository.",
    }),
    nollmDataRoot: Type.String({
      description: "Absolute path to Nollm-owned alpha state.",
    }),
    alphaFixturePath: Type.String({
      description: "Absolute path to the synthetic alpha field fixture.",
    }),
    commandTimeoutMs: Type.Optional(
      Type.Integer({ default: 15000, minimum: 1000, maximum: 60000 })
    ),
    maxFacts: Type.Optional(Type.Integer({ default: 3, minimum: 1, maximum: 20 })),
    maxCharacters: Type.Optional(
      Type.Integer({ default: 1200, minimum: 100, maximum: 10000 })
    ),
    maxContextCharacters: Type.Optional(
      Type.Integer({ default: 4096, minimum: 200, maximum: 65536 })
    ),
    captureMode: Type.Optional(Type.Literal("receipt_only")),
    allowAgentIds: Type.Optional(Type.Array(Type.String())),
  },
  { additionalProperties: false }
);

// Legacy path segment names that must never be a data root
const LEGACY_SEGMENTS = new Set([
  "memory", "memory.md", "dreams.md",
  "legacy_workspace", "legacy-workspace",
]);

export function isLegacyPathSegment(absPath: string): boolean {
  // Normalize separators to forward slash, split into parts
  const normalized = absPath.replace(/\\/g, "/").toLowerCase();
  const parts = normalized.split("/").filter((p) => p.length > 0);
  for (const part of parts) {
    if (LEGACY_SEGMENTS.has(part)) {
      return true;
    }
  }
  // Also check basename without extension
  const basename = parts[parts.length - 1] || "";
  const basenameNoExt = basename.replace(/\.[^.]+$/, "");
  if (LEGACY_SEGMENTS.has(basenameNoExt)) {
    return true;
  }
  return false;
}

export function normalizeConfig(config: PluginConfig): NormalizedConfig {
  const nollmRepoRoot = requireAbsolutePath(config.nollmRepoRoot, "nollmRepoRoot");
  const nollmDataRoot = requireAbsolutePath(config.nollmDataRoot, "nollmDataRoot");
  const alphaFixturePath = requireAbsolutePath(
    config.alphaFixturePath,
    "alphaFixturePath"
  );
  const sidecarScript = path.resolve(
    nollmRepoRoot,
    "reference/python/scripts/run_openclaw_nollm_provider.py"
  );
  if (!fs.existsSync(sidecarScript)) {
    throw new Error(`sidecar script not found: ${sidecarScript}`);
  }
  requirePathUnder(alphaFixturePath, nollmRepoRoot, "alphaFixturePath", "nollmRepoRoot");

  // Segment-aware legacy path rejection
  if (isLegacyPathSegment(nollmDataRoot)) {
    throw new Error(`nollmDataRoot must not be inside or be a legacy memory path: ${nollmDataRoot}`);
  }

  const allowAgentIds = Array.isArray(config.allowAgentIds)
    ? config.allowAgentIds.filter((id) => typeof id === "string" && id.length > 0)
    : ["main"];

  return {
    pythonCommand: config.pythonCommand || "python3",
    nollmRepoRoot,
    nollmDataRoot,
    alphaFixturePath,
    sidecarScript,
    commandTimeoutMs: boundedInteger(
      config.commandTimeoutMs ?? 15000,
      1000,
      60000,
      "commandTimeoutMs"
    ),
    maxFacts: boundedInteger(config.maxFacts ?? 3, 1, 20, "maxFacts"),
    maxCharacters: boundedInteger(
      config.maxCharacters ?? 1200,
      100,
      10000,
      "maxCharacters"
    ),
    maxContextCharacters: boundedInteger(
      config.maxContextCharacters ?? 4096,
      200,
      65536,
      "maxContextCharacters"
    ),
    captureMode: config.captureMode || "receipt_only",
    allowAgentIds,
  };
}

export function configurationRequiredStatus(
  config: PluginConfig
): SidecarResult & {
  status?: "configuration_required";
  required_fields?: string[];
  message?: string;
} {
  const required = ["nollmRepoRoot", "nollmDataRoot", "alphaFixturePath"];
  const missing = required.filter((field) => {
    const value = config[field as keyof PluginConfig];
    return typeof value !== "string" || value.trim() === "";
  });
  if (missing.length === 0) {
    return { ok: true };
  }
  return {
    ok: false,
    status: "configuration_required",
    required_fields: required,
    message: "Configure nollmRepoRoot, nollmDataRoot, and alphaFixturePath.",
    error: {
      code: "configuration_error",
      message: `Missing required Nollm provider config: ${missing.join(", ")}.`,
      retryable: false,
    },
  };
}

function requireAbsolutePath(value: string | undefined, field: string): string {
  if (!value || !path.isAbsolute(value)) {
    throw new Error(`${field} must be an absolute path.`);
  }
  return path.resolve(value);
}

function requirePathUnder(
  value: string,
  root: string,
  valueName: string,
  rootName: string
): void {
  const relative = path.relative(path.resolve(root), path.resolve(value));
  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    return;
  }
  throw new Error(`${valueName} must resolve under ${rootName}.`);
}

function boundedInteger(
  value: number,
  minimum: number,
  maximum: number,
  field: string
): number {
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${field} must be an integer between ${minimum} and ${maximum}.`);
  }
  return value;
}
