import path from "node:path";

export const ConfigSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    dataRoot: { type: "string", description: "Nollm data root. Defaults to ~/.openclaw/nollm." },
    memoryWorkspace: { type: "string", description: "Advanced migration override for an existing Nollm memory workspace." },
    runtimeExecutable: { type: "string", description: "Advanced path to a packaged Nollm runtime sidecar." },
    runtimeArgs: { type: "array", items: { type: "string" }, default: [] },
    pythonExecutable: { type: "string", description: "Development-only Python bridge executable." },
    nollmRepoRoot: { type: "string", description: "Development-only Nollm repository root." },
    autoCapture: { type: "boolean", default: false },
    importMemoryCore: { type: "boolean", default: true },
    debug: { type: "boolean", default: false },
    commandTimeoutMs: { type: "integer", minimum: 1000, maximum: 300000, default: 120000 },
    operationTtlMs: { type: "integer", minimum: 1000, maximum: 3600000, default: 300000 },
    maxResults: { type: "integer", minimum: 1, maximum: 32, default: 8 },
    maxContextCharacters: { type: "integer", minimum: 200, maximum: 65536, default: 8192 }
  }
};

function finiteInteger(value, fallback, min, max, field) {
  const resolved = value ?? fallback;
  if (!Number.isInteger(resolved) || resolved < min || resolved > max) {
    throw new Error(`${field} must be an integer between ${min} and ${max}`);
  }
  return resolved;
}

function optionalString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

export function normalizeConfig(raw = {}, resolvePath = (value) => value) {
  const dataRoot = resolvePath(optionalString(raw.dataRoot) ?? "~/.openclaw/nollm");
  const memoryWorkspace = optionalString(raw.memoryWorkspace);
  const runtimeExecutable = optionalString(raw.runtimeExecutable);
  const pythonExecutable = optionalString(raw.pythonExecutable);
  const nollmRepoRoot = optionalString(raw.nollmRepoRoot);
  const runtimeArgs = Array.isArray(raw.runtimeArgs)
    ? raw.runtimeArgs.filter((item) => typeof item === "string")
    : [];
  const runtimeMode = runtimeExecutable
    ? "packaged"
    : pythonExecutable && nollmRepoRoot
      ? "development-python"
      : "unavailable";
  return {
    dataRoot: path.resolve(dataRoot),
    memoryWorkspace: memoryWorkspace ? path.resolve(resolvePath(memoryWorkspace)) : undefined,
    runtimeExecutable: runtimeExecutable ? path.resolve(resolvePath(runtimeExecutable)) : undefined,
    runtimeArgs,
    pythonExecutable: pythonExecutable ? path.resolve(resolvePath(pythonExecutable)) : undefined,
    nollmRepoRoot: nollmRepoRoot ? path.resolve(resolvePath(nollmRepoRoot)) : undefined,
    runtimeMode,
    autoCapture: raw.autoCapture === true,
    importMemoryCore: raw.importMemoryCore !== false,
    debug: raw.debug === true,
    commandTimeoutMs: finiteInteger(raw.commandTimeoutMs, 120000, 1000, 300000, "commandTimeoutMs"),
    operationTtlMs: finiteInteger(raw.operationTtlMs, 300000, 1000, 3600000, "operationTtlMs"),
    maxResults: finiteInteger(raw.maxResults, 8, 1, 32, "maxResults"),
    maxContextCharacters: finiteInteger(raw.maxContextCharacters, 8192, 200, 65536, "maxContextCharacters")
  };
}

export function safeAgentSegment(agentId) {
  const value = String(agentId ?? "").trim();
  if (!value) throw new Error("agentId is required");
  const safe = value.replace(/[^A-Za-z0-9._-]/g, "_").slice(0, 128);
  if (!safe || safe === "." || safe === "..") throw new Error("agentId is invalid");
  return safe;
}
