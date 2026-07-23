import test from "node:test";
import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, rm, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { AbsorptionWorker, CAPTURE_PLUGIN_VERSION, CaptureStore, buildCaptureSourceWindowGroups } from "../dist/capture.js";

async function workspace(run) {
  const root = await mkdtemp(join(tmpdir(), "nollm-capture-"));
  try { await run(root); } finally { await rm(root, { recursive: true, force: true }); }
}

const input = (overrides = {}) => ({ scopeKey: "user-a", sessionKey: "session-1", turnIdentity: "run-1", userUtf8: "原文 user\nline 2", assistantUtf8: "answer 😀", capturedEpochMs: 1000, ...overrides });

test("Capture publishes exact immutable bytes and duplicate hooks replay", () => workspace(async root => {
  assert.equal(CAPTURE_PLUGIN_VERSION, "0.17.0");
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
  assert.equal(record.plugin_version, "0.17.0");
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

test("role directives are append-only, reopenable, and default assistant to context-only", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input({ mainRunIdentity: "run-1" }));
  const pending = await store.publishDirective({
    captureId: record.capture_id, mainRunIdentity: "run-1", assistantRoleMode: "source",
    memoryToolActions: ["surface"], recalledStatementIds: [], sequence: 1, finalized: false,
  });
  const final = await store.publishDirective({
    captureId: record.capture_id, mainRunIdentity: "run-1", assistantRoleMode: "memory_derived",
    memoryToolActions: ["recall", "surface"], selectedEntryId: "entry-a",
    recalledStatementIds: ["statement-a"], sequence: 2, finalized: true,
  });
  assert.equal(pending.directive.finalized, false);
  assert.equal(final.directive.assistant_role_mode, "memory_derived");
  assert.equal((await store.directive(record.capture_id)).directive_id, final.directive.directive_id);
  assert.equal((await new CaptureStore(root).directive(record.capture_id)).selected_entry_id_sha256.length, 64);

  const legacy = await store.publish(input({ turnIdentity: "legacy", mainRunIdentity: "legacy" }));
  const fallback = await store.directiveForAbsorption(legacy.record, legacy.record.captured_epoch_ms, 30000);
  assert.equal(fallback.assistant_role_mode, "context_only");
  assert.equal(fallback.finalization_reason, "safe_default_missing");
  assert.equal(fallback.finalized, true);
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

test("Writer context is chronological same-session prior-only and does not change Capture state", () => workspace(async root => {
  const store = new CaptureStore(root);
  const older = await store.publish(input({ turnIdentity: "context-1", capturedEpochMs: 1000, userUtf8: "context one" }));
  const newest = await store.publish(input({ turnIdentity: "context-2", capturedEpochMs: 2000, userUtf8: "context two" }));
  await store.publish(input({ sessionKey: "other-session", turnIdentity: "other", capturedEpochMs: 2500, userUtf8: "foreign" }));
  const source = await store.publish(input({ turnIdentity: "source", capturedEpochMs: 3000, userUtf8: "that evening" }));
  const future = await store.publish(input({ turnIdentity: "future", capturedEpochMs: 4000, userUtf8: "future" }));

  const context = await store.contextBefore([source.record], 2, 1000);
  assert.deepEqual(context.map(record => record.capture_id), [older.record.capture_id, newest.record.capture_id]);
  assert.equal((await store.currentState(older.record.capture_id)).status, "captured");
  assert.equal((await store.currentState(newest.record.capture_id)).status, "captured");
  assert.equal((await store.currentState(future.record.capture_id)).status, "captured");
}));

test("evaluated zero-new preserves Capture but exits pending fallback", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "evaluated_no_new_propositions", { attempt: 1 });
  assert.equal((await store.renderPending("user-a", { maxCaptures: 4, maxChars: 500, maxAgeMs: 5000 }, 2000)).injection, "");
  assert.equal((await store.read(record.capture_id)).content_sha256, record.content_sha256);
}));

test("legacy semantic terminal states migrate append-only without changing Raw Capture", () => workspace(async root => {
  const store = new CaptureStore(root);
  for (const [index, legacyStatus, expected] of [
    [1, "no_memory", "evaluated_no_new_propositions_legacy"],
    [2, "deferred", "retryable_defer_legacy"],
  ]) {
    const { record } = await store.publish(input({ turnIdentity: `legacy-${index}`, userUtf8: `legacy ${index}` }));
    const rawBefore = await readFile(store.capturePath(record.capture_id), "utf8");
    const event = {
      schema_version: "nollm_openclaw_capture_state_event_v1", event_id: `legacy-${index}`,
      capture_id: record.capture_id, status: legacyStatus, event_epoch_ms: 2000, attempt: 1,
    };
    await mkdir(store.eventDirectory(record.capture_id), { recursive: true });
    await writeFile(join(store.eventDirectory(record.capture_id), `legacy-${index}.json`), `${JSON.stringify(event)}\n`, "utf8");
    assert.equal((await store.currentState(record.capture_id)).status, expected);
    assert.equal(await readFile(store.capturePath(record.capture_id), "utf8"), rawBefore);
    assert.equal((await store.events(record.capture_id)).length, 3);
  }
}));

