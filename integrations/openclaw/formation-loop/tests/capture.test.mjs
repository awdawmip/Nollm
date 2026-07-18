import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { AbsorptionWorker, CaptureStore } from "../dist/capture.js";

async function workspace(run) {
  const root = await mkdtemp(join(tmpdir(), "nollm-capture-"));
  try { await run(root); } finally { await rm(root, { recursive: true, force: true }); }
}

const input = (overrides = {}) => ({ scopeKey: "user-a", sessionKey: "session-1", turnIdentity: "run-1", userUtf8: "原文 user\nline 2", assistantUtf8: "answer 😀", capturedEpochMs: 1000, ...overrides });

test("Capture publishes exact immutable bytes and duplicate hooks replay", () => workspace(async root => {
  const store = new CaptureStore(root);
  const first = await store.publish(input());
  const bytes = await readFile(store.capturePath(first.record.capture_id), "utf8");
  const replay = await store.publish(input({ capturedEpochMs: 2000 }));
  assert.equal(replay.record.capture_id, first.record.capture_id);
  assert.equal(replay.replayed, true);
  assert.equal(await readFile(store.capturePath(first.record.capture_id), "utf8"), bytes);
  const record = await store.read(first.record.capture_id);
  assert.equal(record.user_utf8, "原文 user\nline 2");
  assert.deepEqual(record.turn_order, ["user", "assistant"]);
  assert.equal(record.user_utf8_bytes, Buffer.byteLength(record.user_utf8, "utf8"));
  assert.equal(record.assistant_utf8_bytes, Buffer.byteLength(record.assistant_utf8, "utf8"));
  assert.equal(record.visible_endpoint_kind, "visible_assistant_delivery");
  assert.equal(record.plugin_version, "0.16.0");
}));

test("one scope workspace turn identity cannot publish conflicting content", () => workspace(async root => {
  const store = new CaptureStore(root);
  const first = await store.publish(input({ workspaceKey: "workspace-a" }));
  await assert.rejects(
    store.publish(input({ workspaceKey: "workspace-a", assistantUtf8: "different answer" })),
    /immutable Capture conflict/,
  );
  assert.equal((await store.allRecords()).length, 1);
  assert.equal((await store.allRecords())[0].capture_id, first.record.capture_id);
}));

test("corrupt Capture files are skipped with explicit diagnostics", () => workspace(async root => {
  const store = new CaptureStore(root);
  await store.publish(input());
  await writeFile(join(root, "captures", "corrupt.json"), "{bad", "utf8");
  const scan = await store.scanRecords();
  assert.equal(scan.records.length, 1);
  assert.deepEqual(scan.diagnostics.map(item => item.file), ["corrupt.json"]);
}));

test("missing sidecar is reconstructed from immutable Capture", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await rm(store.eventDirectory(record.capture_id), { recursive: true, force: true });
  assert.equal((await store.currentState(record.capture_id)).status, "captured");
}));

test("pending fallback is cross-session, scope isolated, bounded, and admission removes it", () => workspace(async root => {
  const store = new CaptureStore(root);
  const one = await store.publish(input());
  await store.publish(input({ scopeKey: "user-b", sessionKey: "other", turnIdentity: "run-2", userUtf8: "secret" }));
  const pending = await store.renderPending("user-a", { maxCaptures: 4, maxChars: 500, maxAgeMs: 5000 }, 2000);
  assert.deepEqual(pending.captureIds, [one.record.capture_id]);
  assert.match(pending.injection, /原文 user/);
  assert.doesNotMatch(pending.injection, /secret/);
  await store.appendEvent(one.record.capture_id, "admitted", { attempt: 1, statementIds: ["dream:one"] });
  assert.equal((await store.renderPending("user-a", { maxCaptures: 4, maxChars: 500, maxAgeMs: 5000 }, 2000)).injection, "");
}));

test("terminal defer preserves Capture but exits pending fallback", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "deferred", { attempt: 1, error: "no durable memory" });
  assert.equal((await store.renderPending("user-a", { maxCaptures: 4, maxChars: 500, maxAgeMs: 5000 }, 2000)).injection, "");
  assert.equal((await store.read(record.capture_id)).content_sha256, record.content_sha256);
}));

