import assert from "node:assert/strict";
import { test } from "node:test";
import { buildNollmMemoryPrompt, createNollmProvider } from "../src/provider.js";
import {
  MemoryOperationRegistry,
  createMemoryGetFactory,
  createMemorySearchFactory,
} from "../src/memory-tools.js";

// Exercise the V3.14 JS contract without starting a runtime, service, or sidecar.
const CONFIG = { maxResults: 3, maxContextCharacters: 2048, operationTtlMs: 1000 };
const CONTEXT = { agentId: "agent-a", sessionKey: "session-a" };
const SCOPE = { ...CONTEXT, workspace: "/virtual/agent-a" };
const SURFACE = { ok: true, status: "surface", page: { regions: ["region-a"] }, root_identity: "root-a" };

function fakeBridge(responses = [], { available = true, workspace = "/virtual/agent-a" } = {}) {
  const pending = [...responses];
  return {
    available,
    calls: [],
    workspaceForAgent() { return workspace; },
    async call(envelope, signal) {
      this.calls.push({ envelope: structuredClone(envelope), signal });
      assert.ok(pending.length, "unexpected bridge call");
      return pending.shift();
    },
  };
}

function searchHarness(responses, options) {
  const bridge = fakeBridge(responses, options);
  const registry = new MemoryOperationRegistry({ ttlMs: CONFIG.operationTtlMs });
  const factory = createMemorySearchFactory({ bridge, registry, config: CONFIG });
  return { bridge, registry, factory, tool: factory(CONTEXT) };
}

async function startSearch(harness, signal) {
  const result = await harness.tool.execute("call-surface", { query: "meeting" }, signal);
  assert.equal(result.details.status, "surface");
  return result.details.operationId;
}

test("V3.14 registers memory capability and both tools without starting its service", async () => {
  const registered = { tools: [], services: [] };
  const provider = createNollmProvider({
    pluginConfig: {},
    resolvePath: () => "/virtual/nollm",
    registerMemoryCapability(value) { registered.capability = value; },
    registerTool(factory, options) { registered.tools.push({ factory, options }); },
    registerService(value) { registered.services.push(value); },
    logger: { warn() { assert.fail("service must not be started by registration"); } },
  });
  assert.equal(provider.config.runtimeMode, "unavailable");
  assert.deepEqual(registered.tools.map(({ options }) => options.names), [["memory_search"], ["memory_get"]]);
  assert.equal(registered.capability.promptBuilder, buildNollmMemoryPrompt);
  assert.equal(registered.capability.flushPlanResolver(), null);
  assert.deepEqual(await registered.capability.publicArtifacts.listArtifacts(), []);
  assert.equal(registered.services.length, 1);
  assert.equal(registered.services[0].id, "nollm-memory-runtime");
});

