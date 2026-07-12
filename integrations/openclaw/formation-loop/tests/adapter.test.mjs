import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import plugin, { registerDreamAgent, wellFormedText } from "../dist/index.js";

test("manifest exposes no main-agent Formation tool", () => {
  const manifest = JSON.parse(fs.readFileSync(new URL("../openclaw.plugin.json", import.meta.url)));
  assert.deepEqual(manifest.contracts.tools, []);
  assert.equal(manifest.configSchema.properties.model_mode.default, "inherit");
  assert.equal(manifest.configSchema.properties.persist_subagent_transcripts.const, false);
});

test("wire text replaces isolated UTF-16 surrogates before UTF-8 encoding", () => {
  assert.equal(wellFormedText("valid \udc94 text"), "valid \ufffd text");
});

test("plugin registers channel delivery and Gateway completion hooks with no tool", () => {
  const hooks = new Map(); let toolCount = 0;
  registerDreamAgent({ pluginConfig: { enabled: false }, on(name, handler) { hooks.set(name, handler); }, registerTool() { toolCount += 1; } });
  assert.deepEqual([...hooks.keys()].sort(), ["agent_end", "before_agent_run", "llm_output", "message_received", "message_sent"]);
  assert.equal(toolCount, 0);
});

test("missing host configuration fails open after delivery", async () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: {}, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { async run() { spawnCount += 1; return { runId: "bad" }; } } } });
  hooks.get("message_received")({ content: "A durable user preference." }, { sessionKey: "s" });
  hooks.get("llm_output")({ provider: "p", model: "m" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: true, content: "Normal visible reply." }, { sessionKey: "s" });
  assert.equal(spawnCount, 0);
});

test("failed delivery and disallowed model never spawn Dream", async () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: { python_executable: "python", nollm_repo_root: ".", allowed_models: ["allowed/model"] }, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { async run() { spawnCount += 1; return { runId: "bad" }; } } } });
  hooks.get("message_received")({ content: "Durable material." }, { sessionKey: "s" });
  hooks.get("llm_output")({ provider: "other", model: "model" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: false, content: "not delivered" }, { sessionKey: "s" });
  await hooks.get("message_sent")({ success: true, content: "delivered" }, { sessionKey: "s" });
  hooks.get("agent_end")({ success: true, runId: "channel-run", messages: [] }, { sessionKey: "s", messageProvider: "telegram" });
  assert.equal(spawnCount, 0);
});

test("plugin entry is an ordinary hook plugin", () => {
  assert.equal(plugin.id, "nollm-formation");
  assert.equal(typeof plugin.register, "function");
});
