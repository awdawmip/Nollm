import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import plugin, { asciiJson, boundedTurns, extractAssistantText, extractResolvedModel, extractUserTurns, formationRetryable, modelOverride, placementRetryable, registerDreamAgent, shouldApplyPlacement, surfaceBudget, turnKey, wellFormedText } from "../dist/index.js";

test("manifest exposes no main-agent Formation tool", () => {
  const manifest = JSON.parse(fs.readFileSync(new URL("../openclaw.plugin.json", import.meta.url)));
  assert.deepEqual(manifest.contracts.tools, []);
  assert.equal(manifest.configSchema.properties.prompt_version.default, "dream-json-p1");
  assert.equal(manifest.configSchema.properties.model_mode.default, "inherit");
  assert.equal(manifest.configSchema.properties.persist_subagent_transcripts.const, false);
  assert.equal(manifest.configSchema.properties.surface_page_size.maximum, 8);
  assert.equal(manifest.configSchema.properties.recall_surface_max_calls.default, 12);
  assert.equal(manifest.configSchema.properties.placement_surface_max_calls.default, 16);
  assert.equal(JSON.stringify(manifest.configSchema).includes("cursor"), false);
});

test("Surface budgets are fixed structural values with bounded calls", () => {
  const recall = surfaceBudget({}, "recall");
  const placement = surfaceBudget({}, "placement");
  assert.deepEqual(Object.keys(recall), Object.keys(placement));
  assert.equal(recall.page_size, 8);
  assert.equal(recall.max_calls, 12);
  assert.equal(placement.max_calls, 16);
  assert.equal("query" in recall, false);
  assert.equal("session" in recall, false);
});

test("wire text replaces isolated UTF-16 surrogates before UTF-8 encoding", () => {
  assert.equal(wellFormedText("valid \udc94 text"), "valid \ufffd text");
});

test("Python bridge wire is ASCII-safe and lossless for Windows pipes", () => {
  const value = { text: "项目周会 📅 每周二上午九点" };
  const wire = asciiJson(value);
  assert.equal(/[^\x00-\x7f]/.test(wire), false);
  assert.deepEqual(JSON.parse(wire), value);
});

test("plugin registers channel delivery, recall preparation, and Gateway completion hooks with no tool", () => {
  const hooks = new Map(); let toolCount = 0;
  registerDreamAgent({ pluginConfig: { enabled: false }, on(name, handler) { hooks.set(name, handler); }, registerTool() { toolCount += 1; } });
  assert.deepEqual([...hooks.keys()].sort(), ["agent_end", "agent_turn_prepare", "before_agent_run", "llm_output", "message_received", "message_sent", "subagent_ended", "subagent_spawned"]);
  assert.equal(toolCount, 0);
});

test("recall NONE paths emit explicit audit evidence", () => {
  const source = fs.readFileSync(new URL("../src/index.ts", import.meta.url), "utf8");
  assert.match(source, /built\.status === "complete_none"/);
  assert.match(source, /rendered\.outcome === "none"/);
  assert.equal((source.match(/status: "completed_none", stage: "recall"/g) ?? []).length, 2);
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

test("shadow Formation never continues into Placement", () => {
  const parsed = { ok: true, statements: [{ statement_id: "s" }] };
  assert.equal(shouldApplyPlacement({ write_mode: "shadow", statement_store_workspace: "C:\\temp" }, parsed, "meituan/LongCat-2.0"), false);
  assert.equal(shouldApplyPlacement({ write_mode: "statement-store", statement_store_workspace: "C:\\temp" }, parsed, "meituan/LongCat-2.0"), true);
});

test("engineering input errors never trigger a Formation model retry", () => {
  assert.equal(formationRetryable({ ok: false, error: "invalid_input" }), false);
  assert.equal(formationRetryable({ ok: false, error: "bridge_process_error" }), false);
  assert.equal(formationRetryable({ ok: false, error: "invalid_json" }), true);
  assert.equal(formationRetryable({ ok: false, error: "invalid_schema" }), true);
});

test("Placement retries only JSON and schema failures", () => {
  assert.equal(placementRetryable({ ok: false, error: "invalid_json" }), true);
  assert.equal(placementRetryable({ ok: false, error: "invalid_schema" }), true);
  assert.equal(placementRetryable({ ok: false, error: "invalid_input" }), false);
  assert.equal(placementRetryable({ ok: false, error: "bridge_process_error" }), false);
});

test("plugin entry is an ordinary hook plugin", () => {
  assert.equal(plugin.id, "nollm-formation");
  assert.equal(typeof plugin.register, "function");
});
