import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, unlink } from "node:fs/promises";
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
  assert.equal((await store.read(first.record.capture_id)).user_utf8, "原文 user\nline 2");
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

test("stale processing claims recover and callback failure becomes retry", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "processing", { attempt: 1, batchId: "dead", eventEpochMs: 1000 });
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async () => { throw new Error("provider down"); });
  assert.equal((await worker.runOnce(2000)).status, "completed");
  const state = await store.currentState(record.capture_id);
  assert.equal(state.status, "retry"); assert.equal(state.attempt, 2); assert.match(state.error, /provider down/);
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
