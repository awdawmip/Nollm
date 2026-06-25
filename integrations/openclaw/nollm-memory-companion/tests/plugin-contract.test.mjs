import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { getToolPluginMetadata } from "openclaw/plugin-sdk/tool-plugin";
import entry from "../dist/index.js";
import {
  buildSidecarArgv,
  clampSearchLimit,
  configurationRequiredStatus,
  normalizeConfig,
  resolvePythonExecutable,
  runSidecarCommand
} from "../dist/sidecar.js";

const packageRoot = path.resolve(import.meta.dirname, "..");
const toolNames = [
  "nollm_memory_status",
  "nollm_field_overview",
  "nollm_open_well",
  "nollm_surface",
  "nollm_focus",
  "nollm_drift",
  "nollm_read",
  "nollm_recall_trace"
];
const isWindows = process.platform === "win32";

test("default export exposes real defineToolPlugin metadata", () => {
  const metadata = getToolPluginMetadata(entry);

  assert.ok(metadata);
  assert.equal(metadata.id, "nollm-memory-companion");
  assert.deepEqual(metadata.tools.map((tool) => tool.name), toolNames);
  assert.equal(metadata.configSchema.type, "object");
  assert.equal(metadata.configSchema.additionalProperties, false);
  assert.equal(metadata.configSchema.required, undefined);
});

test("generated manifest matches native OpenClaw metadata shape", () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(packageRoot, "openclaw.plugin.json"), "utf8"));

  assert.equal(manifest.id, "nollm-memory-companion");
  assert.deepEqual(manifest.contracts.tools, toolNames);
  assert.equal(Object.hasOwn(manifest, "toolMetadata"), false);
  assert.equal(manifest.configSchema.type, "object");
  assert.equal(manifest.configSchema.required, undefined);
  assert.ok(manifest.configSchema.properties.pythonExecutable);
  assert.ok(manifest.configSchema.properties.pythonArgs);
  assert.ok(manifest.activation);
  assert.equal(manifest.activation.onStartup, false);
  assert.deepEqual(manifest.skills, ["skill"]);
  assert.equal(Object.hasOwn(manifest, "kind"), false);
  assert.equal(Object.hasOwn(manifest, "entry"), false);
  assert.equal(Object.hasOwn(manifest, "tools"), false);
  assert.equal(JSON.stringify(manifest).includes("plugins.slots.memory"), false);
});

test("package metadata uses native extension entry", () => {
  const packageJson = JSON.parse(fs.readFileSync(path.join(packageRoot, "package.json"), "utf8"));

  assert.deepEqual(packageJson.openclaw.extensions, ["./dist/index.js"]);
  assert.equal(packageJson.scripts.test, "npm run build && node --test tests/*.test.mjs");
  assert.equal(packageJson.devDependencies.openclaw, "latest");
});

test("builds argv and clamps search limit", () => {
  const fixture = makeFixture();
  const config = normalizeConfig(fixture.config);
  const argv = buildSidecarArgv(config, "search", { query: "gravity", limit: 99 });

  assert.equal(argv[0], config.sidecarScript);
  assert.deepEqual(argv.slice(1, 7), ["--repo-root", config.nollmRepoRoot, "search", "--workspace", config.workspaceRoot, "--out"]);
  assert.equal(argv.includes("--query"), true);
  assert.equal(argv.at(-1), "5");
  assert.equal(clampSearchLimit(0, 5), 1);
  assert.equal(clampSearchLimit(9, 5), 5);
  assert.equal(clampSearchLimit(99, 20), 20);
});

test("pythonArgs are passed as discrete argv before sidecar script", () => {
  const fixture = makeFixture();
  const fakePython = fixture.config.pythonArgs[0];
  const config = normalizeConfig({
    ...fixture.config,
    pythonArgs: [fakePython, "--no-warnings"]
  });

  assert.equal(config.pythonExecutable, process.execPath);
  assert.deepEqual(config.pythonArgs, [fakePython, "--no-warnings"]);
});

