import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import plugin, { boundedTurns, extractAssistantText, extractResolvedModel, extractUserTurns, modelOverride, registerDreamAgent, turnKey, wellFormedText } from "../dist/index.js";

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
  assert.deepEqual([...hooks.keys()].sort(), ["agent_end", "before_agent_run", "llm_output", "message_received", "message_sent", "subagent_ended", "subagent_spawned"]);
  assert.equal(toolCount, 0);
});

test("ConversationMaterial uses real role messages and excludes system content", () => {
  const messages = [
    { role: "system", content: "hidden bootstrap" },
    { role: "user", content: "first\nuser" },
    { role: "assistant", content: [{ type: "text", text: "prior answer" }] },
    { role: "user", content: [{ type: "text", text: "current user" }] },
    { role: "assistant", content: "current answer" },
  ];
  assert.deepEqual(extractUserTurns(messages).map(x => x.content_utf8), ["first\nuser", "current user"]);
  assert.equal(extractAssistantText(messages), "current answer");
  const bounded = boundedTurns(extractUserTurns(messages), extractAssistantText(messages), 1000);
  assert.deepEqual(bounded.map(x => x.role), ["user", "user", "assistant"]);
  assert.equal(JSON.stringify(bounded).includes("hidden bootstrap"), false);
});

test("TurnKey prefers run identity and is stable across hooks", () => {
  assert.equal(turnKey("s", "run-1", "inbound", "one"), turnKey("s", "run-1", "outbound", "two"));
  assert.notEqual(turnKey("s", "run-1"), turnKey("s", "run-2"));
});

test("canonical model refs project to Host provider and model fields", () => {
  assert.deepEqual(modelOverride("meituan/LongCat-2.0"), { provider: "meituan", model: "LongCat-2.0" });
  assert.equal(modelOverride("missing-provider"), undefined);
});

test("resolved child model comes from the final assistant session message", () => {
  const messages = [
    { role: "assistant", provider: "old", model: "old-model", content: "first" },
    { role: "user", content: "next" },
    { role: "assistant", provider: "meituan", model: "LongCat-2.0", content: "final" },
  ];
  assert.deepEqual(extractResolvedModel(messages), {
    resolved_provider: "meituan",
    resolved_model: "LongCat-2.0",
    resolved_model_ref: "meituan/LongCat-2.0",
  });
  assert.deepEqual(extractResolvedModel([{ role: "assistant", content: "missing metadata" }]), {});
});

test("hook callbacks return synchronously and do not call runtime inline", () => {
  const hooks = new Map(); let spawnCount = 0;
  registerDreamAgent({ pluginConfig: {}, on(name, handler) { hooks.set(name, handler); }, runtime: { subagent: { run() { spawnCount += 1; } } } });
  hooks.get("message_received")({ content: "real user", runId: "r" }, { sessionKey: "s", runId: "r" });
  const channelReturn = hooks.get("message_sent")({ success: true, content: "reply", runId: "r" }, { sessionKey: "s", runId: "r" });
  const turnReturn = hooks.get("agent_end")({ success: true, runId: "r", messages: [{ role: "user", content: "real user" }, { role: "assistant", content: "reply" }] }, { sessionKey: "s", runId: "r", messageProvider: "webchat" });
  assert.equal(channelReturn, undefined);
  assert.equal(turnReturn, undefined);
  assert.equal(spawnCount, 0);
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