test("memory prompt requires both available tools and documents their URI contract", () => {
  for (const tools of [[], ["memory_search"], ["memory_get"]]) {
    assert.deepEqual(buildNollmMemoryPrompt({ availableTools: tools }), []);
  }
  const prompt = buildNollmMemoryPrompt({ availableTools: new Set(["memory_search", "memory_get"]) }).join("\n");
  assert.match(prompt, /memory_search/);
  assert.match(prompt, /memory_get/);
  assert.match(prompt, /nollm:\/\//);
  assert.match(prompt, /do not claim to remember/);
});

test("tool factories require a host agent identity", () => {
  const bridge = fakeBridge();
  const registry = new MemoryOperationRegistry();
  for (const factory of [
    createMemorySearchFactory({ bridge, registry, config: CONFIG }),
    createMemoryGetFactory({ bridge, config: CONFIG }),
  ]) {
    for (const context of [undefined, {}, { agentId: " " }]) assert.equal(factory(context), null);
  }
  assert.equal(bridge.calls.length, 0);
});

test("unavailable runtime returns empty search/get boundaries without bridge calls", async () => {
  const { tool, bridge, registry } = searchHarness([], { available: false });
  const search = await tool.execute("call", { query: "meeting" });
  assert.equal(search.details.status, "unavailable");
  assert.deepEqual(search.details.results, []);
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  const result = await get.execute("call", { path: "nollm://statement/id" });
  assert.equal(result.details.status, "unavailable");
  assert.equal(result.details.text, "");
  assert.equal(registry.operations.size, 0);
  assert.equal(bridge.calls.length, 0);
});

test("registry binds operations to agent, session, and workspace", (t) => {
  t.mock.method(Date, "now", () => 100);
  const registry = new MemoryOperationRegistry({ ttlMs: 100 });
  const operation = registry.create(SCOPE, { query: "meeting" });
  for (const scope of [
    { ...SCOPE, agentId: "other-agent" },
    { ...SCOPE, sessionKey: "other-session" },
    { ...SCOPE, workspace: "/other/workspace" },
  ]) assert.equal(registry.get(operation.operationId, scope), undefined);
  assert.equal(registry.get(operation.operationId, SCOPE), operation);
  assert.equal(registry.get("unknown-operation", SCOPE), undefined);
});

test("registry refreshes a valid operation TTL and expires it at the boundary", (t) => {
  let now = 100;
  t.mock.method(Date, "now", () => now);
  const registry = new MemoryOperationRegistry({ ttlMs: 50 });
  const operation = registry.create(SCOPE, {});
  now = 149;
  assert.equal(registry.get(operation.operationId, SCOPE), operation);
  now = 199;
  assert.equal(registry.get(operation.operationId, SCOPE), undefined);
  assert.equal(registry.operations.size, 0);
});

test("registry evicts the oldest created operation when capacity is reached", (t) => {
  let now = 100;
  t.mock.method(Date, "now", () => now);
  const registry = new MemoryOperationRegistry({ capacity: 2, ttlMs: 1000 });
  const first = registry.create(SCOPE, {});
  now = 110;
  const second = registry.create(SCOPE, {});
  now = 120;
  const third = registry.create(SCOPE, {});
  assert.equal(registry.operations.size, 2);
  assert.equal(registry.get(first.operationId, SCOPE), undefined);
  assert.equal(registry.get(second.operationId, SCOPE), second);
  assert.equal(registry.get(third.operationId, SCOPE), third);
  registry.delete(third.operationId);
  assert.equal(registry.get(third.operationId, SCOPE), undefined);
});

test("invalid search parameters do not allocate operations or call the bridge", async () => {
  const { tool, bridge, registry } = searchHarness([]);
  for (const params of [
    {}, { query: " " }, { query: "meeting", operationId: "old-operation" },
    { action: "open_region", regionId: "region" }, { action: "select_fact", candidateId: "fact" },
  ]) assert.equal((await tool.execute("call", params)).details.status, "invalid_parameters");
  assert.equal(registry.operations.size, 0);
  assert.equal(bridge.calls.length, 0);
});

test("surface requests carry host scope, bounded settings, and the caller signal", async () => {
  const harness = searchHarness([SURFACE]);
  const signal = new AbortController().signal;
  const result = await harness.tool.execute("call", { query: "  meeting  " }, signal);
  assert.equal(result.details.status, "surface");
  assert.deepEqual(result.details.results, []);
  assert.equal(result.details.nollm.continue_with_same_tool, true);
  assert.deepEqual(JSON.parse(result.content[0].text), result.details);
  const { envelope, signal: receivedSignal } = harness.bridge.calls[0];
  assert.equal(receivedSignal, signal);
  assert.equal(envelope.operation_id, result.details.operationId);
  assert.equal(envelope.memory_workspace, SCOPE.workspace);
  assert.deepEqual(envelope.history, []);
  assert.equal(envelope.request.scope_id, "agent:agent-a");
  assert.deepEqual(envelope.request.stimulus_material, ["meeting"]);
  assert.equal(envelope.request.locality_max_results, CONFIG.maxResults);
  assert.equal(envelope.request.locality_max_chars, CONFIG.maxContextCharacters);
  assert.equal(envelope.request.ttl_ms, CONFIG.operationTtlMs);
});

test("a failed initial encounter leaves no reusable operation", async () => {
  const harness = searchHarness([{ ok: false, error: "field-unavailable" }]);
  const result = await harness.tool.execute("call", { query: "meeting" });
  assert.equal(result.details.status, "unavailable");
  assert.equal(result.details.reason, "field-unavailable");
  assert.equal(harness.registry.operations.size, 0);
});

test("a continuation cannot reuse another host session's operation", async () => {
  const harness = searchHarness([SURFACE]);
  const operationId = await startSearch(harness);
  const other = harness.factory({ ...CONTEXT, sessionKey: "other-session" });
  const result = await other.execute("call", { action: "open_region", operationId, regionId: "region-a" });
  assert.equal(result.details.status, "operation_unavailable");
  assert.equal(harness.bridge.calls.length, 1);
});

test("continuations replay only successful region/locality navigation", async () => {
  const harness = searchHarness([
    SURFACE, { ok: true, status: "region", page: {} },
    { ok: false, status: "unavailable", error: "stale-entry" },
    { ok: true, status: "locality", facts: ["fact-a"] },
  ]);
  const operationId = await startSearch(harness);
  const navigate = (action, extra) => harness.tool.execute("call", { action, operationId, ...extra });
  assert.equal((await navigate("open_region", { regionId: "region-a" })).details.status, "region");
  const parameters = { regionId: "region-a", entryId: "entry-a" };
  assert.equal((await navigate("enter_locality", parameters)).details.status, "unavailable");
  assert.deepEqual(harness.registry.get(operationId, SCOPE).history, [{ action: "open_region", region_id: "region-a" }]);
  const locality = await navigate("enter_locality", parameters);
  assert.equal(locality.details.status, "locality");
  assert.deepEqual(harness.bridge.calls[3].envelope.history, [
    { action: "open_region", region_id: "region-a" },
    { action: "enter_locality", region_id: "region-a", entry_id: "entry-a" },
  ]);
});

for (const action of ["none", "defer"]) {
  test(`${action} terminates the operation without projection or reusable state`, async () => {
    const harness = searchHarness([SURFACE, { ok: true, status: "terminal" }]);
    const operationId = await startSearch(harness);
    const result = await harness.tool.execute("call", { action, operationId });
    assert.equal(result.details.status, "complete_none");
    assert.deepEqual(result.details.results, []);
    assert.equal(harness.registry.get(operationId, SCOPE), undefined);
    assert.deepEqual(harness.bridge.calls[1].envelope.terminal, {
      action, candidate_id: null, semantic_relation: null, recalled_fact_ids: [],
    });
    assert.equal(harness.bridge.calls.length, 2);
  });
}

test("selected search facts round-trip their documented nollm URI through memory_get", async () => {
  const statementId = "statement/会议 %";
  const item = { statement_id: statementId, content_utf8: "Room 401\nWednesday" };
  const harness = searchHarness([
    SURFACE, { ok: true, status: "locality", facts: [{ fact_id: "fact-a" }] },
    { ok: true, status: "terminal", recalled_statement_ids: [statementId] },
    { ok: true, items: [item], stale_statement_ids: [] },
    { ok: true, items: [item] },
  ]);
  const signal = new AbortController().signal;
  const operationId = await startSearch(harness, signal);
  await harness.tool.execute("call", { action: "enter_locality", operationId, regionId: "region-a", entryId: "entry-a" }, signal);
  const selected = await harness.tool.execute("call", {
    action: "select_fact", operationId, candidateId: "fact-a", semanticRelation: "same", recalledFactIds: ["fact-a"],
  }, signal);
  assert.equal(selected.details.status, "complete");
  assert.equal(harness.registry.get(operationId, SCOPE), undefined);
  assert.deepEqual(harness.bridge.calls[2].envelope.terminal, {
    action: "select_fact", candidate_id: "fact-a", semantic_relation: "same", recalled_fact_ids: ["fact-a"],
  });
  const [result] = selected.details.results;
  assert.equal(result.snippet, item.content_utf8);
  const get = createMemoryGetFactory({ bridge: harness.bridge, config: CONFIG })(CONTEXT);
  const read = await get.execute("call-get", { path: result.path }, signal);
  assert.equal(read.details.status, "complete", "a search-issued URI must be readable by memory_get");
  assert.equal(result.path, `nollm://statement/${encodeURIComponent(statementId)}`);
  assert.equal(read.details.text, item.content_utf8);
  assert.equal(read.details.statementId, statementId);
  assert.deepEqual(harness.bridge.calls[4].envelope.statement_ids, [statementId]);
  assert.ok(harness.bridge.calls.every((call) => call.signal === signal));
});

test("failed selection closes the operation without requesting statement projection", async () => {
  const harness = searchHarness([SURFACE, { ok: false, status: "unavailable", error: "stale-fact" }]);
  const operationId = await startSearch(harness);
  const result = await harness.tool.execute("call", { action: "select_fact", operationId, candidateId: "fact-a" });
  assert.equal(result.details.status, "unavailable");
  assert.equal(result.details.reason, "stale-fact");
  assert.equal(harness.registry.operations.size, 0);
  assert.equal(harness.bridge.calls.length, 2);
});

test("failed statement projection yields no claimed memories and consumes the operation", async () => {
  const harness = searchHarness([
    SURFACE, { ok: true, status: "terminal", recalled_statement_ids: ["statement-a"] },
    { ok: false, error: "projection-unavailable" },
  ]);
  const operationId = await startSearch(harness);
  const result = await harness.tool.execute("call", { action: "select_fact", operationId, candidateId: "fact-a" });
  assert.equal(result.details.status, "complete_none");
  assert.deepEqual(result.details.results, []);
  assert.equal(harness.registry.operations.size, 0);
});

test("memory_get decodes statement identity and paginates current CRLF content", async () => {
  const item = { statement_id: "statement/会议 %", content_utf8: "first\r\nsecond\r\nthird" };
  const bridge = fakeBridge([{ ok: true, items: [item] }, { ok: true, items: [item] }]);
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  const path = `nollm://statement/${encodeURIComponent(item.statement_id)}`;
  const page = await get.execute("call", { path, from: 2, lines: 1 });
  assert.deepEqual(page.details, {
    status: "complete", path, text: "second", from: 2, lines: 1,
    truncated: true, nextFrom: 3, statementId: item.statement_id, currentStatementProjection: true,
  });
  const last = await get.execute("call", { path, from: page.details.nextFrom, lines: 2 });
  assert.equal(last.details.text, "third");
  assert.equal(last.details.truncated, false);
  assert.equal(last.details.nextFrom, undefined);
  assert.deepEqual(bridge.calls[0].envelope.statement_ids, [item.statement_id]);
  assert.equal(bridge.calls[0].envelope.memory_workspace, SCOPE.workspace);
});

test("memory_get rejects foreign, empty, and malformed URI paths without bridge calls", async () => {
  const bridge = fakeBridge();
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  for (const path of [undefined, "", "../statement", "file:///statement", "nolm://statement/id", "nollm://statement/", "nollm://statement/%ZZ"]) {
    const result = await get.execute("call", { path });
    assert.equal(result.details.status, "not_found");
    assert.equal(result.details.text, "");
  }
  assert.equal(bridge.calls.length, 0);
});

test("memory_get does not return text for failed, absent, or non-text projections", async () => {
  const bridge = fakeBridge([
    { ok: false, error: "projection-unavailable" },
    { ok: true, items: [] },
    { ok: true, items: [{ statement_id: "id", content_utf8: null }] },
  ]);
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  for (let index = 0; index < 3; index += 1) {
    const result = await get.execute("call", { path: "nollm://statement/id" });
    assert.equal(result.details.status, "not_found");
    assert.equal(result.details.text, "");
  }
});
