import { spawn } from "node:child_process";
import path from "node:path";
import type { NormalizedConfig, PluginConfig, SidecarFailure, SidecarResult } from "./types.js";

const MAX_CAPTURE_BYTES = 256 * 1024;

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

  requirePathUnder(sidecarScript, nollmRepoRoot, "sidecarScript", "nollmRepoRoot");
  requirePathUnder(sidecarOutDir, workspaceRoot, "sidecarOutDir", "workspaceRoot");

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
  command: "index" | "search" | "get" | "write-candidate" | "status",
  params: Record<string, string | number | undefined> = {}
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

  if (command === "search") {
    argv.push("--query", String(params.query ?? ""));
    argv.push("--limit", String(clampSearchLimit(Number(params.limit ?? config.maxSearchResults), config.maxSearchResults)));
  }
  if (command === "get") {
    argv.push("--id", String(params.id ?? ""));
  }
  if (command === "write-candidate") {
    argv.push("--text", String(params.text ?? ""));
    argv.push("--source", String(params.source ?? ""));
    argv.push("--why", String(params.why ?? "pending explicit review before durable promotion"));
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
  command: "index" | "search" | "get" | "write-candidate" | "status",
  params: Record<string, string | number | undefined> = {}
): Promise<SidecarResult> {
  let normalized: NormalizedConfig;
  try {
    normalized = normalizeConfig(config);
  } catch (error) {
    return sidecarFailure("configuration_error", safeErrorMessage(error), false);
  }

  const argv = buildSidecarArgv(normalized, command, params);
  return await spawnJson(normalized.pythonCommand, argv, normalized.commandTimeoutMs);
}

async function spawnJson(command: string, argv: string[], timeoutMs: number): Promise<SidecarResult> {
  return await new Promise((resolve) => {
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

    child.stdout.on("data", (chunk: Buffer) => {
      stdout = appendBounded(stdout, chunk);
    });
    child.stderr.on("data", (chunk: Buffer) => {
      stderr = appendBounded(stderr, chunk);
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      resolve(sidecarFailure("sidecar_failed", safeErrorMessage(error), true));
    });
    child.on("close", (code) => {
      clearTimeout(timer);
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

function requirePathUnder(value: string, root: string, valueName: string, rootName: string): void {
  const relative = path.relative(root, value);
  if (relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative))) {
    return;
  }
  throw new Error(`${valueName} must resolve under ${rootName}.`);
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

