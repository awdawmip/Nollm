import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import plugin, { parseInferenceEnvelope, resolveOpenClawLauncher } from "../dist/index.js";

test("plugin exposes only explicit formation tool", () => {
  const manifest = JSON.parse(fs.readFileSync(new URL("../openclaw.plugin.json", import.meta.url)));
  assert.deepEqual(manifest.contracts.tools, ["nollm_form_statement"]);
  assert.equal(manifest.properties, undefined);
});

test("Windows cmd launcher resolves node and module", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "aold-launcher-"));
  fs.writeFileSync(path.join(root, "node.exe"), "");
  fs.mkdirSync(path.join(root, "node_modules", "openclaw"), { recursive: true });
  fs.writeFileSync(path.join(root, "node_modules", "openclaw", "openclaw.mjs"), "");
  const launcher = resolveOpenClawLauncher(path.join(root, "openclaw.cmd"));
  assert.equal(launcher.command, path.join(root, "node.exe"));
  assert.equal(launcher.backend, "windows-node-launcher");
  assert.equal(launcher.prefix.at(-1), path.join(root, "node_modules", "openclaw", "openclaw.mjs"));
});

test("Windows cmd launcher rejects missing node or module", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "aold-launcher-"));
  assert.throws(() => resolveOpenClawLauncher(path.join(root, "openclaw.cmd")), /node.exe/);
  fs.writeFileSync(path.join(root, "node.exe"), "");
  assert.throws(() => resolveOpenClawLauncher(path.join(root, "openclaw.cmd")), /openclaw.mjs/);
});

test("direct executable remains direct", () => {
  assert.deepEqual(resolveOpenClawLauncher("C:\\bin\\openclaw.exe"), { command: "C:\\bin\\openclaw.exe", prefix: [], backend: "direct-executable" });
});

test("inference envelope rejects invalid JSON and empty output", () => {
  assert.equal(parseInferenceEnvelope(JSON.stringify({ outputs: [{ text: " answer " }] })), "answer");
  assert.throws(() => parseInferenceEnvelope("bad"), /invalid/);
  assert.throws(() => parseInferenceEnvelope(JSON.stringify({ outputs: [{ text: "" }] })), /empty/);
});

test("registered tool execute fails closed without explicit host configuration", async () => {
  let registered;
  plugin.register({ pluginConfig: {}, registerTool(tool) { registered = tool; } });
  assert.equal(registered.name, "nollm_form_statement");
  const result = await registered.execute("unit-tool-call", {
    request: {
      request_id: "unit-request",
      evidence: [{ evidence_id: "e1", content_utf8: "Remember this exact fact.", source_handle: "chat", context_refs: [] }],
      max_statements: 1,
    },
  });
  assert.deepEqual(result.details, { ok: false, error: "explicit_configuration_required" });
});
