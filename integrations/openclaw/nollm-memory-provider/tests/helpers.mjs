import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export function makeTempDir(prefix = "nollm-test-") {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

export function makeTempRepo(tmpDir) {
  const repoRoot = path.join(tmpDir, "repo");
  const dataRoot = path.join(tmpDir, "data");
  const fixtureDir = path.join(repoRoot, "fixtures");
  fs.mkdirSync(path.join(repoRoot, "reference", "python", "scripts"), { recursive: true });
  fs.mkdirSync(dataRoot, { recursive: true });
  fs.mkdirSync(fixtureDir, { recursive: true });

  const fixtureSrc = path.resolve(import.meta.dirname, "..", "fixtures", "alpha-field.json");
  const fixtureDst = path.join(fixtureDir, "alpha-field.json");
  fs.copyFileSync(fixtureSrc, fixtureDst);

  return { repoRoot, dataRoot, fixturePath: fixtureDst };
}

export function resolvePythonCommand() {
  if (process.env.PYTHON_EXE) return process.env.PYTHON_EXE;
  const candidates = [
    "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\python.exe",
    "C:\\Python314\\python.exe",
    "C:\\Python313\\python.exe",
    "C:\\Python312\\python.exe",
    process.env.PYTHON || "",
  ];
  for (const c of candidates) {
    if (c && fs.existsSync(c)) return c;
  }
  return process.env.PYTHON || "python3";
}

export function makeProviderConfig(tmpDir, overrides = {}) {
  const { repoRoot, dataRoot, fixturePath } = makeTempRepo(tmpDir);
  writeStubSidecar(repoRoot, STUB_STATUS);
  return {
    pythonCommand: resolvePythonCommand(),
    nollmRepoRoot: repoRoot,
    nollmDataRoot: dataRoot,
    alphaFixturePath: fixturePath,
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

export async function invokeEnd(api, event) {
  const handlers = api._events["agent_end"];
  if (!handlers || handlers.length === 0) {
    throw new Error("no agent_end handler registered");
  }
  return handlers[0](event);
}

export function writeStubSidecar(repoRoot, source) {
  const scriptPath = path.join(repoRoot, "reference", "python", "scripts", "run_openclaw_nollm_provider.py");
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
  "config = json.loads(sys.argv[sys.argv.index('--config-json') + 1])",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.status.v1',",
  "  'provider': 'nollm',",
  "  'backend_kind': 'nollm',",
  "  'compatibility_shim': True,",
  "  'field_id': 'alpha_main',",
  "  'field_revision_id': 'rev-1',",
  "  'freshness': 'fresh',",
  "  'data_root': config.get('nollmDataRoot')",
  "}, sort_keys=True))",
].join("\n");

export const STUB_PREPARE = [
  "import json, sys",
  "config = json.loads(sys.argv[sys.argv.index('--config-json') + 1])",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.prepare_result.v1',",
  "  'context': {",
  "    'schema': 'nollm.memory_context.v1',",
  "    'context_id': 'ctx-1',",
  "    'field_id': 'alpha_main',",
  "    'field_revision_id': 'rev-1',",
  "    'freshness': 'fresh',",
  "    'facts': [{",
  "      'shard_id': 'stub-fact',",
  "      'claim': 'stub claim about Nollm',",
  "      'keywords': ['nollm'],",
  "      'epistemic_state': 'source_backed',",
  "      'operational_state': 'active',",
  "      'source_refs': ['nollm://synthetic/fixture/alpha-field#fact-stub']",
  "    }],",
  "    'boundaries': [],",
  "    'warnings': [],",
  "    'completeness': {'mode': 'bounded', 'explicit_absences': []}",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_CAPTURE = [
  "import json, sys",
  "config = json.loads(sys.argv[sys.argv.index('--config-json') + 1])",
  "stdin = json.loads(sys.stdin.read())",
  "data_root = config.get('nollmDataRoot', '/tmp')",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.capture_result.v1',",
  "  'receipt': {",
  "    'receipt_id': 'r-1',",
  "    'event_hash': 'h-1',",
  "    'stored_at': data_root + '/functional-alpha/capture-receipts/r-1.json',",
  "    'state': 'captured_pending_native_ingress',",
  "    'legacy_memory_mutated': False",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_UNAVAILABLE = [
  "import json, sys",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'schema': 'nollm.provider.prepare_result.v1',",
  "  'context': {",
  "    'schema': 'nollm.memory_context.v1',",
  "    'context_id': 'ctx-none',",
  "    'field_id': 'alpha_main',",
  "    'field_revision_id': 'rev-1',",
  "    'freshness': 'unavailable',",
  "    'facts': [],",
  "    'boundaries': [{'scope': 'functional_alpha', 'source': 'unavailable'}],",
  "    'warnings': ['alpha field unavailable'],",
  "    'completeness': {'mode': 'bounded', 'explicit_absences': ['No matching active Nollm memory was found in the Functional Alpha field.']}",
  "  }",
  "}, sort_keys=True))",
].join("\n");

export const STUB_ECHO = [
  "import json, sys",
  "config = json.loads(sys.argv[sys.argv.index('--config-json') + 1])",
  "stdin = json.loads(sys.stdin.read())",
  "print(json.dumps({",
  "  'ok': True,",
  "  'argv': sys.argv,",
  "  'command': stdin.get('command'),",
  "  'config_timeout': config.get('commandTimeoutMs')",
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