test("worker batches captures, serializes execution, and records terminal states", () => workspace(async root => {
  const store = new CaptureStore(root);
  const one = await store.publish(input());
  const two = await store.publish(input({ turnIdentity: "run-2", userUtf8: "second" }));
  let calls = 0;
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records) => {
    calls += 1;
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: [`dream:${record.capture_id.slice(-8)}`] }));
  });
  const [first, concurrent] = await Promise.all([worker.runOnce(2000), worker.runOnce(2000)]);
  assert.equal(first.status, "completed"); assert.equal(concurrent.status, "busy"); assert.equal(calls, 1);
  assert.equal((await store.currentState(one.record.capture_id)).status, "admitted");
  assert.equal((await store.currentState(two.record.capture_id)).status, "admitted");
}));

test("worker never mixes scope workspace or profile partitions", () => workspace(async root => {
  const store = new CaptureStore(root);
  const anchor = await store.publish(input({ workspaceKey: "workspace-a" }));
  const otherScope = await store.publish(input({ scopeKey: "user-b", workspaceKey: "workspace-a", turnIdentity: "run-2" }));
  const otherWorkspace = await store.publish(input({ workspaceKey: "workspace-b", turnIdentity: "run-3" }));
  const seen = [];
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records) => {
    seen.push(records.map(record => record.capture_id));
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: ["dream:partition"] }));
  });
  await worker.runOnce(2000);
  assert.deepEqual(seen, [[anchor.record.capture_id]]);
  assert.equal((await store.currentState(otherScope.record.capture_id)).status, "captured");
  assert.equal((await store.currentState(otherWorkspace.record.capture_id)).status, "captured");
}));

test("stale processing claims recover and callback failure becomes retry", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "processing", { attempt: 1, batchId: "dead", eventEpochMs: 1000 });
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async () => { throw new Error("provider down"); });
  assert.equal((await worker.runOnce(2000)).status, "completed");
  const state = await store.currentState(record.capture_id);
  assert.equal(state.status, "retry"); assert.equal(state.attempt, 2); assert.match(state.error, /provider down/);
}));

test("retry batch identity is preserved and new Captures do not join replay", () => workspace(async root => {
  const store = new CaptureStore(root);
  const one = await store.publish(input());
  const two = await store.publish(input({ turnIdentity: "run-2", userUtf8: "second" }));
  let firstExecutionId;
  const failed = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records, executionId) => {
    firstExecutionId = executionId;
    return records.map(record => ({ captureId: record.capture_id, status: "retry", error: "injected" }));
  });
  const firstRun = await failed.runOnce(2000);
  const fresh = await store.publish(input({ turnIdentity: "run-3", userUtf8: "fresh" }));
  let replayedIds = [], replayExecutionId;
  const replay = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records, executionId) => {
    replayedIds = records.map(record => record.capture_id);
    replayExecutionId = executionId;
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: ["dream:replay"] }));
  });
  const secondRun = await replay.runOnce(3000);
  assert.equal(secondRun.batchId, firstRun.batchId);
  assert.notEqual(replayExecutionId, firstExecutionId);
  assert.deepEqual(replayedIds, [one.record.capture_id, two.record.capture_id]);
  assert.equal((await store.currentState(fresh.record.capture_id)).status, "captured");
}));

test("retry respects bounded exponential backoff", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "retry", { attempt: 1, batchId: "batch-retry", eventEpochMs: 2000, error: "temporary" });
  let calls = 0;
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 10_000, retryBackoffMs: 1000 }, async (_batch, records) => {
    calls += 1;
    return records.map(item => ({ captureId: item.capture_id, status: "admitted", statementIds: ["dream:retry"] }));
  });
  assert.equal((await worker.runOnce(2500)).status, "idle");
  assert.equal(calls, 0);
  assert.equal((await worker.runOnce(3000)).batchId, "batch-retry");
  assert.equal(calls, 1);
}));

test("a live worker lock fails closed without deleting another owner lock", () => workspace(async root => {
  const store = new CaptureStore(root); await store.publish(input());
  const lock = join(root, "worker.lock");
  await (await import("node:fs/promises")).writeFile(lock, "owner", "utf8");
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 60_000 }, async () => []);
  assert.equal((await worker.runOnce(Date.now())).status, "busy");
  assert.equal(await readFile(lock, "utf8"), "owner");
  await unlink(lock);
}));
