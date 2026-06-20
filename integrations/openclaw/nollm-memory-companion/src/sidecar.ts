import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import type { NormalizedConfig, PluginConfig, SidecarFailure, SidecarResult } from "./types.js";

const MAX_CAPTURE_BYTES = 256 * 1024;
const REQUIRED_CONFIG_FIELDS = ["nollmRepoRoot", "workspaceRoot"] as const;

export function normalizeConfig(config: PluginConfig): NormalizedConfig {
  const nollmRepoRoot = requireAbsolutePath(config.nollmRepoRoot, "nollmRepoRoot");
  const workspaceRoot = requireAbsolutePath(config.workspaceRoot, "workspaceRoot");
  const sidecarScript = config.sidecarScript
    ? requireAbsolutePath(config.sidecarScript, "sidecarScript")
    : path.resolve(nollmRepoRoot, "reference/python/scripts/run_openclaw_nollm_memory.py");
  const sidecarOutDir = config.sidecarOutDir
    ? requireAbsolutePath(config.sidecarOutDir, "sidecarOutDir")
    : path.resolve(workspaceRoot, ".nollm-memory");
  const commandTimeoutMs = boundedInteger(config.commandTimeoutMs ?? 15000, 1000, 60000, "commandTimeoutMs");
  const maxSearchResults = boundedInteger(config.maxSearchResults ?? 5, 1, 20, "maxSearchResults");

  requirePathUnder(sidecarScript, nollmRepoRoot, "sidecarScript", "nollmRepoRoot", true);
  requirePathUnder(sidecarOutDir, workspaceRoot, "sidecarOutDir", "workspaceRoot", false);

  return {
    pythonCommand: config.pythonCommand || "python3",
    nollmRepoRoot,
    workspaceRoot,
    sidecarScript,
    sidecarOutDir,
    commandTimeoutMs,
    maxSearchResults
  };
}

export function buildSidecarArgv(
  config: NormalizedConfig,
  command:
    | "index"
    | "search"
    | "recall"
    | "get"
    | "status"
    | "field-overview"
    | "open-well"
    | "surface"
    | "focus"
    | "drift"
    | "read"
    | "recall-trace",
  params: Record<string, string | number | boolean | undefined> = {}
): string[] {
  const argv = [
    config.sidecarScript,
    "--repo-root",
    config.nollmRepoRoot,
    command,
    "--workspace",
    config.workspaceRoot,
    "--out",
    config.sidecarOutDir
  ];

  if (command === "search" || command === "recall") {
    argv.push("--query", String(params.query ?? ""));
    argv.push("--limit", String(clampSearchLimit(Number(params.limit ?? config.maxSearchResults), config.maxSearchResults)));
  }
  if (command === "get") {
    argv.push("--id", String(params.id ?? ""));
  }
  if (command === "field-overview") {
    if (typeof params.field_id === "string" && params.field_id.length > 0) {
      argv.push("--field-id", params.field_id);
    }
    argv.push("--limit", String(Math.max(1, Math.min(100, Math.trunc(Number(params.limit ?? 20))))));
  }
  if (command === "open-well") {
    argv.push("--entry-shard-id", String(params.entry_shard_id ?? ""));
    argv.push("--entry-task", String(params.entry_task ?? ""));
    argv.push("--anchor-vector", String(params.anchor_vector ?? "{}"));
    if (params.revision_id !== undefined) {
      argv.push("--revision-id", String(params.revision_id));
    }
    if (params.ttl_seconds !== undefined) {
      argv.push("--ttl-seconds", String(params.ttl_seconds));
    }
  }
  if (command === "surface") {
    argv.push("--well-id", String(params.well_id ?? ""));
    argv.push("--center-shard-id", String(params.center_shard_id ?? ""));
    argv.push("--radius", String(params.radius ?? 1));
    if (params.target_scale !== undefined) {
      argv.push("--target-scale", String(params.target_scale));
    }
  }
  if (command === "focus") {
    argv.push("--well-id", String(params.well_id ?? ""));
    argv.push("--target-shard-id", String(params.target_shard_id ?? ""));
    if (params.target_scale !== undefined) {
      argv.push("--target-scale", String(params.target_scale));
    }
  }
  if (command === "drift") {
    argv.push("--well-id", String(params.well_id ?? ""));
    argv.push("--current-shard-id", String(params.current_shard_id ?? ""));
    if (params.chosen_shard_id !== undefined) {
      argv.push("--chosen-shard-id", String(params.chosen_shard_id));
    }
    argv.push("--radius", String(params.radius ?? 1));
  }
  if (command === "read") {
    argv.push("--well-id", String(params.well_id ?? ""));
    argv.push("--shard-id", String(params.shard_id ?? ""));
  }
  if (command === "recall-trace") {
    argv.push("--well-id", String(params.well_id ?? ""));
    argv.push("--path", String(params.path ?? "[]"));
  }

  return argv;
}

export function clampSearchLimit(limit: number, maxSearchResults: number): number {
  if (!Number.isFinite(limit)) {
    return maxSearchResults;
  }
  return Math.max(1, Math.min(20, Math.min(Math.trunc(limit), maxSearchResults)));
}

