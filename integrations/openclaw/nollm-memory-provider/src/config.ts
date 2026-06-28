import fs from "node:fs";
import path from "node:path";
import { Type } from "typebox";
import type { NormalizedConfig, PluginConfig, SidecarResult } from "./types.js";

export const ConfigSchema = Type.Object(
  {
    pythonExecutable: Type.String({
      description: "Absolute path to the Python interpreter used to run the Nollm active sidecar.",
    }),
    pythonArgs: Type.Optional(
      Type.Array(Type.String(), { default: [] })
    ),
    nollmRepoRoot: Type.String({
      description: "Absolute path to the Nollm repository.",
    }),
    workspaceRoot: Type.String({
      description: "Absolute path to the OpenClaw workspace root.",
    }),
    nativeStoreRoot: Type.String({
      description: "Absolute path to the native companion store directory.",
    }),
    trialRoot: Type.Optional(Type.String({
      description: "Absolute path to the active-trials directory.",
    })),
    commandTimeoutMs: Type.Optional(
      Type.Integer({ default: 15000, minimum: 1000, maximum: 60000 })
    ),
    maxFacts: Type.Optional(Type.Integer({ default: 4, minimum: 1, maximum: 20 })),
    maxContextCharacters: Type.Optional(
      Type.Integer({ default: 1400, minimum: 200, maximum: 65536 })
    ),
    captureMode: Type.Optional(
      Type.Literal("deterministic_explicit_v1", { default: "deterministic_explicit_v1" })
    ),
    trialMode: Type.Optional(
      Type.Literal("active_empirical_v1", { default: "active_empirical_v1" })
    ),
    trialId: Type.Optional(Type.String({
      description: "Controller-assigned active empirical trial id. Required when trialMode is active_empirical_v1.",
    })),
  },
  { additionalProperties: false }
);

const LEGACY_SEGMENTS = new Set([
  "memory", "memory.md", "dreams.md",
  "legacy_workspace", "legacy-workspace",
]);

export function isLegacyPathSegment(absPath: string): boolean {
  const normalized = absPath.replace(/\\/g, "/").toLowerCase();
  const parts = normalized.split("/").filter((p) => p.length > 0);
  for (const part of parts) {
    if (LEGACY_SEGMENTS.has(part)) {
      return true;
    }
  }
  const basename = parts[parts.length - 1] || "";
  const basenameNoExt = basename.replace(/\.[^.]+$/, "");
  if (LEGACY_SEGMENTS.has(basenameNoExt)) {
    return true;
  }
  return false;
}

export function normalizeConfig(config: PluginConfig): NormalizedConfig {
  const pythonExecutable = requireAbsoluteExecutable(config.pythonExecutable, "pythonExecutable");
  const nollmRepoRoot = requireAbsolutePath(config.nollmRepoRoot, "nollmRepoRoot");
  const workspaceRoot = requireAbsolutePath(config.workspaceRoot, "workspaceRoot");
  const nativeStoreRoot = requireAbsolutePath(config.nativeStoreRoot, "nativeStoreRoot");

  const sidecarScript = path.resolve(
    nollmRepoRoot,
    "reference/python/scripts/run_openclaw_nollm_active_memory.py"
  );
  if (!fs.existsSync(sidecarScript)) {
    throw new Error(`active sidecar script not found: ${sidecarScript}`);
  }

  if (isLegacyPathSegment(nativeStoreRoot)) {
    throw new Error(`nativeStoreRoot must not be inside or be a legacy memory path: ${nativeStoreRoot}`);
  }

  const trialRoot = config.trialRoot
    ? requireAbsolutePath(config.trialRoot, "trialRoot")
    : path.resolve(nativeStoreRoot, "..", "active-trials");

  if (isLegacyPathSegment(trialRoot)) {
    throw new Error(`trialRoot must not be inside or be a legacy memory path: ${trialRoot}`);
  }

  const trialMode = config.trialMode || "active_empirical_v1";
  const trialId = typeof config.trialId === "string" ? config.trialId.trim() : "";
  if (trialMode === "active_empirical_v1" && !trialId) {
    throw new Error("trialId is required when trialMode is active_empirical_v1.");
  }

  return {
    pythonExecutable,
    pythonArgs: Array.isArray(config.pythonArgs) ? config.pythonArgs.filter((a) => typeof a === "string") : [],
    nollmRepoRoot,
    workspaceRoot,
    nativeStoreRoot,
    trialRoot,
    sidecarScript,
    commandTimeoutMs: boundedInteger(
      config.commandTimeoutMs ?? 15000,
      1000,
      60000,
      "commandTimeoutMs"
    ),
    maxFacts: boundedInteger(config.maxFacts ?? 4, 1, 20, "maxFacts"),
    maxContextCharacters: boundedInteger(
      config.maxContextCharacters ?? 1400,
      200,
      65536,
      "maxContextCharacters"
    ),
    captureMode: config.captureMode || "deterministic_explicit_v1",
    trialMode,
    trialId: trialId || undefined,
  };
}

export function configurationRequiredStatus(
  config: PluginConfig
): SidecarResult & {
  status?: "configuration_required";
  required_fields?: string[];
  message?: string;
} {
  const required = ["pythonExecutable", "nollmRepoRoot", "workspaceRoot", "nativeStoreRoot"];
  const activeEmpirical = config.trialMode === undefined || config.trialMode === "active_empirical_v1";
  const missing = required.filter((field) => {
    const value = config[field as keyof PluginConfig];
    return typeof value !== "string" || value.trim() === "";
  });
  if (activeEmpirical && (typeof config.trialId !== "string" || config.trialId.trim() === "")) {
    missing.push("trialId");
  }
  if (missing.length === 0) {
    return { ok: true };
  }
  return {
    ok: false,
    status: "configuration_required",
    required_fields: required,
    message: "Configure pythonExecutable, nollmRepoRoot, workspaceRoot, nativeStoreRoot, and trialId.",
    error: {
      code: "configuration_error",
      message: `Missing required Nollm active memory config: ${missing.join(", ")}.`,
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

function requireAbsoluteExecutable(value: string | undefined, field: string): string {
  if (!value || !path.isAbsolute(value)) {
    throw new Error(`${field} must be an absolute path.`);
  }
  const resolved = path.resolve(value);
  if (!fs.existsSync(resolved)) {
    throw new Error(`${field} executable not found: ${resolved}`);
  }
  const basename = path.basename(resolved).toLowerCase();
  if (basename === "python3" || basename === "python" || basename === "py") {
    // We accept python.exe because it is explicit. Reject bare "python3" only if it is the literal basename without .exe on Windows.
    if (!basename.endsWith(".exe") && process.platform === "win32") {
      throw new Error(`${field} on Windows must be an absolute python.exe, not a PATH launcher.`);
    }
  }
  return resolved;
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
