import fs from "node:fs";
import { execFileSync } from "node:child_process";
import os from "node:os";
import path from "node:path";

export function makeTempDir(prefix = "nollm-test-") {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

export function makeTempRepo(tmpDir) {
  const repoRoot = path.join(tmpDir, "repo");
  const workspaceRoot = path.join(tmpDir, "workspace");
  const nativeStoreRoot = path.join(workspaceRoot, ".nollm-memory", "native-companion-v1");
  const trialRoot = path.join(workspaceRoot, ".nollm-memory", "active-trials");
  fs.mkdirSync(path.join(repoRoot, "reference", "python", "scripts"), { recursive: true });
  fs.mkdirSync(nativeStoreRoot, { recursive: true });
  fs.mkdirSync(trialRoot, { recursive: true });
  return { repoRoot, workspaceRoot, nativeStoreRoot, trialRoot };
}

export function resolvePythonCommand() {
  if (process.env.PYTHON_EXE) return requireAbsolutePython(process.env.PYTHON_EXE, "PYTHON_EXE");
  const candidates = [
    "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\python.exe",
    "C:\\Users\\chaos\\AppData\\Local\\Programs\\Python\\Python314\\python.exe",
    "C:\\Users\\chaos\\AppData\\Local\\Programs\\Python\\Python313\\python.exe",
    "C:\\Users\\chaos\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
    "C:\\Python314\\python.exe",
    "C:\\Python313\\python.exe",
    "C:\\Python312\\python.exe",
    process.env.PYTHON || "",
  ];
  for (const c of candidates) {
    if (c && path.isAbsolute(c) && fs.existsSync(c)) return c;
  }
  const discovered = discoverPythonExecutable();
  if (discovered) return discovered;
  throw new Error("Set PYTHON_EXE to an absolute python executable path for provider tests.");
}

function requireAbsolutePython(value, source) {
  if (!path.isAbsolute(value) || !fs.existsSync(value)) {
    throw new Error(`${source} must be an absolute existing python executable path.`);
  }
  return value;
}

function discoverPythonExecutable() {
  for (const launcher of ["py", "python"]) {
    try {
      const out = execFileSync(
        launcher,
        ["-c", "import sys; print(sys.executable)"],
        { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], timeout: 5000 }
      ).trim();
      if (out && path.isAbsolute(out) && fs.existsSync(out)) return out;
    } catch {
      // Keep probing; tests must end with an absolute executable or fail loudly.
    }
  }
  return "";
}

export function makeProviderConfig(tmpDir, overrides = {}) {
  const { repoRoot, workspaceRoot, nativeStoreRoot, trialRoot } = makeTempRepo(tmpDir);
  writeStubSidecar(repoRoot, STUB_STATUS);
  return {
    pythonExecutable: resolvePythonCommand(),
    pythonArgs: ["-u"],
    nollmRepoRoot: repoRoot,
    workspaceRoot,
    nativeStoreRoot,
    trialRoot,
    commandTimeoutMs: 15000,
    maxFacts: 4,
    maxContextCharacters: 1400,
    captureMode: "deterministic_explicit_v1",
    trialMode: "active_empirical_v1",
    ...overrides,
  };
}

export function makeMockApi(config = {}) {
  const events = { warnings: [] };
  return {
    id: "test-agent-123",
    pluginConfig: config,
    logger: {
      warn: (msg) => events.warnings.push(msg),
      info: () => {},
      debug: () => {},
    },
    registerMemoryCapability: (cap) => {
      events.capability = cap;
    },
    on: (event, handler) => {
      (events[event] ||= []).push(handler);
    },
    _events: events,
  };
}

export async function invokePrepare(api, event, ctx = {}) {
  const handlers = api._events["agent_turn_prepare"];
  if (!handlers || handlers.length === 0) {
    throw new Error("no agent_turn_prepare handler registered");
  }
  return handlers[0](event, ctx);
}

export async function invokeEnd(api, event, ctx = {}) {
  const handlers = api._events["agent_end"];
  if (!handlers || handlers.length === 0) {
    throw new Error("no agent_end handler registered");
  }
  return handlers[0](event, ctx);
}