export async function runSidecarCommand(
  config: PluginConfig,
  command:
    | "index"
    | "search"
    | "recall"
    | "get"
    | "status"
    | "field-overview"
    | "open-well"
    | "surface"
    | "focus"
    | "drift"
    | "read"
    | "recall-trace",
  params: Record<string, string | number | boolean | undefined> = {},
  signal?: AbortSignal
): Promise<SidecarResult> {
  const missing = missingRequiredConfig(config);
  if (missing.length > 0) {
    return sidecarFailure(
      "configuration_error",
      `Nollm companion configuration is required before running ${command}: ${missing.join(", ")}.`,
      false
    );
  }
  let normalized: NormalizedConfig;
  try {
    normalized = normalizeConfig(config);
  } catch (error) {
    return sidecarFailure("configuration_error", safeErrorMessage(error), false);
  }

  const argv = buildSidecarArgv(normalized, command, params);
  return await spawnJson(normalized.pythonCommand, argv, normalized.commandTimeoutMs, signal);
}

export function missingRequiredConfig(config: PluginConfig): string[] {
  return REQUIRED_CONFIG_FIELDS.filter((field) => {
    const value = config[field];
    return typeof value !== "string" || value.trim() === "";
  });
}

export function configurationRequiredStatus(config: PluginConfig): SidecarResult & {
  status?: "configuration_required";
  required_fields?: string[];
  message?: string;
} {
  const missing = missingRequiredConfig(config);
  if (missing.length === 0) {
    return { ok: true };
  }
  return {
    ok: false,
    status: "configuration_required",
    required_fields: [...REQUIRED_CONFIG_FIELDS],
    message: "Configure nollmRepoRoot and workspaceRoot before using Nollm companion tools.",
    error: {
      code: "configuration_error",
      message: `Missing required Nollm companion config: ${missing.join(", ")}.`,
      retryable: false
    }
  };
}

async function spawnJson(command: string, argv: string[], timeoutMs: number, signal?: AbortSignal): Promise<SidecarResult> {
  return await new Promise((resolve) => {
    if (signal?.aborted) {
      resolve(sidecarFailure("sidecar_timeout", "Nollm sidecar command was aborted before start.", true));
      return;
    }
    const child = spawn(command, argv, {
      shell: false,
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"]
    });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, timeoutMs);
    const abort = () => {
      timedOut = true;
      child.kill("SIGKILL");
    };
    signal?.addEventListener("abort", abort, { once: true });

    child.stdout.on("data", (chunk: Buffer) => {
      stdout = appendBounded(stdout, chunk);
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr = appendBounded(stderr, chunk);
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      resolve(sidecarFailure("sidecar_failed", safeErrorMessage(error), true));
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", abort);
      if (timedOut) {
        resolve(sidecarFailure("sidecar_timeout", "Nollm sidecar command timed out.", true));
        return;
      }
      if (code !== 0) {
        resolve(sidecarFailure("sidecar_failed", conciseSidecarFailure(stderr || stdout), true));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        resolve(sidecarFailure("sidecar_invalid_json", "Nollm sidecar returned invalid JSON.", true));
      }
    });
  });
}

function requireAbsolutePath(value: string | undefined, field: string): string {
  if (!value || !path.isAbsolute(value)) {
    throw new Error(`${field} must be an absolute path.`);
  }
  return path.resolve(value);
}

function requirePathUnder(value: string, root: string, valueName: string, rootName: string, mustExist: boolean): void {
  const canonicalRoot = canonicalExistingPath(root, rootName);
  const canonicalValue = mustExist ? canonicalExistingPath(value, valueName) : canonicalCandidatePath(value);
  const relative = path.relative(canonicalRoot, canonicalValue);
  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    return;
  }
  throw new Error(`${valueName} must resolve under ${rootName}.`);
}

function canonicalExistingPath(value: string, field: string): string {
  try {
    return fs.realpathSync.native(value);
  } catch {
    throw new Error(`${field} must exist for canonical path validation.`);
  }
}

function canonicalCandidatePath(value: string): string {
  if (fs.existsSync(value)) {
    return fs.realpathSync.native(value);
  }
  const existingParent = nearestExistingParent(value);
  const canonicalParent = fs.realpathSync.native(existingParent);
  return path.resolve(canonicalParent, path.relative(existingParent, value));
}

function nearestExistingParent(value: string): string {
  let current = path.dirname(value);
  while (!fs.existsSync(current)) {
    const next = path.dirname(current);
    if (next === current) {
      throw new Error(`No existing parent found for ${value}.`);
    }
    current = next;
  }
  return current;
}

function boundedInteger(value: number, minimum: number, maximum: number, field: string): number {
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${field} must be an integer between ${minimum} and ${maximum}.`);
  }
  return value;
}

function appendBounded(current: string, chunk: Buffer): string {
  const next = current + chunk.toString("utf8");
  if (Buffer.byteLength(next, "utf8") <= MAX_CAPTURE_BYTES) {
    return next;
  }
  return next.slice(0, MAX_CAPTURE_BYTES);
}

function sidecarFailure(code: SidecarFailure["error"]["code"], message: string, retryable: boolean): SidecarFailure {
  return {
    ok: false,
    error: {
      code,
      message,
      retryable
    }
  };
}

function conciseSidecarFailure(text: string): string {
  const firstLine = text.split(/\r?\n/).find((line) => line.trim()) ?? "Nollm sidecar command failed.";
  return firstLine.slice(0, 240);
}

function safeErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message.slice(0, 240);
  }
  return "Nollm sidecar adapter error.";
}
