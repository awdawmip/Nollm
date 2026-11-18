import assert from "node:assert/strict";
import { test } from "node:test";
import { MemoryOperationRegistry, createMemoryGetFactory, createMemorySearchFactory } from "../src/memory-tools.js";

// Synthetic projection responses only; no runtime, Python, service, or database.
const CONFIG = { maxResults: 3, maxContextCharacters: 2048, operationTtlMs: 1000 };
const CONTEXT = { agentId: "agent-a", sessionKey: "session-a" };

function fakeBridge(responses) {
  const pending = [...responses];
  return {
    available: true,
    calls: [],
    workspaceForAgent() { return "/virtual/agent-a"; },
    async call(envelope) {
      this.calls.push(structuredClone(envelope));
      assert.ok(pending.length, "unexpected synthetic bridge call");
      return pending.shift();
    },
  };
}

function assertWire(result) {
  assert.deepEqual(JSON.parse(result.content[0].text), result.details);
}

async function searchProjection(items, following = []) {
  const bridge = fakeBridge([
    { ok: true, status: "surface", page: {}, root_identity: "synthetic-root" },
    { ok: true, status: "terminal", recalled_statement_ids: ["requested"] },
    { ok: true, items, stale_statement_ids: [] },
    ...following,
  ]);
  const registry = new MemoryOperationRegistry();
  const search = createMemorySearchFactory({ bridge, registry, config: CONFIG })(CONTEXT);
  const surface = await search.execute("surface", { query: "synthetic query" });
  assert.equal(surface.details.status, "surface");
  const result = await search.execute("select", {
    action: "select_fact", operationId: surface.details.operationId, candidateId: "synthetic-fact",
  });
  assert.equal(registry.operations.size, 0);
  assertWire(result);
  return { bridge, result };
}

async function getProjection(item) {
  const bridge = fakeBridge([{ ok: true, items: [item] }]);
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  const result = await get.execute("get", { path: "nollm://statement/requested" });
  assert.deepEqual(bridge.calls[0].statement_ids, ["requested"]);
  assertWire(result);
  return { bridge, result };
}

test("wrapped Unicode Statement ID round-trips unchanged with existing CRLF pagination", async () => {
  const id = " \tstatement/e\u0301/会议 😀 %\n ";
  const item = { statement_id: id, content_utf8: "first\r\nsecond\r\nthird" };
  const { bridge, result } = await searchProjection([item], [
    { ok: true, items: [item] }, { ok: true, items: [item] },
  ]);
  assert.equal(result.details.status, "complete");
  const [entry] = result.details.results;
  assert.equal(entry.statement_id, id);
  assert.equal(entry.citation, `nollm:${id}`);
  assert.equal(entry.snippet, item.content_utf8);
  assert.equal(entry.path, `nollm://statement/${encodeURIComponent(id)}`);
  assert.equal(decodeURIComponent(entry.path.slice("nollm://statement/".length)), id);
  const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
  const page = await get.execute("page", { path: entry.path, from: 2, lines: 1 });
  assert.deepEqual(page.details, {
    status: "complete", path: entry.path, text: "second", from: 2, lines: 1,
    truncated: true, nextFrom: 3, statementId: id, currentStatementProjection: true,
  });
  const last = await get.execute("last", { path: entry.path, from: page.details.nextFrom, lines: 2 });
  assert.equal(last.details.text, "third");
  assert.equal(last.details.truncated, false);
  assert.equal(last.details.nextFrom, undefined);
  assert.equal(last.details.statementId, id);
  assert.deepEqual(bridge.calls.slice(3).map((call) => call.statement_ids), [[id], [id]]);
  assertWire(page);
  assertWire(last);
});