test("builds dream cortex navigation argv", () => {
  const fixture = makeFixture();
  const config = normalizeConfig(fixture.config);
  const overview = buildSidecarArgv(config, "field-overview", { field_id: "field_a", limit: 2 });
  const well = buildSidecarArgv(config, "open-well", {
    entry_shard_id: "surface_openclaw_nollm",
    entry_task: "task",
    anchor_vector: "{\"openclaw\":1}",
    revision_id: "rev_1",
    ttl_seconds: 120
  });
  const surface = buildSidecarArgv(config, "surface", {
    well_id: "well_1",
    center_shard_id: "surface_openclaw_nollm",
    radius: 2,
    target_scale: "bridge"
  });
  const focus = buildSidecarArgv(config, "focus", {
    well_id: "well_1",
    target_shard_id: "bridge_active_memory_cortex",
    target_scale: "fine"
  });
  const drift = buildSidecarArgv(config, "drift", {
    well_id: "well_1",
    current_shard_id: "bridge_active_memory_cortex",
    chosen_shard_id: "lateral_search_adapter_boundary"
  });
  const read = buildSidecarArgv(config, "read", { well_id: "well_1", shard_id: "bridge_active_memory_cortex" });
  const trace = buildSidecarArgv(config, "recall-trace", {
    well_id: "well_1",
    path: "[\"surface_openclaw_nollm\"]"
  });

  assert.equal(overview.includes("field-overview"), true);
  assert.equal(well.includes("--anchor-vector"), true);
  assert.equal(well.includes("--revision-id"), true);
  assert.equal(well.includes("--ttl-seconds"), true);
  assert.equal(surface.includes("--center-shard-id"), true);
  assert.equal(focus.includes("--target-shard-id"), true);
  assert.equal(drift.includes("--current-shard-id"), true);
  assert.equal(read.includes("read"), true);
  assert.equal(read.includes("--well-id"), true);
  assert.equal(trace.includes("recall-trace"), true);
});

test("unconfigured tools fail closed without spawning sidecar", async () => {
  const status = configurationRequiredStatus({});
  assert.equal(status.ok, false);
  assert.equal(status.status, "configuration_required");
  assert.deepEqual(status.required_fields, ["nollmRepoRoot", "workspaceRoot"]);

  const failed = await runSidecarCommand({ pythonExecutable: "__should_not_spawn__" }, "search", { query: "x" });
  assert.equal(failed.ok, false);
  assert.equal(failed.error.code, "configuration_error");
  assert.match(failed.error.message, /nollmRepoRoot/);
});

test("validates configured paths and output containment", () => {
  const fixture = makeFixture();
  assert.throws(() => normalizeConfig({ ...fixture.config, nollmRepoRoot: "relative" }), /absolute path/);
  assert.throws(
    () => normalizeConfig({ ...fixture.config, sidecarOutDir: path.join(os.tmpdir(), "outside-nollm-memory") }),
    /sidecarOutDir must resolve under workspaceRoot/
  );
  assert.throws(
    () => {
      const outsideScript = path.join(fixture.workspaceRoot, "outside.js");
      fs.writeFileSync(outsideScript, "console.log('{}');\n", "utf8");
      normalizeConfig({ ...fixture.config, sidecarScript: outsideScript });
    },
    /sidecarScript must resolve under nollmRepoRoot/
  );
});

test("returns structured failures for timeout, non-zero exit, and invalid JSON", async () => {
  const fixture = makeFixture();
  fs.writeFileSync(
    fixture.sidecarScript,
    "const mode = process.env.NOLLM_TEST_MODE; if (mode === 'timeout') setTimeout(() => {}, 10000); else if (mode === 'fail') { console.error('sidecar failed safely'); process.exit(2); } else if (mode === 'invalid') console.log('not json'); else console.log(JSON.stringify({ ok: true }));\n",
    "utf8"
  );

  process.env.NOLLM_TEST_MODE = "fail";
  const failed = await runSidecarCommand(fixture.config, "status");
  assert.equal(failed.ok, false);
  assert.equal(failed.error.code, "sidecar_failed");

  process.env.NOLLM_TEST_MODE = "invalid";
  const invalid = await runSidecarCommand(fixture.config, "status");
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error.code, "sidecar_invalid_json");

  process.env.NOLLM_TEST_MODE = "timeout";
  const timeout = await runSidecarCommand(
    { ...fixture.config, commandTimeoutMs: 1000 },
    "status"
  );
  assert.equal(timeout.ok, false);
  assert.equal(timeout.error.code, "sidecar_timeout");
  delete process.env.NOLLM_TEST_MODE;
});

test("status success reports safe resolved executable metadata", async () => {
  const fixture = makeFixture();
  const status = await runSidecarCommand(fixture.config, "status");
  assert.equal(status.ok, true);
  assert.equal(status.python_executable, process.execPath);
});

test("Windows rejects bare python3/python/py with structured error", { skip: !isWindows }, async () => {
  const fixture = makeFixture();
  for (const launcher of ["python3", "python", "py"]) {
    const failed = await runSidecarCommand(
      { ...fixture.config, pythonCommand: launcher, pythonExecutable: undefined },
      "status"
    );
    assert.equal(failed.ok, false, `expected failure for ${launcher}`);
    assert.equal(failed.error.code, "legacy_python_launcher_rejected", `expected legacy launcher rejection for ${launcher}`);
    assert.match(failed.error.message, /absolute python\.exe/);
  }
});

