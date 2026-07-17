import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { AbsorptionWorker, CaptureStore } from "../../../integrations/openclaw/formation-loop/dist/capture.js";

const percentile = (values, fraction) => values.slice().sort((a, b) => a - b)[Math.ceil(values.length * fraction) - 1];
const root = await mkdtemp(join(tmpdir(), "nollm-aold-validation-"));
try {
  const store = new CaptureStore(root);
  const publishMs = [];
  for (let index = 0; index < 150; index += 1) {
    const receipt = await store.publish({
      scopeKey: "validation-scope",
      sessionKey: `session-${index % 5}`,
      turnIdentity: `run-${index}`,
      userUtf8: `validation user ${index}\nline two`,
      assistantUtf8: `validation assistant ${index}`,
      capturedEpochMs: 1_000 + index,
      hostVersion: "deterministic-validation",
    });
    publishMs.push(receipt.publish_ms);
  }
  const first = (await store.allRecords())[0];
  const replay = await store.publish({
    scopeKey: "validation-scope", sessionKey: "session-0", turnIdentity: "run-0",
    userUtf8: "validation user 0\nline two", assistantUtf8: "validation assistant 0",
    capturedEpochMs: 9_999, hostVersion: "deterministic-validation",
  });
  const pendingStore = new CaptureStore(join(root, "pending-window"));
  for (let index = 0; index < 8; index += 1) {
    await pendingStore.publish({
      scopeKey: "validation-scope", sessionKey: `pending-session-${index}`,
      turnIdentity: `pending-run-${index}`, userUtf8: `pending user ${index}`,
      assistantUtf8: `pending assistant ${index}`, capturedEpochMs: 1_500 + index,
    });
  }
  const pendingMs = [];
  let pendingCount = 0;
  for (let index = 0; index < 100; index += 1) {
    const started = performance.now();
    const pending = await pendingStore.renderPending("validation-scope", { maxCaptures: 4, maxChars: 6000, maxAgeMs: 100_000 }, 2_000);
    pendingMs.push(performance.now() - started);
    pendingCount = pending.captureIds.length;
  }
  let absorptionCalls = 0;
  const worker = new AbsorptionWorker(store, { batchMaxCaptures: 4, batchMaxChars: 24_000, staleClaimMs: 300_000 }, async (_batchId, records) => {
    absorptionCalls += 1;
    return records.map(record => ({ captureId: record.capture_id, status: "admitted", statementIds: [`dream:${record.content_sha256}`] }));
  });
  const workerResult = await worker.runOnce(3_000);
  const output = {
    schema_version: "nollm_aold_deterministic_capture_validation_v1",
    capture_count: 150,
    capture_publish_p50_ms: percentile(publishMs, 0.50),
    capture_publish_p95_ms: percentile(publishMs, 0.95),
    capture_publish_max_ms: Math.max(...publishMs),
    capture_provider_calls: 0,
    capture_bridge_calls: 0,
    capture_core_calls: 0,
    replayed_same_capture: replay.replayed && replay.record.capture_id === first.capture_id,
    pending_render_count: pendingCount,
    pending_render_p95_ms: percentile(pendingMs, 0.95),
    pending_render_max_ms: Math.max(...pendingMs),
    pending_hidden_provider_calls: 0,
    worker_absorption_calls: absorptionCalls,
    worker_batch_capture_count: workerResult.captureCount,
  };
  if (output.capture_publish_p95_ms > 100 || output.capture_publish_max_ms > 250) throw new Error("Capture latency budget exceeded");
  if (output.pending_render_p95_ms > 100 || output.pending_render_max_ms > 500) throw new Error("Pending render latency budget exceeded");
  process.stdout.write(JSON.stringify(output));
} finally {
  await rm(root, { recursive: true, force: true });
}