for (const { name, id, content } of [
  { name: "space-only", id: " ", content: " " },
  { name: "tab/newline-only", id: "\t\n", content: " \t\n" },
]) {
  test(`canonical ${name} ID and content stay valid and unchanged`, async () => {
    const item = { statement_id: id, content_utf8: content };
    const { bridge, result } = await searchProjection([item], [{ ok: true, items: [item] }]);
    assert.equal(result.details.status, "complete");
    const [entry] = result.details.results;
    assert.equal(entry.statement_id, id);
    assert.equal(entry.citation, `nollm:${id}`);
    assert.equal(entry.snippet, content);
    assert.equal(entry.path, `nollm://statement/${encodeURIComponent(id)}`);
    const get = createMemoryGetFactory({ bridge, config: CONFIG })(CONTEXT);
    const read = await get.execute("get", { path: entry.path });
    assert.equal(read.details.status, "complete");
    assert.equal(read.details.statementId, id);
    assert.equal(read.details.text, content);
    assert.deepEqual(bridge.calls[3].statement_ids, [id]);
    assertWire(read);
  });
}

test("ordinary search output keeps its standard result fields", async () => {
  const { result } = await searchProjection([{ statement_id: "normal-id", content_utf8: "alpha\nbeta" }]);
  assert.equal(result.details.status, "complete");
  assert.deepEqual(result.details.results, [{
    path: "nollm://statement/normal-id", startLine: 1, endLine: 2, score: 1,
    snippet: "alpha\nbeta", source: "memory", citation: "nollm:normal-id", statement_id: "normal-id",
    geometry_ordered: true, score_is_not_truth_proof: true,
  }]);
});

test("shape validation does not impose requested/current ID equality", async () => {
  const { result } = await getProjection({ statement_id: "different-current-id", content_utf8: "synthetic current text" });
  assert.equal(result.details.status, "complete");
  assert.equal(result.details.statementId, "different-current-id");
  assert.equal(result.details.text, "synthetic current text");
  // Acceptance here tests shape only; it does not establish a real alias binding.
});

test("mixed projection filters malformed items and preserves valid neighbor identities", async () => {
  const items = [null, 7, false, "not-an-item", [],
    { statement_id: "first", content_utf8: "alpha" },
    { statement_id: "empty-content", content_utf8: "" },
    { statement_id: " second ", content_utf8: "\t\n" },
  ];
  const { result } = await searchProjection(items);
  assert.equal(result.details.status, "complete");
  assert.deepEqual(result.details.results.map((item) => item.statement_id), ["first", " second "]);
  assert.deepEqual(result.details.results.map((item) => item.snippet), ["alpha", "\t\n"]);
  assert.deepEqual(result.details.results.map((item) => decodeURIComponent(item.path.slice("nollm://statement/".length))),
    ["first", " second "]);
});

const INVALID_ITEMS = [
  ["missing ID", { content_utf8: "body" }],
  ["null ID", { statement_id: null, content_utf8: "body" }],
  ["number ID", { statement_id: 0, content_utf8: "body" }],
  ["boolean ID", { statement_id: false, content_utf8: "body" }],
  ["object ID", { statement_id: { value: "id" }, content_utf8: "body" }],
  ["array ID", { statement_id: ["id"], content_utf8: "body" }],
  ["empty ID", { statement_id: "", content_utf8: "body" }],
  ["missing content", { statement_id: "id" }],
  ["null content", { statement_id: "id", content_utf8: null }],
  ["number content", { statement_id: "id", content_utf8: 0 }],
  ["boolean content", { statement_id: "id", content_utf8: false }],
  ["object content", { statement_id: "id", content_utf8: { value: "body" } }],
  ["array content", { statement_id: "id", content_utf8: ["body"] }],
  ["empty content", { statement_id: "id", content_utf8: "" }],
];

for (const [name, item] of INVALID_ITEMS) {
  test(`search/get reject canonical-invalid ${name}`, async () => {
    const search = await searchProjection([item]);
    assert.equal(search.result.details.status, "complete_none");
    assert.deepEqual(search.result.details.results, []);
    const get = await getProjection(item);
    assert.deepEqual(get.result.details, { status: "not_found", path: "nollm://statement/requested", text: "" });
    assert.equal(get.result.details.currentStatementProjection, undefined);
  });
}