test("Windows requires pythonExecutable when no legacy command given", { skip: !isWindows }, async () => {
  const fixture = makeFixture();
  const failed = await runSidecarCommand(
    { ...fixture.config, pythonCommand: undefined, pythonExecutable: undefined },
    "status"
  );
  assert.equal(failed.ok, false);
  assert.equal(failed.error.code, "windows_python_executable_required");
});

test("Windows rejects non-absolute pythonExecutable", { skip: !isWindows }, async () => {
  const fixture = makeFixture();
  const failed = await runSidecarCommand(
    { ...fixture.config, pythonExecutable: "python.exe" },
    "status"
  );
  assert.equal(failed.ok, false);
  assert.equal(failed.error.code, "python_executable_not_absolute");
});

test("legacy absolute pythonCommand is accepted on Windows", { skip: !isWindows }, async () => {
  const fixture = makeFixture();
  const status = await runSidecarCommand(
    { ...fixture.config, pythonCommand: process.execPath, pythonExecutable: undefined },
    "status"
  );
  assert.equal(status.ok, true);
});

test("shell remains false in sidecar spawn", async () => {
  const fixture = makeFixture();
  const status = await runSidecarCommand(fixture.config, "status");
  assert.equal(status.ok, true);
  assert.equal(status.shell, false);
});

function makeFakePython(root) {
  const script = path.join(root, "fake-python.js");
  fs.writeFileSync(
    script,
    [
      "const cp = require('child_process');",
      "const fs = require('fs');",
      "const path = require('path');",
      "const args = process.argv.slice(2);",
      "if (args.includes('-c')) {",
      "  console.log(JSON.stringify({",
      "    executable: process.execPath,",
      "    version: 'fake-python-for-tests',",
      "    sysPrefix: '/fake',",
      "    platform: process.platform",
      "  }));",
      "  process.exit(0);",
      "}",
      "const thisScript = path.resolve(__filename);",
      "let sidecarScript = null;",
      "let sidecarScriptIndex = -1;",
      "for (let i = 0; i < args.length; i++) {",
      "  const candidate = args[i];",
      "  try {",
      "    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {",
      "      const realCandidate = fs.realpathSync(candidate);",
      "      if (realCandidate !== thisScript) {",
      "        sidecarScript = candidate;",
      "        sidecarScriptIndex = i;",
      "        break;",
      "      }",
      "    }",
      "  } catch {}",
      "}",
      "const sidecarArgs = sidecarScript ? args.slice(sidecarScriptIndex + 1) : [];",
      "if (sidecarScript) {",
      "  const result = cp.spawnSync(process.execPath, [sidecarScript, ...sidecarArgs], {",
      "    encoding: 'utf8',",
      "    shell: false,",
      "    windowsHide: true",
      "  });",
      "  process.stdout.write(result.stdout ?? '');",
      "  process.stderr.write(result.stderr ?? '');",
      "  process.exit(result.status ?? 0);",
      "} else {",
      "  console.log(JSON.stringify({ ok: true, shell: false, python_executable: process.execPath }));",
      "}",
      ""
    ].join("\n"),
    "utf8"
  );
  return script;
}

function makeFixture(overrides = {}) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "nollm-plugin-test-"));
  const nollmRepoRoot = path.join(root, "nollm");
  const workspaceRoot = path.join(root, "workspace");
  const scriptDir = path.join(nollmRepoRoot, "reference", "python", "scripts");
  fs.mkdirSync(scriptDir, { recursive: true });
  fs.mkdirSync(workspaceRoot, { recursive: true });
  const sidecarScript = path.join(scriptDir, "run_openclaw_nollm_memory.js");
  fs.writeFileSync(sidecarScript, "console.log(JSON.stringify({ ok: true, shell: false, python_executable: process.execPath }));\n", "utf8");
  const sidecarOutDir = path.join(workspaceRoot, ".nollm-memory");
  const fakePython = makeFakePython(root);
  return {
    nollmRepoRoot,
    workspaceRoot,
    sidecarScript,
    config: {
      pythonExecutable: process.execPath,
      pythonArgs: [fakePython],
      nollmRepoRoot,
      workspaceRoot,
      sidecarScript,
      sidecarOutDir,
      commandTimeoutMs: 5000,
      maxSearchResults: 5,
      ...overrides
    }
  };
}