test("oversized Capture receives a dedicated batch instead of starving", () => workspace(async root => {
  const store = new CaptureStore(root);
  const oversized = await store.publish(input({ userUtf8: "x".repeat(2500), assistantUtf8: "y".repeat(2500) }));
  let observed = [];
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records) => {
    observed = records.map(record => record.capture_id);
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: ["statement:oversized"] }));
  });
  assert.equal((await worker.runOnce(2000)).status, "completed");
  assert.deepEqual(observed, [oversized.record.capture_id]);
}));

test("source windows cover UTF-8 content deterministically with bounded overlap", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input({ userUtf8: "界".repeat(24000), assistantUtf8: "z".repeat(12000) }));
  const first = buildCaptureSourceWindowGroups([record], 12000, 32000, 128);
  const second = buildCaptureSourceWindowGroups([record], 12000, 32000, 128);
  assert.deepEqual(first, second);
  const windows = first.flat();
  assert.ok(Buffer.byteLength(record.user_utf8, "utf8") > 65536);
  assert.ok(windows.every(window => Buffer.byteLength(window.text_utf8, "utf8") <= 12000));
  for (const role of ["user", "assistant"]) {
    const roleWindows = windows.filter(window => window.role === role).sort((a, b) => a.window_index - b.window_index);
    assert.equal(roleWindows[0].start, 0);
    assert.equal(roleWindows.at(-1).end, [...record[`${role}_utf8`]].length);
    for (let index = 1; index < roleWindows.length; index += 1) {
      assert.ok(roleWindows[index].start <= roleWindows[index - 1].end);
      assert.ok(roleWindows[index].start >= roleWindows[index - 1].end - 128);
    }
  }
}));

test("incomplete continuation resumes immediately after worker restart", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  const evaluation = {
    writer_schema: "writer-v4", prompt_version: "prompt-v4", context_fingerprint: "context",
    current_memory_fingerprint: "memory", source_coverage: "partial", evaluation_epoch_ms: 2000,
  };
  const continuation = { group_index: 0, pass_index: 1, total_groups: 1, covered_ranges: [], uncovered_ranges: [{ capture_id: record.capture_id, role: "user", start: 1, end: 2 }] };
  const first = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async () => [
    { captureId: record.capture_id, status: "incomplete_continuation", statementIds: ["statement:one"], evaluation, continuation },
  ]);
  assert.equal((await first.runOnce(2000)).status, "completed");
  const second = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async () => [
    { captureId: record.capture_id, status: "admitted", statementIds: ["statement:one", "statement:two"], evaluation },
  ]);
  assert.equal((await second.runOnce(2001)).status, "completed");
  assert.deepEqual((await store.currentState(record.capture_id)).statement_ids, ["statement:one", "statement:two"]);
}));

test("zero-new evaluation is skipped only while its identity remains current", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  const evaluation = {
    writer_schema: "writer-v4", prompt_version: "prompt-v4", context_fingerprint: "context",
    current_memory_fingerprint: "memory", source_coverage: "complete", evaluation_epoch_ms: 2000,
  };
  await store.appendEvent(record.capture_id, "evaluated_no_new_propositions", { attempt: 1, evaluation, eventEpochMs: 2000 });
  let absorbed = 0;
  const stable = new AbsorptionWorker(store, {
    batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100,
    reevaluationNeeded: async () => false,
  }, async () => { absorbed += 1; return []; });
  assert.equal((await stable.runOnce(2001)).status, "idle");
  assert.equal(absorbed, 0);
  const changed = new AbsorptionWorker(store, {
    batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100,
    reevaluationNeeded: async () => true,
  }, async () => {
    absorbed += 1;
    return [{ captureId: record.capture_id, status: "evaluated_no_new_propositions", evaluation }];
  });
  assert.equal((await changed.runOnce(2002)).status, "completed");
  assert.equal(absorbed, 1);
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

test("worker never mixes scope workspace session or profile partitions", () => workspace(async root => {
  const store = new CaptureStore(root);
  const anchor = await store.publish(input({ workspaceKey: "workspace-a" }));
  const otherScope = await store.publish(input({ scopeKey: "user-b", workspaceKey: "workspace-a", turnIdentity: "run-2" }));
  const otherWorkspace = await store.publish(input({ workspaceKey: "workspace-b", turnIdentity: "run-3" }));
  const otherSession = await store.publish(input({ workspaceKey: "workspace-a", sessionKey: "session-2", turnIdentity: "run-4" }));
  const seen = [];
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records) => {
    seen.push(records.map(record => record.capture_id));
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: ["dream:partition"] }));
  });
  await worker.runOnce(2000);
  assert.deepEqual(seen, [[anchor.record.capture_id]]);
  assert.equal((await store.currentState(otherScope.record.capture_id)).status, "captured");
  assert.equal((await store.currentState(otherWorkspace.record.capture_id)).status, "captured");
  assert.equal((await store.currentState(otherSession.record.capture_id)).status, "captured");
}));