export function writeStubSidecar(repoRoot, source) {
  const scriptPath = path.join(repoRoot, "reference", "python", "scripts", "run_openclaw_nollm_active_memory.py");
  fs.writeFileSync(scriptPath, source, "utf8");
  return scriptPath;
}

export function listFiles(dir, extFilter = null) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...listFiles(full, extFilter));
    } else if (!extFilter || full.endsWith(extFilter)) {
      results.push(full);
    }
  }
  return results;
}

export const STUB_STATUS = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.active_memory_status.v1',",
  "  'store': 'nollm_native_companion',",
  "  'native_record_count': 7,",
  "  'active_revision_id': 'nrev_1234',",
  "  'python_executable': sys.executable,",
  "  'capture_mode': 'deterministic_explicit_v1',",
  "  'trial_mode': 'active_empirical_v1'",
  "}, sort_keys=True))",
].join("\n");

export const STUB_PREPARE = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.prepare.v2',",
  "  'context': {",
  "    'schema': 'NOLLM_MEMORY_CONTEXT_V1',",
  "    'freshness': 'fresh',",
  "    'facts': [{",
  "      'memory_id': 'nmem_stub',",
  "      'claim': 'stub claim about Nollm',",
  "      'kind': 'note',",
  "      'source': 'nollm_native_companion',",
  "      'revision_id': 'nrev_stub'",
  "    }],",
  "    'boundaries': [],",
  "    'warnings': [],",
  "    'explicit_absences': []",
  "  },",
  "  'metrics': {",
  "    'native_record_count': 7,",
  "    'result_count': 1,",
  "    'rendered_context_characters': 200,",
  "    'recall_mode': 'exact'",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_CAPTURE = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.active_memory_capture.v1',",
  "  'capture': {",
  "    'event_id': 'evt_1',",
  "    'promoted_count': 1,",
  "    'deduplicated_count': 0,",
  "    'suppressed_count': 0,",
  "    'rejected_count': 0,",
  "    'records': [{ 'memory_id': 'nmem_1', 'kind': 'identity', 'source': 'active_turn_explicit_v1' }]",
  "  },",
  "  'metrics': {",
  "    'user_messages_seen': 1,",
  "    'assistant_messages_ignored': 0,",
  "    'candidate_count': 1,",
  "    'latency_ms': 12",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_UNAVAILABLE = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.prepare.v2',",
  "  'context': {",
  "    'schema': 'NOLLM_MEMORY_CONTEXT_V1',",
  "    'freshness': 'none',",
  "    'facts': [],",
  "    'boundaries': [],",
  "    'warnings': [],",
  "    'explicit_absences': ['No Nollm native companion memory matched this query.']",
  "  },",
  "  'metrics': {",
  "    'native_record_count': 7,",
  "    'result_count': 0,",
  "    'rendered_context_characters': 120,",
  "    'recall_mode': 'none'",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_ECHO = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'argv': sys.argv,",
  "  'command': stdin.get('command'),",
  "  'native_store_root': next((sys.argv[i+1] for i in range(len(sys.argv)-1) if sys.argv[i] == '--native-store-root'), None)",
  "}, sort_keys=True))",
].join("\n");

export const STUB_SLOW = [
  "import json, sys, time",
  "stdin = json.loads(sys.stdin.read())",
  "time.sleep(10)",
  "print(json.dumps({'ok': True, 'command': stdin.get('command')}, sort_keys=True))",
].join("\n");

export const STUB_INVALID_JSON = [
  "print('this is not valid json')",
].join("\n");

export const STUB_NONZERO_ACTIVE_ERROR = [
  "import json, sys",
  "print(json.dumps({",
  "  'ok': False,",
  "  'schema': 'nollm.active_memory_error.v1',",
  "  'error': {'code': 'native_recall_failed', 'message': 'Native active recall failed.', 'retryable': True}",
  "}, sort_keys=True))",
  "raise SystemExit(1)",
].join("\n");
