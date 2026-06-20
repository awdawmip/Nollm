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
  runSidecarCommand
} from "../dist/sidecar.js";

const packageRoot = path.resolve(import.meta.dirname, "..");
const toolNames = [
  "nollm_field_overview",
  "nollm_open_well",
  "nollm_surface",
  "nollm_focus",
  "nollm_drift",
  "nollm_read",
  "nollm_recall_trace",
  "nollm_memory_status"
];

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

  assert.equal(argv[0], fixture.sidecarScript);
  assert.deepEqual(argv.slice(1, 7), ["--repo-root", config.nollmRepoRoot, "search", "--workspace", config.workspaceRoot, "--out"]);
  assert.equal(argv.includes("--query"), true);
  assert.equal(argv.at(-1), "5");
  assert.equal(clampSearchLimit(0, 5), 1);
  assert.equal(clampSearchLimit(9, 5), 5);
  assert.equal(clampSearchLimit(99, 20), 20);
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

  const failed = await runSidecarCommand({ pythonCommand: "__should_not_spawn__" }, "search", { query: "x" });
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
  const failed = await runSidecarCommand({ ...fixture.config, pythonCommand: process.execPath }, "status");
  assert.equal(failed.ok, false);
  assert.equal(failed.error.code, "sidecar_failed");

  process.env.NOLLM_TEST_MODE = "invalid";
  const invalid = await runSidecarCommand({ ...fixture.config, pythonCommand: process.execPath }, "status");
  assert.equal(invalid.ok, false);
  assert.equal(invalid.error.code, "sidecar_invalid_json");

  process.env.NOLLM_TEST_MODE = "timeout";
  const timeout = await runSidecarCommand(
    { ...fixture.config, pythonCommand: process.execPath, commandTimeoutMs: 1000 },
    "status"
  );
  assert.equal(timeout.ok, false);
  assert.equal(timeout.error.code, "sidecar_timeout");
  delete process.env.NOLLM_TEST_MODE;
});

function makeFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "nollm-plugin-test-"));
  const nollmRepoRoot = path.join(root, "nollm");
  const workspaceRoot = path.join(root, "workspace");
  const scriptDir = path.join(nollmRepoRoot, "reference", "python", "scripts");
  fs.mkdirSync(scriptDir, { recursive: true });
  fs.mkdirSync(workspaceRoot, { recursive: true });
  const sidecarScript = path.join(scriptDir, "run_openclaw_nollm_memory.js");
  fs.writeFileSync(sidecarScript, "console.log(JSON.stringify({ ok: true }));\n", "utf8");
  const sidecarOutDir = path.join(workspaceRoot, ".nollm-memory");
  return {
    nollmRepoRoot,
    workspaceRoot,
    sidecarScript,
    config: {
      pythonCommand: process.execPath,
      nollmRepoRoot,
      workspaceRoot,
      sidecarScript,
      sidecarOutDir,
      commandTimeoutMs: 5000,
      maxSearchResults: 5
    }
  };
}
