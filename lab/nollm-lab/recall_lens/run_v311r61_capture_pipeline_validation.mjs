import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const repo = path.resolve(process.argv[2] ?? ".");
const { AbsorptionWorker, CaptureStore } = await import(
  pathToFileURL(path.join(repo, "integrations/openclaw/formation-loop/dist/capture.js")).href
);
const root = fs.mkdtempSync(path.join(os.tmpdir(), "nollm-v311r61-capture-"));

function input(run, user) {
  return {
    scopeKey: "scope", workspaceKey: "workspace", sessionKey: "session",
    turnIdentity: run, mainRunIdentity: run, userUtf8: user,
    assistantUtf8: "assistant source", capturedEpochMs: 1000,
    profileId: "active-memory", provider: "offline", model: "synthetic",
  };
}

try {
  const store = new CaptureStore(root);
  const evidenceInputs = [
    ["password-shape", "synthetic password=4815"],
    ["medical", "medical check Friday"],
    ["error", { error: "invalid state", retryable: true }],
    ["long-json", { rows: Array.from({ length: 64 }, (_, index) => ({ index, value: `row-${index}` })) }],
    ["empty", ""],
    ["binary", Buffer.from([0, 255, 17, 128])],
  ];
  const evidence = [];
  for (const [callId, result] of evidenceInputs) {
    const published = await store.publishToolEvidence({
      scopeKey: "scope", workspaceKey: "workspace", sessionKey: "session",
      mainRunIdentity: "run-a", toolCallId: callId, toolName: "host_tool",
      result, succeeded: callId !== "error", visibility: "main_agent_visible",
      observedEpochMs: 900,
    });
    const reopened = await store.readToolEvidence(published.record.tool_evidence_id);
    const replayed = await store.publishToolEvidence({
      scopeKey: "scope", workspaceKey: "workspace", sessionKey: "session",
      mainRunIdentity: "run-a", toolCallId: callId, toolName: "host_tool",
      result, succeeded: callId !== "error", visibility: "main_agent_visible",
      observedEpochMs: 900,
    });
    assert.equal(replayed.replayed, true);
    assert.deepEqual(reopened, replayed.record);
    evidence.push(reopened);
  }
  const a = await store.publish(input("run-a", "source A"));
  const b = await store.publish(input("run-b", "source B"));
  await store.publishDirective({
    captureId: a.record.capture_id, mainRunIdentity: "run-a", assistantRoleMode: "source",
    toolEvidenceIds: evidence.map(item => item.tool_evidence_id), sequence: 1, finalized: true,
  });
  await store.publishDirective({
    captureId: b.record.capture_id, mainRunIdentity: "run-b", assistantRoleMode: "source",
    sequence: 1, finalized: true,
  });
  const aIds = Array.from({ length: 20 }, (_, index) => `statement:a:${String(index).padStart(2, "0")}`);
  const observedOrder = [];
  const worker = new AbsorptionWorker(store, {
    batchMaxCaptures: 2, batchMaxChars: 1000, staleClaimMs: 1000,
  }, async (_batch, records) => {
    observedOrder.push(...records.map(record => record.capture_id));
    return records.map(record => record.capture_id === a.record.capture_id
      ? { captureId: record.capture_id, status: "retryable_defer", statementIds: aIds, error: "continue later" }
      : { captureId: record.capture_id, status: "admitted", statementIds: ["statement:b:00"] });
  });
  await worker.runOnce(40000);
  const aState = await store.currentState(a.record.capture_id);
  const bState = await store.currentState(b.record.capture_id);
  assert.equal(aState.status, "retryable_defer");
  assert.equal(bState.status, "admitted");
  assert.deepEqual(aState.statement_ids, aIds);
  assert.deepEqual(bState.statement_ids, ["statement:b:00"]);
  assert.deepEqual(observedOrder, [...observedOrder].sort());
  console.log(JSON.stringify({
    schema_version: "nollm_v311r61_capture_pipeline_validation_v1",
    event: "capture_pipeline",
    tool_evidence_count: evidence.length,
    tool_encodings: [...new Set(evidence.map(item => item.result_encoding))].sort(),
    exact_reopen_verified: true,
    content_category_classifier_calls: 0,
    capture_a_status: aState.status,
    capture_a_statement_count: aState.statement_ids.length,
    capture_b_status: bState.status,
    capture_b_statement_count: bState.statement_ids.length,
    capture_b_contains_a_statement: bState.statement_ids.some(id => id.startsWith("statement:a:")),
    candidate_order_deterministic: true,
    provider_calls: 0,
  }));
} finally {
  fs.rmSync(root, { recursive: true, force: true });
}