test("stale processing claims recover and callback failure becomes retry", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "processing", { attempt: 1, batchId: "dead", eventEpochMs: 1000 });
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async () => { throw new Error("provider down"); });
  assert.equal((await worker.runOnce(2000)).status, "completed");
  const state = await store.currentState(record.capture_id);
  assert.equal(state.status, "retryable_defer"); assert.equal(state.attempt, 2); assert.match(state.error, /provider down/);
}));

test("retry batch identity is preserved and new Captures do not join replay", () => workspace(async root => {
  const store = new CaptureStore(root);
  const one = await store.publish(input());
  const two = await store.publish(input({ turnIdentity: "run-2", userUtf8: "second" }));
  let firstExecutionId;
  const failed = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, async (_batch, records, executionId) => {
    firstExecutionId = executionId;
    return records.map(record => ({ captureId: record.capture_id, status: "retryable_defer", error: "injected" }));
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
  await store.appendEvent(record.capture_id, "retryable_defer", { attempt: 1, batchId: "batch-retry", eventEpochMs: 2000, error: "temporary" });
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

test("stale processing recovery preserves batch identity", () => workspace(async root => {
  const store = new CaptureStore(root);
  const { record } = await store.publish(input());
  await store.appendEvent(record.capture_id, "processing", { attempt: 2, batchId: "batch-original", eventEpochMs: 1000 });
  let observedBatch;
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 1, batchMaxChars: 1000, staleClaimMs: 100 }, async batchId => {
    observedBatch = batchId;
    return [{ captureId: record.capture_id, status: "admitted", statementIds: ["dream:stable"] }];
  });
  const result = await worker.runOnce(2000);
  assert.equal(result.batchId, "batch-original");
  assert.equal(observedBatch, "batch-original");
  assert.equal((await store.currentState(record.capture_id)).status, "admitted");
}));

test("terminal state interruption resumes only unfinished capture without duplicate admission", () => workspace(async root => {
  const store = new CaptureStore(root);
  const one = await store.publish(input());
  const two = await store.publish(input({ turnIdentity: "run-2", userUtf8: "second" }));
  const admitted = new Set();
  let absorptionCalls = 0;
  const absorb = async (_batchId, records) => {
    absorptionCalls += 1;
    return records.map(record => {
      admitted.add(record.capture_id);
      return { captureId: record.capture_id, status: "admitted", statementIds: [`dream:${record.capture_id}`] };
    });
  };
  const originalAppend = store.appendEvent.bind(store);
  let interrupted = false;
  store.appendEvent = async (captureId, status, options) => {
    if (!interrupted && captureId === two.record.capture_id && status === "admitted") {
      interrupted = true;
      throw new Error("process stopped before terminal state write");
    }
    return originalAppend(captureId, status, options);
  };
  const first = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, absorb);
  await assert.rejects(first.runOnce(2000), /terminal state write/);
  const originalBatch = (await store.currentState(two.record.capture_id)).batch_id;
  store.appendEvent = originalAppend;
  const restarted = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 1000, staleClaimMs: 100 }, absorb);
  const resumed = await restarted.runOnce(3000);
  assert.equal(resumed.batchId, originalBatch);
  assert.equal(resumed.captureCount, 1);
  assert.equal((await store.currentState(one.record.capture_id)).status, "admitted");
  assert.equal((await store.currentState(two.record.capture_id)).status, "admitted");
  assert.equal(admitted.size, 2);
  assert.equal(absorptionCalls, 2);
}));

test("diagnose reports retry deadline oldest backlog and stale processing", () => workspace(async root => {
  const store = new CaptureStore(root);
  const retry = await store.publish(input({ capturedEpochMs: 1000 }));
  const processing = await store.publish(input({ turnIdentity: "run-2", capturedEpochMs: 1500 }));
  await store.appendEvent(retry.record.capture_id, "retryable_defer", { attempt: 2, batchId: "batch", eventEpochMs: 3000, error: "temporary" });
  await store.appendEvent(processing.record.capture_id, "processing", { attempt: 1, batchId: "batch-2", eventEpochMs: 2000 });
  const diagnostic = await store.diagnose(5000, 1000, 2000);
  assert.equal(diagnostic.pending_capture_count, 2);
  assert.equal(diagnostic.oldest_pending_age_ms, 4000);
  assert.equal(diagnostic.next_retry_epoch_ms, 5000);
  assert.equal(diagnostic.stale_processing_count, 1);
  assert.equal(diagnostic.state_counts.retryable_defer, 1);
  assert.equal(diagnostic.state_counts.processing, 1);
}));
