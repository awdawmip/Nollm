import assert from "node:assert/strict";
import test from "node:test";
import {
  buildSidecarArgv,
  clampSearchLimit,
  normalizeConfig,
  runSidecarCommand
} from "../src/sidecar.ts";

const root = process.platform === "win32" ? "C:\\repo\\nollm" : "/repo/nollm";
const workspace = process.platform === "win32" ? "C:\\workspace\\openclaw" : "/workspace/openclaw";

test("builds sidecar argv without shell strings", () => {
  const config = normalizeConfig({ nollmRepoRoot: root, workspaceRoot: workspace });
  const argv = buildSidecarArgv(config, "search", { query: "gravity", limit: 99 });

  assert.equal(argv[0].endsWith("run_openclaw_nollm_memory.py"), true);
  assert.deepEqual(argv.slice(1, 7), ["--repo-root", config.nollmRepoRoot, "search", "--workspace", config.workspaceRoot, "--out"]);
  assert.equal(argv.includes("--query"), true);
  assert.equal(argv.at(-1), "5");
});

test("validates workspace and output path boundaries", () => {
  assert.throws(() => normalizeConfig({ nollmRepoRoot: "relative", workspaceRoot: workspace }), /absolute path/);
  assert.throws(
    () =>
      normalizeConfig({
        nollmRepoRoot: root,
        workspaceRoot: workspace,
        sidecarOutDir: process.platform === "win32" ? "C:\\other\\.nollm-memory" : "/other/.nollm-memory"
      }),
    /sidecarOutDir must resolve under workspaceRoot/
  );
});

test("clamps max search results", () => {
  assert.equal(clampSearchLimit(0, 5), 1);
  assert.equal(clampSearchLimit(9, 5), 5);
  assert.equal(clampSearchLimit(99, 20), 20);
});

test("returns structured failure for subprocess errors", async () => {
  const result = await runSidecarCommand(
    { pythonCommand: "__missing_nollm_python__", nollmRepoRoot: root, workspaceRoot: workspace, commandTimeoutMs: 1000 },
    "status"
  );
  assert.equal(result.ok, false);
  if (result.ok === false) {
    assert.equal(result.error.code, "sidecar_failed");
    assert.equal(result.error.retryable, true);
  }
});

